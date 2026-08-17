from collections.abc import Mapping
from datetime import date
from typing import Any

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.models import Meal, MealPage, School, SchoolPage, SchoolSummary
from app.services.lunch import LunchService


class FakeService(LunchService):
    def __init__(self) -> None:
        pass

    async def search_schools(
        self, query: str, page: int, page_size: int
    ) -> SchoolPage:
        if query == "없음":
            return SchoolPage(
                items=[], totalCount=0, page=page, pageSize=page_size
            )
        return SchoolPage(
            items=[
                School(
                    officeCode="B10",
                    schoolCode="7010569",
                    name="예시고등학교",
                    region="서울특별시",
                    schoolType="고등학교",
                    address="서울특별시 예시로 1",
                )
            ],
            totalCount=1,
            page=page,
            pageSize=page_size,
        )

    async def get_meals(
        self,
        office_code: str,
        school_code: str,
        date_from: date,
        date_to: date,
    ) -> MealPage:
        from app.services.lunch import validate_date_range

        validate_date_range(date_from, date_to)
        return MealPage(
            school=SchoolSummary(
                officeCode=office_code,
                schoolCode=school_code,
                name="예시고등학교",
            ),
            from_=date_from,
            to=date_to,
            items=[
                Meal(
                    date=date_from,
                    mealType="중식",
                    dishes=["현미밥", "미역국"],
                    calories="650 Kcal",
                )
            ],
        )


def client() -> TestClient:
    settings = Settings("test-key", "https://example.test", "http://localhost:5173")
    return TestClient(create_app(settings, FakeService()))


def test_search_schools_success() -> None:
    with client() as test_client:
        response = test_client.get("/api/schools", params={"query": "예시"})
    assert response.status_code == 200
    assert response.json()["items"][0]["name"] == "예시고등학교"


def test_search_schools_rejects_blank_query() -> None:
    with client() as test_client:
        response = test_client.get("/api/schools", params={"query": "   "})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_get_meals_returns_internal_contract() -> None:
    params: Mapping[str, Any] = {
        "officeCode": "B10",
        "schoolCode": "7010569",
        "from": "2026-08-17",
        "to": "2026-08-17",
    }
    with client() as test_client:
        response = test_client.get("/api/meals", params=params)
    assert response.status_code == 200
    assert response.json()["items"][0]["dishes"] == ["현미밥", "미역국"]


def test_get_meals_rejects_long_range() -> None:
    with client() as test_client:
        response = test_client.get(
            "/api/meals",
            params={
                "officeCode": "B10",
                "schoolCode": "7010569",
                "from": "2026-08-01",
                "to": "2026-09-01",
            },
        )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "DATE_RANGE_TOO_LONG"
