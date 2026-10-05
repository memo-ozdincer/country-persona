"""Check original attention and optimizer kernels on the selected Blackwell GPU."""
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys
import torch


def main():
    output = Path(sys.argv[1])
    record = {'packages': dict(sorted((d.metadata['Name'], d.version) for d in importlib.metadata.distributions())),
              'torch_cuda': torch.version.cuda, 'capability': list(torch.cuda.get_device_capability()),
              'device_name': torch.cuda.get_device_name(), 'driver': subprocess.check_output(
                  ['nvidia-smi', '--query-gpu=driver_version', '--format=csv,noheader'], text=True).splitlines()[0]}
    from flash_attn import flash_attn_func
    q = torch.randn(2, 1024, 28, 128, device='cuda', dtype=torch.bfloat16, requires_grad=True)
    try:
        result = flash_attn_func(q, q, q, causal=True)
        result.float().sum().backward()
        torch.cuda.synchronize()
        record['flash_attention_2'] = {'status': 'forward_backward_passed', 'output_finite': bool(result.isfinite().all())}
    except Exception as exc:
        record['flash_attention_2'] = {'status': 'unsupported', 'error': str(exc), 'error_type': type(exc).__name__}
    output.write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps(record['flash_attention_2']), flush=True)
    from deepspeed.ops.adam import FusedAdam
    param = torch.nn.Parameter(torch.ones(1024, device='cuda'))
    optimizer = FusedAdam([param], lr=5e-5, betas=(0.9, 0.98), weight_decay=0)
    param.square().sum().backward()
    optimizer.step()
    torch.cuda.synchronize()
    record['fused_adam'] = {'status': 'one_synthetic_parameter_step_passed', 'parameter_changed': bool((param < 1).all()),
                            'research_model_optimizer_steps': 0}
    output.write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps({k: record[k] for k in ['device_name', 'capability', 'flash_attention_2', 'fused_adam']}), flush=True)


if __name__ == '__main__': main()
