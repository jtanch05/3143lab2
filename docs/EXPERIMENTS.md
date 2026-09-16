# Task 1 and Task 2 workload experiments

Keep the original `task1.c` (cyclic) and `task2.c` (dynamic, 64) as the baselines.
The alternatives are separate files with the same helpers, timing boundaries,
prime-testing algorithm, gather operations, sorting and output approach.

| Task | Original | Alternatives | Resources per comparison job |
| --- | --- | --- | --- |
| 1 | task1.c: cyclic | task1_block.c: contiguous blocks | 4 MPI processes, 2 per node, 1 CPU per process |
| 2 | task2.c: dynamic, 64 | task2_static.c: static | 4 MPI processes, 2 per node, 4 threads per process |

Task 1 block boundaries use `total_pairs * my_rank / p` (inclusive) and
`total_pairs * (my_rank + 1) / p` (exclusive). These ranges cover all candidate
pairs exactly once and differ in length by at most one pair. Ranks may receive
empty ranges for very small inputs. Primes 2 and 3 are still added by the root.

## 1. Upload

In WinSCP, upload these four new files from this folder into your existing CAAS
folder `/srv/home/jtan0493/FIT3143/Lab2`:

- task1_block.c
- task2_static.c
- task1_compare.job
- task2_compare.job

Keep task1.c and task2.c there as well. No changes are needed to the original job files.

## 2. Compile in PuTTY

Run each command and stop if it reports an error:

```bash
cd ~/FIT3143/Lab2
sed -i 's/\r$//' task1_block.c task2_static.c task1_compare.job task2_compare.job
module load openmpi/4.1.5-gcc-11.2.0-ux65npg
mpicc -O2 task1.c -lm -o task1
mpicc -O2 task1_block.c -lm -o task1_block
mpicc -O2 -fopenmp task2.c -lm -o task2
mpicc -O2 -fopenmp task2_static.c -lm -o task2_static
```

## 3. Check correctness first

```bash
sbatch task1_compare.job 100 1
```

Record the returned job number. Use `squeue -u $USER` to wait, then read
`cat slurm-12345.out`, replacing 12345 with that job number.
Expect two prime counts of 25, last values of 97, and the PASS message.

Then run:

```bash
sbatch task2_compare.job 100 1
```

Read its corresponding SLURM output after completion. Expect two prime counts
of 25, last values of 97, and the PASS message. The jobs stop on a failed run or
a difference between output files. If a job disappears from the queue without a
PASS message, inspect its log and `sacct -j JOB_ID --format=JobID,State,ExitCode`.

## 4. Compare performance after correctness passes

```bash
sbatch task1_compare.job 10000000 3
```

Wait for completion and inspect the log, then:

```bash
sbatch task2_compare.job 10000000 3
```

The first argument is n; the second is the number of repetitions **per variant**.
Task 1 performs 6 program runs; Task 2 performs 6. The 10-minute time limit covers
the entire comparison job. Start with these values before increasing n.

Each job runs its variants sequentially on the same allocated nodes. The original
programs use their original filenames, but run inside a new job-specific results
folder, so the previous correctness output in Lab2 remains available.
Each repetition's timing report is saved separately. Prime lists are checked
after each repetition and overwritten by the next repetition within that job.

For Task 1, compare overall time and the spread between the four rank computation
times. For Task 2, compare overall and parallel computation time. Use the median
of the three runs and note variability; do not pick a winner from a single run.
These small experiments use a fixed variant order; repeat a close result with
the order reversed before making a strong conclusion.

If times are mostly below one second, try 20000000, then 50000000, subject to the
whole-job limit. The 100-input test cannot measure scheduling performance:
dynamic chunk size 64 exceeds the local iteration count in that small run.

Send the two correctness logs first. Then send the two larger comparison logs
so we can select and justify the workload distributions from measured results.
Do not change the final source files based on assumptions about which is faster.
