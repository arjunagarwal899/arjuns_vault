import pandas as pd
from prettytable import PrettyTable


def describe_model(model, describe_frozen: bool = False):
    information = pd.DataFrame(columns=["Module"]).set_index("Module")

    for module, parameter in model.named_parameters():
        parameter: nn.Parameter
        if not describe_frozen and not parameter.requires_grad:
            continue
        information.loc[module, "Device"] = parameter.device
        information.loc[module, "Parameters"] = parameter.numel()

    information.loc["TOTAL", "Parameters"] = information["Parameters"].sum()
    information.loc["TOTAL", "Device"] = "N/A"

    information = information.reset_index()
    information = information.astype({"Parameters": int})

    information["Parameters"] = information["Parameters"].apply(lambda x: f"{x:,}")

    description = information.iloc[:-1]
    summary = information.iloc[-1:]

    table = PrettyTable(information.columns.tolist())
    table.add_rows(description.values.tolist())
    table.add_divider()
    table.add_rows(summary.values.tolist())
    print(table)


if __name__ == "__main__":
    from torch import nn

    # Example usage
    model = nn.Sequential(nn.Linear(10, 20), nn.ReLU(), nn.Linear(20, 10))
    model[0].to("cuda:0")
    describe_model(model)
