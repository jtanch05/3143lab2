# Prepared while the CAAS dataset waits

**Current remaining-work instructions:** follow `FINISH_RUNBOOK.md`. It supersedes the smaller `hybrid_scaling.job` experiment below with complete 1–16 dimension coverage and a per-input theory reference sweep. Do not submit both workflows.

Update, 17 September: all 30 result folders have been downloaded and validated (360 reports, 90 matching hash groups). Graphs 1/2 and dataset CSVs are in `prepared/`. Do not repeat the dataset. The instructions below for collecting Slurm logs remain useful for the submission evidence. Next compute work is the supplementary hybrid experiment.

The original 30 jobs are already submitted. Do not rerun submit_dataset.sh.

## Ready locally

- `presentation.md`: slide copy, speaker notes and timings.
- `prepared/`: two rank-balance charts, Graphs 3 and 4, partial Graph 5, draft model Graph 6, PNG/PDF versions and calculation CSVs.
- `THEORY_WORKSHEET.md`: measured Task 1 fraction and normalization; Task 2 pending.
- `prepare_results.py`: rebuilds these results from original logs.
- `hybrid_scaling.job`: supplementary hybrid configurations and 1 x 1 baseline, prepared but not submitted or tested on CAAS.
- `submission_draft/`: local evidence copies and manifest. This is incomplete and not yet a final Moodle package.

## Current CAAS jobs

Check `squeue -u $USER` occasionally. When it is empty, confirm job completion rather than assuming success. For a particular job, use `sacct -j JOBID --format=JobID,State,ExitCode,Elapsed`. A failed predecessor can leave later jobs waiting on dependencies.

Once all 30 finish successfully, combine their logs in CAAS:

```bash
cd ~/FIT3143/Lab2
cat slurm-{130914..130943}.out > dataset_all_results.txt
```

Download that file and the dataset result folders with WinSCP. The combined log is convenient for review; retain the per-run records and hashes as evidence. Validate 30 distinct n values, three repeats and three PASS messages per job before graphing. A complete set should contain 360 program results and 90 successful four-program comparisons. Graphs 1 and 2 remain pending these actual data.

## Additional hybrid run, when ready

Upload `hybrid_scaling.job` beside the existing `task2.c` on CAAS. This new job compiles its own executable inside its result directory and retains a reference prime list. It does not use or overwrite the dataset executables.

```bash
cd ~/FIT3143/Lab2
sed -i 's/\r$//' hybrid_scaling.job
sbatch hybrid_scaling.job 100 1
```

After it finishes, inspect that job's slurm output. All configurations must match, with 25 primes ending in 97. Then submit the performance run:

```bash
sbatch hybrid_scaling.job 100000000 3
```

This collects p=1,2,4 and t=1,2,4 (nine configurations) sequentially, at most 16 total CPUs. The 10-minute limit is a limit, not a queue-time estimate. It adds process variation for Graphs 5/7 and a 1 x 1 hybrid model reference. It does not extend hybrid tests to every possible process/thread count; MPI and OpenMP baseline scaling already cover 1 through 16 workers.

## Evidence and final handoff

Review `submission_draft/README.md`. Add final completed dataset logs, hybrid results and hardware details, finish seven graphs, then rehearse the 6:40 script. Confirm names/IDs/emails and preserve genuine screenshots. Export the final slides/documentation and AI records as required. The announcement allows ZIP submission; check the actual Moodle size limit before creating/uploading the final archive.

No CAAS job has been submitted by this preparation work. The additional job has a local Bash syntax check only; actual compilation and execution still require CAAS.
