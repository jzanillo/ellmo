.PHONY:  default

default: help

help:
	@echo
	@echo 'Make commands:'
	@echo '	make lint				Run linter'
	@echo '	make lint-fix				Run linter and apply changes'
	@echo '	make format				Run formatter'
	@echo '	make format-fix				Run formatter and apply changes'
	@echo '	make requirements			Populate requirements.txt from Poetry'

lint:
	poetry run ruff check .

lint-fix:
	poetry run ruff check . --fix

format:
	poetry run black . --diff

format-fix:
	poetry run black .

requirements:
	@poetry export -f requirements.txt --output requirements.txt --without-hashes