"""Build reproducible figures and tables from saved CAAS logs (no CAAS access).
Run: python prepare_results.py
Requires matplotlib. Original logs and C programs are read-only inputs.
"""
from pathlib import Path
import csv
import re
from statistics import median, mean
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'prepared'
OUT.mkdir(exist_ok=True)
plt.rcParams.update({'font.size': 12, 'axes.spines.top': False,
                     'axes.spines.right': False, 'figure.figsize': (9, 5.5)})

def value(text, pattern):
    match = re.search(pattern, text)
    if not match:
        raise ValueError(f'Missing required log field: {pattern}')
    return float(match[1])

def read_run(path):
    text = path.read_text()
    overall = value(text, r'(?:Overall time[^\n]*?|Total time[^\n]*?): ([\d.]+) seconds')
    compute = value(text, r'(?:Parallel computation time \(max process\)|Computation time): ([\d.]+) seconds')
    communication_match = re.search(r'MPI communication time \(broadcast \+ gather \+ gatherv, max process\): ([\d.]+) seconds', text)
    count = int(value(text, r'Prime numbers found: (\d+)'))
    ranks = [float(t) for _, t in re.findall(r'Process (\d+) computation time: ([\d.]+)', text)]
    return {'source': str(path.relative_to(ROOT)), 'overall': overall,
            'compute': compute,
            'communication': float(communication_match[1]) if communication_match else None,
            'count': count, 'ranks': ranks}

def runs(folder, prefix):
    result = [read_run(p) for p in sorted((ROOT / folder).glob(prefix + '_run_*.txt'))]
    if not result:
        raise ValueError(f'No logs for {folder}/{prefix}')
    if any(r['count'] != 5761455 for r in result):
        raise ValueError('Unexpected n=100 million prime count')
    return result

def csv_file(name, rows):
    with (OUT / name).open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

def save(name, title, ylabel, caption):
    ax = plt.gca()
    ax.set_title(title, pad=15)
    ax.set_ylabel(ylabel)
    ax.grid(axis='y', alpha=.2)
    plt.gcf().text(.02, .02, caption, fontsize=9)
    plt.tight_layout(rect=(0, .09, 1, 1))
    for ext in ('png', 'pdf'):
        plt.savefig(OUT / f'{name}.{ext}', dpi=180)
    plt.close()

serial = runs('lab1_baselines_129504', 'serial')
baseline = median(r['overall'] for r in serial)
workers = [1, 2, 4, 8, 16]
mpi_folders = ['129144', '129145', '129074', '129146', '129147']
mpi = {p: runs('task1_compare_' + job, 'task1') for p, job in zip(workers, mpi_folders)}
omp = {t: runs('lab1_baselines_129504', f'openmp_{t}') for t in workers}
hybrid = {t: runs('task2_compare_' + job, 'task2')
          for t, job in [(1, '129323'), (2, '129324'), (4, '129075')]}
summary, raw = [], []
for name, mapping in [('MPI', mpi), ('OpenMP', omp), ('Hybrid', hybrid)]:
    for k, records in mapping.items():
        p, t = (k, 1) if name == 'MPI' else ((1, k) if name == 'OpenMP' else (4, k))
        med = median(r['overall'] for r in records)
        summary.append(dict(implementation=name, n=100000000, mpi_processes=p,
                            threads_per_process=t, workers=p*t, repeats=len(records),
                            median_overall_s=med, min_overall_s=min(r['overall'] for r in records),
                            max_overall_s=max(r['overall'] for r in records),
                            empirical_speedup=baseline/med))
        for r in records:
            raw.append(dict(implementation=name, processes=p, threads=t, source=r['source'],
                            overall_s=r['overall'], computation_s=r['compute']))
csv_file('scaling_summary.csv', summary)
csv_file('scaling_raw.csv', raw)

