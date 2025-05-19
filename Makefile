.PHONY: help setup

help: ## 명령어 목록을 출력합니다.
@grep -E '^[a-zA-Z_-]+:.*?## .+' Makefile | awk 'BEGIN {FS=":.*?## "}; {printf "%-15s %s\n", $$1, $$2}'

setup: ## 개발 의존성을 설치합니다.
@if [ -f poetry.lock ] || grep -q "\[tool.poetry\]" pyproject.toml 2>/dev/null; then \
poetry install; \
else \
pip install -e .[dev]; \
fi
