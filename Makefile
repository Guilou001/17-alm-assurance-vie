# Prérequis : uv
UV ?= uv

setup:
	$(UV) sync --locked --all-extras

test:             ## 13 tests fermés, sans réseau
	$(UV) run pytest

lint:
	$(UV) run ruff check src tests

all:              ## fetch + lab (réseau requis)
	$(UV) run lic fetch
	$(UV) run lic lab
