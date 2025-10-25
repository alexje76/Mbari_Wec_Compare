import pandas as pd
import pandas.testing as pdt
import mainDF_management as m


def test_access_mainDF_reads_csv(tmp_path, monkeypatch):
    """When a mainDF.csv exists it should be read and returned as a DataFrame."""
    # prepare a CSV in a temp dir and switch CWD so access_mainDF() finds it
    df_expected = pd.DataFrame([{"a": 1, "b": "x"}, {"a": 2, "b": "y"}])
    csv_path = tmp_path / "mainDF.csv"
    df_expected.to_csv(csv_path, index=False)

    monkeypatch.chdir(tmp_path)                # make access_mainDF look in tmp_path
    df_actual = m.access_mainDF()

    # compare frames (ignore index differences)
    pdt.assert_frame_equal(df_actual.reset_index(drop=True), df_expected.reset_index(drop=True))


def test_access_mainDF_returns_empty_when_missing(tmp_path, monkeypatch):
    """When mainDF.csv is missing the function should return an empty DataFrame."""
    # ensure no mainDF.csv exists and call access_mainDF()
    monkeypatch.chdir(tmp_path)
    df_actual = m.access_mainDF()

    assert isinstance(df_actual, pd.DataFrame)
    assert df_actual.empty
