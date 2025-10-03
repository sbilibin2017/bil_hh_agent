SRC := backend
EXCLUDE := "tests/*,*/test_*.py,*/test/*"

.PHONY: all
all: format lint

.PHONY: format
format:
	@echo "Formatting code..."
	poetry run black $(SRC)
	poetry run isort $(SRC)
	poetry run autoflake --in-place --remove-unused-variables --remove-all-unused-imports --recursive $(SRC)
	@echo "Code formatting completed."

.PHONY: lint
lint:
	@echo "Running flake8 linting (excluding tests)..."
	poetry run flake8 --exclude=$(EXCLUDE) $(SRC)
	@echo "Running mypy type checking (excluding tests)..."
	poetry run mypy --exclude=$(EXCLUDE) $(SRC)

.PHONY: test
test:
	@echo "Running tests..."
	poetry run pytest --disable-warnings -q $(SRC)
