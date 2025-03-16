import numpy as np
import pandas as pd
from scipy import stats as st


def combine_cols(
    data: pd.DataFrame, cols: list[str], method: str, strict: bool = False, supermajority_requirement: float = 2 / 3
):
    cols = [col for col in cols if col in data.columns]

    df = data[cols]

    if method == "majority":
        combined = pd.Series(
            st.mode(df.values.astype(np.float16), axis=1, nan_policy="omit", keepdims=False).mode, index=df.index
        )
    elif method == "supermajority":
        df = df.astype(int)
        assert set(np.unique(df.values)).issubset({0, 1}), "Supermajority can only be used on binary data"
        assert 0 < supermajority_requirement < 1, "Supermajority requirement must be between 0 and 1"

        combined = (df.sum(axis=1) > int(len(cols) * supermajority_requirement)) * 1.0
    elif method == "preference":
        combined = df[cols[0]]
        for col in cols:
            combined = combined.fillna(df[col])
    elif method == "union":
        combined = df.any(axis=1) * 1.0
    elif method == "intersection":
        combined = df.all(axis=1) * 1.0
    else:
        raise ValueError("Given method is unknown")

    if strict:
        combined[df.isna().any(axis=1)] = np.nan
    else:
        combined[df.isna().all(axis=1)] = np.nan

    return combined
