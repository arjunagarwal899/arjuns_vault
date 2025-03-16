from prettytable import PrettyTable


def describe_model(model):
    total_params = 0

    table = PrettyTable(["Module", "Parameters"])
    for module, parameters in model.named_parameters():
        if not parameters.requires_grad:
            continue
        params = parameters.numel()
        table.add_row([module, f"{params:,}"])
        total_params += params
    print(f"Total Parameters: {total_params:,}")
    print(table)
