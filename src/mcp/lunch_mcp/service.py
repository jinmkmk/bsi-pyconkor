from collections.abc import Mapping
from datetime import date
import html
import re
from typing import Any

from lunch_mcp.errors import (
    InvalidInputError,
    MealsNotFoundError,
    NeisResponseError,
    SchoolNotFoundError,
)
from lunch_mcp.models import LunchResult, Meal, School, SchoolSearchResult
from lunch_mcp.neis import NeisClient


BREAK_PATTERN = re.compile(r"<br\s*/?>", re.IGNORECASE)
TAG_PATTERN = re.compile(r"<[^>]+>")
ALLERGEN_PATTERN = re.compile(r"\s*\((?:\d+[.\s]*)+\)\s*$")
CODE_PATTERN = re.compile(r"^[A-Za-z0-9]+$")


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


def validate_date_range(date_from: date, date_to: date) -> None:
    if date_from > date_to:
        raise InvalidInputError("시작일은 종료일보다 늦을 수 없습니다.")
    if (date_to - date_from).days + 1 > 31:
        raise InvalidInputError("급식은 최대 31일까지 조회할 수 있습니다.")


def validate_code(value: str, label: str) -> str:
    normalized = value.strip()
    if not normalized or not CODE_PATTERN.fullmatch(normalized):
        raise InvalidInputError(f"{label} 형식을 확인해 주세요.")
    return normalized


class LunchService:
    def __init__(self, client: NeisClient) -> None:
        self._client = client

    async def search_schools(
        self, query: str, limit: int = 20
    ) -> SchoolSearchResult:
        normalized_query = query.strip()
        if not normalized_query:
            raise InvalidInputError("공백이 아닌 학교 이름을 입력해 주세요.")
        if not 1 <= limit <= 100:
            raise InvalidInputError("검색 결과 수는 1부터 100 사이여야 합니다.")

        rows, total_count = await self._client.search_schools(
            normalized_query, limit
        )
        if not rows:
            raise SchoolNotFoundError
        schools = [self._school_from_row(row) for row in rows]
        return SchoolSearchResult(
            schools=schools,
            total_count=max(total_count, len(schools)),
        )

    async def get_lunches(
        self,
        office_code: str,
        school_code: str,
        date_from: date,
        date_to: date,
    ) -> LunchResult:
        normalized_office_code = validate_code(office_code, "교육청 코드")
        normalized_school_code = validate_code(school_code, "학교 코드")
        validate_date_range(date_from, date_to)
        rows = await self._client.get_lunches(
            normalized_office_code,
            normalized_school_code,
            date_from.strftime("%Y%m%d"),
            date_to.strftime("%Y%m%d"),
        )
        lunch_rows = [
            row for row in rows if str(row.get("MMEAL_SC_CODE", "2")) == "2"
        ]
        if not lunch_rows:
            raise MealsNotFoundError
        meals = sorted(
            (self._meal_from_row(row) for row in lunch_rows),
            key=lambda meal: meal.date,
        )
        school_name = next(
            (
                str(row["SCHUL_NM"])
                for row in lunch_rows
                if row.get("SCHUL_NM")
            ),
            "선택한 학교",
        )
        return LunchResult(
            school_name=school_name,
            office_code=normalized_office_code,
            school_code=normalized_school_code,
            date_from=date_from,
            date_to=date_to,
            meals=meals,
        )

    @staticmethod
    def _school_from_row(row: Mapping[str, Any]) -> School:
        try:
            return School(
                name=str(row["SCHUL_NM"]),
                office_name=str(row.get("ATPT_OFCDC_SC_NM", "")),
                office_code=str(row["ATPT_OFCDC_SC_CODE"]),
                school_code=str(row["SD_SCHUL_CODE"]),
                region=str(row.get("LCTN_SC_NM", "")),
                school_type=str(row.get("SCHUL_KND_SC_NM", "")),
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
                dishes=normalize_dishes(row.get("DDISH_NM")),
                calories=str(row["CAL_INFO"]) if row.get("CAL_INFO") else None,
                nutrition=str(row["NTR_INFO"]) if row.get("NTR_INFO") else None,
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise NeisResponseError from exc
