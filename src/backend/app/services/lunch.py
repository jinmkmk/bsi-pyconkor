from datetime import date
import html
import re
from typing import Any, Mapping

from app.clients.neis import NeisClient
from app.errors import ApiError, NeisResponseError
from app.models import Meal, MealPage, School, SchoolPage, SchoolSummary


BREAK_PATTERN = re.compile(r"<br\s*/?>", re.IGNORECASE)
TAG_PATTERN = re.compile(r"<[^>]+>")
ALLERGEN_PATTERN = re.compile(r"\s*\((?:\d+[.\s]*)+\)\s*$")


def validate_date_range(date_from: date, date_to: date) -> None:
    if date_from > date_to:
        raise ApiError(
            400,
            "INVALID_DATE_RANGE",
            "시작일은 종료일보다 늦을 수 없습니다.",
            {"from": "날짜 범위를 확인해 주세요."},
        )
    if (date_to - date_from).days + 1 > 31:
        raise ApiError(
            400,
            "DATE_RANGE_TOO_LONG",
            "급식은 최대 31일까지 조회할 수 있습니다.",
            {"to": "종료일을 시작일로부터 31일 이내로 선택해 주세요."},
        )


def normalize_dishes(value: Any) -> list[str]:
    if not isinstance(value, str):
        return []
    normalized = BREAK_PATTERN.sub("\n", value)
    normalized = html.unescape(TAG_PATTERN.sub("", normalized))
    return [
        ALLERGEN_PATTERN.sub("", line).strip()
        for line in normalized.splitlines()
        if ALLERGEN_PATTERN.sub("", line).strip()
    ]


class LunchService:
    def __init__(self, client: NeisClient) -> None:
        self._client = client

    async def search_schools(
        self, query: str, page: int, page_size: int
    ) -> SchoolPage:
        rows, total_count = await self._client.search_schools(
            query, page, page_size
        )
        items = [self._school_from_row(row) for row in rows]
        return SchoolPage(
            items=items,
            totalCount=total_count,
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
        validate_date_range(date_from, date_to)
        rows = await self._client.get_meals(
            office_code,
            school_code,
            date_from.strftime("%Y%m%d"),
            date_to.strftime("%Y%m%d"),
        )
        lunch_rows = [
            row for row in rows if str(row.get("MMEAL_SC_CODE", "2")) == "2"
        ]
        items = sorted(
            (self._meal_from_row(row) for row in lunch_rows),
            key=lambda meal: meal.date,
        )
        school_name = next(
            (
                str(row.get("SCHUL_NM"))
                for row in lunch_rows
                if row.get("SCHUL_NM")
            ),
            "선택한 학교",
        )
        return MealPage(
            school=SchoolSummary(
                officeCode=office_code,
                schoolCode=school_code,
                name=school_name,
            ),
            from_=date_from,
            to=date_to,
            items=items,
        )

    @staticmethod
    def _school_from_row(row: Mapping[str, Any]) -> School:
        try:
            return School(
                officeCode=str(row["ATPT_OFCDC_SC_CODE"]),
                schoolCode=str(row["SD_SCHUL_CODE"]),
                name=str(row["SCHUL_NM"]),
                region=str(row.get("LCTN_SC_NM", "")),
                schoolType=str(row.get("SCHUL_KND_SC_NM", "")),
                address=str(row.get("ORG_RDNMA", "")),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise NeisResponseError from exc

    @staticmethod
    def _meal_from_row(row: Mapping[str, Any]) -> Meal:
        try:
            raw_date = str(row["MLSV_YMD"])
            return Meal(
                date=date(
                    int(raw_date[0:4]), int(raw_date[4:6]), int(raw_date[6:8])
                ),
                mealType="중식",
                dishes=normalize_dishes(row.get("DDISH_NM")),
                calories=str(row["CAL_INFO"]) if row.get("CAL_INFO") else None,
                nutrition=str(row["NTR_INFO"]) if row.get("NTR_INFO") else None,
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise NeisResponseError from exc
