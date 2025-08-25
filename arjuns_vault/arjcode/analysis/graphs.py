import numpy as np
import pandas as pd
import seaborn as sns
from arjcode.analysis.constants import NO_DATA_ERROR
from arjcode.analysis.utils import check_cols, drop_na, preprocess_data
from matplotlib import pyplot as plt
from sklearn.metrics import average_precision_score, confusion_matrix, precision_recall_curve, roc_auc_score, roc_curve


def scatterplot(
    data: pd.DataFrame,
    y_gt_col: str,
    y_scores_col: str,
    sort_by: str = "gts",
):
    print("-------------------------")
    print("GT:".ljust(6), y_gt_col)
    print("Score:".ljust(6), y_scores_col)
    print()

    cols = [y_gt_col, y_scores_col]
    missing_cols = check_cols(data, cols)
    if len(missing_cols):
        print(f"Missing columns: {missing_cols}")
    else:
        df = preprocess_data(data, cols)

        if sort_by is None:
            pass
        elif sort_by == "gts":
            df = df.sort_values("GT")
        elif sort_by == "scores":
            df = df.sort_values("Score")
        else:
            raise ValueError("Invalid `sort_by` provided")

        if len(df) == 0:
            print(NO_DATA_ERROR)
        else:
            plt.figure(figsize=(10, 8))
            plt.ylim((0, 1))
            for x, i in enumerate(df.index):
                if df.loc[i, "GT"] == 1:
                    color = "g."
                else:
                    color = "r."
                plt.plot(x, df.loc[i, "Score"], color)
            plt.xlabel("Index")
            plt.ylabel("Score")
            plt.show()
    print("-------------------------")


def roc(
    data: pd.DataFrame,
    y_gt_cols: list[str],
    y_scores_cols: list[str] = [],
    rads_cols: list[str] = [],
    smoothen_curve: bool = False,
):
    print("-------------------------")
    print("GTs:".ljust(7), y_gt_cols)
    print("Scores:".ljust(7), y_scores_cols)
    print()

    plt.figure(figsize=(8, 8))
    plt.xlim(-0.05, 1.05)
    plt.ylim(-0.05, 1.05)
    plt.plot((0, 1), (0, 1), "r")
    plt.plot((0, 0, 1), (0, 1, 1), "g")

    assert len(y_gt_cols) > 0, "At least one `y_gt_col` must be provided"

    missing_cols = check_cols(data, y_gt_cols + y_scores_cols)
    if len(missing_cols):
        print(f"Missing columns: {missing_cols}")
        y_gt_cols = [col for col in y_gt_cols if col not in missing_cols]
        y_scores_cols = [col for col in y_scores_cols if col not in missing_cols]

    for y_gt_col in y_gt_cols:
        for y_scores_col in y_scores_cols:
            cols = [y_gt_col, y_scores_col]
            df = preprocess_data(data, cols)

            if len(df) == 0:
                continue

            fpr, tpr, _ = roc_curve(df["GT"], df["Score"])
            auc = round(roc_auc_score(df["GT"], df["Score"]), 3)
            label = f"AUC ({y_gt_col}, {y_scores_col}): {auc}"

            if smoothen_curve:
                sns.lineplot(x=fpr, y=tpr, label=label)
            else:
                plt.plot(fpr, tpr, label=label)

        for rad_col in rads_cols:
            cols = [y_gt_col, rad_col]
            df = drop_na(data, cols)

            df[y_gt_col] = df[y_gt_col].astype(bool)
            df[rad_col] = df[rad_col].astype(bool)
            tp = len(df[df[y_gt_col] & df[rad_col]])
            fp = len(df[~df[y_gt_col] & df[rad_col]])
            fn = len(df[df[y_gt_col] & ~df[rad_col]])
            tn = len(df[~df[y_gt_col] & ~df[rad_col]])

            try:
                tpr = tp / (tp + fn)
                fpr = fp / (fp + tn)
            except ZeroDivisionError:
                continue

            label = f"{rad_col} ({y_gt_col}): ({round(tpr, 3)}, {round(1 - fpr, 3)})"
            plt.plot(fpr, tpr, "x", label=label)

    plt.xlabel("FPR = (1 - TNR)")
    plt.ylabel("TPR")
    plt.legend(bbox_to_anchor=(1.0, 1.01), loc="upper left")
    plt.xticks(np.arange(0, 1, 0.05), rotation=90)
    plt.yticks(np.arange(0, 1, 0.05))
    plt.show()
    print("-------------------------")


