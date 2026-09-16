# FIT3143 Lab 2 — Experiment and Presentation Working Notes

**17 September update:** all 30 input folders downloaded and locally validated: 360 program reports, 90 matching four-file hash groups, consistent counts/configurations. Graphs 1/2 are now generated; see `prepared/DATASET_VALIDATION.md` for measured trends and variability. The older submission-only status below is historical. The 30 Slurm `.out` files are still absent locally, so scheduler exit status and node evidence have not been verified from those logs.

This is the working source for the final 6–7 minute presentation. It records what was tested, what the results mean, and what evidence is still missing. Do not copy every table onto the slides; use the key graphs and keep the detailed numbers for Q&A.

**Preparation artifacts now available:** `presentation.md` contains the current slide copy and speaker notes. `prepared/` contains the two workload-balance charts, Graphs 3/4, partial Graph 5, a draft Task 1 Amdahl Graph 6, and reproducible CSV calculations. `THEORY_WORKSHEET.md` explains the model and baseline conversion. `NEXT_STEPS.md` covers the remaining CAAS work. `submission_draft/` contains evidence copies, genuine screenshots and labelled prime files. Use these newer artifacts where the earlier planning text below still describes theory/figures as pending. Task 2 theory and the 30-value dataset remain incomplete.

**Updated 16 September 2026:** the 30-value dataset has been submitted as jobs `130914`–`130943`, for `n = 100,000,000` to `129,000,000`. Submission is confirmed; successful completion and results have not yet been checked. Do not rerun it simply to prepare slides. The combined-script `n = 100` correctness run (`129656`) passed. No program changes are needed for this outline.

## 1. Main claim

The experiments support two final implementation choices:

- **Task 1:** cyclic MPI workload distribution.
- **Task 2:** cyclic MPI distribution with OpenMP `schedule(dynamic, 64)` inside each MPI process.

Both choices preserve correctness. At `n = 100,000,000` on one CAAS node, cyclic MPI was more balanced and about 17% faster overall than block MPI at four processes. The hybrid dynamic schedule was about 8.4% faster overall than static at four MPI processes and four OpenMP threads per process.

The final presentation must not claim that these are universally best. They were the best of the tested alternatives under the controlled CAAS configurations.

## 2. Experiment method

### Environment and controls

- Experiments ran on Monash CAAS under Slurm.
- The compared variants ran **sequentially inside the same allocation**, avoiding competition for the same CPU and memory resources.
- Every comparison used the same `n`, process/thread configuration, compiler optimisation and output rules.
- C programs were compiled with `-O2`.
- MPI programs used `mpicc`; hybrid programs also used `-fopenmp`.
- Each timed configuration was repeated three or five times; the **median overall time** is reported.
- Correctness was checked by prime count, last prime, `diff`, and for the large runs by matching SHA-256 hashes.
- Speedup uses the rerun Week 4 serial implementation on CAAS:

  `speedup = serial overall time / parallel overall time`

### Timing scope

The reported overall time includes computation, required MPI communication, sorting and file output. This matches the rubric's emphasis on overall performance rather than computation alone.

There is one limitation to disclose: the Week 4 and Lab 2 timers are comparable but not perfectly identical. The Week 4 timer starts after input/setup, whereas the MPI timer begins after `MPI_Init` and includes input/configuration. Both include computation and file output. This small boundary difference matters most for very short runs, which is why the final graphs should use runs longer than roughly one second.

### Why use maximum process time?

Parallel completion is limited by the slowest process. Therefore, computation and communication summaries use the maximum process time rather than an average that could hide imbalance.

## 3. Correctness evidence

### Small correctness test: `n = 100`

All variants produced:

- 25 primes;
- last prime `97`;
- identical prime-list files.

This was checked for:

- Task 1 cyclic and block;
- Task 2 dynamic and static;
- Week 4 serial and OpenMP with 1, 2, 4, 8 and 16 threads.

### Large correctness test: `n = 100,000,000`

All saved prime lists contained:

