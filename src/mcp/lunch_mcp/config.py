"""Runtime configuration for the MCP server."""

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    neis_api_key: str
    neis_base_url: str = "https://open.neis.go.kr"
    request_timeout: float = 8.0
    host: str = "0.0.0.0"
    port: int = 8001

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            neis_api_key=os.getenv("NEIS_API_KEY", "").strip(),
            neis_base_url=os.getenv(
                "NEIS_BASE_URL", "https://open.neis.go.kr"
            ).rstrip("/"),
            request_timeout=float(os.getenv("NEIS_REQUEST_TIMEOUT", "8")),
            host=os.getenv("MCP_HOST", "0.0.0.0"),
            port=int(os.getenv("MCP_PORT", "8001")),
        )

    def validate(self) -> None:
        if not self.neis_api_key:
            raise RuntimeError("NEIS_API_KEY 환경 변수가 필요합니다.")
        if self.request_timeout <= 0:
            raise RuntimeError("NEIS_REQUEST_TIMEOUT은 0보다 커야 합니다.")
        if not 1 <= self.port <= 65535:
            raise RuntimeError("MCP_PORT는 1부터 65535 사이여야 합니다.")
