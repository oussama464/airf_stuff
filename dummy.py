import polars as pl

schema = {
    "dataset": pl.Utf8(),  # note the ()
    "filename": pl.Utf8(),
    "control_date": pl.Date(),  # Date instance
    "generation_ts": pl.Datetime("ns"),  # datetime with ns precision
    "total_rows_per_file": pl.Int64(),
    "not_null_rows_count_per_file": pl.Int64(),
}

df = pl.read_json("synthetic_metadata.json").with_columns(
    pl.col("control_date").cast(pl.Date), pl.col("generation_ts").str.to_datetime()
)

df_dataset = (
    df.group_by("dataset")
    .agg(
        [
            pl.len().alias("total_dq_files"),
            pl.sum("total_rows_per_file").alias("total_rows"),
            pl.sum("not_null_rows_count_per_file").alias("total_errors"),
        ]
    )
    .with_columns(pct_error_rate=100 * pl.col("total_errors") / pl.col("total_rows"))
)

df_dataset_control_date = (
    df.group_by(["dataset", "control_date"])
    .agg(
        [
            pl.len().alias("total_dq_files"),
            pl.sum("total_rows_per_file").alias("total_rows"),
            pl.sum("not_null_rows_count_per_file").alias("total_errors"),
        ]
    )
    .with_columns(pct_error_rate=100 * pl.col("total_errors") / pl.col("total_rows"))
    .sort("control_date")
)
