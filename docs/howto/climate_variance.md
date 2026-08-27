# Climate variance

To compare variability, reduce the time dimension explicitly with
[`v.variance(dim="time", keep_dim=False)`](../reference/verbs/variance.md).
Variance has squared input units; a z-score is a different, dimensionless result.

- [Observed PRISM verb gallery](../vignettes/verbs_gallery.ipynb): executable offline notebook.
- [gridMET variability recipe](../recipes/gridmet_variance_cube.md): live temperature request.
- [PRISM precipitation recipe](../recipes/prism_variance_cube.md): live precipitation anomalies.
- [Order matters](../learn/order.md): why changing the sequence changes the question.
