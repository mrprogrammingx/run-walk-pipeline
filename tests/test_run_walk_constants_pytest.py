import pandas as pd
import pandas.api.types as ptypes


def test_constants_mapping_values():
    from run_walk_constants import ACTIVITY_LABELS, WRIST_LABELS

    # explicit expected mappings
    assert ACTIVITY_LABELS[0] == "walking"
    assert ACTIVITY_LABELS[1] == "running"
    assert WRIST_LABELS[0] == "left"
    assert WRIST_LABELS[1] == "right"

    # keys are small integer sets
    assert set(ACTIVITY_LABELS.keys()) == {0, 1}
    assert set(WRIST_LABELS.keys()) == {0, 1}


def apply_dashboard_like_labeling(df: pd.DataFrame) -> pd.DataFrame:
    """Apply the same integer-code -> label mapping logic used in the
    Streamlit dashboard's table view. Returns a new DataFrame with mapped
    columns (doesn't modify input).
    """
    from run_walk_constants import ACTIVITY_LABELS, WRIST_LABELS

    display_df = df.copy()
    if "activity" in display_df.columns:
        if display_df["activity"].dtype in ("int64", "int32", "int8") or ptypes.is_integer_dtype(display_df["activity"]):
            display_df["activity"] = display_df["activity"].map(ACTIVITY_LABELS).fillna(display_df["activity"].astype(str))
    if "wrist" in display_df.columns:
        if display_df["wrist"].dtype in ("int64", "int32", "int8") or ptypes.is_integer_dtype(display_df["wrist"]):
            display_df["wrist"] = display_df["wrist"].map(WRIST_LABELS).fillna(display_df["wrist"].astype(str))
    return display_df


def test_labeling_on_dataframe_with_known_and_unknown_codes():
    # include known codes (0/1) and unknown codes (2/3) to ensure fallback
    df = pd.DataFrame(
        {
            "activity": [0, 1, 2],
            "wrist": [0, 1, 3],
            "username": ["u1", "u2", "u3"],
            "date": pd.to_datetime(["2026-03-01", "2026-03-02", "2026-03-03"]),
            "samples": [10, 20, 5],
        }
    )

    out = apply_dashboard_like_labeling(df)

    # known mappings should be replaced with labels
    assert out.loc[0, "activity"] == "walking"
    assert out.loc[1, "activity"] == "running"
    assert out.loc[0, "wrist"] == "left"
    assert out.loc[1, "wrist"] == "right"

    # unknown codes should fall back to stringified numeric code
    assert out.loc[2, "activity"] == "2"
    assert out.loc[2, "wrist"] == "3"