- 5,761,455 primes;
- last prime `99,999,989`;
- the same SHA-256 hash.

This confirms that the workload and scheduling changes affected performance, not the result.

## 4. Task 1 — MPI implementation

### Design

Each MPI process receives the same upper bound `n`. It independently tests its assigned candidates, stores local primes, and participates in collective communication so rank 0 can combine, sort and write the complete result.

Important MPI operations:

- `MPI_Bcast`: sends the input to every process.
- `MPI_Gather`: collects each process's local prime count.
- `MPI_Gatherv`: collects different numbers of primes from the processes.
- `MPI_Reduce` with `MPI_MAX`: records the slowest process time.

### Workload alternatives

**Cyclic distribution** assigns candidates in a round-robin pattern. For process `r` among `p` processes, its candidates are spaced by `p`.

**Block distribution** assigns each process one contiguous interval.

Primality tests for larger candidates generally require more trial divisions. With block distribution, the process owning the high-number interval therefore receives more expensive work. Cyclic distribution mixes small and large candidates across ranks and improves balance.

### Workload-selection result at `n = 100,000,000`, four processes, one node

| Variant | Median max computation time | Median overall time | Observation |
| --- | ---: | ---: | --- |
| Cyclic | 3.121986 s | 3.922206 s | Rank times were close to one another |
| Block | 4.027106 s | 4.726977 s | Rank times ranged roughly 1.93–4.03 s |

Cyclic reduced median overall time by approximately **17.0%** relative to block:

`(4.726977 - 3.922206) / 4.726977 × 100 ≈ 17.0%`

### Process scaling at `n = 100,000,000`

| Processes | Cyclic overall median | Block overall median | Cyclic speedup vs serial |
| ---: | ---: | ---: | ---: |
| 1 | 13.239176 s | 13.247327 s | 0.98× |
| 2 | 7.012439 s | 8.342937 s | 1.84× |
| 4 | 3.922206 s | 4.726977 s | 3.30× |
| 8 | 2.486940 s | 2.817344 s | 5.20× |
| 16 | 1.677054 s | 1.796585 s | 7.71× |

Interpretation:

- One MPI process is slightly slower than serial because MPI adds setup and collection overhead without adding parallelism.
- Increasing processes reduces computation time, but speedup is sublinear.
- Sorting, output and MPI collection remain and eventually limit overall speedup.
- Cyclic and block are almost identical with one process because there is no inter-process distribution difference.
- Cyclic becomes more useful as the work is divided among multiple processes.

### Comparison with Week 4 OpenMP at equal worker counts

Serial median overall time: **12.928922 s**.

| Workers | OpenMP overall | OpenMP speedup | MPI cyclic overall | MPI speedup |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 13.048655 s | 0.99× | 13.239176 s | 0.98× |
| 2 | 6.838205 s | 1.89× | 7.012439 s | 1.84× |
| 4 | 3.702183 s | 3.49× | 3.922206 s | 3.30× |
| 8 | 2.132696 s | 6.06× | 2.486940 s | 5.20× |
| 16 | 1.377939 s | 9.38× | 1.677054 s | 7.71× |

OpenMP was faster in these one-node tests. A plausible explanation is its shared-memory collection strategy, whereas MPI gathers distributed results and rank 0 sorts them. These tests compare whole implementations and do not isolate the cause of the gap. MPI supports multiple nodes, whereas this OpenMP implementation is limited to shared memory; this is a capability distinction, not evidence of a measured multi-node speed advantage.

## 5. Task 2 — Hybrid MPI + OpenMP

### Design

MPI divides the global candidate space between processes. OpenMP then divides each process's assigned candidates among its local threads. This produces two levels of parallelism:

`total workers = MPI processes × OpenMP threads per process`

For example, `4 MPI × 4 OpenMP = 16 total worker threads`.

### OpenMP scheduling alternatives

**Static scheduling** divides loop iterations among threads in advance. It has low scheduling overhead but cannot react when some candidate ranges take longer.

