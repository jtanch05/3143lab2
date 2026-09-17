# MPI and hybrid prime search

> Superseded on 17 September 2026 by `READY_TO_PASTE_SLIDES.md`. That file contains the completed seven-graph slide content, updated Graph 4 figures, hybrid theory, speaker notes and appendices. The earlier working draft below is retained for history and must not be pasted as the final version.

Working slide copy and speaker notes. Target: 6 minutes 40 seconds. Names, student IDs and Monash emails: [complete for both presenters]. Pending panels must be completed before the final presentation.

## 1. Objective (15 seconds)

On slide: Find all primes below n using MPI and hybrid MPI + OpenMP. Preserve correctness and distribute the computation evenly.

Say: “We adapted our Week 4 prime search to distributed processes, then added threads within each process. We tested workload alternatives and measured overall speedup.”

## 2. Experiment method and correctness (35 seconds)

On slide: CAAS, Slurm, -O2 compilation. Sequential experiments within an allocation. Three or five repeats, median overall wall-clock time. n=100 produces 25 primes, ending in 97. Large tests at n=100 million produce 5,761,455 primes, ending in 99,999,989.

Say: “We reran the Week 4 serial and OpenMP baselines on CAAS. We checked matching output lists before comparing timings. Overall time includes the work of collecting, sorting and writing the results where required. Queue waiting is not part of program runtime.”

Visual: a cropped genuine CAAS correctness screenshot. Place detailed configuration and hashes in the appendix.

## 3. Task 1: cyclic workload distribution (55 seconds)

On slide: Rank r tests candidate-pair indices r, r+p, r+2p, and so on. Each pair contains 5+6*pair and 7+6*pair, bounded by n. MPI_Bcast shares n. MPI_Gather collects counts. MPI_Gatherv collects variable-length prime lists. Rank 0 sorts and writes.

Figure: `prepared/balance_task1.png`.

Say: “Equal contiguous ranges contain unequal computation costs. Higher ranges can require more divisibility checks. Cyclic distribution spreads these candidate sizes across ranks. The bars show median computation time and whiskers retain every run's variation. At four processes, cyclic reduces median overall time from 4.727 to 3.922 seconds, approximately 17 percent.”

Class support: Topic 7C pages 15-16; extra class around 1:39:54-1:40:50.

## 4. Input-size experiments (40 seconds)

On slide: Graph 1, runtime vs n; Graph 2, empirical speedup vs n. MPI(4) and OpenMP(4), using serial at each matching n as denominator.

Figures: `prepared/graph1.png` and `prepared/graph2.png`. Jobs 130914-130943 supply 30 sizes, 100 to 129 million, with three repeats. All 360 reports and 90 recorded four-file hash comparisons passed local validation.

Say: “Runtime generally increases across the tested range. At four workers, OpenMP achieves about 3.45 to 3.73 times serial speed, while MPI achieves about 3.05 to 3.39 times. OpenMP is faster at every tested size. Speedup fluctuates rather than increasing consistently with n. We retain all repetitions and use medians.”

Appendix: `prepared/DATASET_VALIDATION.md` records variability. One hybrid run at n=101 million spent 3.318 seconds in sorting/output; the cause is not established. The 30 Slurm output files still need collecting for scheduler/node evidence.

## 5. MPI and OpenMP worker scaling (35 seconds)

Figure: `prepared/graph3.png`.

On slide: At 16 workers, MPI achieves 7.71x and OpenMP 9.38x against Week 4 serial. Fixed n=100 million.

Say: “Increasing workers reduced runtime, but speedup was sublinear. Root collection, sorting and file output remain. Pure OpenMP was faster in these single-node measurements. MPI can also operate across nodes, but these results alone do not establish a multi-node advantage.”

Appendix caveat: separate CAAS allocations, three repeats except five for MPI(4), and small timer-boundary differences.

## 6. Task 2: hybrid design and scheduling (45 seconds)

On slide: MPI distributes candidates among processes. OpenMP threads test local candidates with dynamic chunks of 64. Threads mark distinct flag positions; each process collects its local primes before MPI gathering.

Figure: `prepared/balance_task2.png`.

Say: “We compared dynamic(64) with static using identical process and thread counts. At four processes and four threads each, dynamic reduced median overall time from 1.962 to 1.798 seconds, about 8.4 percent. These are per-process measurements. They show faster computation, but do not directly measure individual thread balance or prove an optimal chunk size.”

## 7. Hybrid scaling (45 seconds)

Figures: `prepared/graph4.png` and `prepared/graph5_partial.png`.

On slide: Four MPI processes with 1, 2 and 4 threads each achieve 3.29x, 5.35x and 7.19x speedup. Compare 4 x 4 hybrid with 16-thread OpenMP.

Say: “For Graph 4, the MPI reference remains four processes while we add hybrid threads. For Graph 5, pure OpenMP has the same total workers as the hybrid configuration.”

PENDING: extend Graph 5 with varying MPI process counts using the prepared hybrid experiment. Replace the partial figure before submission.

## 8. Theoretical measurement method (45 seconds)

On slide: Measure the candidate loop and overall time with one MPI process. Residual fraction f=(overall-loop)/overall. Task 1 median f=0.05578. Amdahl own-program reference: 1/[f+(1-f)/p].

Say: “Our model treats the candidate loop as ideally parallel and the remaining time as constant. We measure that fraction using one process, so we do not divide an already-parallel time again. We convert the model to the Week 4 serial baseline so both curves use the same denominator. Added communication overhead is not included in this simple reference.”

Detailed derivation: `THEORY_WORKSHEET.md`. Task 2 fraction remains pending its 1 x 1 measurement.

## 9. Empirical and theoretical speedup (60 seconds)

Figure: `prepared/graph6_model_draft.png`. Graph 7: PENDING hybrid baseline and process/thread matrix.

On slide: Task 1 at 16 processes: idealized reference 8.51x, measured 7.71x. Both use Week 4 serial as baseline.

Say: “The model and measurement separate as the process count rises. The fixed-residual assumption does not capture growing communication costs, changes in sorting/output cost, or imperfect compute scaling. Our communication timers also include waiting, so they are not pure network-transfer measurements.”

Add the measured hybrid result and its assumptions after completing Graph 7. Do not silently use Task 1's serial fraction for Task 2.

## 10. Conclusions (25 seconds)

On slide: Correct output in completed checks. Cyclic improves the tested MPI workload balance. Dynamic(64) improves tested multithreaded hybrid runtime. Remaining overhead limits overall scaling.

Say: “Our measurements justify the chosen methods among the alternatives tested. We preserved all repetitions and measured the complete timed program, including output. We do not claim a universally optimal partitioning algorithm.”

## Q&A and appendix

Use the answers in `PRESENTATION_WORKING_NOTES.md`, especially why Gatherv is needed, why maximum process time matters, why blocking communication includes waiting, and why 4 x 4 needs a 16-thread OpenMP comparison. Know where the timers start and stop in the submitted source.

Keep raw repetitions, workload plots, comparison job IDs, source code, output hashes and sorted prime files available. Add an AI-use declaration matching the assistance actually received and include all required prompt PDFs. Both presenters should practise explaining the code without AI assistance.
