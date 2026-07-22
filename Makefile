# Living Water Audio Control — developer Makefile
# Single virtualenv installs backend + player-agent + shared-contracts (LOCAL_MVP).

VENV ?= .venv
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
UV := $(shell command -v uv 2>/dev/null)

.DEFAULT_GOAL := help

.PHONY: help
help: ## Показать список команд
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

$(VENV):
	python3 -m venv $(VENV)

.PHONY: install
install: $(VENV) ## Установить все зависимости в единый venv
ifeq ($(UV),)
	$(PIP) install -U pip
	$(PIP) install -e ./packages/shared-contracts/python
	$(PIP) install -e './apps/backend[dev]'
	$(PIP) install -e './apps/player-agent[dev]'
else
	$(UV) pip install --python $(PY) -U pip
	$(UV) pip install --python $(PY) -e ./packages/shared-contracts/python
	$(UV) pip install --python $(PY) -e './apps/backend[dev]'
	$(UV) pip install --python $(PY) -e './apps/player-agent[dev]'
endif

.PHONY: migrate
migrate: ## Применить миграции БД
	cd apps/backend && ../../$(PY) -m alembic upgrade head

.PHONY: makemigration
makemigration: ## Создать новую миграцию (make makemigration m="msg")
	cd apps/backend && ../../$(PY) -m alembic revision --autogenerate -m "$(m)"

.PHONY: seed
seed: ## Засеять стартовые данные (OWNER, сценарии, настройки)
	cd apps/backend && ../../$(PY) -m app.cli seed

.PHONY: scan-music
scan-music: ## Импортировать треки из storage/music
	cd apps/backend && ../../$(PY) -m app.cli scan-music

.PHONY: run-backend
run-backend: ## Запустить backend + бот (uvicorn)
	cd apps/backend && ../../$(PY) -m uvicorn app.main:app --host 0.0.0.0 --port 8000

.PHONY: run-agent
run-agent: ## Запустить Player Agent
	cd apps/player-agent && ../../$(PY) -m agent.main

.PHONY: lint
lint: ## ruff check
	$(PY) -m ruff check apps packages

.PHONY: format
format: ## ruff format
	$(PY) -m ruff format apps packages
	$(PY) -m ruff check --fix apps packages

.PHONY: typecheck
typecheck: ## mypy
	$(PY) -m mypy apps/backend/app apps/player-agent/agent

.PHONY: test
test: ## pytest (unit + integration)
	$(PY) -m pytest apps/backend/tests apps/player-agent/tests -q

.PHONY: test-cov
test-cov: ## pytest с покрытием
	$(PY) -m pytest apps/backend/tests apps/player-agent/tests --cov=apps --cov-report=term-missing

.PHONY: check
check: lint typecheck test ## Полная проверка

.PHONY: clean
clean: ## Очистить кэши
	rm -rf .ruff_cache .mypy_cache .pytest_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