**Dynamic scheduling with chunk size 64** gives threads small chunks during execution. A thread that finishes early requests another chunk, improving balance at the cost of scheduling overhead.

The specification asks for different workload-distribution approaches; it does not require every OpenMP schedule. Comparing static with dynamic(64) is a focused experiment and avoids unnecessary variants.

### Scheduling result at `n = 100,000,000`, four MPI processes

| Threads per process | Total workers | Dynamic(64) overall | Static overall | Interpretation |
| ---: | ---: | ---: | ---: | --- |
| 1 | 4 | 3.930754 s | 3.896378 s | Static marginally faster; no useful thread balancing with one thread |
| 2 | 8 | 2.416699 s | 2.726167 s | Dynamic approximately 11.4% faster |
| 4 | 16 | 1.798036 s | 1.962138 s | Dynamic approximately 8.4% faster |

Dynamic(64) was faster in every paired repeat at two and four threads per process. It is retained as the final Task 2 schedule because it improves balance when each MPI process actually has multiple OpenMP workers.

### Hybrid scaling and comparisons

| Configuration | Total workers | Hybrid overall | Hybrid speedup | Equal-worker OpenMP speedup |
| --- | ---: | ---: | ---: | ---: |
| 4 MPI × 1 thread | 4 | 3.930754 s | 3.29× | 3.49× at 4 threads |
| 4 MPI × 2 threads | 8 | 2.416699 s | 5.35× | 6.06× at 8 threads |
| 4 MPI × 4 threads | 16 | 1.798036 s | 7.19× | 9.38× at 16 threads |

Interpretation:

- Adding OpenMP threads improves hybrid performance while the MPI process count remains fixed.
- Hybrid speedup is sublinear because MPI collection, root sorting and output do not shrink in proportion to the number of workers.
- On one node, pure OpenMP remains faster at equal total worker counts because it avoids inter-process communication and duplicated MPI-process state.
- Hybrid MPI + OpenMP is still important for multi-node systems: MPI handles communication between nodes while OpenMP uses the cores within each node.

## 6. Variability and limitations

- Short `n = 10,000,000` runs were useful for correctness and early comparisons, but most overall times were below one second. They should not be the main performance evidence.
- Initial two-node `n = 100,000,000` Task 1 results were variable and briefly reversed the block/cyclic ordering. Controlled one-node, five-repeat results were more stable and showed the expected cyclic advantage.
- CAAS is a shared cluster. Queue placement, nodes and system load can create noise even with the same requested resources.
- The MPI communication measurement includes time spent waiting inside collective operations. It can therefore reflect workload imbalance as well as data-transfer cost.
- Medians reduce the effect of isolated slow runs, but the final presentation should still acknowledge run-to-run variation.

## 7. Required seven graphs and current status

| Graph | Required comparison | Status |
| ---: | --- | --- |
| 1 | MPI vs OpenMP runtime as `n` increases; serial included for context | **Ready:** prepared/graph1.png, 30 sizes and three repeats |
| 2 | MPI vs OpenMP empirical speedup as `n` increases, both relative to serial | **Ready:** prepared/graph2.png, matching serial baseline at each n |
| 3 | MPI vs OpenMP empirical speedup at equal process/thread counts | **Data ready** for 1, 2, 4, 8 and 16 workers |
| 4 | Hybrid vs Task 1 MPI speedup as OpenMP threads increase at fixed MPI processes | **Ready for 4 MPI with 1, 2 and 4 threads** |
| 5 | Hybrid vs OpenMP at matching total worker counts, varying MPI processes and threads | **Partial:** 4 × 1, 4 × 2 and 4 × 4 ready; MPI-process variation still needed |
| 6 | Task 1 empirical vs theoretical speedup as MPI processes increase | **Draft model ready:** see THEORY_WORKSHEET.md and prepared/graph6_model_draft.png |
| 7 | Task 2 empirical vs theoretical speedup as processes/threads increase | **Partly ready; more hybrid process scaling and theory needed** |

Do not manufacture the missing lines. Finish the dataset and theoretical analysis, then replace the status text with final figure references.

