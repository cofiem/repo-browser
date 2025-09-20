# Contributing guide

## Development

Use `BUILDKIT_PROGRESS=plain` before the docker compose commands to see all the output.

```shell
# To upgrade dependencies
docker compose run --build --rm upgrade_deps

# Start local server
docker compose up --build --menu=false dev_app
# Stop local server
docker compose down dev_app

# To get the contents of the python3-apt package locally
docker build --target export_deps --output export_deps .

# To run manage.py commands
docker compose run --build --rm dev_app python manage.py

# To run tests
docker compose run --build --rm dev_app pytest -n auto --cov=discover --cov=examine --cov=intrigue
```


## Run tests and linters


