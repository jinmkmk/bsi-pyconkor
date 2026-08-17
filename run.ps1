$ErrorActionPreference = "Stop"

if (-not (Test-Path ".env")) {
    throw ".env 파일이 없습니다. .env.example을 복사하고 NEIS_API_KEY를 입력해 주세요."
}

$apiKeyLine = Get-Content ".env" | Where-Object { $_ -match '^\s*NEIS_API_KEY\s*=\s*.+$' }
if (-not $apiKeyLine) {
    throw ".env의 NEIS_API_KEY에 발급받은 인증키를 입력해 주세요."
}

docker compose up --build
