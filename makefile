.venv:
	poetry install

test: .venv
	poetry run pytest --cov kronk -v

init:
	poetry run python -m kronk.database

worker:
	poetry run python -m kronk.worker

generate:
	poetry run python -m kronk.generate_tasks

distributor:
	poetry run python -m kronk.distributor

.PHONY: test init worker generate distributor
