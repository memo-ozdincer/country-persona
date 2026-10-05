"""Launch only on an empty selected GPU and record positively identified project descendants."""
import argparse
from datetime import datetime, timezone
import importlib.metadata
import json
import os
from pathlib import Path
import socket
import subprocess
import time


def write(path, data):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(data, indent=2) + '\n')
    temporary.replace(path)


def identity(pid):
    proc = Path('/proc') / str(pid)
    stat = proc.joinpath('stat').read_text().rsplit(')', 1)[1].split()
    ticks = int(stat[19])
    boot = next(int(l.split()[1]) for l in Path('/proc/stat').read_text().splitlines() if l.startswith('btime '))
    return {'host': socket.gethostname(), 'pid': pid, 'parent_pid': int(stat[1]),
            'process_start_ticks': ticks, 'process_start_utc': datetime.fromtimestamp(
                boot + ticks / os.sysconf('SC_CLK_TCK'), timezone.utc).isoformat(),
            'command': [x.decode() for x in proc.joinpath('cmdline').read_bytes().split(b'\0') if x]}


def descendants(root):
    found = {root}
    changed = True
    while changed:
        changed = False
        for proc in Path('/proc').iterdir():
            if not proc.name.isdigit() or int(proc.name) in found: continue
            try:
                stat = proc.joinpath('stat').read_text().rsplit(')', 1)[1].split()
                if int(stat[1]) in found:
                    found.add(int(proc.name)); changed = True
            except (FileNotFoundError, ProcessLookupError, PermissionError): pass
    return found


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gpu-uuid', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--cwd', type=Path, required=True)
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[0] == '--' else args.command
    args.output.mkdir(parents=True, exist_ok=False)
    rows = subprocess.check_output(['nvidia-smi', '--query-gpu=uuid,name,memory.used,utilization.gpu,index',
                                    '--format=csv,noheader,nounits'], text=True).splitlines()
    selected = [r.split(',') for r in rows if r.split(',')[0].strip() == args.gpu_uuid]
    processes = subprocess.check_output(['nvidia-smi', '--query-compute-apps=gpu_uuid,pid,process_name',
                                         '--format=csv,noheader'], text=True).splitlines()
    occupied = [r for r in processes if r.split(',')[0].strip() == args.gpu_uuid]
    if len(selected) != 1 or int(selected[0][2]) != 0 or int(selected[0][3]) != 0 or occupied:
        raise RuntimeError('Selected GPU is occupied; all existing processes left untouched')
    env = os.environ.copy()
    # vLLM 0.11's device introspection parses numeric IDs; keep the UUID as the ownership anchor.
    env['CUDA_DEVICE_ORDER'] = 'PCI_BUS_ID'
    env['CUDA_VISIBLE_DEVICES'] = selected[0][4].strip()
    env['OMP_NUM_THREADS'] = '8'
    env['TOKENIZERS_PARALLELISM'] = 'false'
    env['HF_HUB_OFFLINE'] = '1'
    env['WANDB_MODE'] = 'disabled'
    reference_root = Path('/mfs1/u/memo/country-persona-research/reference-reproductions/20261004')
    headers = reference_root / 'python-headers/usr/include'
    includes = str(headers / 'python3.12') + ':' + str(headers)
    for key in ['C_INCLUDE_PATH', 'CPLUS_INCLUDE_PATH', 'CPATH']:
        env[key] = includes + (':' + env[key] if env.get(key) else '')
    env['CUDA_HOME'] = str(reference_root / 'cuda-12.8')
    env['PATH'] = str(reference_root / 'cuda-12.8/bin') + ':' + env['PATH']
    env['TORCH_EXTENSIONS_DIR'] = str(reference_root / 'torch-extensions')
    env['TRITON_CACHE_DIR'] = str(reference_root / 'triton-cache')
    env['TORCHINDUCTOR_CACHE_DIR'] = str(reference_root / 'torchinductor-cache')
    env['VLLM_CACHE_ROOT'] = str(reference_root / 'vllm-cache')
    env['MAX_JOBS'] = '4'
    launch = {'status': 'launching', 'launcher': identity(os.getpid()), 'command': command,
              'cwd': str(args.cwd), 'run_directory': str(args.output.resolve()),
              'gpu_uuids': [args.gpu_uuid], 'gpu_name': selected[0][1].strip(),
              'cuda_visible_devices': env['CUDA_VISIBLE_DEVICES'], 'cuda_device_order': env['CUDA_DEVICE_ORDER'],
              'memory_used_mib_before_launch': 0, 'slurm_job_id': None,
              'started_utc': datetime.now(timezone.utc).isoformat(), 'owned_processes': []}
    write(args.output / 'launch.json', launch)
    known = {}
    start = time.monotonic()
    with (args.output / 'console.log').open('w') as log:
        child = subprocess.Popen(command, cwd=args.cwd, env=env, stdout=log, stderr=subprocess.STDOUT)
        launch['child'] = identity(child.pid)
        write(args.output / 'launch.json', launch)
        while child.poll() is None:
            for pid in descendants(child.pid):
                try:
                    item = identity(pid)
                    known[(pid, item['process_start_ticks'])] = item
                except (FileNotFoundError, ProcessLookupError): pass
            launch['status'] = 'running'
            launch['owned_processes'] = list(known.values())
            launch['elapsed_seconds'] = time.monotonic() - start
            write(args.output / 'launch.json', launch)
            time.sleep(5)
    launch.update(status='completed' if child.returncode == 0 else 'failed', exit_code=child.returncode,
                  ended_utc=datetime.now(timezone.utc).isoformat(), elapsed_seconds=time.monotonic() - start)
    write(args.output / 'launch.json', launch)
    print(json.dumps({k: launch[k] for k in ['status', 'exit_code', 'elapsed_seconds', 'gpu_name']}), flush=True)
    raise SystemExit(child.returncode)


if __name__ == '__main__': main()