Source: specification PDF pages 6–7. The numbered graph requirements explicitly allow POSIX Threads **or** OpenMP; these graphs use OpenMP. The introductory paragraph also mentions both Week 4 parallel tasks, so retain awareness of that broader wording, but do not label POSIX a missing mandatory graph series. Confirm with the teaching team if they expect additional coverage beyond the numbered graphs.

For the submitted `n` sweep, MPI and OpenMP both use four workers. Hybrid uses 4 processes × 4 threads, so its results must not be presented as an equal-worker comparison with the four-thread OpenMP series. Use the separate matching-worker experiments for Graph 5.

## 8. Slide plan for a 6–7 minute presentation

The specification suggests approximately 3 minutes for Task 1, 2 minutes for Task 2 and 2 minutes for performance/theory. Use the following **6 minutes 40 seconds** rehearsal budget, leaving 20 seconds before the seven-minute maximum. Q&A is separate. Speaker notes below are prompts to explain in our own words, not text to paste onto slides.

| Slide | Time | Cumulative | Main evidence |
| --- | ---: | ---: | --- |
| 1. Objective | 15 s | 0:15 | Problem and team details |
| 2. Method and correctness | 35 s | 0:50 | Correctness logs; timer boundaries |
| 3. MPI design and distribution | 55 s | 1:45 | Cyclic/block comparison |
| 4. Runtime and speedup vs input size | 40 s | 2:25 | Graphs 1–2, pending |
| 5. MPI worker scaling | 35 s | 3:00 | Graph 3 |
| 6. Hybrid design and scheduling | 45 s | 3:45 | Dynamic/static comparison |
| 7. Hybrid worker scaling | 45 s | 4:30 | Graphs 4–5, latter incomplete |
| 8. Theory measurement method | 45 s | 5:15 | Model parameters, pending |
| 9. Empirical vs theoretical | 60 s | 6:15 | Graphs 6–7, pending |
| 10. Conclusions | 25 s | 6:40 | Supported findings and limitations |

### Slide 1 — Title and objective (15 seconds)

- Open MPI and hybrid MPI + OpenMP prime search.
- Goal: preserve correctness while improving performance through balanced workload distribution.
- One-line result: cyclic MPI and dynamic(64) hybrid were the strongest tested choices.

Visual: a simple diagram showing serial → MPI processes → OpenMP threads.

Add both presenters' names, student IDs and Monash emails. Leave placeholders until confirmed.

### Slide 2 — Experimental method and correctness (35 seconds)

- CAAS, Slurm, one-node controlled comparisons.
- Same input/resources within each comparison.
- Three or five repeats; report medians.
- Overall time includes compute, communication, sorting and output.
- Correctness checked before performance claims.

Visual: compact experiment pipeline, not a wall of text.

On-slide correctness callout: `n = 100: 25 primes, last = 97, files match`. Large-input callout: `n = 100 million: 5,761,455 primes, last = 99,999,989`.

Speaker cue: “CAAS allocates the resources; MPI coordinates the processes. We ran compared variants sequentially and report median overall wall-clock time, not computation alone.” Keep exact hardware/compiler versions in the appendix after verification; do not invent them.

### Slide 3 — Cyclic distribution balances MPI work (55 seconds)

- Explain rank, process count, cyclic and block assignment.
- Explain why larger candidates are generally more expensive.
- Show cyclic vs block rank-time imbalance and the 17% overall improvement at four processes.

Visual: two small candidate-distribution diagrams plus one compact bar chart.

Use **candidate-pair indices**, not individual integers, in the distribution diagram: cyclic rank `r` gets pairs `r, r+p, r+2p, ...`; each pair tests `5+6*pair` and the next candidate two numbers later, within the bound. Block gives contiguous pair-index ranges. Root handles 2 and 3.

Short code-flow caption: `Bcast(n) → local prime search → Gather(counts) → Gatherv(primes) → root sort/write`. Explain counts are gathered first because local prime counts differ.

