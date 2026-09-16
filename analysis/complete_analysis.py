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
    return [base.read_run(p) for p in paths]

def hashes(path, count):
    entries = [line.split() for line in path.read_text().splitlines() if line.strip()]
    if len(entries) != count or any(len(e)!=2 or not re.fullmatch('[0-9a-fA-F]{64}', e[0]) for e in entries):
        raise ValueError(f'Invalid hash record: {path}')
    values = {e[0].lower() for e in entries}
    if len(values) != 1:
        raise ValueError(f'Output mismatch: {path}')
    return next(iter(values))

def estimate(rr, workers, serial):
    t1 = median(r['overall'] for r in rr)
    f = median((r['overall']-r['compute'])/r['overall'] for r in rr)
    return serial/(t1*(f+(1-f)/workers)), f

folders = list(ROOT.glob('finish_hybrid_100000000_p*_*'))
if folders:
    mapping = {}
    for d in folders:
        p = int(re.fullmatch(r'finish_hybrid_100000000_p(\d+)_\d+', d.name)[1])
        if p in mapping: raise ValueError('Multiple hybrid jobs for same p: select a documented dataset explicitly')
        mapping[p] = d
    if set(mapping) != {1,2,4,8,16}: raise ValueError('Hybrid results require p=1,2,4,8,16')
    configs = []
    reference = records(mapping[1], 'hybrid_p1_t1')
    for p in sorted(mapping):
        d = mapping[p]
        for t in [t for t in [1,2,4,8,16] if p*t<=16]:
            rr = records(d, f'hybrid_p{p}_t{t}')
            if any(r['count'] != 5761455 or len(r['ranks'])!=p for r in rr):
                raise ValueError('Incorrect prime count or rank count')
            for i in (1,2,3):
                hashes(d/f'hashes_t{t}_run_{i}.txt', 3)
                text = (d/f'hybrid_p{p}_t{t}_run_{i}.txt').read_text()
                if int(base.value(text,r'MPI processes: (\d+)'))!=p or int(base.value(text,r'OpenMP threads per process: (\d+)'))!=t:
                    raise ValueError('Incorrect hybrid configuration')
            model,f = estimate(reference, p*t, base.baseline)
            configs.append(dict(p=p,t=t,workers=p*t,overall_s=median(r['overall'] for r in rr),
                                empirical=base.baseline/median(r['overall'] for r in rr),
                                openmp=base.baseline/median(r['overall'] for r in base.omp[p*t]),
                                model=model,serial_fraction=f,source=d.name))
    base.csv_file('hybrid_completed.csv', configs)
    x=list(range(len(configs))); labels=[f"{r['p']}x{r['t']}" for r in configs]
    for graph,other,label in [('graph5','openmp','OpenMP at matching total workers'),('graph7','model','Amdahl reference (constant residual)')]:
        plt.figure(figsize=(11,6))
        plt.plot(x,[r['empirical'] for r in configs],'o-',label='Hybrid measured')
        plt.plot(x,[r[other] for r in configs],'s--',label=label)
        plt.xticks(x,labels,rotation=45); plt.xlabel('MPI processes x threads per process; grouped by process count')
        plt.legend()
        base.save(graph,'Hybrid configurations at n = 100 million','Speedup against Week 4 serial',
                  'Three repeats; total workers <= 16. Separate CAAS allocations.\n'+
                  ('OpenMP threads equal p*t; common Week 4 serial baseline.' if graph=='graph5' else 'Model uses measured hybrid 1x1 fraction; ideal loop scaling, fixed residual.'))
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
    for n,d in sorted(lookup.items()):
        dataset=next(ROOT.glob(f'dataset_{n}_*'))
        serial=median(r['overall'] for r in records(dataset,'serial'))
        for kind,w in [('mpi',4),('hybrid',16)]:
            ref=records(d,f'{kind}_n{n}')
            measured=records(dataset,kind)
            for i in (1,2,3):
                expected=hashes(dataset/f'prime_hashes_{i}.txt',4)
                if hashes(d/f'hashes_n{n}_run_{i}.txt',2)!=expected:
                    raise ValueError('Theory output does not match original dataset')
                if ref[i-1]['count']!=measured[i-1]['count'] or len(ref[i-1]['ranks'])!=1:
                    raise ValueError('Theory count/rank mismatch')
            model,f=estimate(ref,w,serial)
            rows.append(dict(n=n,implementation=kind,workers=w,serial_fraction=f,
                             one_worker_overall_s=median(r['overall'] for r in ref),
                             empirical=serial/median(r['overall'] for r in measured),model=model))
    base.csv_file('theory_input_sizes.csv',rows)
    for kind in ['mpi','hybrid']:
        selected=[r for r in rows if r['implementation']==kind]
        plt.figure()
        for field,label in [('empirical','Measured'),('model','Amdahl reference')]:
            plt.plot([r['n']/1e6 for r in selected],[r[field] for r in selected],'o-',label=label)
        plt.xlabel('n (millions)'); plt.legend()
        base.save('appendix_theory_n_'+kind,kind.upper()+': theory and measurement across input sizes',
                  'Speedup against matching Week 4 serial',
                  'MPI: 4 processes; hybrid: 4x4. Each input has its own measured one-worker fraction.\nIdeal loop scaling and fixed residual at each n; no added communication model.')
    print('Theoretical input-size analysis generated for both tasks at all 30 sizes.')
else:
    print('PENDING: no finish_theory performance folders. Input-size theory not generated.')