balance_rows = []
for task, folder, variants in [
    ('Task 1', 'task1_compare_129074', [('Cyclic', 'task1'), ('Block', 'task1_block')]),
    ('Task 2', 'task2_compare_129075', [('Dynamic(64)', 'task2'), ('Static', 'task2_static')])]:
    plt.figure()
    for j, (label, prefix) in enumerate(variants):
        records = runs(folder, prefix)
        for r in records:
            balance_rows.append(dict(task=task, variant=label, source=r['source'],
                                     rank0_s=r['ranks'][0], rank1_s=r['ranks'][1],
                                     rank2_s=r['ranks'][2], rank3_s=r['ranks'][3],
                                     max_over_mean=max(r['ranks'])/mean(r['ranks']),
                                     overall_s=r['overall']))
        vals = [[r['ranks'][i] for r in records] for i in range(4)]
        mids = [median(v) for v in vals]
        errors = [[m-min(v) for m,v in zip(mids, vals)], [max(v)-m for m,v in zip(mids, vals)]]
        plt.bar([i+(j-.5)*.36 for i in range(4)], mids, .36,
                yerr=errors, capsize=4, label=label)
    plt.xticks(range(4), [f'Rank {i}' for i in range(4)])
    plt.legend()
    save('balance_' + task.lower().replace(' ', ''), task + ': computation time by MPI rank',
         'Computation time (seconds)',
         'n = 100 million; 4 MPI processes' + ('; 4 threads/process' if task == 'Task 2' else '') +
         '\nFive repeats: bars = per-rank medians; whiskers = min/max. All repeats retained.')
csv_file('workload_balance_raw.csv', balance_rows)

plt.figure()
for label, mapping in [('MPI cyclic', mpi), ('OpenMP', omp)]:
    plt.plot(workers, [baseline/median(r['overall'] for r in mapping[p]) for p in workers], 'o-', label=label)
plt.plot(workers, workers, '--', color='grey', label='Linear reference S = workers')
plt.xticks(workers)
plt.xlabel('MPI processes / OpenMP threads')
plt.legend()
save('graph3', 'Equal-worker scaling at n = 100 million', 'Speedup against Week 4 serial',
     'Ratio of median overall times; serial median = %.6f s.\n3 repeats, except MPI(4): 5. Separate CAAS allocations.' % baseline)

plt.figure()
ts = [1, 2, 4]
plt.plot(ts, [baseline/median(r['overall'] for r in hybrid[t]) for t in ts], 'o-', label='Hybrid: 4 MPI processes')
plt.axhline(baseline/median(r['overall'] for r in mpi[4]), linestyle='--', color='orange', label='Task 1: 4 MPI processes')
plt.xticks(ts)
plt.xlabel('OpenMP threads per MPI process')
plt.legend()
save('graph4', 'Hybrid thread scaling with four MPI processes', 'Speedup against Week 4 serial',
     'n = 100 million; total hybrid workers = 4, 8, 16.\nTask 1 reference stays at 4 workers. Ratios of median overall times.')

plt.figure()
for label, ys in [('Hybrid', [baseline/median(r['overall'] for r in hybrid[t]) for t in ts]),
                  ('OpenMP', [baseline/median(r['overall'] for r in omp[4*t]) for t in ts])]:
    plt.plot([4,8,16], ys, 'o-', label=label)
plt.xticks([4,8,16], ['4\nHybrid 4 x 1', '8\nHybrid 4 x 2', '16\nHybrid 4 x 4'])
plt.xlabel('Total workers (OpenMP threads = MPI processes x threads/process)')
plt.legend()
save('graph5_partial', 'PARTIAL: hybrid and OpenMP at equal worker counts', 'Speedup against Week 4 serial',
     'n = 100 million. Process count remains 4 here.\nAdditional MPI-process configurations are required to complete Graph 5.')

# Communication-aware Amdahl model following the Week 7 extra-class example.
# Start with the Week 4 serial program, then add the measured MPI communication
# and blocking time for each target process count.  The predicted runtime is
# equivalent to the fraction form 1 / [rs + rp/p + x(p)].
serial_compute = median(r['compute'] for r in serial)
serial_residual = baseline - serial_compute
theory = []
curves = []
for p in workers:
    communication = 0.0 if p == 1 else median(r['communication'] for r in mpi[p])
    reference = baseline + communication
    rp = serial_compute / reference
    x = communication / reference
    rs = 1 - rp - x
    predicted = serial_residual + serial_compute/p + communication
    class_speedup = 1 / (rs + rp/p + x)
    theory.append(dict(processes=p, serial_overall_s=baseline,
                       serial_computation_s=serial_compute,
                       serial_residual_s=serial_residual,
                       communication_blocking_s=communication,
                       reference_s=reference, rp=rp, rs=rs, x=x,
                       predicted_overall_s=predicted,
                       class_speedup=class_speedup))
    curves.append(dict(processes=p, rp=rp, rs=rs, x=x,
                       communication_blocking_s=communication,
                       predicted_overall_s=predicted,
                       class_speedup=class_speedup,
                       model_week4_baseline=baseline/predicted,
                       empirical_week4_baseline=baseline/median(r['overall'] for r in mpi[p])))