On-slide result: cyclic **3.922 s**, block **4.727 s**, approximately **17% lower overall time** at `n = 100 million`, four MPI processes, five repetitions. Do not call a 17% time reduction a 17% speedup.

### Slide 4 — Runtime and speedup as input size grows (40 seconds)

- Use required Graphs 1–2 side by side, with readable axes.
- Graph 1: `n` vs median overall seconds; MPI(4) and OpenMP(4), optionally serial.
- Graph 2: `n` vs speedup; both denominators are serial at that same `n`.
- **Pending:** insert curves only after jobs `130914`–`130943` are validated.

Speaker cue to complete later: “Across this tested input range, [measured trend].” Do not predict monotonic speedup or extrapolate from the narrow 100–129 million range.

### Slide 5 — More MPI processes reduce time, but not linearly (35 seconds)

- Required Graph 3: workers 1, 2, 4, 8 and 16 vs empirical speedup, MPI and OpenMP at equal worker counts.
- Fixed `n = 100 million`; serial median **12.929 s**.
- At 16 workers: MPI **7.71×**, OpenMP **9.38×**.

Speaker cue: “Prime testing scales, but collection, root sorting and file writing remain. OpenMP was faster on one node in these tests; that does not show MPI is unsuitable for multiple nodes.” Include repeat counts in captions: MPI four-process point uses five repeats, other scaling points and OpenMP use three. Baselines were rerun on CAAS, but not all series share the same allocation.

### Slide 6 — Hybrid design and scheduling choice (45 seconds)

- Explain the two-level hierarchy: processes between memory spaces, threads inside each process.
- Compare static with dynamic(64).
- Show the 1-, 2- and 4-thread scheduling table or chart.
- State that dynamic helps only when multiple threads can share uneven work.

Visual: four MPI process boxes, each containing four thread markers. Threads write to distinct flag positions; each process then collects its local results before MPI gathering. Describe this simply rather than adding a new abstraction.

On-slide result at 4 × 4: dynamic(64) **1.798 s**, static **1.962 s**, approximately **8.4% lower overall time**. Speaker cue: “Dynamic assigns another chunk to a free thread. Our measurements support this choice; we did not directly measure every thread's workload. With one thread, static was slightly faster.”

### Slide 7 — Hybrid scaling and equal-worker comparisons (45 seconds)

- Use required Graphs 4–5.
- Always compare against equal total workers: e.g. `4 MPI × 4 OpenMP = 16`, so compare with 16 OpenMP/POSIX threads.
- Explain why hybrid remains behind pure OpenMP on one node but enables multi-node use.

Graph 4: fixed four MPI processes; hybrid thread counts 1, 2, 4 yield **3.29×, 5.35×, 7.19×** speedup. Task 1 MPI(4) stays a constant **3.30×** reference. These are all speedups against Week 4 serial, not ratios of hybrid to MPI.

Graph 5: label configurations explicitly as `p × t`; compare OpenMP with `p*t` threads. Current data vary `t` at `p=4` only. **Pending:** add process-count variation before calling this graph complete.

### Slide 8 — How we measure the theoretical model (45 seconds)

- Empirical: `S = T_Week4_serial / T_parallel`, using overall time at matching `n`.
- **Pending:** choose and justify the class-taught Amdahl or Gustafson method and identify actual measured serial/parallel regions.
- Show the measurement configuration, timer boundaries, fraction calculation and baseline explicitly.

Speaker cue: “Theoretical speedup is a model with assumptions, not a fitted target.” If using fixed-work Amdahl, the reference formula is `S(w) = 1 / (f + (1-f)/w)`. Do not fill in `f` until its measurement is defensible. A model relative to the parallel program's one-worker time is not automatically normalized to the Week 4 serial baseline; reconcile that before overlaying curves.

Do not sum separate per-rank phase maxima to estimate a serial fraction: they can come from different ranks and include overlapping waiting. Hybrid `w=p*t` is an approximation requiring explanation, because changing processes and changing threads affect different overheads. A hybrid 1 × 1 reference may be needed; it is not yet available in the recorded results.