def pr(
    data: pd.DataFrame,
    y_gt_cols: list[str],
    y_scores_cols: list[str] = [],
    rads_cols: list[str] = [],
    smoothen_curve: bool = False,
):
    print("-------------------------")
    print("GTs:".ljust(7), y_gt_cols)
    print("Scores:".ljust(7), y_scores_cols)
    print()

    plt.figure(figsize=(8, 8))
    plt.xlim(-0.05, 1.05)
    plt.ylim(-0.05, 1.05)
    plt.plot((0, 1), (1, 0), "r")
    plt.plot((0, 1, 1), (1, 1, 0), "g")

    assert len(y_gt_cols) > 0, "At least one `y_gt_col` must be provided"

    missing_cols = check_cols(data, y_gt_cols + y_scores_cols)
    if len(missing_cols):
        print(f"Missing columns: {missing_cols}")
        y_gt_cols = [col for col in y_gt_cols if col not in missing_cols]
        y_scores_cols = [col for col in y_scores_cols if col not in missing_cols]

    for y_gt_col in y_gt_cols:
        for y_scores_col in y_scores_cols:
            cols = [y_gt_col, y_scores_col]
            df = preprocess_data(data, cols)

            if len(df) == 0:
                continue

            precision, recall, _ = precision_recall_curve(df["GT"], df["Score"])
            ap = round(average_precision_score(df["GT"], df["Score"]), 3)
            label = f"AP ({y_gt_col}, {y_scores_col}): {ap}"

            if smoothen_curve:
                sns.lineplot(x=recall, y=precision, label=label)
            else:
                plt.plot(recall, precision, label=label)

        for rad_col in rads_cols:
            cols = [y_gt_col, rad_col]
            df = drop_na(data, cols)

            df[y_gt_col] = df[y_gt_col].astype(bool)
            df[rad_col] = df[rad_col].astype(bool)
            tp = len(df[df[y_gt_col] & df[rad_col]])
            fp = len(df[~df[y_gt_col] & df[rad_col]])
            fn = len(df[df[y_gt_col] & ~df[rad_col]])

            try:
                precision = tp / (tp + fp)
                recall = tp / (tp + fn)
            except ZeroDivisionError:
                continue

            label = f"{rad_col} ({y_gt_col}): ({round(recall, 3)}, {round(precision, 3)})"
            plt.plot(recall, precision, "x", label=label)

    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.legend(bbox_to_anchor=(1.0, 1.01), loc="upper left")
    plt.xticks(np.arange(0, 1, 0.05), rotation=90)
    plt.yticks(np.arange(0, 1, 0.05))
    plt.show()
    print("-------------------------")


def sen_spec(
    data: pd.DataFrame,
    y_gt_col: str,
    y_scores_cols: list[str],
    smoothen_curve: bool = False,
):
    print("-------------------------")
    print("GT:".ljust(7), y_gt_col)
    print("Scores:".ljust(7), y_scores_cols)
    print()

    plt.figure(figsize=(8, 8))
    plt.xlim(-0.05, 1.05)
    plt.ylim(-0.05, 1.05)

    missing_cols = check_cols(data, [y_gt_col] + y_scores_cols)
    if len(missing_cols):
        print(f"Missing columns: {missing_cols}")
    else:
        colours = plt.cm.get_cmap("rainbow", len(y_scores_cols))
        for i, y_scores_col in enumerate(y_scores_cols):
            cols = [y_gt_col, y_scores_col]
            df = preprocess_data(data, cols)

            if len(df) == 0:
                continue

            fpr, tpr, thresholds = roc_curve(df["GT"], df["Score"])  # , drop_intermediate=False)
            indices = (thresholds >= 0) & (thresholds <= 1)
            fpr, tpr, thresholds = fpr[indices], tpr[indices], thresholds[indices]

            if smoothen_curve:
                sns.lineplot(x=thresholds, y=tpr, label=y_scores_col, c=colours(i))
                sns.lineplot(x=thresholds, y=1 - fpr, c=colours(i))
            else:
                plt.plot(thresholds, tpr, label=y_scores_col, c=colours(i))
                plt.plot(thresholds, 1 - fpr, c=colours(i))

    plt.xlabel("Threshold")
    plt.ylabel("Sen / Spec")
    plt.legend(bbox_to_anchor=(1.0, 1.01), loc="upper left")
    plt.xticks(np.arange(0, 1.01, 0.05), rotation=90)
    plt.yticks(np.arange(0, 1.01, 0.05))
    plt.show()
    print("-------------------------")


def compare_models(
    data: pd.DataFrame,
    y_gt_col: str,
    y_scores_col1: str,
    y_scores_col2: str,
    threshold1: float = None,
    threshold2: float = None,
):
    df = data.sort_values(by=y_gt_col, ascending=False)

    text_params = {
        "fontsize": "medium",
        "bbox": dict(facecolor="white", edgecolor="black", alpha=0.9, boxstyle="round,pad=0.3"),
    }

    sns.jointplot(
        x=df[y_scores_col1],
        y=df[y_scores_col2],
        hue=df[y_gt_col],
        xlim=(0, 1),
        ylim=(0, 1),
        palette=["red", "green"],
        s=10,
    )

    if threshold1 is not None and isinstance(threshold1, float):
        plt.axvline(threshold1, linestyle="--", linewidth=1)

    if threshold2 is not None and isinstance(threshold2, float):
        plt.axhline(threshold2, linestyle="--", linewidth=1)

    if (
        threshold1 is not None
        and threshold2 is not None
        and isinstance(threshold1, float)
        and isinstance(threshold2, float)
    ):
        p000, p001, p010, p011 = confusion_matrix(
            df.loc[df[y_gt_col] == 0, y_scores_col1] > threshold1, df.loc[df[y_gt_col] == 0, y_scores_col2] > threshold2
        ).ravel()
        p100, p101, p110, p111 = confusion_matrix(
            df.loc[df[y_gt_col] == 1, y_scores_col1] > threshold1, df.loc[df[y_gt_col] == 1, y_scores_col2] > threshold2
        ).ravel()

        plt.text(threshold1 - 0.03, 0.02, f"{p000}\n{p100}", ha="right", va="bottom", **text_params)
        plt.text(threshold1 + 0.03, 0.02, f"{p010}\n{p110}", ha="left", va="bottom", **text_params)
        plt.text(threshold1 - 0.03, 0.98, f"{p001}\n{p101}", ha="right", va="top", **text_params)
        plt.text(threshold1 + 0.03, 0.98, f"{p011}\n{p111}", ha="left", va="top", **text_params)

    plt.legend([], [], frameon=False)
    plt.show()
