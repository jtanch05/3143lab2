# Week 4 baselines on CAAS

lab1_serial.c and lab1_openmp.c are unchanged text copies of Downloads/task1 (2).c
and task3 (2).c. task2 (2).c is Pthreads; we use OpenMP for the comparison graphs.
Original inputs, algorithms, function names, timers and output filenames are retained.

Both use CLOCK_MONOTONIC wall-clock timing despite comments calling it CPU time.
Use Total time (including output) for empirical speedup. Computation time includes
preparation and collection, unlike the isolated MPI computation measurement.
Both produce sorted results directly, so no extra sorting should be added.

Timer boundaries are comparable but not identical: baseline input and OpenMP
configuration are outside the timer and the output-status printf is inside.
MPI input/configuration are inside its overall timer and reporting is outside.
Record these differences in the methodology. Both include prime computation and
file output at n >= 100. Do not use MPI with one process as the Week 4 serial baseline.

The job runs serial and OpenMP with 1, 2, 4, 8 and 16 threads sequentially on one
allocated node. Each step requests the matching CPU count. Results go into a new
lab1_baselines_JOBID folder, preserving the Lab 2 files with the same output names.
Timing reports are saved separately. Prime lists are overwritten each repetition,
compared after each OpenMP run, and the final serial and OpenMP lists are retained.

## Upload and compile

Upload lab1_serial.c, lab1_openmp.c and lab1_baselines.job to CAAS FIT3143/Lab2.
Run each command in PuTTY; stop if compilation fails:

```bash
cd ~/FIT3143/Lab2
sed -i 's/\r$//' lab1_serial.c lab1_openmp.c lab1_baselines.job
module load openmpi/4.1.5-gcc-11.2.0-ux65npg
gcc -O2 lab1_serial.c -lm -o lab1_serial
gcc -O2 -fopenmp lab1_openmp.c -lm -o lab1_openmp
sbatch lab1_baselines.job 100 1
squeue -u $USER
```

Read slurm-JOBID.out using the returned job number. Expect six reports with
25 primes each, five PASS messages, and two final prime values of 97.
Compare against your existing MPI n=100 output if it has not been replaced:

```bash
diff task1_primelist.txt lab1_baselines_JOBID/task1_primelist.txt
```

Replace JOBID with the correctness job number. Once correctness passes:

```bash
sbatch lab1_baselines.job 100000000 3
```

This performs 18 runs within a ten-minute allocation. Download the new results
folder and SLURM log for checking and median timing calculations.
Empirical speedup = Week 4 serial overall time / parallel overall time at the same n.
The 30-n dataset, further hybrid process scaling and theoretical measurements
remain separate work.
