# 1. Overall workflow (pseudocode)

Goal: replace slow high-fidelity FE runs with a fast surrogate that predicts lightning-induced damage area from specimen geometry.

```
INPUT : design variables x = (plate length L, plate width W, top-ply angle theta)
OUTPUT: predicted damage area for two thresholds
          moderate damage area (MDA): 300 C < T < 500 C
          severe damage area   (SDA): T > 500 C

1. Define the design space
     L, W in [100, 300] mm ; theta in {0, 45, 90} deg

2. Choose training points
     baseline set  = full-factorial grid (3 x 3 x 3 = 27 runs)
     extra sets    = space-filling samples (e.g. Latin hypercube) and
                     separate non-grid test geometries

3. For each design point x_i:
     build coupled electric-thermal FE model (Joule heating) from a template
     apply the standard lightning current waveform
     run the analysis
     post-process the nodal temperature field:
         area where T is between 300 and 500 C -> MDA_i
         area where T > 500 C                  -> SDA_i
     store (x_i, MDA_i, SDA_i)

4. Fit and compare surrogate families           (see 02_surrogate_fitting.md)

5. Validate on held-out geometries              (see 03_validation.md)

6. Select the surrogate that is accurate AND physically plausible
```

## Notes
- FE meshing is aligned with the fibre direction of the top ply, because misaligned meshes change the predicted damage area.
- A single high-fidelity run can take days, which is why the surrogate is needed.
