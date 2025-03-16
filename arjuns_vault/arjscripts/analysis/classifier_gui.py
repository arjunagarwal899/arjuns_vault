from time import time

import pandas as pd
from IPython.display import display
from ipywidgets import interactive, widgets


def _get_estimated_time_to_completion(df: pd.DataFrame, n_cur, n_left, n_total):
    # Average number of datapoints to estimate time required to complete analysis
    lookback_multiplier = min(40, int(0.40 * n_total))

    # Calculate median time taken over all datapoints
    median_time = df.timestamp.diff(1).median()

    # Decide on the datapoints to use to make estimation
    df_est = df[df.timestamp >= time() - median_time * lookback_multiplier]

    if len(df_est) > 1:
        # Take average of datapoints decided
        time_per_iter = (df_est.iloc[-1].timestamp - df_est.iloc[0].timestamp) / (len(df_est) - 1)
        n_datapoints_used = len(df_est)
    else:
        # If no datapoints accepted by criterion, take average of (mean and median time) over all datapoints
        time_per_iter = (median_time + (time() - df.iloc[0].timestamp) / n_cur) / 2
        n_datapoints_used = len(df)

    # Calculate actual total time
    est_time = time_per_iter * n_left

    return est_time, time_per_iter, n_datapoints_used


def _print_stats(df, n_total, label_groups):
    """
    Calculates and displays the various stats w.r.t the current classification situation

    Args:
        df (object): pandas DataFrame containing all classification datapoints till now
        n_total (int): total number of classification datapoints expected
        label_groups (dict[str, list[str]]): the classification labels displayed for each datapoint
    """

    # Calculate basic variables
    n_cur = len(df)
    n_left = n_total - n_cur

    print("\nStats")
    print(f"Completed:\t{n_cur}/{n_total}\t({(n_cur * 100) // n_total}% complete, {n_left} remaining)")

    if n_left != 0:
        print("Estimated time:\t", end="")

        # Require at least 10 datapoints to make an estimation
        if n_cur < 10:
            print(f"(Need {10 - n_cur} more datapoints)")
        else:
            (
                est_time,
                time_per_iter,
                n_datapoints_used,
            ) = _get_estimated_time_to_completion(df, n_cur, n_left, n_total)

            if est_time / 60 < 1:
                est_time = round(est_time, 1)
                iter_per_time = round(1 / time_per_iter, 1)
                print(f"{est_time}s \t({iter_per_time}/s", end="")
            elif est_time / 3600 < 1:
                est_time = round(est_time / 60, 1)
                iter_per_time = round(60 / time_per_iter, 1)
                print(f"{est_time}m \t({iter_per_time}/m", end="")
            else:
                est_time = round(est_time / 3600, 1)
                iter_per_time = round(3600 / time_per_iter, 1)
                print(f"{est_time}h \t({iter_per_time}/h", end="")

            print(f", {n_datapoints_used} datapoints used)")

    # Calculate stats
    stats = pd.DataFrame(columns=label_groups)

    for i in df.index:
        new_row = {}
        for groupname, labels in label_groups.items():
            for label in labels:
                if df.loc[i, f"{groupname}__{label}"] is True:
                    new_row[groupname] = label
                    break
        stats = pd.concat([stats, pd.DataFrame([new_row])], ignore_index=True)

    stats = stats.value_counts()
    stats = stats.sort_index()
    stats = stats.to_frame("Count")
    display(stats)


def _reset_toggle_buttons(choices):
    """
    To reset the toggle buttons whenever required (for e.g. when all classification labels have been marked)

    Args:
        choices (dict[str, widget]): all the choices to be reset
    """
    for groupname, choice in choices.items():
        if groupname == "comments":
            choice.value = ""
        else:
            choice.value = None


def classifier(indices, vis_data, label_groups, show_stats=True):
    """
    GUI which can aid in classifying data visualized in any manner. Data has to be referenceable using a unique key.
    All classification outputs are returned in the form of a pandas DataFrame.

    Args:
        indices (list): list of unique keys which can reference the data to be visualized
        vis_data (object): function which visualizes the data based on the unique key
        label_groups (dict[str, list[str]]): the classification labels to be viewed for each datapoint
        show_stats (bool, optional): Whether or not to print current stats at the end of the visualization.
            Defaults to True.

    Returns:
        object: GUI which can be `display()`ed in a jupyter notebook
    """

    # Set up dataframe
    all_labels = []
    for groupname, labels in label_groups.items():
        for label in labels:
            all_labels.append(f"{groupname}__{label}")

    df = pd.DataFrame(
        columns=[
            "Index",  # Save the unique key of each datapoint
            "timestamp",  # Save the timestamp at which each datapoint was added to the dataframe
            *all_labels,  # The classification labels
        ]
    )

    # Set up widgets
    choices = {}
    choices["actions"] = widgets.ToggleButtons(options=["UNDO"], value=None, description="Actions:")
    for groupname, labels in label_groups.items():
        choices[groupname] = widgets.ToggleButtons(options=labels, value=None, description=f"{groupname}:")
    choices["comments"] = widgets.Text(value="", description="Comments:")

    # Interact
    cur_i = 0

    def callback(**kwargs):
        nonlocal cur_i, df

        if cur_i < 0:
            cur_i = 0
            print("Cannot undo any further")

        assert len(indices) > 0, 'No data has been provided i.e. parameter "indices" is empty'

        # If all the data has been classified
        if cur_i == len(indices):
            print("You have gone through all the data! Congratulations!")

            # Visualize stats
            if show_stats:
                _print_stats(df, len(indices), label_groups)
        elif kwargs["actions"] == "UNDO":  # Else if undo was pressed
            cur_i -= 1
            df = df.drop(df[df.Index == indices[cur_i]].index)

            # Reset toggle buttons
            _reset_toggle_buttons(choices)
        else:
            # If all groups have values
            new_row = {"Index": indices[cur_i], "timestamp": time()}

            for label in all_labels:
                new_row[label] = False

            flag = False
            for groupname, label_selected in kwargs.items():
                if groupname == "actions":
                    continue

                if groupname == "comments":
                    new_row[groupname] = label_selected
                    continue

                if label_selected is None:
                    flag = True
                    break

                # Add element to dataframe
                new_row[f"{groupname}__{label_selected}"] = True

            if not flag:
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

                # Increment cur_i
                cur_i += 1

                # Reset toggle buttons
                _reset_toggle_buttons(choices)
            else:
                # Show image
                vis_data(indices[cur_i])

                # Visualize stats
                if show_stats:
                    _print_stats(df, len(indices), label_groups)

        return df.drop("timestamp", axis=1).set_index("Index")

    gui = interactive(callback, **choices)
    return gui
