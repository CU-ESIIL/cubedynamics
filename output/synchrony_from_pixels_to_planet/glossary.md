# One-page glossary

Concise terms used in the discussion PDF.

**Cold synchrony.** Spearman rank correlation calculated only on pair-valid dates when both locations' daily minimum temperatures are at or below their own median thresholds in the analysis window.

**Warm synchrony.** Spearman rank correlation calculated only on pair-valid dates when both locations' daily maximum temperatures are above their own median thresholds in the analysis window.

**Delta synchrony.** Cold synchrony minus warm synchrony. Positive means cold-tail synchrony is stronger; negative means warm-tail synchrony is stronger.

**Focal / center pixel.** The reference location held fixed while it is compared with locations in its observation window.

**Pair.** Two geographic locations plus their conditional relationship and support information.

**Local synchrony surface.** A 2-D map of pair relationships between one focal center and every comparison location in its local domain.

**Stack.** The collection of local surfaces created by moving the focal center. It is a stack of relationships, not repeated temperature maps.

**Relative coordinates.** Offsets dx and dy from the focal center, which is always represented as (0,0).

**Absolute geography.** The fixed latitude/longitude or grid coordinates of the focal and comparison locations.

**Canonical pair.** One undirected identity for endpoints i and j, so S(i,j) and S(j,i) are not counted as independent evidence.

**Relational field.** The full collection S(x,y,dx,dy): focal geography plus within-surface relative geometry.

**Overlap.** Multiple focal-center surfaces revisiting the same absolute geographic cells or edges through different relationships.

**Observation window.** The finite spatial neighborhood within which pairs are evaluated; its maximum radius is an observation limit, not automatically a characteristic synchrony scale.

**Local normalization.** Defining states relative to each location's own distribution or local context.

**Global normalization.** Defining states or scales from a pooled global reference; useful for some comparisons but capable of washing out regional variation.