### Slide 9 — Empirical vs theoretical speedup (60 seconds)

- Use required Graphs 6–7.
- State the selected model and measured serial fraction.
- Explain the gap using communication, load imbalance, sorting/output and shared-cluster variability.
- Do not present a theoretical curve until its assumptions and inputs are documented.

### Slide 10 — Conclusions and limitations (25 seconds)

- Correct results for every tested variant.
- Cyclic MPI improved balance; dynamic(64) improved hybrid balance.
- Parallel speedup was sublinear because non-parallel work and communication remain.
- Mention timing-boundary and CAAS-variability limitations.
- End with one sentence about what would improve next: larger controlled multi-node experiments or distributed sorting/output.

### Q&A / appendix (outside the 6:40 presentation)

Keep backup slides for raw repetitions, correctness hashes, job configuration and timing definitions. These support answers without crowding the main presentation.

Also retain the variable two-node results, per-rank computation times, model derivation and AI declaration. Do not remove inconvenient runs or describe the final schedule as universally optimal. Follow the required AI prompt-PDF submission process; no AI tools during the assessed presentation/Q&A.

## 9. Likely Q&A answers

### Why did you choose cyclic rather than block distribution?

The cost of primality testing is not uniform: larger candidates generally require more divisibility checks. Block distribution concentrates expensive candidates in the high-number rank. Cyclic distribution mixes candidate sizes across ranks, producing closer per-rank computation times and a lower median overall time.

### Why not test every OpenMP schedule and chunk size?

The requirement is to experiment with different workload-distribution approaches, not exhaust every parameter. Static and dynamic(64) represent a clear low-overhead versus load-balancing comparison. Dynamic(64) consistently won with multiple threads, so further schedule searching was not necessary for the final implementation.

### Why use `MPI_Gatherv`?

Different processes find different numbers of primes. `MPI_Gatherv` lets rank 0 receive a different element count from every process. A regular `MPI_Gather` would require equal counts or padding.

### Why is MPI communication time sometimes large?

A blocking collective includes waiting. If one process finishes its computation later, earlier processes wait inside the collective. The recorded value can therefore contain both real communication cost and the effect of workload imbalance.

### Why is OpenMP faster than MPI on one node?

OpenMP threads share one address space and do not need to gather separate result arrays between processes. MPI adds process setup, collective communication and root-side collection. MPI is designed to scale beyond a single shared-memory node.

### Why is speedup not equal to the number of workers?

Only the prime-testing work scales strongly. MPI setup, communication, sorting and file output remain, and additional workers introduce coordination overhead. Load imbalance and CAAS variability add further losses.

### Why use the median?

CAAS timings can include occasional delays from system activity. The median represents the typical run without allowing one unusually slow repetition to dominate the result.

### Is `4 MPI × 4 OpenMP` compared with four or sixteen OpenMP threads?

Sixteen. The fair shared-memory comparison uses the same total number of workers: `4 × 4 = 16`.

## 10. Remaining work before the final slides

1. Collect and validate the already-submitted 30-value dataset; check completion, repetitions and correctness before calculating medians.
2. Retain Week 4 serial as the empirical baseline and OpenMP as the selected shared-memory graph comparison.
3. Complete hybrid scaling with more MPI-process configurations for Graphs 5 and 7.
4. Calculate theoretical speedup using the class-taught Amdahl or Gustafson method and document the measured fraction used.
5. Generate all seven graphs with readable axes, units, legends and captions.
6. Replace this document's pending graph entries with final observations.
7. Build and rehearse the final 6–7 minute deck.
8. Add the generative-AI declaration and upload prompt records as PDFs.

## 11. Files and evidence to preserve

- Final source: `task1.c`, `task2.c`.
- Workload alternatives: `task1_block.c`, `task2_static.c`.
- CAAS comparison folders for correctness and timing evidence.
- Week 4 serial/OpenMP baseline outputs.
- Slurm `.out` files and job scripts.
- Final raw CSV, calculation sheet and graph source.
- AI prompt-record PDFs and declaration.

