import math

import lightning as L
from prettytable import PrettyTable


class MyLightningModule(L.LightningModule):
    def __init__(
        self,
        log_gradients: bool = True,
        print_large_gradient_norms: bool = False,
        large_normalized_gradient_norm_threshold: float = 100.0,
        find_unused_parameters: bool = False,
    ):
        super().__init__()
        self.log_gradients = log_gradients
        self.print_large_gradient_norms = print_large_gradient_norms
        self.large_normalized_gradient_norm_threshold = large_normalized_gradient_norm_threshold
        self.find_unused_parameters = find_unused_parameters

    def print_log(self):
        """Should be called at the end of every epoch to print a table of all metrics that were logged"""
        if self.global_rank != 0:
            return

        numbers = self.trainer.logged_metrics
        numbers = list(numbers.items())
        for i in range(len(numbers)):
            numbers[i] = [*numbers[i][0].split("/"), round(float(numbers[i][1]), 5)]
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
        if self.log_gradients:
            norm = 0.0
            normalized_norm = 0.0
            max_abs = 0.0
            for name, param in self.named_parameters():
                if param.grad is not None:
                    param_norm = param.grad.detach().norm(2).item()
                    normalized_param_norm = param_norm / math.sqrt(param.numel())
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
                        "train_grad/param_normalized_norm": normalized_norm,
                        "train_grad/max_abs": max_abs,
                    },
                    sync_dist=True,
                )
            except Exception:
                print(f"Error in logging gradients {norm}, {max_abs}")

    def on_before_zero_grad(self, optimizer):
        """Should be run to identify all unused parameters in case of "unused parameters" error.
        Use with ddp_find_unused_parameters_true"""
        if self.find_unused_parameters:
            if self.global_rank == 0:
                print("Zero grad params")
                for name, param in self.named_parameters():
                    if param.grad is None:
                        print(name)
                print()
