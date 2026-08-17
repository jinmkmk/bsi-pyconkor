"""Safe domain errors exposed as MCP tool errors."""


class LunchMcpError(Exception):
    code = "INTERNAL_ERROR"
    safe_message = "요청을 처리하지 못했습니다."


class InvalidInputError(LunchMcpError):
    code = "INVALID_INPUT"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.safe_message = message


class SchoolNotFoundError(LunchMcpError):
    code = "SCHOOL_NOT_FOUND"
    safe_message = "검색 결과가 없습니다. 학교 이름을 확인해 주세요."


class MealsNotFoundError(LunchMcpError):
    code = "MEALS_NOT_FOUND"
    safe_message = "선택한 기간에 등록된 중식 정보가 없습니다."


class NeisUnavailableError(LunchMcpError):
    code = "SERVICE_UNAVAILABLE"
    safe_message = "현재 급식 조회 서비스를 사용할 수 없습니다. 잠시 후 다시 시도해 주세요."


class NeisTimeoutError(LunchMcpError):
    code = "UPSTREAM_TIMEOUT"
    safe_message = "급식 조회 시간이 초과되었습니다. 다시 시도해 주세요."


class NeisResponseError(LunchMcpError):
    code = "UPSTREAM_ERROR"
    safe_message = "급식 정보를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요."
