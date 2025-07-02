import itertools

import numpy as np
import pandas as pd
from confidenceinterval import roc_auc_score as ci_roc_auc_score
from confidenceinterval import tnr_score, tpr_score
from sklearn.metrics import roc_auc_score as sk_roc_auc_score


def thresh(df: pd.DataFrame, scores_col: str, thresholds: list, strict: bool = True):
    if not isinstance(thresholds, list):
        thresholds = [thresholds]

    threshed = df[scores_col].copy()
    threshed = threshed.astype(float)
    threshed[:] = np.nan

    def _thresh(indices, threshold):
        assert (
            isinstance(threshold, float) and 0 <= threshold <= 1
        ), f"Threshold must be between 0 and 1. Threshold used: {threshold}"
        indices = threshed[threshed.isna()].index.intersection(indices)
        threshed.loc[indices] = (df.loc[indices, scores_col] > threshold).astype(int)

    for threshold_info in thresholds:
        assert isinstance(threshold_info, (tuple, float)), "Threshold info must be a float or a tuple"
        if isinstance(threshold_info, float):
            threshold_info = (None, {None: threshold_info})

        assert len(threshold_info) == 2, "Threshold tuple must be of the format (str, dict[str, float])"
        colname, subset_thresholds = threshold_info
        assert colname is None or str(colname) in df.columns.values, f"Column {colname} not found in dataframe"
        assert isinstance(subset_thresholds, dict), "Subset thresholds for column {colname} must be a dict"
        for subset, threshold in subset_thresholds.items():
            if subset is None:
                indices = threshed.index
            else:
                indices = df[df[colname] == subset].index
            _thresh(indices, threshold)
    threshed[df[scores_col].isna()] = np.nan

    if strict:
        assert (
            threshed[~df[scores_col].isna()].isna().sum() == 0
        ), "Strict thresholding failed. Please provide a default threshold for foolproof usage."

    return threshed


def get_thresh_cols(thresholds: list):
    if not isinstance(thresholds, list):
        return []

    colnames = []
    for threshold_info in thresholds:
        if isinstance(threshold_info, tuple):
            colnames.append(threshold_info[0])
    return colnames


def get_uncertain(scores: pd.Series, thresholds: tuple[float, float]):
    uncertain = scores.copy()

    uncertain = uncertain.astype(float)
    uncertain[:] = 0
    uncertain[(thresholds[0] <= scores) & (scores < thresholds[1])] = 1
    uncertain = uncertain.astype(int)

    return uncertain


def get_truth_table(seriess: dict[str, pd.Series]):
    df = pd.DataFrame(data=seriess).value_counts()

    for truth in itertools.product([0, 1], repeat=len(seriess)):
        if truth not in df.index:
            df = pd.concat([df, pd.Series({truth: 0})])

    df = df.sort_index()

    return df


def drop_na(df: pd.DataFrame, cols: list[str] = None, drop_method: str = "any"):
    if cols is None:
        cols = df.columns
    dropped_df = df.dropna(subset=cols, how=drop_method)
    return dropped_df


def preprocess_data(data: pd.DataFrame, cols: list[str], other_cols: list[str] = [], drop_method: str = "any"):
    df = data[cols + other_cols]
    df = drop_na(df, cols, drop_method)
    df = df.rename(
        columns={
            cols[0]: "GT",
            cols[1]: "Score",
        }
    )
    df = df.astype({"GT": int})

    return df


