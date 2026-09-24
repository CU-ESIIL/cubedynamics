# Speaker guide: From two pixels to a planet

Use one page at a time. Pause on the question before advancing.

## Page 1: When do two places experience climate together?

- **Purpose:** Start with one real pair through time.
- **Main point:** Synchrony asks a conditional question, not ordinary all-date correlation.
- **Likely confusion:** Thinking the two lines must have equal absolute temperatures.
- **Ask the group:** What part of these histories should count as unusually cold or warm?

## Page 2: What counts as cold or warm?

- **Purpose:** Show the current median-split semantics.
- **Main point:** Each location supplies its own pair-valid threshold inside the 90-day window.
- **Likely confusion:** Assuming one shared temperature cutoff or a fixed global threshold.
- **Ask the group:** Should the reference distribution remain local when we scale up?

## Page 3: Cold synchrony

- **Purpose:** Make the cold calculation tangible.
- **Main point:** Rank correlation uses only dates where both TMIN values are at or below their own medians.
- **Likely confusion:** Reading cold synchrony as frequency of cold days.
- **Ask the group:** What information is excluded when we condition on the joint cold tail?

## Page 4: Warm synchrony

- **Purpose:** Mirror the cold page exactly.
- **Main point:** Rank correlation uses only dates where both TMAX values are above their own medians.
- **Likely confusion:** Assuming warm is simply the negative of cold.
- **Ask the group:** Why might the warm relationship differ from the cold relationship?

## Page 5: Delta synchrony

- **Purpose:** Introduce the signed contrast.
- **Main point:** Delta S = cold S - warm S; blue positive means cold dominates, red negative means warm dominates.
- **Likely confusion:** Interpreting red as hot temperature rather than warm-dominant synchrony.
- **Ask the group:** Do we want Delta alone, or cold and warm beside it?

## Page 6: One center, one neighbor

- **Purpose:** Translate the pair into a spatial edge.
- **Main point:** One line on a map represents the calculation just learned.
- **Likely confusion:** Treating the line as movement or heat flow.
- **Ask the group:** What changes if the neighbor moves but the center stays fixed?

## Page 7: One center, many neighbors

- **Purpose:** Repeat the same calculation around one center.
- **Main point:** Every spoke has cold, warm, and Delta values.
- **Likely confusion:** Assuming neighboring spokes are independent replicates.
- **Ask the group:** Which neighbors should be inside the observation window?

## Page 8: The local synchrony surface

- **Purpose:** Replace spokes with one readable relational map.
- **Main point:** Every cell is its relationship with the same gold center.
- **Likely confusion:** Calling it an ordinary map of conditions at each cell.
- **Ask the group:** What does a blue cell mean on this surface?

## Page 9: Why this is not an ordinary climate map

- **Purpose:** Contrast state and relation.
- **Main point:** A temperature map asks what is here; a synchrony surface asks how here relates to the center.
- **Likely confusion:** Reading the relational color as degrees Celsius.
- **Ask the group:** What must the legend say to prevent that mistake?

## Page 10: Move the center one pixel

- **Purpose:** Introduce a second focal view without combining it.
- **Main point:** A new center produces a new complete surface.
- **Likely confusion:** Assuming the second surface is a shifted copy.
- **Ask the group:** Which values are shared geography and which are new relationships?

## Page 11: The two surfaces overlap

- **Purpose:** Show vertical stacking in 3-D.
- **Main point:** The layers revisit absolute cells from different focal centers.
- **Likely confusion:** Thinking layer height is a physical altitude or time axis.
- **Ask the group:** What does the vertical dimension index?

## Page 12: Move again

- **Purpose:** Grow the stack to four layers.
- **Main point:** Every focal center contributes another relational view.
- **Likely confusion:** Thinking more layers mean repeated temperature observations.
- **Ask the group:** What stays fixed as the focal center moves?

## Page 13: Fill a small grid of centers

- **Purpose:** Scale the stack intuition to 25 centers.
- **Main point:** A 5 x 5 focal grid creates 25 overlapping local surfaces.
- **Likely confusion:** Confusing center count with neighbor count.
- **Ask the group:** How many times can one absolute cell appear?

## Page 14: The 20 x 20 thought experiment

