PYTHON ?= python3
VENV ?= .venv
PY := $(VENV)/bin/python

.PHONY: install test test-offline test-streaming test-fire docs clean-venv

$(PY):
	$(PYTHON) -m venv $(VENV)

install: $(PY)
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -e ".[dev]"

test: test-offline

test-offline: install
	$(PY) -m pytest -m "not integration and not online" --maxfail=1 --disable-warnings -q

test-streaming: install
	$(PY) -m pytest tests/test_prism_ncss_streaming.py \
		tests/test_gridmet_streaming_contract.py \
		tests/test_global_climate_streaming.py \
		tests/test_median_split_synchrony_verb.py \
		tests/test_spatial_units.py \
		tests/test_real_fire_vase_gridmet_smoke.py \
		src/cubedynamics/tests/test_streaming_contracts.py \
		--maxfail=1 --disable-warnings -q

test-fire: install
	$(PY) -m pytest tests/test_fire_vase_panel.py \
		tests/test_diagnostic_panel.py \
		tests/test_real_fire_vase_gridmet_smoke.py \
		tests/test_fire_hull_api.py \
		tests/test_fire_plot_loader_calls.py \
		-q

docs: install
	$(PY) -m mkdocs build --strict

clean-venv:
	rm -rf $(VENV)
