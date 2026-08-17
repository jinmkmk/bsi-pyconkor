#!/usr/bin/env sh
set -eu

if [ ! -f .env ]; then
  echo ".env 파일이 없습니다. .env.example을 복사하고 NEIS_API_KEY를 입력해 주세요." >&2
  exit 1
fi

if ! grep -Eq '^[[:space:]]*NEIS_API_KEY[[:space:]]*=[[:space:]]*.+$' .env; then
  echo ".env의 NEIS_API_KEY에 발급받은 인증키를 입력해 주세요." >&2
  exit 1
fi

docker compose up --build
