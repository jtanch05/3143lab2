# Theory worksheet

Status: The communication-aware Week 7 Amdahl model and the 30-input theory sweep are complete. These are modelling assumptions to explain during the presentation, not claims of optimality.

## Measured baseline and calculation

All empirical speedups use the median Week 4 serial overall time at the same n. At n = 100,000,000, the serial median is 12.928922 seconds and serial computation median is 12.485802 seconds, from job 129504. The serial residual is therefore 0.443120 seconds.

The model follows the Week 7 extra-class MPI example. For every target process count `p`, use the target configuration's median measured MPI communication and blocking time `K(p)`. Define:

```text
T_reference(p) = T_serial + K(p)
rp(p) = C_serial / T_reference(p)
x(p) = K(p) / T_reference(p)
rs(p) = 1 - rp(p) - x(p)

T_predicted(p) = (T_serial - C_serial) + C_serial/p + K(p)
S_class(p) = 1 / [rs(p) + rp(p)/p + x(p)] = T_reference(p) / T_predicted(p)
S_model_Week4(p) = T_serial / T_predicted(p)
                  = [T_serial / T_reference(p)] * S_class(p)
S_empirical_Week4(p) = 12.928922 / median(measured MPI overall time at p)
```

`S_class` uses the communication-augmented reference time taught in class. The plotted theoretical speedup uses the Week 4 serial numerator so it has the same baseline as empirical speedup, as required by the assessment. The two expressions use the same predicted runtime.

| Processes | K(p) measured (s) | Class Amdahl | Model vs Week 4 | Empirical vs Week 4 |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 0.000000 | 1.000 | 1.000 | 0.977 |
| 2 | 0.010483 | 1.932 | 1.931 | 1.844 |
| 4 | 0.007372 | 3.622 | 3.620 | 3.296 |
| 8 | 0.008905 | 6.428 | 6.424 | 5.199 |
| 16 | 0.019889 | 10.414 | 10.398 | 7.709 |

Sources and full-precision values are in `prepared/theory_mpi_measurements.csv` and `prepared/theory_mpi_curve.csv`. The final figure is `prepared/graph6.png` (also PDF).

## What this assumes

The serial candidate-testing loop scales ideally in this reference. The model retains the measured Week 4 serial residual and adds the measured MPI communication and blocking term for each configuration. Sorting/output costs, waiting behaviour and memory effects can still change with process count, so the measured curve can differ from this reference.

The MPI timer starts after MPI_Init and stops before the reporting collectives and MPI_Finalize. Week 4 starts its timer after input. Explain these boundaries when comparing implementations. Slurm queue time is outside every benchmark timer.

Class references: Workshop 7 slides 5 and 11-13, Topic 7A, and the Week 7 extra-class worked example. Our `K(p)` term is the program's reported maximum MPI communication time and includes blocking waits. It is therefore a communication-and-waiting term, not a pure network-transfer measurement. Summing maximum phase times from different ranks can double-count waiting and does not reconstruct a sequential execution time.

## Task 2 completed calculation

Task 2 uses the same Week 4 serial baseline, with a separate measured communication-and-waiting term for every `p x t` layout:

```text
T_predicted(p,t) = (T_serial - C_serial) + C_serial/(p*t) + K(p,t)
S_model_Week4(p,t) = T_serial / T_predicted(p,t)
```

At 16 workers, the model ranges from 9.62x to 10.53x because measured communication differs by layout. The five measured layouts range from 6.836370x to 7.553533x. Their observed ranges overlap, so the lowest median (2x8) does not establish statistical superiority. Graphs 5 and 7 use all 15 configurations in jobs 134608-134612. Graph 4 uses the p=4 subset and the MPI-only runs in job 134610. Full values: `prepared/hybrid_completed.csv`, `prepared/finish_hybrid_raw.csv` and `prepared/graph4_reference.csv`.

Using workers=p*t is an approximation: local collection, replicated preparation and MPI communication react differently to changes in p and t. The model treats the Week 4 candidate-testing loop as scalable work. It does not claim every remaining instruction is globally serial.

Compare measured configurations with the reference at their total worker count, keep the p x t labels, and discuss differences between configurations with equal total workers. Do not use Task 1's fraction as a measured Task 2 fraction.

## Input-size theory

Jobs 134613-134622 provide MPI(1) and hybrid(1x1) correctness checks at all 30 inputs. For the theory curves, each input uses its matching Week 4 serial overall and computation medians plus the measured communication-and-waiting term from the original MPI(4) or hybrid(4x4) run. Results: `prepared/theory_input_sizes.csv` and `prepared/theory_baseline_raw.csv`. Figures: `appendix_theory_n_mpi` and `appendix_theory_n_hybrid`, PNG and PDF.

The separate input-size and fixed-input scaling batches have distinct measurements. Do not silently mix their baseline values. Reproduce the complete graph set with `python complete_analysis.py`.
