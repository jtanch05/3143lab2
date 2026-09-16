# Increasing problem-size experiment

Purpose: collect overall timings for 30 distinct n values with fixed resources.
Sizes: 100,000,000 to 129,000,000 inclusive, in steps of 1,000,000.
This deliberately modest range starts at the tested input with measured overall
times above one second. It supports a local scaling trend, not broad asymptotic claims.

Each job handles one n with three repetitions of each implementation:

- Week 4 serial: 1 CPU
- Week 4 OpenMP: 4 threads
- Task 1 cyclic MPI: 4 processes
- Task 2 dynamic(64) hybrid: 4 MPI processes x 4 threads

All four execute sequentially on the same allocated node. The OpenMP/MPI counts
match for the increasing-n comparison. Hybrid has 16 workers here; use the separate
16-thread OpenMP data for a fixed-n equal-worker comparison, not this 4-thread series.
Thirty jobs produce 360 program runs, retaining every timing report.
No C changes or recompilation are needed if the four existing executables are current.

## First validate the combined job

Upload dataset.job and submit_dataset.sh to CAAS ~/FIT3143/Lab2, then run:

```bash
cd ~/FIT3143/Lab2
sed -i 's/\r$//' dataset.job submit_dataset.sh
sbatch dataset.job 100 1
squeue -u $USER
```

Read slurm-JOBID.out using its actual job number. All four reports must say 25
primes, followed by PASS, a line count of 25, and last prime 97.
The combined job's source has been checked locally; CAAS execution remains to be verified.

## Submit the dataset after that passes

```bash
bash submit_dataset.sh
```

Run this once. It submits all 30 jobs and prints their IDs. The next job starts
only after the previous job succeeds; Dependency in squeue is expected.
If a job fails, later jobs wait rather than silently continuing. Inspect the failed
job log before resubmitting anything. Each job has its own ten-minute limit.

## Outputs and storage

Each job creates dataset_N_JOBID containing serial, OpenMP, MPI and hybrid timing
reports for each repetition, input files and output hashes. The SLURM log includes
the allocated node, settings, reports, prime counts and success checks.

After each successful full comparison the job deletes its own four generated
prime lists to avoid exceeding the 5 GB home quota. Their SHA256 hashes remain.
It does not touch previous results or files outside its new results directory.
If a run or comparison fails, the script stops before cleanup for that repetition.

Download all new dataset_N_JOBID folders and their SLURM logs after completion.
Use median overall times, then serial median / parallel median for speedup at each n.
Existing fixed-n worker-scaling results supplement this dataset. Additional hybrid
process scaling and theoretical-model measurements still need to be completed.
