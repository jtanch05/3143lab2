#!/bin/bash
# Run from ~/FIT3143/Lab2 AFTER the dataset.job correctness check passes.
# 30 distinct sizes: 100,000,000 through 129,000,000, step 1,000,000.
# Dependencies keep jobs sequential and stop later jobs if a predecessor fails.
set -e
previous_job=""
for ((i = 0; i < 30; i++))
do
    n=$((100000000 + i * 1000000))
    if [ -z "$previous_job" ]; then
        job_id=$(sbatch --parsable dataset.job "$n" 3)
    else
        job_id=$(sbatch --parsable --dependency="afterok:$previous_job" dataset.job "$n" 3)
    fi
    job_id=${job_id%%;*}
    echo "n=$n job=$job_id"
    previous_job=$job_id
done
