# Remaining experiment runbook

17 September 2026. The original 30-input dataset is complete. This runbook replaces the earlier `hybrid_scaling.job` plan. Use the new files below, not both workflows.

## Upload with WinSCP

Upload `finish_hybrid.job`, `finish_theory.job` and `submit_finish.sh` into `~/FIT3143/Lab2`. The existing `task1.c`, `task2.c` and `lab1_serial.c` must be beside them. The job compiles executables inside each new result directory. Original algorithm source and earlier results remain unchanged.

## First run the small checks

In PuTTY:

```bash
cd ~/FIT3143/Lab2
sed -i 's/\r$//' finish_hybrid.job finish_theory.job submit_finish.sh
sbatch finish_hybrid.job 100 1
sbatch finish_theory.job 100 1 1
```

The first tests one MPI process with 1, 2, 4, 8 and 16 threads; the second tests the two one-worker baselines. Inspect both returned job IDs with `cat slurm-JOBID.out` when they finish. Expect PASS lines, 25 primes and last prime 97. Errors must be resolved before the performance batch.

## Submit missing measurements once

After both checks pass:

```bash
bash submit_finish.sh
```

This submits 15 jobs linked by successful-completion dependencies:

| Jobs | Measurements | Purpose |
| --- | --- | --- |
| 5 | n=100 million; p=1,2,4,8,16; t powers of two up to 16/p; three repeats | 15 hybrid configurations, Graphs 5/7 and hybrid 1x1 reference |
| 10 | Three n values per job, covering 100–129 million; MPI(1) and hybrid(1x1); three repeats | Per-input serial/parallel fractions for theoretical analysis of both tasks |

Each job has a ten-minute limit and uses at most 16 CPUs. Experiments run sequentially. This does not rerun the completed four-implementation dataset. Existing OpenMP 1/2/4/8/16 results supply the matching-worker comparison. Graphs use the same Week 4 serial denominator, with separate allocation limitations disclosed. New serial/MPI reports in the hybrid jobs provide extra checks and context.

The hybrid sweep varies each dimension up to 16 while respecting p*t<=16. It does not run 16x16 on a 16-core allocation. Theory batches retain only the last input's actual prime files under fixed names, with hashes and reports for all inputs. Downloaded original prime-output evidence is already preserved.

## Collect and analyse

Download every `finish_hybrid_100000000_p...` and `finish_theory_...` folder into the local Lab 2 folder, along with their `slurm-...out` files. Retain the small-check outputs as evidence too.

Locally:

```powershell
python complete_analysis.py
```

It regenerates existing charts, checks new output hashes/configurations and generates Graphs 5/7 plus two appendix theory-vs-n figures when complete. Partial datasets cause an explicit error. If multiple jobs repeat the same configuration, select a documented set rather than silently combining them.

Still collect the original 30 `slurm-130914.out` through `slurm-130943.out` files. Job logs and actual compute-node hardware output are useful submission evidence. Capture successful performance output screenshots, not just queue screenshots.

## Model and presentation work

Theoretical speedup uses each implementation's one-worker measured loop and residual times. The model assumes ideal loop scaling and a fixed residual, then converts to the matching Week 4 serial denominator. In hybrid mode, p*t is an approximation because local collection and replicated preparation scale differently with p and t. Communication growth is a reason for disagreement, not an independently fitted correction.

Finalise Graph 6 with those assumptions visible. Review the new curves before replacing the pending Graph 5/7 panels. Include input-size theory in the appendix and refer to its result briefly in the talk.

Complete names/IDs/emails, genuine AI prompt PDFs, the reviewed AI declaration and final slides/export. Refresh the submission draft and manifest after adding results. Existing two-node experiments must be retained and labelled as such, alongside controlled one-node comparisons. The numbered graph requirements allow OpenMP or POSIX, but broader wording mentions both; our selected graph baseline is OpenMP.

## Verification status

All three new shell scripts pass local Bash syntax checks. The analysis script compiles and correctly reports missing measurements with the current data. No new CAAS jobs have been submitted from Codex, and the new job scripts have not yet been compiled/executed on CAAS. The small checks above are required before trusting their outputs.
