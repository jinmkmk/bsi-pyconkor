import httpx
import pytest

from lunch_mcp.config import Settings
from lunch_mcp.errors import NeisTimeoutError, NeisUnavailableError
from lunch_mcp.neis import NeisClient


async def test_search_schools_calls_neis_contract() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/hub/schoolInfo"
        assert request.url.params["KEY"] == "test-key"
        assert request.url.params["SCHUL_NM"] == "예시"
        return httpx.Response(
            200,
            json={
                "schoolInfo": [
                    {
                        "head": [
                            {"list_total_count": 1},
                            {"RESULT": {"CODE": "INFO-000"}},
                        ]
                    },
                    {"row": [{"SCHUL_NM": "예시고등학교"}]},
                ]
            },
        )

    client = NeisClient(
        Settings(neis_api_key="test-key"),
        transport=httpx.MockTransport(handler),
    )

    rows, total = await client.search_schools("예시", 20)

    assert total == 1
    assert rows[0]["SCHUL_NM"] == "예시고등학교"


async def test_no_data_is_an_empty_result() -> None:
    client = NeisClient(
        Settings(neis_api_key="test-key"),
        transport=httpx.MockTransport(
            lambda _: httpx.Response(
                200, json={"RESULT": {"CODE": "INFO-200"}}
            )
        ),
    )

    rows, total = await client.search_schools("없는학교", 20)

    assert rows == []
    assert total == 0


async def test_unavailable_result_is_not_hidden_as_empty() -> None:
    client = NeisClient(
        Settings(neis_api_key="test-key"),
        transport=httpx.MockTransport(
            lambda _: httpx.Response(
                200, json={"RESULT": {"CODE": "ERROR-300"}}
            )
        ),
    )

    with pytest.raises(NeisUnavailableError):
        await client.search_schools("예시", 20)


async def test_timeout_is_mapped_without_request_details() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("secret request details", request=request)

    client = NeisClient(
        Settings(neis_api_key="test-key"),
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(NeisTimeoutError) as exc_info:
        await client.search_schools("예시", 20)

    assert "secret" not in str(exc_info.value)
