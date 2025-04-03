# install dependencies
# this project uses uv to manage dependencies
deps:
	uv sync --all-groups --locked --all-packages

# serve the api (requires redis to be running)
dev: 
	OTEL_SDK_DISABLED=false uv run pygeoapi openapi generate local.config.yml --output-file local.openapi.yml
	OTEL_SDK_DISABLED=false PYGEOAPI_CONFIG=local.config.yml PYGEOAPI_OPENAPI=local.openapi.yml uv run pygeoapi serve --starlette

devNoOTEL:
	OTEL_SDK_DISABLED=true uv run pygeoapi openapi generate local.config.yml --output-file local.openapi.yml
	OTEL_SDK_DISABLED=true PYGEOAPI_CONFIG=local.config.yml PYGEOAPI_OPENAPI=local.openapi.yml uv run pygeoapi serve --starlette

test:
	# run tests in parallel with pytest-xdist and stop after first failure; run in verbose mode and show durations of the 5 slowest tests
	uv run pyright && uv run pytest -n 20 -x --maxfail=1 -vv --durations=5

cov:
	uv run pytest -n 20 -x --maxfail=1 -vv --durations=5 --cov

cyclo:
	uv run radon cc --order SCORE --show-complexity --min B .

clean:
	rm -rf .venv/
	rm -rf .pytest_cache/
	
