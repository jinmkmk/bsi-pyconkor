from collections.abc import Mapping
from typing import Any

import httpx

from app.config import Settings
from app.errors import (
    NeisResponseError,
    NeisTimeoutError,
    NeisUnavailableError,
)


NO_DATA_CODE = "INFO-200"
UNAVAILABLE_CODES = {"ERROR-290", "ERROR-300", "ERROR-301", "INFO-300"}


class NeisClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def search_schools(
        self, query: str, page: int, page_size: int
    ) -> tuple[list[Mapping[str, Any]], int]:
        data = await self._get(
            "schoolInfo",
            {"SCHUL_NM": query, "pIndex": page, "pSize": page_size},
        )
        return self._extract_rows(data, "schoolInfo")

    async def get_meals(
        self,
        office_code: str,
        school_code: str,
        date_from: str,
        date_to: str,
    ) -> list[Mapping[str, Any]]:
        data = await self._get(
            "mealServiceDietInfo",
            {
                "ATPT_OFCDC_SC_CODE": office_code,
                "SD_SCHUL_CODE": school_code,
                "MMEAL_SC_CODE": "2",
                "MLSV_FROM_YMD": date_from,
                "MLSV_TO_YMD": date_to,
                "pIndex": 1,
                "pSize": 100,
            },
        )
        rows, _ = self._extract_rows(data, "mealServiceDietInfo")
        return rows

    async def _get(self, endpoint: str, params: dict[str, str | int]) -> Any:
        request_params = {
            "KEY": self._settings.neis_api_key,
            "Type": "json",
            **params,
        }
        try:
            async with httpx.AsyncClient(
                base_url=self._settings.neis_base_url,
                timeout=self._settings.request_timeout,
            ) as client:
                response = await client.get(f"/hub/{endpoint}", params=request_params)
                response.raise_for_status()
                return response.json()
        except httpx.TimeoutException as exc:
            raise NeisTimeoutError from exc
        except (httpx.HTTPError, ValueError) as exc:
            raise NeisResponseError from exc

    @staticmethod
    def _extract_rows(
        payload: Any, key: str
    ) -> tuple[list[Mapping[str, Any]], int]:
        if not isinstance(payload, Mapping):
            raise NeisResponseError

        top_result = payload.get("RESULT")
        if isinstance(top_result, Mapping):
            NeisClient._raise_for_result(top_result)
            return [], 0

        sections = payload.get(key)
        if not isinstance(sections, list):
            raise NeisResponseError

        rows: list[Mapping[str, Any]] = []
        total_count = 0
        for section in sections:
            if not isinstance(section, Mapping):
                raise NeisResponseError
            head = section.get("head")
            if isinstance(head, list):
                for item in head:
                    if not isinstance(item, Mapping):
                        continue
                    if "list_total_count" in item:
                        total_count = int(item["list_total_count"])
                    result = item.get("RESULT")
                    if isinstance(result, Mapping):
                        NeisClient._raise_for_result(result)
            section_rows = section.get("row")
            if isinstance(section_rows, list):
                if not all(isinstance(row, Mapping) for row in section_rows):
                    raise NeisResponseError
                rows.extend(section_rows)
        return rows, total_count

    @staticmethod
    def _raise_for_result(result: Mapping[str, Any]) -> None:
        code = str(result.get("CODE", ""))
        if code in {"INFO-000", NO_DATA_CODE}:
            return
        if code in UNAVAILABLE_CODES or code.startswith("ERROR-3"):
            raise NeisUnavailableError
        raise NeisResponseError
