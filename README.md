# FIT3143 Lab 2

Submission-support files for the Message Passing Interface assessment.

## Required implementation files

- `src/task1.c` - Open MPI prime-search implementation.
- `src/task2.c` - Hybrid Open MPI + OpenMP prime-search implementation.

## Comparison implementations

- `src/task1_block.c` - block-distribution comparison for Task 1.
- `src/task2_static.c` - static-scheduling comparison for Task 2.

## Supporting material

- `docs/` - presentation draft, theory notes, experiment notes, and reproducibility documentation.
- `figures/` - generated performance figures and supporting CSV data.
- `analysis/` - scripts and slide-data inputs used to generate the figures.
- `jobs/` - CAAS/Slurm job and submission scripts.
- `evidence/screenshots/` - screenshots showing correctness checks and CAAS job submission.
- `evidence/prime_outputs/` - sorted prime-number output files from representative Task 1 and Task 2 runs.
- `evidence/caas_logs/` - supplementary CAAS run reports and Slurm output available locally.

## Submission status

This repository is a preparation snapshot, not the final Moodle submission. Before submitting, review and complete the presentation, replace any partial/draft figures, add student names/IDs/emails, and include the AI declaration and prompt-record PDFs required by the assessment specification.

The repository now includes the available CAAS evidence requested by the teaching-team announcement. It does not include AI declaration/prompt-record PDFs because those must be exported from the actual AI conversation and reviewed for accuracy before submission.