- **Purpose:** Bridge the toy stack to the real experiment.
- **Main point:** The real block has 400 focal centers and 400 complete surface cells per center.
- **Likely confusion:** Treating 160,000 directed views as independent pairs.
- **Ask the group:** Why are there only 80,200 canonical pairs?

## Page 15: What each stack element means

- **Purpose:** Zoom into one absolute location q.
- **Main point:** The column contains S(p1,q), S(p2,q), ...: distinct relationships involving q.
- **Likely confusion:** Calling the column repeated estimates of one intrinsic synchrony of q.
- **Ask the group:** What scientific question can this column answer?

## Page 16: Relative view

- **Purpose:** Define dx and dy only after the stack is understood.
- **Main point:** The focal center is always recentered at (0,0).
- **Likely confusion:** Assuming equal offsets always refer to equal geography.
- **Ask the group:** What useful shape information does the relative view preserve?

## Page 17: Move the center

- **Purpose:** Show geography moving through a relative window.
- **Main point:** Fixed terrain changes offset when the center moves.
- **Likely confusion:** Thinking the terrain itself moves.
- **Ask the group:** How would we put the fixed feature back in place?

## Page 18: Absolute view

- **Purpose:** Project the same values to latitude and longitude.
- **Main point:** Known geographic alignment strongly improved agreement in the current real block.
- **Likely confusion:** Assuming alignment is learned or optimized.
- **Ask the group:** What does alignment reveal that relative coordinates hide?

## Page 19: The central insight

- **Purpose:** State the overlap hypothesis plainly.
- **Main point:** Overlap is informative only when relationship locations remain attached to geography.
- **Likely confusion:** Assuming overlap automatically creates a final map.
- **Ask the group:** Which repeatable geographic signal should we extract next?

## Page 20: Ordinary convolution

- **Purpose:** Introduce the sliding-window analogy.
- **Main point:** A kernel slides, operates locally, and usually reduces immediately.
- **Likely confusion:** Assuming our method uses the same weighted sum.
- **Ask the group:** Which part of this geometry resembles our moving center?

## Page 21: Our relational version

- **Purpose:** Map the analogy onto climate time series.
- **Main point:** The moving operation returns a complete relational surface instead of one scalar.
- **Likely confusion:** Calling the operator a learned filter.
- **Ask the group:** What do we gain by retaining the neighborhood?

## Page 22: Why this is not a CNN

- **Purpose:** Set the analogy boundary.
- **Main point:** There are no trained filters, labels, backpropagation, or learned objective.
- **Likely confusion:** Overselling machine learning novelty.
- **Ask the group:** What scientific assumption defines our operator?

## Page 23: We have too much information

- **Purpose:** Finally name the four-dimensional object.
- **Main point:** x,y index focal geography; dx,dy index the relative comparison location.
- **Likely confusion:** Treating all four axes as ordinary spatial dimensions.
- **Ask the group:** Which dimensions can we reduce without losing the question?

## Page 24: The tempting easy solution

- **Purpose:** Demonstrate independent scalar reduction.
- **Main point:** Median/dispersion make maps but cannot recover the 2-D arrangement.
- **Likely confusion:** Assuming a stable map is automatically an informative map.
- **Ask the group:** What geometry disappears in a median?

## Page 25: Radial reduction

- **Purpose:** Show a transparent structured baseline.
- **Main point:** Distance profiles retain more structure but privilege radius.
- **Likely confusion:** Assuming synchrony must decay monotonically.
- **Ask the group:** What patterns would a radial summary miss?

## Page 26: Radial + directional

- **Purpose:** Show the strongest interpretable independent baseline.
- **Main point:** Direction improves reconstruction, but each surface is still summarized alone.
- **Likely confusion:** Equating lower reconstruction error with a final scientific product.
- **Ask the group:** Is independent summarization enough when surfaces overlap?

## Page 27: The overlap idea

- **Purpose:** Introduce align-first analysis.
- **Main point:** Align neighboring surfaces geographically before choosing the reduction.
- **Likely confusion:** Thinking this requires learned image registration.
- **Ask the group:** What geographic organization is repeatedly supported?

## Page 28: What the feasibility experiment found

