"""Run after downloading finish_hybrid_* and finish_theory_* folders.
Reuses the existing plotting/data reader. Refuses incomplete performance sets.
"""
import re
from statistics import median
import matplotlib.pyplot as plt
import prepare_results as base

ROOT, OUT = base.ROOT, base.OUT

def records(folder, prefix):
    paths = sorted(folder.glob(prefix + '_run_*.txt'))
    if [p.name for p in paths] != [f'{prefix}_run_{i}.txt' for i in (1,2,3)]:
        raise ValueError(f'{folder}/{prefix}: need exactly three repetitions')
    result = [base.read_run(p) for p in paths]
    for r in result:
        if not (r['overall'] > 0 and 0 <= r['compute'] <= r['overall']):
            raise ValueError(f"Invalid timings: {r['source']}")
    return result

def hashes(path, count):
    entries = [line.split() for line in path.read_text().splitlines() if line.strip()]
    if len(entries) != count or any(len(e)!=2 or not re.fullmatch('[0-9a-fA-F]{64}', e[0]) for e in entries):
        raise ValueError(f'Invalid hash record: {path}')
    expected_names = {2: {'task1_primelist.txt', 'task2_primelist.txt'},
                      3: {'reference_primelist.txt', 'task1_primelist.txt', 'task2_primelist.txt'},
                      4: {'serial_primelist.txt', 'task3_primelist.txt', 'task1_primelist.txt', 'task2_primelist.txt'}}
    if {e[1] for e in entries} != expected_names[count]:
        raise ValueError(f'Unexpected hash filenames: {path}')
    values = {e[0].lower() for e in entries}
    if len(values) != 1:
        raise ValueError(f'Output mismatch: {path}')
    return next(iter(values))

def check_config(folder, prefix, n, p, t=None):
    for i in (1, 2, 3):
        text = (folder/f'{prefix}_run_{i}.txt').read_text()
        if int(base.value(text, r'\bn: (\d+)')) != n or int(base.value(text, r'MPI processes: (\d+)')) != p:
            raise ValueError(f'Incorrect MPI configuration: {folder}/{prefix}')
        ranks = [int(r) for r in re.findall(r'Process (\d+) computation time:', text)]
        if sorted(ranks) != list(range(p)):
            raise ValueError(f'Incorrect rank IDs: {folder}/{prefix}')
        if t is not None and (int(base.value(text, r'OpenMP threads per process: (\d+)')) != t
                              or int(base.value(text, r'Total worker threads: (\d+)')) != p*t):
            raise ValueError(f'Incorrect thread configuration: {folder}/{prefix}')

def communication_aware_model(serial_overall, serial_compute, communication, workers):
    """Week 7 MPI Amdahl form: rs + rp/workers + x(communication)."""
    reference = serial_overall + communication
    rp = serial_compute / reference
    x = communication / reference
    rs = 1 - rp - x
    predicted = (serial_overall - serial_compute) + serial_compute/workers + communication
    return {
        'model': serial_overall / predicted,
        'predicted_overall_s': predicted,
        'rp': rp,
        'rs': rs,
        'x': x,
    }

