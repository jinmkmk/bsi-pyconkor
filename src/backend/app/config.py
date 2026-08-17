from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    neis_api_key: str
    neis_base_url: str
    frontend_origin: str
    request_timeout: float = 8.0

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            neis_api_key=os.getenv("NEIS_API_KEY", "").strip(),
            neis_base_url=os.getenv(
                "NEIS_BASE_URL", "https://open.neis.go.kr"
            ).rstrip("/"),
            frontend_origin=os.getenv(
                "FRONTEND_ORIGIN", "http://localhost:5173"
            ).rstrip("/"),
        )

    def validate(self) -> None:
        if not self.neis_api_key:
            raise RuntimeError("NEIS_API_KEY 환경 변수가 필요합니다.")
