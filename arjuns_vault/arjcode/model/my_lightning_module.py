import math
from functools import partial

import lightning as L
import torch
from prettytable import PrettyTable
from torch import nn


class MyLightningModule(L.LightningModule):
    def __init__(
        self,
        log_gradients: bool = True,
        print_small_gradient_norms: bool = False,
        print_large_gradient_norms: bool = False,
        small_normalized_gradient_norm_threshold: float = 1e-2,
        large_normalized_gradient_norm_threshold: float = 1e2,
        identify_unused_parameters: bool = False,
    ):
        super().__init__()
        self.log_gradients = log_gradients
        self.print_small_gradient_norms = print_small_gradient_norms
        self.print_large_gradient_norms = print_large_gradient_norms
        self.small_normalized_gradient_norm_threshold = small_normalized_gradient_norm_threshold
        self.large_normalized_gradient_norm_threshold = large_normalized_gradient_norm_threshold
        self.identify_unused_parameters = identify_unused_parameters

    def register_nans_infs_logging_hook(self):
        def identify_nans_infs_hook(module: nn.Module, input, output, module_name):
            nan_weights_names = []
            nan_input_names = []
            nan_outputs_names = []

            # Check weights
            for name, param in module.named_parameters():
                if param is not None and (torch.isnan(param).any() or torch.isinf(param).any()):
                    nan_weights_names.append(name)

            def recurse(data, name="output"):
                if isinstance(data, torch.Tensor):
                    yield name, data
                elif isinstance(data, (list, tuple)):
                    for i, item in enumerate(data):
                        yield from recurse(item, f"{name}.{i}")
                elif isinstance(data, dict):
                    for key, value in data.items():
                        yield from recurse(value, f"{name}.{key}")

            # Check inputs
            if input is not None:
                for name, item in recurse(input):
                    if torch.isnan(item).any() or torch.isinf(item).any():
                        nan_input_names.append(name)

            # Check outputs
            if output is not None:
                for name, item in recurse(output):
                    if torch.isnan(item).any() or torch.isinf(item).any():
                        nan_outputs_names.append(name)

            if nan_weights_names or nan_input_names or nan_outputs_names:
                print(f"NaN detected in {module_name}")
                if nan_weights_names:
                    print("Weights:")
                    print(nan_weights_names)
                if nan_input_names:
                    print("Inputs:")
                    print(nan_input_names)
                if nan_outputs_names:
                    print("Outputs:")
                    print(nan_outputs_names)

        for name, module in self.named_modules():
            module.register_forward_hook(partial(identify_nans_infs_hook, module_name=name))
        print("Identify NaN and Inf hook registered")

    def print_log(self):
        """Should be called at the end of every epoch to print a table of all metrics that were logged"""
        if self.global_rank != 0:
            return

        def split_key(key):
            """Ensures that only a 2-tuple is returned"""
            if "/" not in key:
                return "NO HEADER", key
            splitted = key.split("/")
            if len(splitted) > 2:
                splitted[0] = "/".join(splitted[:-1])
                splitted[1] = splitted[-1]
            return tuple(splitted[:2])

        numbers = self.trainer.logged_metrics
        numbers = list(numbers.items())
        for i, (key, value) in enumerate(numbers):
            value = round(float(value), 5)
            key = split_key(key)
            numbers[i] = key + (value,)
        numbers = sorted(numbers)

        print()
        print()
        print(f"Epoch = {self.current_epoch:<4}")
        table = PrettyTable(["Header", "Metric", "Value"])
        table.add_rows(numbers)
        print(table)
        print()

    def on_after_backward(self):
        # Log gradient info
        if self.training and self.log_gradients:
            norm = 0.0
            normalized_norm = 0.0
            max_abs = 0.0
            for name, param in self.named_parameters():
                if param.grad is not None:
                    param_norm = param.grad.detach().norm(2).item()
                    normalized_param_norm = param_norm / math.sqrt(param.numel())
                    if (
                        self.print_small_gradient_norms
                        and normalized_param_norm < self.small_normalized_gradient_norm_threshold
                    ):
                        print(
                            f"{name.ljust(50)} -- "
                            f"Gradient norm:{param_norm}\t"
                            f"Normalized gradient norm:{normalized_param_norm}"
                        )
                    if (
                        self.print_large_gradient_norms
                        and normalized_param_norm > self.large_normalized_gradient_norm_threshold
                    ):
                        print(
                            f"{name.ljust(50)} -- "
                            f"Gradient norm:{param_norm}\t"
                            f"Normalized gradient norm:{normalized_param_norm}"
                        )
                    norm += param_norm**2
                    normalized_norm += normalized_param_norm**2
                    max_abs = max(max_abs, param.grad.detach().abs().max().item())
            norm = norm**0.5
            normalized_norm = normalized_norm**0.5
            try:
                self.log_dict(
                    {
                        "train_grad/norm": norm,
                        "train_grad/norm_per_param": normalized_norm,
                        "train_grad/max_abs": max_abs,
                    },
                    sync_dist=True,
                    on_step=True,
                    on_epoch=False,
                )
            except Exception:
                print(f"Error in logging gradients {norm}, {max_abs}")

    def on_before_zero_grad(self, optimizer):
        """Should be run to identify all unused parameters in case of "unused parameters" error.
        Use with ddp_identify_unused_parameters_true"""
        if self.identify_unused_parameters:
            if self.global_rank == 0 and self.trainer.global_step > 0:  # Don't run on first step
                print("Zero grad params")
                for name, param in self.named_parameters():
                    if param.grad is None:
                        print(name)
                print()
