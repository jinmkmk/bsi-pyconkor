from datetime import date

import pytest

from app.errors import ApiError
from app.services.lunch import normalize_dishes, validate_date_range


def test_normalize_dishes_removes_html_and_allergen_numbers() -> None:
    assert normalize_dishes("현미밥 (1. 5.)<br/>미역국<br>배추김치") == [
        "현미밥",
        "미역국",
        "배추김치",
    ]


def test_validate_date_range_rejects_reverse_range() -> None:
    with pytest.raises(ApiError, match="시작일"):
        validate_date_range(date(2026, 8, 18), date(2026, 8, 17))


def test_validate_date_range_rejects_more_than_31_days() -> None:
    with pytest.raises(ApiError, match="31일"):
        validate_date_range(date(2026, 8, 1), date(2026, 9, 1))
