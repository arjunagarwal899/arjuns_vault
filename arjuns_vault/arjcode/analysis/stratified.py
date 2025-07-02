import pandas as pd
from arjcode.analysis.constants import NO_DATA_ERROR, TABLE_COLUMNS
from arjcode.analysis.utils import (
    add_metrics,
    check_cols,
    get_thresh_cols,
    get_uncertain,
    preprocess_data,
    style_df,
    thresh,
)
from IPython.display import display


def stratified_analysis(
    data: pd.DataFrame,
    y_gt_col: str,
    y_scores_col: str,
    strata_cols: list[str] = [],
    unpack_strata_cols: bool = False,
    threshold: float = 0.5,
    far_thresholds: tuple[float, float] = (0.1, 0.9),
    uncertainty_ranges: list[tuple[float, float]] = [(0.4, 0.6)],
    y_gt_desc: str = "No description",
    limit: int = None,
    table_columns=TABLE_COLUMNS,
    show_bars: bool = True,
    return_df: bool = False,
):
    if not return_df:
        print("-------------------------")
        print("GT:".ljust(16), y_gt_col, f"({y_gt_desc})")
        print("Score:".ljust(16), y_scores_col)
        print("Threshold:".ljust(16), threshold)
        print("Far thresholds:".ljust(16), far_thresholds)
        print()

    if not strata_cols:
        data = data.copy()
        data["Data"] = "All"
        strata_cols = ["Data"]

    uncertainty_colnames = []
    for uncertainty_range in uncertainty_ranges:
        uncertainty_colnames.append(f"[{uncertainty_range[0]}, {uncertainty_range[1]})")

    cols = [y_gt_col, y_scores_col, *strata_cols]
    thresh_cols = get_thresh_cols(threshold)
    other_cols = list(set(thresh_cols) - set(cols))

    missing_cols = check_cols(data, cols + other_cols)
    if missing_cols:
        print(f"Missing columns: {missing_cols}")
    else:
        df = preprocess_data(data, cols, other_cols)
        df["Pred"] = thresh(df, "Score", threshold)
        df["Far FN Pred"] = thresh(df, "Score", far_thresholds[0])
        df["Far FP Pred"] = thresh(df, "Score", far_thresholds[1])
        for i, uncertainty_range in enumerate(uncertainty_ranges):
            df[f"Uncertain{i}"] = get_uncertain(df["Score"], uncertainty_range)

        if len(df) == 0:
            print(NO_DATA_ERROR, f"({strata_cols})")
        else:
            if unpack_strata_cols:
                for strata_col in strata_cols:
                    if isinstance(df[strata_col].values[0], (list, tuple)):
                        indices = df.index
                        new_rows = []
                        for i in indices:
                            new_row = df.loc[i].to_dict()
                            for val in df.loc[i, strata_col]:
                                new_row[strata_col] = str(val)
                                new_rows.append(new_row)
                        df = df.drop(index=indices)
                        df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)

            df = pd.DataFrame(
                df.groupby(strata_cols, sort=False)
                .apply(lambda x: add_metrics(x, uncertainty_ranges, uncertainty_colnames))
                .reset_index(drop=True)
            )
            df = df.groupby(strata_cols, sort=False).agg(
                {colname: "max" for colname in table_columns}
                | {uncertainty_colname: "max" for uncertainty_colname in uncertainty_colnames}
            )

            if limit is not None:
                df = df.sort_values("Total", ascending=False)
                df = df.iloc[: min(limit, len(df))]

            df.index = df.index.astype(str)
            df = df.sort_index()

            if not return_df:
                df = style_df(df, show_bars)
                display(df)
    if not return_df:
        print("-------------------------")
    else:
        return df
