.PHONY: all run-all steel al6061

PYTHON ?= python
BASE_ARGS = --epsilon 0.8 --T_in_max 303 --mu_req 2000 --q_expected 0.023

all: run-all

run-all: steel al6061

steel:
	$(PYTHON) -m hab_sphere.cli --material steel $(BASE_ARGS)

al6061:
	$(PYTHON) -m hab_sphere.cli --material al6061 $(BASE_ARGS)
