# 2. Surrogate fitting (pseudocode)

Families compared, from simplest to most flexible:

| Family | Idea | Why it was tried |
|---|---|---|
| Quadratic polynomial | smooth low-order trend | works for moderate damage area |
| Cubic polynomial | more curvature | tests whether extra order helps |
| Generalised additive model (GAM) | sum of smooth 1-D shape functions, optional pairwise interactions | handles non-linear trends |
| Gaussian process regression (GPR) | smooth interpolation with uncertainty | enforces smoothness on sparse data |
| Support vector regression (SVR) | kernel regression with an error tube | alternative smooth non-linear fit |

```
FOR each family F:
    FOR each configuration c of F:                 # one factor studied at a time
        predictors   in { raw geometry, geometry + distance-from-centre features }
        polynomial:  order, interaction terms
        GAM:         interactions in { none, pairwise, all }
        GPR:         kernel in { squared-exponential, Matern, rational quadratic },
                     per-input length scales on/off, noise level
        SVR:         kernel in { RBF, polynomial, linear },
                     tube width epsilon, penalty C

        standardise predictors using training data only
        fit model on training set
        record: train error, test error, leave-one-out CV error, complexity

    keep the best configuration(s) of F by cross-validated error

COMPARE the best of each family on the same held-out geometries
```

## Hyper-parameter tuning (GPR, SVR)
```
define search ranges for kernel parameters / noise / C / epsilon
objective(params) = leave-one-out CV error of the model fitted with params
run Bayesian optimisation over objective for a fixed evaluation budget
return the best params, then refit on all training data
```

## Why one factor at a time
Changing one setting per tier (predictor set, then kernel, then regularisation) makes it clear which choice drives an improvement, which matters when only a few dozen expensive FE results exist.