- **Purpose:** Present the measured alignment comparison.
- **Main point:** Absolute alignment greatly improved Delta correlation and gradient agreement in one bounded block.
- **Likely confusion:** Calling a feasibility result a production algorithm.
- **Ask the group:** Which result is most compelling, and what replication is missing?

## Page 29: Local block

- **Purpose:** Anchor scaling in the actual 20 x 20 experiment.
- **Main point:** The current relational object is real but geographically bounded.
- **Likely confusion:** Mistaking the block for statewide evidence.
- **Ask the group:** What must remain invariant when we tile outward?

## Page 30: Colorado

- **Purpose:** Show the existing statewide signature product.
- **Main point:** The operation already supports tiled, halo-aware statewide execution.
- **Likely confusion:** Treating one reduced signature as the final overlap product.
- **Ask the group:** Which statewide product should be compared with the new aligned view?

## Page 31: CONUS

- **Purpose:** Make continental scaling spatially concrete.
- **Main point:** Every pixel may be a focal center with a finite observation window.
- **Likely confusion:** Imagining an all-to-all continental graph.
- **Ask the group:** What window and tiling strategy makes this bounded?

## Page 32: The computational picture

- **Purpose:** Show the scalable dataflow.
- **Main point:** Sparse canonical pairs, tiles, halos, streaming, checkpoints, and parallelism avoid dense 4-D memory.
- **Likely confusion:** Assuming we must hold S(x,y,dx,dy) densely.
- **Ask the group:** Which intermediate is the durable scientific object?

## Page 33: What would the final map mean?

- **Purpose:** Separate candidate meanings.
- **Main point:** There may be several legitimate map products, not one arbitrary score.
- **Likely confusion:** Combining magnitude, heterogeneity, coherence, asymmetry, and change prematurely.
- **Ask the group:** Which quantity should a primary map communicate?

## Page 34: What does hot mean?

- **Purpose:** Introduce climate-relative thresholds.
- **Main point:** The same absolute temperature can be extreme at one place and ordinary at another.
- **Likely confusion:** Using one global Celsius cutoff by default.
- **Ask the group:** Relative to which distribution should hot and cold be defined?

## Page 35: Relative extremes are a feature

- **Purpose:** Explain the strength of local thresholds.
- **Main point:** Places in different climates can be compared by departures relative to themselves.
- **Likely confusion:** Assuming local standardization removes all climate context.
- **Ask the group:** What scientifically meaningful cross-climate question does this enable?

## Page 36: But relativity creates a new problem

- **Purpose:** Separate synchrony from climatic similarity.
- **Main point:** Joint local warm tails can occur at very different absolute temperatures and regimes.
- **Likely confusion:** Calling relative synchrony absolute similarity.
- **Ask the group:** What absolute context must travel with a synchrony map?

## Page 37: Local versus global variance

- **Purpose:** Make washout risk visible.
- **Main point:** Global variation can dwarf coherent regional departures.
- **Likely confusion:** Normalizing once at the global level because it is convenient.
- **Ask the group:** Which local structures must remain visible by design?

## Page 38: The normalization question

- **Purpose:** Lay out options without selecting one.
- **Main point:** Local, regional, multiscale, dual, and hierarchical representations answer different questions.
- **Likely confusion:** Presenting alternatives as mutually interchangeable.
- **Ask the group:** Which strategy best protects both comparability and local meaning?

## Page 39: The answer depends on the reference frame

- **Purpose:** Connect spatial and temporal definitions.
- **Main point:** Reference distribution and observation window can both change the answer.
- **Likely confusion:** Treating a map as scale-free.
- **Ask the group:** Which reference choices must appear in every product's metadata?

## Page 40: We should not search for one magic radius

- **Purpose:** Use current window sensitivity honestly.
- **Main point:** Rmax is an observation limit, not a discovered synchrony scale.
- **Likely confusion:** Selecting 40 km because one comparison looks stable.
- **Ask the group:** How stable should a result be as the window expands?

## Page 41: Keep relationships first

- **Purpose:** Protect the fundamental object.
- **Main point:** Canonical pair relationships can support multiple downstream views.
- **Likely confusion:** Discarding pairs after making the first map.
- **Ask the group:** What minimal provenance must each pair retain?

