# Capabilities & Verbs  
*A textbook-style reference for Climate Cube Math*

Climate Cube Math expresses spatiotemporal analysis as a **grammar**:

> **Data → Transformations → Statistics → Events → Visualization**

This page walks through that grammar step by step.  
Each verb is presented with:
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
1. Aggregation verbs (collapse time)
These verbs reduce a spatiotemporal cube
X
(
x
,
y
,
t
)
X(x,y,t)
into a spatial field by aggregating over time.
v.mean
Science
허
(
x
,
y
)
=
1
T
∑

t
=
1
T
X
(
x
,
y
,
t
)
허(x,y)= 
T
1
​
 
t=1
헇
T
​
 X(x,y,t)
pipe(cube) | v.mean() | v.plot(title="Mean NDVI")
v.sum
S
(
x
,
y
)
=
∑

t
=
1
T
X
(
x
,
y
,
t
)
S(x,y)= 
t=1
헇
T
​
 X(x,y,t)
pipe(cube) | v.sum() | v.plot(title="Cumulative NDVI")
v.min / v.max
min
⁡

t
X
(
x
,
y
,
t
)
,
max
⁡

t
X
(
x
,
y
,
t
)
t
min
​
 X(x,y,t), 
t
max
​
 X(x,y,t)
pipe(cube) | v.max() | v.plot(title="Maximum NDVI")
2. Distributional & tail behavior
v.quantile
Q
q
(
x
,
y
)
=
inf
⁡
{
z
:
P
(
X
(
x
,
y
,
t
)
≤
z
)
≥
q
}
Q 
q
​
 (x,y)=inf{z:P(X(x,y,t)≤z)≥q}
pipe(cube) | v.quantile(0.9) | v.plot(title="90th percentile NDVI")
v.lower_tail
X
L
(
x
,
y
,
t
)
=
X
(
x
,
y
,
t
)
∣
X
≤
Q
q
(
x
,
y
)
X 
L
​
 (x,y,t)=X(x,y,t)∣X≤Q 
q
​
 (x,y)
pipe(cube) | v.lower_tail(q=0.1) | v.plot(title="Lower-tail NDVI")
v.upper_tail
X
U
(
x
,
y
,
t
)
=
X
(
x
,
y
,
t
)
∣
X
≥
Q
q
(
x
,
y
)
X 
U
​
 (x,y,t)=X(x,y,t)∣X≥Q 
q
​
 (x,y)
pipe(cube) | v.upper_tail(q=0.9) | v.plot(title="Upper-tail NDVI")
3. Variability & synchrony
v.variance
V
a
r
(
x
,
y
)
=
1
T
−
1
∑

t
=
1
T
(
X
(
x
,
y
,
t
)
−
허
(
x
,
y
)
)
2
Var(x,y)= 
T−1
1
​
 
t=1
헇
T
​
 (X(x,y,t)−허(x,y)) 
2
 
pipe(cube) | v.variance() | v.plot(title="NDVI Variability")
v.std
σ
(
x
,
y
)
=
V
a
r
(
x
,
y
)
σ(x,y)= 
Var(x,y)
​
 
pipe(cube) | v.std() | v.plot(title="NDVI Std Dev")
v.synchrony
핍
=
V
a
r
(
∑
i
X
i
(
t
)
)
∑
i
V
a
r
(
X
i
(
t
)
)
핍= 
∑ 
i
​
 Var(X 
i
​
 (t))
Var(∑ 
i
​
 X 
i
​
 (t))
​
 
pipe(cube) | v.synchrony() | v.plot(title="Spatial Synchrony")
4. Temporal structure
v.climatology
X
ˉ
(
x
,
y
,
d
)
=
E
[
X
(
x
,
y
,
t
)
∣
 d
]
X
ˉ
 (x,y,d)=E[X(x,y,t)∣d]
pipe(cube) | v.climatology()
v.anomaly
A
(
x
,
y
,
t
)
=
X
(
x
,
y
,
t
)
−
X
ˉ
(
x
,
y
,
t
)
A(x,y,t)=X(x,y,t)− 
X
ˉ
 (x,y,t)
pipe(cube) | v.anomaly() | v.plot(title="NDVI Anomalies")
v.rolling
허
w
(
x
,
y
,
t
)
=
1
w
∑
k
=
0
w
−
1
X
(
x
,
y
,
t
−
k
)
허 
w
​
 (x,y,t)= 
w
1
​
 
 k=0
헇
w−1
​
 X(x,y,t−k)
pipe(cube) | v.rolling(window=30) | v.mean()
v.detrend
X
′
(
x
,
y
,
t
)
=
X
(
x
,
y
,
t
)
−
(
α
t
+
β
)
X 
′
 (x,y,t)=X(x,y,t)−(αt+β)
pipe(cube) | v.detrend() | v.plot(title="Detrended NDVI")
5. Event & hull-based operations
v.vase
X
황
=
X
(
x
,
y
,
t
)
⋅
1
(
x
,
y
,
t
)
∈
황
X 
황
​
 =X(x,y,t)⋅1 
(x,y,t)∈황
​
 
from cubedynamics.fire_time_hull import load_fired_conus_ak

fired = load_fired_conus_ak(which="daily")
event_geom = fired.geometry.iloc[0]

pipe(cube) | v.vase(vase=event_geom) | v.plot()
6. Visualization verbs
v.plot
pipe(cube) | v.mean() | v.plot()
v.lexcube
pipe(cube) | v.lexcube()
Event visualization
pipe(cube) | v.vase(vase=event_geom) | v.lexcube()
Putting it all together
pipe(cube) \
| v.anomaly() \
| v.variance() \
| v.vase(vase=event_geom) \
| v.lexcube()
