# Quickstart

Install an external wheel, read actual observations, and apply two verbs.
No source clone or editable installation is needed for this page.

## Install

**Current state: 0.1.0rc1 is not published.** Obtain the tested wheel and SHA256
from the maintainer, or wait for publication. Follow the
[installation and release instructions](getting_started/install.md) first.
That page distinguishes supplied local wheels, future GitHub Release assets,
future PyPI prereleases, and contributor checkouts. Plain PyPI installation
does not work today.

## First executable example — public reviewed observations

This small public extract holds PRISM daily maximum temperature near Boulder,
January 1–30, 2024, in °C. It is external example data, not bundled package data.
The URL is pinned to an existing commit and its bytes are verified before use.
Downloading requires network access; failure stops the example, with no
synthetic replacement. Its [provenance](https://github.com/CU-ESIIL/cubedynamics/blob/862a80aed8a2781b40e6e5293fd6cfbcba887aa4/tests/fixtures/real_data/prism_boulder_january_2024.provenance.json)
records the original provider query and limitations.

<!-- external-quickstart: observations -->
```python
from io import BytesIO
from urllib.request import urlopen
import hashlib
import xarray as xr
from cubedynamics import data, pipe, verbs as v

url = (
    "https://raw.githubusercontent.com/CU-ESIIL/cubedynamics/"
    "862a80aed8a2781b40e6e5293fd6cfbcba887aa4/tests/fixtures/real_data/"
    "prism_boulder_january_2024.nc"
)
with urlopen(url, timeout=30) as response:
    payload = response.read(1_000_001)  # Bound this deliberately small download.
expected = "630b8857d8e0e66409bed3c03194ead009506d093adae5411f39727e0c0e4cf7"
if len(payload) > 1_000_000 or hashlib.sha256(payload).hexdigest() != expected:
    raise RuntimeError("PRISM example bytes differ from the reviewed extract")
with xr.open_dataset(BytesIO(payload), engine="scipy") as observed:
    temperature = observed["tmax"].load()
print(temperature.attrs["units"])
```

The deliberate load closes this small input safely; it is not a recommendation
to eagerly load long climate records.

## Compose the analysis

<!-- external-quickstart: analysis -->
```python
import matplotlib.pyplot as plt

spatial_anomaly = (
    pipe(temperature)
    | v.anomaly(dim="time")
    | v.mean(dim=("y", "x"), keep_dim=False)
).unwrap()
spatial_anomaly.plot()
plt.title("Boulder · daily departure from January 1–30, 2024 mean")
plt.ylabel("Temperature departure (°C)")
plt.show()
```

Subtract each cell's mean for the requested dates, then average over space.
This is a departure from the selected period, not a multi-decade climatology.

## Request the noun directly from its provider

Discovery and help do not need observations:

<!-- external-quickstart: discovery -->
```python
print(data.describe("temperature", "prism"))
help(data.temperature)
help(v.mean)
```

For a live request, use the documented noun API with a bounded three-day query.
This is a separate provider-access check, not a replacement for the pinned
example above. Provider outages are reported as errors.

<!-- external-quickstart: live -->
```python
live_temperature = data.temperature(
    source="prism", statistic="maximum",
    bbox=[-105.55, 39.85, -105.05, 40.15],
    start="2024-01-01", end="2024-01-03",
)
(pipe(live_temperature) | v.mean(over="time", keep_dim=False)).unwrap().plot()
plt.title("PRISM · mean daily maximum · January 1–3, 2024")
plt.show()
```

The [temperature reference](library/nouns/temperature.md) describes source,
units, coverage, and provenance. A shared noun does not harmonize providers.

## Continue

- [Learn](learn/index.md): seven short lessons.
- [Library](library/index.md): environmental nouns and sources.
- [Documents](documentation/index.md): arguments and behavior.
- [Vignettes](vignettes/index.md): complete reproducible analyses.
