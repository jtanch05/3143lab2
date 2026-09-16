#!/bin/bash
# After smoke tests pass: bash submit_finish.sh
# Submits ONLY missing experiment sets, not the completed dataset.
set -euo pipefail
previous=''
submit() {
    local id
    if [[ -z "$previous" ]]; then
        id=$(sbatch --parsable "$@")
    else
        id=$(sbatch --parsable --dependency="afterok:$previous" "$@")
    fi
    previous=${id%%;*}
    echo "Submitted $previous: $*"
}
for p in 1 2 4 8 16; do
    submit --ntasks="$p" --ntasks-per-node="$p" --cpus-per-task="$((16/p))" finish_hybrid.job 100000000 3
done
for ((n=100000000; n<=127000000; n+=3000000)); do
    submit finish_theory.job "$n" 3 3
done
