from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import date

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ToolAnnotations
from starlette.requests import Request
from starlette.responses import JSONResponse

from lunch_mcp.config import Settings
from lunch_mcp.errors import LunchMcpError
from lunch_mcp.models import LunchResult, SchoolSearchResult
from lunch_mcp.neis import NeisClient
from lunch_mcp.service import LunchService


def create_server(
    settings: Settings | None = None,
    service: LunchService | None = None,
) -> FastMCP:
    resolved_settings = settings or Settings.from_env()
    resolved_service = service or LunchService(NeisClient(resolved_settings))

    @asynccontextmanager
    async def lifespan(_: FastMCP) -> AsyncIterator[None]:
        resolved_settings.validate()
        yield

    server = FastMCP(
        name="school-lunch",
        instructions=(
            "학교 이름으로 학교 식별 정보를 찾고, 선택한 학교의 중식 메뉴를 "
            "최대 31일 범위로 조회합니다."
        ),
        host=resolved_settings.host,
        port=resolved_settings.port,
        streamable_http_path="/mcp",
        stateless_http=True,
        json_response=True,
        lifespan=lifespan,
        transport_security=TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=["127.0.0.1:*", "localhost:*", "[::1]:*"],
            allowed_origins=[
                "http://127.0.0.1:*",
                "http://localhost:*",
                "http://[::1]:*",
            ],
        ),
    )
    read_only = ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    )

    @server.tool(
        name="search_schools",
        title="학교 검색",
        description=(
            "학교 이름 일부로 후보 학교를 검색합니다. 각 후보의 학교명, 교육청명과 "
            "교육청 코드, 학교 코드, 지역, 학교 종류, 주소를 반환합니다."
        ),
        annotations=read_only,
        structured_output=True,
    )
    async def search_schools(
        query: str,
        limit: int = 20,
    ) -> SchoolSearchResult:
        try:
            return await resolved_service.search_schools(query, limit)
        except LunchMcpError as exc:
            raise ToolError(f"{exc.code}: {exc.safe_message}") from exc

    @server.tool(
        name="get_school_lunches",
        title="학교 중식 조회",
        description=(
            "학교 검색에서 얻은 교육청 코드와 학교 코드, ISO 형식 시작일·종료일로 "
            "최대 31일의 날짜별 중식 메뉴를 조회합니다."
        ),
        annotations=read_only,
        structured_output=True,
    )
    async def get_school_lunches(
        office_code: str,
        school_code: str,
        date_from: date,
        date_to: date,
    ) -> LunchResult:
        try:
            return await resolved_service.get_lunches(
                office_code, school_code, date_from, date_to
            )
        except LunchMcpError as exc:
            raise ToolError(f"{exc.code}: {exc.safe_message}") from exc

    @server.custom_route("/health", methods=["GET"], include_in_schema=False)
    async def health(_: Request) -> JSONResponse:
        return JSONResponse({"status": "ok"})

    return server


mcp = create_server()


def main() -> None:
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
