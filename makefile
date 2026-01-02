.venv:
	uv sync

test: .venv
	uv run pytest --cov kronk -v

init:
	uv run python -m kronk.database

worker:
	uv run python -m kronk.worker

generate:
	uv run python -m kronk.generate_tasks

distributor:
	uv run python -m kronk.distributor

.PHONY: test init worker generate distributor
