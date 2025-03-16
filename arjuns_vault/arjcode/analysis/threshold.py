import numpy as np
import pandas as pd
from arjcode.analysis.constants import NO_DATA_ERROR, TABLE_COLUMNS
from arjcode.analysis.utils import add_metrics, check_cols, find_nearest, preprocess_data, style_df, thresh
from IPython.display import display
from sklearn.metrics import roc_curve


def threshold_analysis(
    data: pd.DataFrame,
    y_gt_col: str,
    y_scores_col: str,
    thresholds_slice: tuple[float] = (0.4, 0.6 + 1e-5, 0.05),
    desired_sensitivities_slice: tuple[float] = (0.7, 1.0 - 1e-5, 0.05),
    desired_specificities_slice: tuple[float] = (0.7, 1.0 - 1e-5, 0.05),
    custom_thresholds: tuple[float] = (),
    show_only_custom: bool = False,
    strata_cols: list[str] = [],
    far_thresholds: tuple[float, float] = (0.1, 0.9),
    y_gt_desc: str = "No description",
    table_columns: list[str] = TABLE_COLUMNS,
    show_bars: bool = True,
    pm_mode: bool = False,
):
    if pm_mode:
        custom_thresholds = np.linspace(0, 1, 101, endpoint=True)
        show_only_custom = True
        table_columns = ["TP", "FN", "FP", "TN", "Sen", "Spec"]

    print("-------------------------")
    print("GT:".ljust(16), y_gt_col, f"({y_gt_desc})")
    print("Score:".ljust(16), y_scores_col)
    print()

    cols = [y_gt_col, y_scores_col, *strata_cols]
    missing_cols = check_cols(data, cols)
    if len(missing_cols):
        print(f"Missing columns: {missing_cols}")
    else:
        if not strata_cols:
            data = data.copy()
            data["Data"] = "All"
            strata_cols = ["Data"]
            cols += strata_cols

        df = preprocess_data(data, cols)

        if len(df) == 0:
            print(NO_DATA_ERROR)
        else:
            final_df = []
            for _names, _df in df.groupby(strata_cols):
                dfs = []

                # P = len(_df[_df["GT"] == 1])
                # N = len(_df[_df["GT"] == 0])

                def get_threshed_df(x, threshold):
                    x = x.copy()
                    x["Threshold"] = threshold
                    x["Pred"] = thresh(x, "Score", threshold)
                    x["Far FN Pred"] = thresh(x, "Score", far_thresholds[0])
                    x["Far FP Pred"] = thresh(x, "Score", far_thresholds[1])
                    return x

                thresholds = set()

                for threshold in custom_thresholds:
                    threshold = np.round(threshold, 3)
                    threshold = np.clip(threshold, 0, 1)
                    if threshold not in thresholds:
                        thresholds.add(threshold)
                        dfs.append(get_threshed_df(_df, threshold))

                if not show_only_custom:
                    for threshold in np.arange(*thresholds_slice):
                        threshold = np.round(threshold, 3)
                        threshold = np.clip(threshold, 0, 1)
                        if threshold not in thresholds:
                            thresholds.add(threshold)
                            dfs.append(get_threshed_df(_df, threshold))

                    fpr, tpr, roc_thresholds = roc_curve(_df["GT"], _df["Score"])
                    tnr = 1 - fpr

                    for desired_sensitivity in np.arange(*desired_sensitivities_slice):
                        threshold = roc_thresholds[find_nearest(tpr, desired_sensitivity)]
                        threshold = np.round(threshold, 3)
                        threshold = np.clip(threshold, 0, 1)
                        if threshold not in thresholds:
                            thresholds.add(threshold)
                            dfs.append(get_threshed_df(_df, threshold))

                    for desired_specificity in np.arange(*desired_specificities_slice):
                        threshold = roc_thresholds[find_nearest(tnr, desired_specificity)]
                        threshold = np.round(threshold, 3)
                        threshold = np.clip(threshold, 0, 1)
                        if threshold not in thresholds:
                            thresholds.add(threshold)
                            dfs.append(get_threshed_df(_df, threshold))

                    if True:
                        threshold = roc_thresholds[find_nearest(tpr - tnr, 0)]
                        threshold = np.round(threshold, 3)
                        threshold = np.clip(threshold, 0, 1)
                        if threshold not in thresholds:
                            thresholds.add(threshold)
                            dfs.append(get_threshed_df(_df, threshold))

                _df = pd.concat(dfs)
                _df = pd.DataFrame(_df.groupby("Threshold", group_keys=False).apply(add_metrics))
                _df = _df.groupby("Threshold").agg({colname: np.max for colname in table_columns})
                _df = _df.sort_index()
                _names = [_names] if not isinstance(_names, list) else _names
                _df.index = pd.MultiIndex.from_tuples(
                    [(*_names, threshold) for threshold in _df.index], names=[*strata_cols, _df.index.name]
                )
                final_df.append(_df)

            final_df = pd.concat(final_df)
            final_df = style_df(final_df, show_bars)
            display(final_df)
    print("-------------------------")
