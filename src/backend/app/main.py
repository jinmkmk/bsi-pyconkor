from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import date
import logging
import time
from uuid import uuid4

from fastapi import Depends, FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.clients.neis import NeisClient
from app.config import Settings
from app.errors import (
    ApiError,
    NeisResponseError,
    NeisTimeoutError,
    NeisUnavailableError,
)
from app.models import MealPage, SchoolPage
from app.services.lunch import LunchService


logger = logging.getLogger("school_lunch")


def create_app(
    settings: Settings | None = None,
    service: LunchService | None = None,
) -> FastAPI:
    resolved_settings = settings or Settings.from_env()

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        resolved_settings.validate()
        yield

    application = FastAPI(
        title="급식 배틀 API",
        version="0.1.0",
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[resolved_settings.frontend_origin],
        allow_methods=["GET"],
        allow_headers=["Content-Type", "X-Request-ID"],
    )
    resolved_service = service or LunchService(NeisClient(resolved_settings))

    def get_service() -> LunchService:
        return resolved_service

    @application.middleware("http")
    async def request_context(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid4())
        request.state.request_id = request_id
        started_at = time.perf_counter()
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "request path=%s status=%s duration_ms=%.1f",
            request.url.path,
            response.status_code,
            (time.perf_counter() - started_at) * 1000,
        )
        return response

    def error_response(request: Request, error: ApiError) -> JSONResponse:
        return JSONResponse(
            status_code=error.status_code,
            content={
                "error": {
                    "code": error.code,
                    "message": error.message,
                    "requestId": getattr(request.state, "request_id", str(uuid4())),
                    **({"fields": error.fields} if error.fields else {}),
                }
            },
        )

    @application.exception_handler(ApiError)
    async def handle_api_error(request: Request, exc: ApiError) -> JSONResponse:
        return error_response(request, exc)

    @application.exception_handler(RequestValidationError)
    async def handle_validation(
        request: Request, _: RequestValidationError
    ) -> JSONResponse:
        return error_response(
            request,
            ApiError(422, "VALIDATION_ERROR", "요청 값을 확인해 주세요."),
        )

    @application.exception_handler(NeisUnavailableError)
    async def handle_unavailable(
        request: Request, _: NeisUnavailableError
    ) -> JSONResponse:
        return error_response(
            request,
            ApiError(
                503,
                "SERVICE_UNAVAILABLE",
                "현재 급식 조회 서비스를 사용할 수 없습니다. 잠시 후 다시 시도해 주세요.",
            ),
        )

    @application.exception_handler(NeisTimeoutError)
    async def handle_timeout(
        request: Request, _: NeisTimeoutError
    ) -> JSONResponse:
        return error_response(
            request,
            ApiError(
                504,
                "UPSTREAM_TIMEOUT",
                "급식 조회 시간이 초과되었습니다. 다시 시도해 주세요.",
            ),
        )

    @application.exception_handler(NeisResponseError)
    async def handle_bad_response(
        request: Request, _: NeisResponseError
    ) -> JSONResponse:
        return error_response(
            request,
            ApiError(
                502,
                "UPSTREAM_ERROR",
                "급식 정보를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.",
            ),
        )

    @application.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @application.get("/api/schools", response_model=SchoolPage)
    async def search_schools(
        query: str = Query(min_length=1),
        page: int = Query(1, ge=1),
        page_size: int = Query(20, alias="pageSize", ge=1, le=100),
        lunch_service: LunchService = Depends(get_service),
    ) -> SchoolPage:
        normalized_query = query.strip()
        if not normalized_query:
            raise ApiError(
                422,
                "VALIDATION_ERROR",
                "학교 이름을 입력해 주세요.",
                {"query": "공백이 아닌 학교 이름이 필요합니다."},
            )
        return await lunch_service.search_schools(
            normalized_query, page, page_size
        )

    @application.get(
        "/api/meals",
        response_model=MealPage,
        response_model_by_alias=True,
    )
    async def get_meals(
        office_code: str = Query(alias="officeCode", min_length=1),
        school_code: str = Query(alias="schoolCode", min_length=1),
        date_from: date = Query(alias="from"),
        date_to: date = Query(alias="to"),
        lunch_service: LunchService = Depends(get_service),
    ) -> MealPage:
        return await lunch_service.get_meals(
            office_code, school_code, date_from, date_to
        )

    return application


app = create_app()
