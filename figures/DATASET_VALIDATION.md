# 30-input dataset validation

Validated 30 input sizes (100–129 million), 360 program reports and 90 four-file hash comparisons.
All four implementations have identical recorded hashes at each input and repetition. Hashes also match across repetitions for each input.
Prime counts agree across implementations and repetitions. MPI/OpenMP configurations match the experiment design.

These checks use downloaded reports and recorded hashes. The benchmark deleted its prime lists after hashing, so these are not fresh hashes of retained output files. The 30 Slurm logs/accounting records were not supplied in this download; scheduler exit status and node identity remain to be documented.

## Median results

| Implementation | n=100 million (s) | n=129 million (s) | Speedup range |
| --- | ---: | ---: | ---: |
| serial | 12.948174 | 18.371746 | 1.000–1.000x |
| openmp | 3.706730 | 5.170964 | 3.448–3.727x |
| mpi | 3.975437 | 5.548189 | 3.049–3.391x |
| hybrid | 1.662401 | 2.288515 | 6.651–8.180x |

Hybrid uses 16 workers, while MPI/OpenMP here use four. Hybrid results are retained in the CSV but omitted from the equal-worker Graphs 1/2.
Graph 3 continues to use the original scaling experiments. Do not silently replace just its four-process point with this different allocation.

## Repetition variation

- serial: largest (max-min)/median spread 11.9% at n=124,000,000; range 17.256–19.446 seconds.
- openmp: largest (max-min)/median spread 13.8% at n=128,000,000; range 5.151–5.873 seconds.
- mpi: largest (max-min)/median spread 16.3% at n=121,000,000; range 5.180–6.096 seconds.
- hybrid: largest (max-min)/median spread 135.5% at n=101,000,000; range 1.682–4.146 seconds.
