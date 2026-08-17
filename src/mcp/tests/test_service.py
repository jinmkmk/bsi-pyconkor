from datetime import date

import pytest

from lunch_mcp.errors import (
    InvalidInputError,
    MealsNotFoundError,
    SchoolNotFoundError,
)
from lunch_mcp.service import LunchService, normalize_dishes


class FakeClient:
    def __init__(self) -> None:
        self.school_rows = [
            {
                "SCHUL_NM": "예시고등학교",
                "ATPT_OFCDC_SC_NM": "서울특별시교육청",
                "ATPT_OFCDC_SC_CODE": "B10",
                "SD_SCHUL_CODE": "7010569",
                "LCTN_SC_NM": "서울특별시",
                "SCHUL_KND_SC_NM": "고등학교",
                "ORG_RDNMA": "서울특별시 예시로 1",
            }
        ]
        self.meal_rows = [
            {
                "SCHUL_NM": "예시고등학교",
                "MMEAL_SC_CODE": "2",
                "MLSV_YMD": "20260818",
                "DDISH_NM": "현미밥 (1. 5.)<br/>미역국",
                "CAL_INFO": "650 Kcal",
            }
        ]

    async def search_schools(self, query: str, limit: int):
        return self.school_rows, len(self.school_rows)

    async def get_lunches(
        self, office_code: str, school_code: str, date_from: str, date_to: str
    ):
        return self.meal_rows


def test_normalize_dishes_removes_html_and_allergen_numbers() -> None:
    assert normalize_dishes("현미밥 (1. 5.)<br/>미역국<br>배추김치") == [
        "현미밥",
        "미역국",
        "배추김치",
    ]


async def test_search_schools_returns_identifiers() -> None:
    result = await LunchService(FakeClient()).search_schools("예시")

    assert result.schools[0].office_name == "서울특별시교육청"
    assert result.schools[0].office_code == "B10"
    assert result.schools[0].school_code == "7010569"


async def test_search_schools_rejects_empty_result() -> None:
    client = FakeClient()
    client.school_rows = []

    with pytest.raises(SchoolNotFoundError):
        await LunchService(client).search_schools("없는학교")


async def test_get_lunches_returns_sorted_normalized_meals() -> None:
    client = FakeClient()
    client.meal_rows.insert(
        0,
        {
            "SCHUL_NM": "예시고등학교",
            "MMEAL_SC_CODE": "2",
            "MLSV_YMD": "20260819",
            "DDISH_NM": "보리밥<br>된장국",
        },
    )

    result = await LunchService(client).get_lunches(
        "B10", "7010569", date(2026, 8, 18), date(2026, 8, 19)
    )

    assert [meal.date.isoformat() for meal in result.meals] == [
        "2026-08-18",
        "2026-08-19",
    ]
    assert result.meals[0].dishes == ["현미밥", "미역국"]


async def test_get_lunches_rejects_no_meal_result() -> None:
    client = FakeClient()
    client.meal_rows = []

    with pytest.raises(MealsNotFoundError):
        await LunchService(client).get_lunches(
            "B10", "7010569", date(2026, 8, 18), date(2026, 8, 18)
        )


async def test_get_lunches_rejects_invalid_date_range() -> None:
    with pytest.raises(InvalidInputError, match="시작일"):
        await LunchService(FakeClient()).get_lunches(
            "B10", "7010569", date(2026, 8, 19), date(2026, 8, 18)
        )