folders = list(ROOT.glob('finish_hybrid_100000000_p*_*'))
if folders:
    mapping = {}
    for d in folders:
        p = int(re.fullmatch(r'finish_hybrid_100000000_p(\d+)_\d+', d.name)[1])
        if p in mapping: raise ValueError('Multiple hybrid jobs for same p: select a documented dataset explicitly')
        mapping[p] = d
    if set(mapping) != {1,2,4,8,16}: raise ValueError('Hybrid results require p=1,2,4,8,16')
    configs = []
    validation_raw = []
    serial_compute = median(r['compute'] for r in base.serial)
    for p in sorted(mapping):
        d = mapping[p]
        if (d/'serial_input.txt').read_text().split() != ['100000000']:
            raise ValueError('Incorrect serial input')
        for kind in ('serial', 'mpi'):
            extra = records(d, kind)
            if any(r['count'] != 5761455 for r in extra):
                raise ValueError('Incorrect baseline prime count')
            validation_raw.extend(dict(implementation=kind, **r) for r in extra)
        check_config(d, 'mpi', 100000000, p)
        for t in [t for t in [1,2,4,8,16] if p*t<=16]:
            rr = records(d, f'hybrid_p{p}_t{t}')
            check_config(d, f'hybrid_p{p}_t{t}', 100000000, p, t)
            validation_raw.extend(dict(implementation='hybrid', **r) for r in rr)
            if any(r['count'] != 5761455 or len(r['ranks'])!=p for r in rr):
                raise ValueError('Incorrect prime count or rank count')
            for i in (1,2,3):
                if hashes(d/f'hashes_t{t}_run_{i}.txt', 3) != 'fb7e00e2e7eb157e21837f89d0911c01729ebbbd9a18f8608f6e3936b9f953ee':
                    raise ValueError('Hybrid output differs from the original n=100 million reference')
                text = (d/f'hybrid_p{p}_t{t}_run_{i}.txt').read_text()
                if int(base.value(text,r'MPI processes: (\d+)'))!=p or int(base.value(text,r'OpenMP threads per process: (\d+)'))!=t:
                    raise ValueError('Incorrect hybrid configuration')
            communication = median(r['communication'] for r in rr)
            theory = communication_aware_model(base.baseline, serial_compute, communication, p*t)
            configs.append(dict(p=p,t=t,workers=p*t,overall_s=median(r['overall'] for r in rr),
                                min_overall_s=min(r['overall'] for r in rr),max_overall_s=max(r['overall'] for r in rr),
                                empirical=base.baseline/median(r['overall'] for r in rr),
                                openmp=base.baseline/median(r['overall'] for r in base.omp[p*t]),
                                communication_blocking_s=communication, source=d.name, **theory))
    base.csv_file('hybrid_completed.csv', configs)
    base.csv_file('finish_hybrid_raw.csv', validation_raw)
    # Keep Graph 4 consistent with Graphs 5/7 and compare against MPI in the same job.
    fixed = [r for r in configs if r['p'] == 4]
    mpi4 = records(mapping[4], 'mpi')
    mpi4_speedup = base.baseline/median(r['overall'] for r in mpi4)
    plt.figure()
    plt.plot([r['t'] for r in fixed], [r['empirical'] for r in fixed], 'o-', label='Hybrid: 4 MPI processes')
    plt.axhline(mpi4_speedup, linestyle='--', color='orange', label='Task 1: 4 MPI processes (same job)')
    plt.xticks([1,2,4]); plt.xlabel('OpenMP threads per MPI process'); plt.legend()
    base.save('graph4', 'Hybrid thread scaling with four MPI processes', 'Speedup against Week 4 serial',
              'n = 100 million; three repeats; MPI and hybrid from job 134610.\nHybrid uses 4, 8, 16 workers; MPI stays at 4. Same serial baseline as Graphs 5/7.')
    base.csv_file('graph4_reference.csv', [dict(mpi_processes=4, overall_s=median(r['overall'] for r in mpi4),
                                             empirical=mpi4_speedup, source=mapping[4].name)])
    x=list(range(len(configs))); labels=[f"{r['p']}x{r['t']}" for r in configs]
    for graph,other,label in [('graph5','openmp','OpenMP at matching total workers'),('graph7','model','Amdahl prediction (Week 4 baseline)')]:
        plt.figure(figsize=(11,6))
        plt.plot(x,[r['empirical'] for r in configs],'o-',label='Hybrid measured')
        plt.plot(x,[r[other] for r in configs],'s--',label=label)
        plt.xticks(x,labels,rotation=45); plt.xlabel('MPI processes x threads per process; grouped by process count')
        for boundary in (4.5, 8.5, 11.5, 13.5):
            plt.axvline(boundary, color='grey', alpha=.25, linewidth=1)
        plt.ylim(bottom=0)
        plt.legend()
        base.save(graph,'Hybrid configurations at n = 100 million','Speedup against Week 4 serial',
                  'Three repeats; total workers <= 16. Separate CAAS allocations.\n'+
                  ('OpenMP threads equal p*t; common Week 4 serial baseline.' if graph=='graph5' else 'Model uses Week 4 serial computation and measured communication/blocking at each p x t.'))
    print('Graphs 5 and 7 generated from 15 measured hybrid configurations.')
else:
    print('PENDING: no finish_hybrid performance folders. Graphs 5/7 not generated.')

theory_folders = [d for d in ROOT.glob('finish_theory_*_*') if int(d.name.split('_')[2])>=100000000]
if theory_folders:
    lookup={}
    for d in theory_folders:
        for path in d.glob('mpi_n*_run_1.txt'):
            n=int(re.search(r'mpi_n(\d+)',path.name)[1])
            if n in lookup: raise ValueError('Duplicate theory input; select runs explicitly')
            lookup[n]=d
    if set(lookup)!=set(range(100000000,130000000,1000000)):
        raise ValueError('Theory sweep incomplete: expected all 30 inputs')
    rows=[]
    theory_raw=[]
    for n,d in sorted(lookup.items()):
        dataset=next(ROOT.glob(f'dataset_{n}_*'))
        serial=median(r['overall'] for r in records(dataset,'serial'))
        for kind,w in [('mpi',4),('hybrid',16)]:
            ref=records(d,f'{kind}_n{n}')
            theory_raw.extend(dict(n=n, implementation=kind, **r) for r in ref)
            check_config(d, f'{kind}_n{n}', n, 1, 1 if kind == 'hybrid' else None)
            measured=records(dataset,kind)
            for i in (1,2,3):
                expected=hashes(dataset/f'prime_hashes_{i}.txt',4)
                if hashes(d/f'hashes_n{n}_run_{i}.txt',2)!=expected:
                    raise ValueError('Theory output does not match original dataset')
                if ref[i-1]['count']!=measured[i-1]['count'] or len(ref[i-1]['ranks'])!=1:
                    raise ValueError('Theory count/rank mismatch')
            serial_compute = median(r['compute'] for r in records(dataset, 'serial'))
            communication = median(r['communication'] for r in measured)
            theory = communication_aware_model(serial, serial_compute, communication, w)
            rows.append(dict(n=n,implementation=kind,workers=w,
                             serial_overall_s=serial, serial_computation_s=serial_compute,
                             communication_blocking_s=communication,
                             empirical=serial/median(r['overall'] for r in measured), **theory))
    base.csv_file('theory_input_sizes.csv',rows)
    base.csv_file('theory_baseline_raw.csv',theory_raw)
    for kind in ['mpi','hybrid']:
        selected=[r for r in rows if r['implementation']==kind]
        plt.figure()
        for field,label in [('empirical','Measured'),('model','Amdahl reference')]:
            plt.plot([r['n']/1e6 for r in selected],[r[field] for r in selected],'o-',label=label)
        plt.xlabel('n (millions)'); plt.legend()
        base.save('appendix_theory_n_'+kind,kind.upper()+': theory and measurement across input sizes',
                  'Speedup against matching Week 4 serial',
                  'MPI: 4 processes; hybrid: 4x4. Each input uses its serial computation time.\nCommunication term is the median measured MPI communication and blocking time.')
    print('Theoretical input-size analysis generated for both tasks at all 30 sizes.')
else:
    print('PENDING: no finish_theory performance folders. Input-size theory not generated.')
