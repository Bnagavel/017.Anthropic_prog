# 3. Validation and physical-plausibility checks (pseudocode)

Small, expensive datasets make it easy to over-claim. The checks below guard against that.

```
SPLITS
    train   = baseline grid points
    test    = non-grid geometries never used in fitting
    extra   = space-filling points (can be added to train in later scenarios)
    if a point is in both train and predict sets:
        flag the result as IN-SAMPLE so it is never reported as held-out

METRICS (per model)
    train R2, test R2, RMSE
    leave-one-out CV RMSE
    complexity penalty (number of terms / effective parameters)

PHYSICAL PLAUSIBILITY
    predict on a dense sweep along each input (e.g. vary width, hold others)
    reject or flag a model if its curve:
        has step-like jumps with no physical cause
        goes negative or far outside the observed range
        shows large oscillations between training points
    for probabilistic models (GPR):
        check prediction intervals cover held-out points
        check uncertainty grows away from training data

EXTRAPOLATION GUARD
    clip plotted predictions to a multiple of the observed range,
    so one bad extrapolation does not hide the shape of the rest of the curve

RANK
    rank candidates by cross-validated error, then discard any that fail the
    plausibility checks
```

## Lessons so far
- A good R2 is not enough: a boosted-tree-style GAM scored well but produced step-like predictions on sparse data.
- Higher-order polynomials can miss training points and extrapolate badly.
- Smooth interpolators (GPR/SVR) are being evaluated to address both problems.
