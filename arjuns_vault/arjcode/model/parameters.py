from torch import nn


def freeze_module(module: nn.Module):
    for param in module.parameters():
        param.requires_grad = False
    module.eval()


def freeze_modules(modules: list[nn.Module]):
    for module in modules:
        freeze_module(module)


def unfreeze_module(module: nn.Module):
    module.train()
    for param in module.parameters():
        param.requires_grad = True
    module.eval()


def unfreeze_modules(modules: list[nn.Module]):
    for module in modules:
        unfreeze_module(module)
