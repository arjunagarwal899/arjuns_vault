from time import perf_counter

import psutil
import torch
from torch import nn


def profile(device, model: nn.Module, *model_args, **model__kwargs):
    # Track memory before execution
    torch.cuda.reset_peak_memory_stats()
    process = psutil.Process()
    initial_mem = process.memory_info().rss  # in bytes

    tic = perf_counter()
    sample_output = model(*model_args, **model__kwargs)
    toc = perf_counter()
    forward_time = toc - tic

    loss: torch.Tensor = sample_output.sum()
    tic = perf_counter()
    loss.backward()
    toc = perf_counter()
    backward_time = toc - tic

    final_mem = process.memory_info().rss  # in bytes

    print()
    if device != torch.device("cpu"):
        print(f"GPU: {torch.cuda.max_memory_allocated(device) / 2**30} GB peak mem used")
    print(f"RAM: {(final_mem - initial_mem) / 2**30} GB peak mem used")
    print(f"Time (forward): {forward_time:.3f} s")
    print(f"Time (backward): {backward_time:.3f} s")
    print(f"Time (backward): {backward_time:.3f} s")
