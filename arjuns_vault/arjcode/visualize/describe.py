import pandas as pd
from prettytable import PrettyTable


def describe_model(model):
    information = pd.DataFrame(columns=["Module"]).set_index("Module")

    for module, parameters in model.named_parameters():
        if not parameters.requires_grad:
            continue
        params = parameters.numel()
        information.loc[module, "Parameters"] = params

    information.loc["TOTAL", "Parameters"] = information["Parameters"].sum()

    information = information.reset_index()
    information = information.astype({"Parameters": int})

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
    describe_model(model)