## 12. Teaching-team announcement: submission evidence and workload balance

Source: announcement and staff replies pasted by the student on 16 September 2026. This supplements the original specification. Staff also confirmed that a ZIP upload is acceptable.

### Submission checklist

- [ ] Final `task1.c` and `task2.c`, slides/documentation and student details.
- [ ] CAAS `.job` files actually used, including comparison/baseline/dataset scripts relevant to the reported experiments. Include `submit_dataset.sh` for reproducibility.
- [ ] Genuine screenshots of CAAS terminal commands and program output. Show the CAAS prompt, job ID/configuration, per-process timings and correctness checks clearly. Do not expose passwords or fabricate terminal evidence.
- [ ] Sorted prime-number output files for Task 1 and Task 2, labelled with their input and originating job. Preserve the actual files, not only their hashes.
- [ ] Supporting Slurm logs, workload comparison results, benchmark measurements and graph/calculation sources.
- [ ] AI declaration and prompt-record PDFs.
- [ ] Check the ZIP contents and Moodle upload limits before submitting. If the work is already submitted and extra files cannot be added, request return to draft through the teaching contact in the announcement.

Existing local output files include `task1_compare_129074/task1_primelist.txt` and `task2_compare_129075/task2_primelist.txt` for `n = 100,000,000`. Preserve these. The dataset script removes its generated prime lists after checks to save storage, so its hashes alone are insufficient for this new file-evidence requirement. Existing retained outputs mean we do not need to repeat all 30 jobs just to obtain prime-list evidence. The announcement does not specify whether every benchmark's prime list must be included; confirm if needed rather than assuming a representative pair meets every expectation.

Screenshots supplied in chat still need collecting into the submission folder. No PNG screenshots were found in the local `Lab 2` folder during this check. Keep existing screenshots showing successful runs, and capture any missing command/output evidence from CAAS. Job submission alone demonstrates submission, not successful execution.

### Workload balance evidence for Slides 3 and 6

The staff clarification asks students aiming for D/HD to demonstrate balanced or optimal workload distribution. Per-MPI-process computational timings are one suggested method. Our existing logs already contain these measurements, so start with them rather than changing the program.

For each variant, chart rank 0–3 on the horizontal axis and computation seconds on the vertical axis. Use all five repetitions from the same configuration, with per-rank medians and min/max whiskers. Label `n = 100,000,000`, four MPI processes, and threads per process. These supporting workload charts are additional to the seven required performance graphs.

- **Task 1:** use `task1_compare_129074/task1_run_*.txt` and `task1_block_run_*.txt`. Cyclic rank times are roughly 3.12 seconds in repeats 2–5, whereas block rank times increase from roughly 1.93 to 4.03 seconds. Keep the slower cyclic first repetition visible in the variability summary. Explain how cyclic assignment spreads candidate-testing cost, then connect this to the 17% median overall-time reduction.
- **Task 2:** use `task2_compare_129075/task2_run_*.txt` and `task2_static_run_*.txt`. Dynamic rank times across the five runs range roughly 0.784–0.899 seconds. Static ranges roughly 1.006–1.248 seconds. Show actual rank measurements alongside the 8.4% median overall-time reduction. Faster completion supports the selected schedule, but it does not by itself prove improved balance between MPI ranks.

Optional simple summary: for each run compute `max(rank compute time) / mean(rank compute time)`. A value close to 1 indicates similar process completion times. Calculate it within each run before summarising repetitions. This is a balance indicator, not speedup or parallel efficiency. Per-rank measurements do not directly reveal balance among OpenMP threads inside a rank.

Suggested conclusion: “Cyclic MPI distributes the tested workload more evenly than block. Dynamic(64) gives lower computation and overall times than static in our tested multithreaded hybrid configurations. These experiments justify our selected methods among the alternatives tested.” Avoid claiming proof of a globally optimal algorithm or a guaranteed grade.