csv_file('theory_mpi_measurements.csv', theory)
csv_file('theory_mpi_curve.csv', curves)
plt.figure()
plt.plot(workers, [r['empirical_week4_baseline'] for r in curves], 'o-', label='Measured MPI')
plt.plot(workers, [r['model_week4_baseline'] for r in curves], 's--', label='Amdahl prediction (Week 4 baseline)')
plt.xticks(workers)
plt.xlabel('MPI processes')
plt.legend()
save('graph6', 'MPI empirical and Amdahl speedup', 'Speedup against Week 4 serial',
     'n = 100 million; serial computation is divided across p processes.\nCommunication term is the median measured MPI communication and blocking time at each p.')
print(f'Serial median: {baseline:.6f}s; serial computation: {serial_compute:.6f}s; serial residual: {serial_residual:.6f}s')
print('Generated balance charts, Graphs 3/4/6, legacy partial Graph 5 and source CSVs in', OUT)

# Validate and plot the downloaded 30-input sweep when it is present.
dataset_folders = sorted(ROOT.glob('dataset_*_*'))
dataset_folders = [d for d in dataset_folders if re.fullmatch(r'dataset_1\d{8}_\d+', d.name)]
if dataset_folders:
    expected = set(range(100000000, 130000000, 1000000))
    actual = [int(d.name.split('_')[1]) for d in dataset_folders]
    if set(actual) != expected or len(actual) != 30:
        raise ValueError('Expected exactly one dataset folder for each of the 30 input sizes')
    data_raw, data_summary = [], []
    names = ['serial', 'openmp', 'mpi', 'hybrid']
    hash_names = {'serial_primelist.txt', 'task3_primelist.txt',
                  'task1_primelist.txt', 'task2_primelist.txt'}
    for folder in dataset_folders:
        n = int(folder.name.split('_')[1])
        if (folder / 'serial_input.txt').read_text().split() != [str(n)]:
            raise ValueError(f'{folder.name}: serial input does not match n')
        if (folder / 'openmp_input.txt').read_text().split() != [str(n), '4']:
            raise ValueError(f'{folder.name}: OpenMP input does not match n/threads')
        records = {name: [] for name in names}
        n_hashes, n_counts = set(), set()
        for repeat in range(1, 4):
            entries = [line.split() for line in (folder / f'prime_hashes_{repeat}.txt').read_text().splitlines() if line.strip()]
            if (len(entries) != 4 or any(len(e) != 2 for e in entries)
                or {e[1] for e in entries} != hash_names
                or any(not re.fullmatch(r'[0-9a-fA-F]{64}', e[0]) for e in entries)
                or len({e[0].lower() for e in entries}) != 1):
                raise ValueError(f'{folder.name}: invalid or unequal hashes in repeat {repeat}')
            n_hashes.add(entries[0][0].lower())
            for name in names:
                path = folder / f'{name}_run_{repeat}.txt'
                r = read_run(path)
                text = path.read_text()
                if not (r['overall'] > 0 and 0 <= r['compute'] <= r['overall']):
                    raise ValueError(f'{path}: inconsistent timings')
                if name in ('mpi', 'hybrid'):
                    if int(value(text, r'\bn: (\d+)')) != n or int(value(text, r'MPI processes: (\d+)')) != 4:
                        raise ValueError(f'{path}: incorrect MPI configuration')
                    if len(r['ranks']) != 4:
                        raise ValueError(f'{path}: missing rank timings')
                if name == 'hybrid' and (int(value(text, r'OpenMP threads per process: (\d+)')) != 4 or int(value(text, r'Total worker threads: (\d+)')) != 16):
                    raise ValueError(f'{path}: incorrect hybrid configuration')
                if name == 'openmp' and int(value(text, r'Threads used: (\d+)')) != 4:
                    raise ValueError(f'{path}: incorrect OpenMP thread count')
                n_counts.add(r['count'])
                records[name].append(r)
                data_raw.append(dict(n=n, implementation=name, repeat=repeat,
                                     overall_s=r['overall'], computation_s=r['compute'],
                                     prime_count=r['count'], sha256=entries[0][0], source=r['source']))
        if len(n_hashes) != 1 or len(n_counts) != 1:
            raise ValueError(f'{folder.name}: output differs across repetitions')
        serial_median = median(r['overall'] for r in records['serial'])
        for name in names:
            vals = [r['overall'] for r in records[name]]
            data_summary.append(dict(n=n, implementation=name, repeats=3,
                                     total_workers={'serial': 1, 'openmp': 4, 'mpi': 4, 'hybrid': 16}[name],
                                     median_overall_s=median(vals), min_overall_s=min(vals),
                                     max_overall_s=max(vals), speedup_vs_serial=serial_median/median(vals),
                                     prime_count=next(iter(n_counts))))
    csv_file('dataset_raw.csv', data_raw)
    csv_file('dataset_summary.csv', data_summary)
    for graph, ylabel in [('graph1', 'Median overall time (seconds)'), ('graph2', 'Speedup against matching Week 4 serial')]:
        plt.figure()
        for name, label in [('serial', 'Serial (1 CPU)'), ('mpi', 'MPI (4 processes)'), ('openmp', 'OpenMP (4 threads)')]:
            rows = [r for r in data_summary if r['implementation'] == name]
            x = [r['n']/1e6 for r in rows]
            y = [r['median_overall_s'] if graph == 'graph1' else r['speedup_vs_serial'] for r in rows]
            plt.plot(x, y, 'o-', markersize=3, label=label)
            if graph == 'graph1':
                plt.fill_between(x, [r['min_overall_s'] for r in rows], [r['max_overall_s'] for r in rows], alpha=.12)
        plt.xlabel('n (millions)')
        plt.legend()
        save(graph, 'Runtime across 30 input sizes' if graph == 'graph1' else 'Empirical speedup across 30 input sizes', ylabel,
             'Three repeats per input; sequential implementations within each allocation.\n' +
             ('Lines = medians; shading = min/max. All repetitions retained.' if graph == 'graph1' else 'Speedup = median serial overall / median parallel overall at the same n.'))
    lines = ['# 30-input dataset validation', '',
             'Validated 30 input sizes (100–129 million), 360 program reports and 90 four-file hash comparisons.',
             'All four implementations have identical recorded hashes at each input and repetition. Hashes also match across repetitions for each input.',
             'Prime counts agree across implementations and repetitions. MPI/OpenMP configurations match the experiment design.',
             '', 'These checks use downloaded reports and recorded hashes. The benchmark deleted its prime lists after hashing, so these are not fresh hashes of retained output files. The 30 Slurm logs/accounting records were not supplied in this download; scheduler exit status and node identity remain to be documented.',
             '', '## Median results', '', '| Implementation | n=100 million (s) | n=129 million (s) | Speedup range |', '| --- | ---: | ---: | ---: |']
    for name in names:
        rows = [r for r in data_summary if r['implementation'] == name]
        lines.append(f"| {name} | {rows[0]['median_overall_s']:.6f} | {rows[-1]['median_overall_s']:.6f} | {min(r['speedup_vs_serial'] for r in rows):.3f}–{max(r['speedup_vs_serial'] for r in rows):.3f}x |")
    lines += ['', 'Hybrid uses 16 workers, while MPI/OpenMP here use four. Hybrid results are retained in the CSV but omitted from the equal-worker Graphs 1/2.',
              'Graph 3 continues to use the original scaling experiments. Do not silently replace just its four-process point with this different allocation.',
              '', '## Repetition variation', '']
    for name in names:
        rows = [r for r in data_summary if r['implementation'] == name]
        worst = max(rows, key=lambda r: (r['max_overall_s']-r['min_overall_s'])/r['median_overall_s'])
        spread = (worst['max_overall_s']-worst['min_overall_s'])/worst['median_overall_s']*100
        lines.append(f"- {name}: largest (max-min)/median spread {spread:.1f}% at n={worst['n']:,}; range {worst['min_overall_s']:.3f}–{worst['max_overall_s']:.3f} seconds.")
    (OUT / 'DATASET_VALIDATION.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    print('\n'.join(lines))
