from datetime import date
from datetime import timedelta

from mcp.shared.memory import create_connected_server_and_client_session

from lunch_mcp.config import Settings
from lunch_mcp.errors import SchoolNotFoundError
from lunch_mcp.models import LunchResult, Meal, School, SchoolSearchResult
from lunch_mcp.server import create_server


class FakeService:
    async def search_schools(
        self, query: str, limit: int = 20
    ) -> SchoolSearchResult:
        if query == "없음":
            raise SchoolNotFoundError
        return SchoolSearchResult(
            schools=[
                School(
                    name="예시고등학교",
                    office_name="서울특별시교육청",
                    office_code="B10",
                    school_code="7010569",
                    region="서울특별시",
                    school_type="고등학교",
                    address="서울특별시 예시로 1",
                )
            ],
            total_count=1,
        )

    async def get_lunches(
        self,
        office_code: str,
        school_code: str,
        date_from: date,
        date_to: date,
    ) -> LunchResult:
        return LunchResult(
            school_name="예시고등학교",
            office_code=office_code,
            school_code=school_code,
            date_from=date_from,
            date_to=date_to,
            meals=[Meal(date=date_from, dishes=["현미밥", "미역국"])],
        )


def test_server_enables_dns_rebinding_protection() -> None:
    server = create_server(
        settings=Settings(neis_api_key="test-key"),
        service=FakeService(),
    )

    security = server.settings.transport_security
    assert security is not None
    assert security.enable_dns_rebinding_protection is True
    assert "localhost:*" in security.allowed_hosts


async def test_mcp_client_lists_and_calls_tools() -> None:
    server = create_server(
        settings=Settings(neis_api_key="test-key"),
        service=FakeService(),
    )

    async with create_connected_server_and_client_session(
        server, read_timeout_seconds=timedelta(seconds=5)
    ) as session:
        tools = await session.list_tools()
        result = await session.call_tool(
            "search_schools", {"query": "예시", "limit": 5}
        )

    assert {tool.name for tool in tools.tools} == {
        "search_schools",
        "get_school_lunches",
    }
    assert result.isError is False
    assert result.structuredContent is not None
    assert result.structuredContent["schools"][0]["office_code"] == "B10"


async def test_domain_error_becomes_mcp_tool_error() -> None:
    server = create_server(
        settings=Settings(neis_api_key="test-key"),
        service=FakeService(),
    )

    async with create_connected_server_and_client_session(
        server, read_timeout_seconds=timedelta(seconds=5)
    ) as session:
        result = await session.call_tool("search_schools", {"query": "없음"})

    assert result.isError is True
    assert "SCHOOL_NOT_FOUND" in result.content[0].text
