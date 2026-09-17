# Final results review, 17 September 2026

## Checks completed

- Read the assessment specification and rubric again before preparing the slide content.
- All 15 final result folders are present: hybrid jobs 134608-134612 and theory jobs 134613-134622.
- Validated 75 final hybrid-batch reports: 45 hybrid, 15 MPI and 15 serial.
- Validated 180 one-worker theory reports: 30 inputs x 2 implementations x 3 repeats.
- Configuration checks cover input, process count, rank IDs, hybrid thread count and total workers. Timings are positive and candidate computation does not exceed overall time.
- All 45 recorded three-file hybrid hash groups match the previously checked n=100 million reference.
- All 90 recorded two-file theory hash groups match the original four-implementation dataset for the corresponding input and repetition.
- Recomputed SHA-256 for all 35 retained prime-list files in the new folders. Each matches its final recorded hash. Earlier iterations' overwritten lists can only be checked through their recorded hashes and reports.
- Revalidated the original 30-input dataset: 360 reports, 90 recorded four-file hash groups.
- All 15 Slurm logs contain the expected PASS lines and final results-folder message. This checks log evidence, not a fresh Slurm accounting query.
- Generated and visually inspected Graphs 1-7, both workload-balance charts and both input-size theory appendix plots. No clipping or overlapping text observed.
- No C algorithms or job scripts were changed.

## Final graph set

Use `graph1.png` through `graph7.png`, or matching PDFs. Supplement with `balance_task1`, `balance_task2`, `appendix_theory_n_mpi` and `appendix_theory_n_hybrid`.

Graph 4 now uses job 134610 for both MPI and hybrid. Its hybrid speedups are 2.8823, 5.2121 and 6.8812x, with MPI(4) at 3.1849x. This supersedes the older Graph 4 data, not the separate scheduling comparison.

Graphs 3 and 6 deliberately retain the original complete MPI scaling series. Graphs 5 and 7 use the complete new hybrid series. All fixed-n graphs use the Week 4 serial median 12.928922 s. Input-size graphs use the matching dataset serial median at each n. Do not replace isolated points across independent batches.

Graph 5 uses equal total worker counts. Graph 4 holds MPI processes fixed while adding threads. Graphs 6/7 use measured one-worker fractions and convert Amdahl runtimes to the same serial baseline as empirical speedup.

## Interpretation and limits

- Cyclic is more balanced than the tested block distribution. Dynamic(64) is faster than static in the main 4x4 comparison, but per-rank data does not establish per-thread balance or universal optimality.
- OpenMP is faster than MPI and hybrid in these equal-worker single-node comparisons. Measurements come from separate allocations and small repetition counts.
- The fastest new hybrid median is 2x8 at 1.711639 s (7.5535x). Overlapping repetition ranges prevent a claim of a statistically established best configuration.
- Overall scaling at 16 workers is sublinear. The rubric's HD language includes near-linear overall speedup and optimal distribution, so these checks do not guarantee an HD.
- Amdahl treats the one-worker residual as constant and candidate computation as ideally scalable. Preparation/local collection and communication may actually change with p and t. It is an explicitly approximate reference.
- Thirty distinct n values satisfy the stated count recommendation, but 100-129 million is a narrow input range.

## Remaining submission work

- Paste content from `READY_TO_PASTE_SLIDES.md`, insert the mapped figures and genuine screenshots, and add both presenters' names, IDs and emails.
- Review the AI declaration and export all required prompt records as PDFs.
- Rehearse for 6-7 minutes and practise Q&A without external tools.
- The original 30 dataset Slurm logs (130914-130943) are not in the Lab 2 root. The dataset reports and hashes exist. Download those logs if needed for stronger allocation/completion evidence.
- The old multi-node result folders exist, but their application reports do not show node allocation. Include the original Slurm output or allocation screenshot proving execution across nodes, as required by the specification.
- The numbered graph list allows OpenMP or POSIX Threads. OpenMP is used here. Broader prose mentions both Week 4 parallel tasks, so seek teaching-team clarification if a separate POSIX comparison is expected.
- `submission_draft` remains an older snapshot. It has not been rebuilt during this graph/slide-content task. Refresh it with final figures, notes and evidence before zipping/uploading. No Moodle upload was performed.

Run `python complete_analysis.py` in Lab 2 to rebuild the full final figure set. Old partial/draft graph files remain for history and should not be submitted as final figures.
