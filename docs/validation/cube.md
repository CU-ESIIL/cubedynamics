---
description: "Pixel-exact validation of all six CubeDynamics HTML cube faces using real PRISM observations."
---

# Cube / HTML validation

The interactive viewer is not validated by appearance alone. The suite builds a
cube from real PRISM maximum temperature, extracts the six base64 PNG textures
from the generated HTML, decodes their RGBA pixels, and compares every pixel to
an independently indexed source array.

![All decoded cube faces](../assets/validation/cube/diagnostic.png)

## Declared face contract

The front of the cube is the newest date and the back is the oldest. CSS rotates
opposite faces in opposite directions, so source arrays are oriented before
encoding:

| Face | Source evidence | Declared display direction |
| --- | --- | --- |
| Front | newest `time × y × x` plane | x unchanged |
| Back | oldest plane | x reversed for `rotateY(180deg)` |
| Left | x-min boundary through time | oldest at back, newest at front |
| Right | x-max boundary through time | time reversed before `rotateY(90deg)` |
| Top | y-min boundary through time | oldest at back, newest at front |
| Bottom | y-max boundary through time | time reversed before `rotateX(-90deg)` |

The renderer now uses `background-size: 100% 100%` for cube and interior
textures. The previous `cover` rule cropped rectangular space-time textures to
a square and could hide evidence on the side faces.

Acceptance requires exactly one of each shell face, no cropping CSS, the stated
orientation for all axes, and exact equality for every decoded RGBA pixel.
