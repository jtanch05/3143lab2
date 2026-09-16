# Theory worksheet

Status: Task 1 reference model calculated. Task 2 model awaits a hybrid 1-process, 1-thread run. These are modelling assumptions to explain during the presentation, not claims of optimality.

## Measured baseline and calculation

All empirical speedups use the median Week 4 serial overall time at the same n. At n = 100,000,000 this is 12.928922 seconds, from job 129504.

For Task 1, job 129144 runs the actual MPI program with one process. This gives a useful way to measure its parallel candidate-testing loop without dividing an already-parallel time again:

| Repeat | Overall T1 (s) | Candidate loop C1 (s) | Residual T1-C1 (s) | Residual / T1 |
| --- | ---: | ---: | ---: | ---: |
| 1 | 13.220626 | 12.500321 | 0.720305 | 0.054483 |
| 2 | 13.239176 | 12.500669 | 0.738507 | 0.055782 |
| 3 | 13.313472 | 12.521834 | 0.791638 | 0.059461 |

Use median T1 = 13.239176 s and median fraction f = 0.055781946. The idealized fixed-work Amdahl model is:

```text
T_model(p) = T1 * [f + (1-f)/p]
S_model_own_baseline(p) = 1 / [f + (1-f)/p]
S_model_Week4(p) = 12.928922 / T_model(p)
S_empirical_Week4(p) = 12.928922 / median(measured MPI overall time at p)
```

The Week 4 conversion matters because MPI(1) is slower than the Week 4 serial program. Without it, the two plotted speedups use different denominators. Both plotted curves start around 0.977 at p=1.

| Processes | Amdahl reference vs Week 4 | Empirical vs Week 4 |
| ---: | ---: | ---: |
| 1 | 0.977 | 0.977 |
| 2 | 1.850 | 1.844 |
| 4 | 3.346 | 3.296 |
| 8 | 5.619 | 5.199 |
| 16 | 8.507 | 7.709 |

Sources and full-precision values are in `prepared/theory_mpi_measurements.csv` and `prepared/theory_mpi_curve.csv`. The generated Graph 6 is labelled a draft model for review.

## What this assumes

The candidate-testing loop scales ideally. The residual (preparation, local overhead, one-process collectives, sorting and output) stays constant. This is an effective nonparallel fraction for this implementation and input, not an immutable property of prime search. Additional communication with more MPI processes is not included. Sorting/output costs and memory behaviour may also change. Thus the measured curve can differ from this reference.

The MPI timer starts after MPI_Init and stops before the reporting collectives and MPI_Finalize. Week 4 starts its timer after input. Explain these boundaries when comparing implementations. Slurm queue time is outside every benchmark timer.

Class references: Workshop 7 slides 5 and 11-13, Topic 7A, and the Week 7 extra-class worked example. The class also discusses a communication-aware extension. Our simple reference explicitly leaves changing communication overhead unmodelled. To add an overhead term, establish non-overlapping measurements and consistent normalization first. Summing maximum phase times from different ranks can double-count waiting and does not reconstruct a sequential execution time.

## Task 2 pending calculation

Current implementation plan: `finish_hybrid.job` and `finish_theory.job`, described in `FINISH_RUNBOOK.md`, supersede the earlier limited `hybrid_scaling.job`. `complete_analysis.py` generates Graphs 5/7 and the input-size theory appendix once those measured reports are downloaded. Existing Task 1 Graph 6 remains a valid idealized reference under the stated assumptions, not a communication-aware prediction.

`hybrid_scaling.job` collects a 1 x 1 reference plus a 1/2/4 MPI by 1/2/4 thread matrix. Once available, use the actual hybrid one-worker candidate-loop timing and overall time to construct an analogous reference. Label a model using workers=p*t as an approximation: local collection, replicated preparation and MPI communication react differently to changes in p and t.

Compare measured configurations with the reference at their total worker count, keep the p x t labels, and discuss differences between configurations with equal total workers. Do not use Task 1's fraction as a measured Task 2 fraction.
