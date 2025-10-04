SRC := .
EXCLUDE := "tests/*,*/test_*.py,*/test/*,.venv/*,*.yml,*.yaml"

.PHONY: all
all: install lint

.PHONY: install
install:
	@echo "Installing dependencies..."
	poetry install --no-interaction --no-ansi

.PHONY: format
format:
	@echo "Formatting code..."
	poetry run black $(SRC)
	poetry run isort $(SRC)
	poetry run autoflake --in-place --remove-unused-variables --remove-all-unused-imports --recursive $(SRC)
	@echo "Code formatting completed."

.PHONY: lint
lint:
	@echo "Running flake8 linting (excluding tests, .venv, yaml)..."
	poetry run flake8 --exclude=$(EXCLUDE) $(SRC)
	@echo "Running mypy type checking (excluding tests, .venv, yaml)..."
	poetry run mypy --exclude=$(EXCLUDE) $(SRC)

.PHONY: test
test:
	@echo "Running tests..."
	poetry run pytest --disable-warnings -q $(SRC)
