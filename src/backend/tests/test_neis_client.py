import pytest

from app.clients.neis import NeisClient
from app.errors import NeisResponseError, NeisUnavailableError


def test_extracts_rows_and_total_count() -> None:
    rows, total = NeisClient._extract_rows(
        {
            "schoolInfo": [
                {
                    "head": [
                        {"list_total_count": 1},
                        {"RESULT": {"CODE": "INFO-000", "MESSAGE": "정상"}},
                    ]
                },
                {"row": [{"SCHUL_NM": "예시고등학교"}]},
            ]
        },
        "schoolInfo",
    )
    assert total == 1
    assert rows == [{"SCHUL_NM": "예시고등학교"}]


def test_no_data_is_a_normal_empty_result() -> None:
    assert NeisClient._extract_rows(
        {"RESULT": {"CODE": "INFO-200", "MESSAGE": "데이터 없음"}},
        "schoolInfo",
    ) == ([], 0)


def test_authentication_error_is_unavailable() -> None:
    with pytest.raises(NeisUnavailableError):
        NeisClient._extract_rows(
            {"RESULT": {"CODE": "ERROR-290", "MESSAGE": "인증 실패"}},
            "schoolInfo",
        )


def test_unknown_result_is_not_hidden_as_empty() -> None:
    with pytest.raises(NeisResponseError):
        NeisClient._extract_rows(
            {"RESULT": {"CODE": "ERROR-999", "MESSAGE": "알 수 없는 오류"}},
            "schoolInfo",
        )