def add_metrics(df: pd.DataFrame, uncertainty_ranges: list = [], uncertainty_colnames: list = []):
    df["GT"] = df["GT"].astype(bool)
    df["Pred"] = df["Pred"].astype(bool)
    df["Far FP Pred"] = df["Far FP Pred"].astype(bool)
    df["Far FN Pred"] = df["Far FN Pred"].astype(bool)
    for i in range(len(uncertainty_ranges)):
        df[f"Uncertain{i}"] = df[f"Uncertain{i}"].astype(bool)

    try:
        auc, auc_ci = ci_roc_auc_score(df["GT"], df["Score"], confidence_level=0.95)
    except Exception:
        auc = sk_roc_auc_score(df["GT"], df["Score"])
        auc_ci = (np.nan, np.nan)
    sen, sen_ci = tpr_score(df["GT"], df["Pred"], confidence_level=0.95)
    spec, spec_ci = tnr_score(df["GT"], df["Pred"], confidence_level=0.95)

    df["Total"] = len(df)
    df["P"] = len(df[df["GT"]])
    df["N"] = len(df[~df["GT"]])
    df["PP"] = len(df[df["Pred"]])
    df["PN"] = len(df[~df["Pred"]])
    df["TP"] = len(df[df["GT"] & df["Pred"]])
    df["FP"] = len(df[~df["GT"] & df["Pred"]])
    df["FN"] = len(df[df["GT"] & ~df["Pred"]])
    df["TN"] = len(df[~df["GT"] & ~df["Pred"]])
    df["Sen"] = sen
    df["Sen 95% CI Lower"] = sen_ci[0]
    df["Sen 95% CI Upper"] = sen_ci[1]
    df["Spec"] = spec
    df["Spec 95% CI Lower"] = spec_ci[0]
    df["Spec 95% CI Upper"] = spec_ci[1]
    df["Youden"] = df["Sen"] + df["Spec"] - 1
    df["PPV"] = df["TP"] / df["PP"]
    df["NPV"] = df["TN"] / df["PN"]
    df["F1"] = (2 * df["TP"]) / (2 * df["TP"] + df["FP"] + df["FN"])
    df["Acc"] = (df["TP"] + df["TN"]) / (df["Total"])
    if np.unique(df["Score"].values).size > 5:
        try:
            df["AUC"] = auc
            df["AUC 95% CI Lower"] = auc_ci[0]
            df["AUC 95% CI Upper"] = auc_ci[1]
        except Exception:
            df["AUC"] = np.nan
            df["AUC 95% CI Lower"] = np.nan
            df["AUC 95% CI Upper"] = np.nan
        df["Far FN"] = len(df[df["GT"] & ~df["Pred"] & ~df["Far FN Pred"]])
        df["Far FP"] = len(df[~df["GT"] & df["Pred"] & df["Far FP Pred"]])
        for i, uncertainty_colname in enumerate(uncertainty_colnames):
            df[uncertainty_colname] = len(df[df[f"Uncertain{i}"]])
    else:
        df["AUC"] = np.nan
        df["Far FN"] = np.nan
        df["Far FP"] = np.nan
        for i, uncertainty_colname in enumerate(uncertainty_colnames):
            df[uncertainty_colname] = np.nan
    return df


def style_df(df: pd.DataFrame, show_bars: bool = True):
    known_colnames = [
        "Total",
        "P",
        "N",
        "AUC",
        "AUC 95% CI Lower",
        "AUC 95% CI Upper",
        "PP",
        "PN",
        "TP",
        "FP",
        "FN",
        "TN",
        "Far FN",
        "Far FP",
        "Sen",
        "Sen 95% CI Lower",
        "Sen 95% CI Upper",
        "Spec",
        "Spec 95% CI Lower",
        "Spec 95% CI Upper",
        "Youden",
        "PPV",
        "NPV",
        "F1",
        "Acc",
    ]
    extra_colname = None
    for i in range(len(df.columns) - 1, 0, -1):
        if df.columns[i - 1] in known_colnames:
            extra_colname = df.columns[i]
            break

    styled_df = (
        df.style.set_table_styles(
            {
                key: [
                    {"selector": "th", "props": [("border-left", "1px solid black")]},
                    {"selector": "td", "props": [("border-left", "1px solid black")]},
                ]
                for key in {
                    "Total",
                    "P",
                    "AUC",
                    "TP",
                    "Far FN",
                    "Sen",
                    "Youden",
                    "PPV",
                    "Acc",
                    "F1",
                    extra_colname,
                }
            }
        )
        .format(precision=3)
        .format_index(precision=3)
    )

    if show_bars:
        bar_styles = {
            "AUC": [(0.5, 1), "gold"],
            "Sen": [(0.5, 1), "lightgreen"],
            "Spec": [(0.5, 1), "lightgreen"],
            "Youden": [(0, 1), "lightsteelblue"],
            "PPV": [(0.5, 1), "salmon"],
            "NPV": [(0.5, 1), "salmon"],
            "F1": [(0.5, 1), "peachpuff"],
            "Acc": [(0.5, 1), "turquoise"],
        }
        for bar_name, bar_style in bar_styles.items():
            if bar_name not in styled_df.columns.values:
                continue
            vmin = bar_style[0][0]
            vmax = bar_style[0][1]
            color = bar_style[1]
            styled_df = styled_df.bar(subset=[bar_name], height=80, width=99, color=color, vmin=vmin, vmax=vmax)

        styled_df = styled_df.set_properties(width="0px")

    return styled_df


def check_cols(df: pd.DataFrame, colnames: list):
    missing_cols = []
    for colname in colnames:
        if colname not in df.columns.values:
            missing_cols.append(colname)
    return missing_cols


def find_nearest(array, value):
    val = np.min(array[array >= value])
    idx = np.abs(array - val).argmin()
    return idx