## Page 42: Then ask questions at multiple scales

- **Purpose:** Show reuse rather than recomputation.
- **Main point:** Local, regional, continental, and global views can derive from the same pair layer where definitions permit.
- **Likely confusion:** Assuming aggregation never changes interpretation.
- **Ask the group:** Which parts can be reused, and which thresholds may need recalculation?

## Page 43: A multiscale synchrony map

- **Purpose:** Offer a discussion hypothesis.
- **Main point:** A location may need local, regional, and broader-scale synchrony values.
- **Likely confusion:** Reading the illustrative layers as an implemented method.
- **Ask the group:** Would a family of scale-indexed maps be more honest than one value?

## Page 44: Relative + absolute

- **Purpose:** Propose a two-axis interpretation.
- **Main point:** Pair relative-extreme synchrony with absolute climate-state similarity.
- **Likely confusion:** Collapsing the two axes before understanding them.
- **Ask the group:** Which scientific cases occupy each quadrant?

## Page 45: PRISM is a gridded model

- **Purpose:** Introduce observational context.
- **Main point:** Raw stations provide a second route to the same pair calculations.
- **Likely confusion:** Calling station comparisons independent before contribution status is known.
- **Ask the group:** What can stations test that the grid alone cannot?

## Page 46: Build the same relationships from stations

- **Purpose:** Show methodological comparability.
- **Main point:** The same cold, warm, and Delta definitions apply to station pairs.
- **Likely confusion:** Rasterizing stations and hiding their irregular network.
- **Ask the group:** How should shared-station dependence affect inference?

## Page 47: Current preliminary result

- **Purpose:** Report station-grid agreement with limits.
- **Main point:** Cold and Delta agreement are encouraging; warm agreement is weak; all contribution statuses are unknown.
- **Likely confusion:** Calling the comparison validation.
- **Ask the group:** Why might warm agreement be weak?

## Page 48: Why stations matter

- **Purpose:** Define a future external test.
- **Main point:** A real gridded geography should receive some support from raw observation relationships.
- **Likely confusion:** Expecting every grid feature to have a nearby station test.
- **Ask the group:** What station density and holdout design would be convincing?

## Page 49: The entire method on one page

- **Purpose:** Rehearse the full narrative.
- **Main point:** Pairs become surfaces, surfaces overlap, geography aligns them, scale choices shape maps.
- **Likely confusion:** Skipping from pair synchrony directly to a global score.
- **Ask the group:** At which arrow is the group least confident?

## Page 50: What we know versus what we are deciding

- **Purpose:** Separate evidence from open choices.
- **Main point:** The relational object is understood; the second-stage map definition is not settled.
- **Likely confusion:** Treating an open design choice as a failure of the first-stage method.
- **Ask the group:** Which open choice should be resolved first?

## Page 51: Question 1

- **Purpose:** Focus discussion on pixel meaning.
- **Main point:** A final pixel may need one or several explicitly named quantities.
- **Likely confusion:** Voting for a metric before stating the use case.
- **Ask the group:** What should one pixel on the final map mean?

## Page 52: Question 2

- **Purpose:** Focus discussion on global extremes.
- **Main point:** Hot and cold can be pixel-relative, region-relative, global, or multiscale.
- **Likely confusion:** Assuming one definition serves every question.
- **Ask the group:** What should hot and cold mean globally?

## Page 53: Question 3

- **Purpose:** Focus discussion on preservation.
- **Main point:** Stability is insufficient if meaningful regional structure disappears.
- **Likely confusion:** Equating smoothness with scientific quality.
- **Ask the group:** How much local variation must we preserve?

## Page 54: Question 4

- **Purpose:** Focus discussion on product family.
- **Main point:** Cold, warm, and Delta may each need multiple spatial scales.
- **Likely confusion:** Forcing everything into a single map for convenience.
- **Ask the group:** Is there one synchrony map or a family of maps?

## Page 55: Question 5

- **Purpose:** End with falsifiable evidence criteria.
- **Main point:** Replication, window stability, synthetic recovery, stations, and independent products can build confidence.
- **Likely confusion:** Ending with a claim that synchrony is solved.
- **Ask the group:** What would convince us the map is real?
