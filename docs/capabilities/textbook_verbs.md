# Capabilities & Verbs
*A textbook-style reference for Climate Cube Math*

Climate Cube Math expresses spatiotemporal analysis as a **grammar**:

> **Data → Transformations → Statistics → Events → Visualization**

This page walks through that grammar step by step. Each verb is presented with:
1. **The scientific operation (math)**
2. **A copy-paste Python example**

---

## Shared setup (used in all examples)

```python
from cubedynamics import pipe, verbs as v
import cubedynamics as cd

# Example spatiotemporal cube
cube = cd.ndvi(
    lat=40.0,
    lon=-105.25,
    start="2022-01-01",
    end="2023-01-01",
)
```

---

## 1. Aggregation verbs (collapse time)
These verbs reduce a spatiotemporal cube \(X(x,y,t)\) into a spatial field by aggregating over time.

### `v.mean`
\[
\bar{X}(x,y)=\frac{1}{T}\sum_{t=1}^T X(x,y,t)
\]
```python
pipe(cube) | v.mean() | v.plot(title="Mean NDVI")
```

### `v.sum`
\[
S(x,y)=\sum_{t=1}^T X(x,y,t)
\]
```python
pipe(cube) | v.sum() | v.plot(title="Cumulative NDVI")
```

### `v.min` / `v.max`
\[
\min_t X(x,y,t), \quad \max_t X(x,y,t)
\]
```python
pipe(cube) | v.max() | v.plot(title="Maximum NDVI")
```

---

## 2. Distributional & tail behavior

### `v.quantile`
\[
Q_q(x,y)=\inf \{ z : P(X(x,y,t) \le z) \ge q \}
\]
```python
pipe(cube) | v.quantile(0.9) | v.plot(title="90th percentile NDVI")
```

### `v.lower_tail`
\[
X_L(x,y,t)=X(x,y,t)\mid X \le Q_q(x,y)
\]
```python
pipe(cube) | v.lower_tail(q=0.1) | v.plot(title="Lower-tail NDVI")
```

### `v.upper_tail`
\[
X_U(x,y,t)=X(x,y,t)\mid X \ge Q_q(x,y)
\]
```python
pipe(cube) | v.upper_tail(q=0.9) | v.plot(title="Upper-tail NDVI")
```

---

## 3. Variability & synchrony

### `v.variance`
\[
\operatorname{Var}(x,y)=\frac{1}{T-1}\sum_{t=1}^T\big(X(x,y,t)-\bar{X}(x,y)\big)^2
\]
```python
pipe(cube) | v.variance() | v.plot(title="NDVI Variability")
```

### `v.std`
\[
\sigma(x,y)=\sqrt{\operatorname{Var}(x,y)}
\]
```python
pipe(cube) | v.std() | v.plot(title="NDVI Std Dev")
```

### `v.synchrony`
\[
\phi = \frac{\operatorname{Var}\left(\sum_i X_i(t)\right)}{\sum_i \operatorname{Var}\big(X_i(t)\big)}
\]
```python
pipe(cube) | v.synchrony() | v.plot(title="Spatial Synchrony")
```

---

## 4. Temporal structure

### `v.climatology`
\[
\bar{X}(x,y,d)=\mathbb{E}[X(x,y,t)\mid d]
\]
```python
pipe(cube) | v.climatology()
```

### `v.anomaly`
\[
A(x,y,t)=X(x,y,t)-\bar{X}(x,y,t)
\]
```python
pipe(cube) | v.anomaly() | v.plot(title="NDVI Anomalies")
```

### `v.rolling`
\[
\bar{X}_w(x,y,t)=\frac{1}{w}\sum_{k=0}^{w-1} X(x,y,t-k)
\]
```python
pipe(cube) | v.rolling(window=30) | v.mean()
```

### `v.detrend`
\[
X'(x,y,t)=X(x,y,t)-(\alpha t+\beta)
\]
```python
pipe(cube) | v.detrend() | v.plot(title="Detrended NDVI")
```

---

## 5. Event & hull-based operations

### `v.vase`
\[
X^{\mathcal{V}} = X(x,y,t) \cdot \mathbf{1}_{(x,y,t)\in \mathcal{V}}
\]
```python
from cubedynamics.fire_time_hull import load_fired_conus_ak

fired = load_fired_conus_ak(which="daily")
event_geom = fired.geometry.iloc[0]

pipe(cube) | v.vase(vase=event_geom) | v.plot()
```

---

## 6. Visualization verbs

### `v.plot`
```python
pipe(cube) | v.mean() | v.plot()
```

### `v.lexcube`
```python
pipe(cube) | v.lexcube()
```

### Event visualization
```python
pipe(cube) | v.vase(vase=event_geom) | v.lexcube()
```

### Putting it all together
```python
pipe(cube) \
    | v.anomaly() \
    | v.variance() \
    | v.vase(vase=event_geom) \
    | v.lexcube()
```
