from datetime import datetime, date
import re
from pprint import pprint
import polars as pl
import polars.selectors as cs
from datetime import datetime, timedelta
import random

import re
from datetime import datetime, date
import hashlib

# Regex to capture base filename, control_date, and generation_ts
# Example: MARKET_DEPTH_2024-10-28_2024-10-29_07-34-10.parquet
EXTRACTION_PATTERN = re.compile(
    r"""^
        (?P<base>.+?)
        _(?P<control>\d{4}-\d{2}-\d{2})
        _(?P<gen>\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})
        (?:\..+)?$
    """,
    re.VERBOSE
)

def get_control_and_generation_ts(filename: str) -> tuple[str, date, datetime]:
    """
    Extracts the base filename (without dates), control_date, and generation timestamp.
    
    Example:
        MARKET_DEPTH_2024-10-28_2024-10-29_07-34-10.parquet
        -> ("MARKET_DEPTH", date(2024, 10, 28), datetime(2024, 10, 29, 7, 34, 10))
    """
    match = EXTRACTION_PATTERN.match(filename)
    if not match:
        raise ValueError(f"No base/control_date/generation_ts in '{filename}'")

    base = match.group("base")
    control_date = datetime.strptime(match.group("control"), "%Y-%m-%d").date()
    gen_ts = datetime.strptime(match.group("gen"), "%Y-%m-%d_%H-%M-%S")
    return base, control_date, gen_ts


def filter_by_latest_generation_ts(dq_file_names: list[str]) -> list[str]:
    """
    For each combination of control_date & base filename (no dates suffix),
    keep only the file with the highest generation_ts.
    Returns a list of the selected filenames.
    """
    best_by_hash: dict[str, tuple[str, str, date, datetime]] = {}

    for fn in dq_file_names:
        base, ctrl_date, gen_ts = get_control_and_generation_ts(fn)
        key_str = f"{ctrl_date.isoformat()}_{base}"
        hash_key = hashlib.md5(key_str.encode('utf-8')).hexdigest()

        # keep only the newest file per control_date + base
        if hash_key not in best_by_hash or gen_ts > best_by_hash[hash_key][3]:
            best_by_hash[hash_key] = (fn, base, ctrl_date, gen_ts)

    return [fn for fn, *_ in best_by_hash.values()]

EXTRACTION_PATTERN = re.compile(
    r"_(\d{4}-\d{2}-\d{2})_(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})"
)



def generate_filenames(start_year=2024, end_year=2025, count=30):
    base = "DQ_IMAD_BONDFUTURES_MARKET_DEPTH"
    files = []

    for _ in range(count):
        # Randomly pick a start date between Jan 1, 2024 and Dec 31, 2025
        start_date = datetime.strptime(f"{start_year}-01-01", "%Y-%m-%d") + timedelta(
            days=random.randint(0, 730)
        )
        end_date = start_date + timedelta(days=1)

        # Random generation time
        generation_time = datetime(
            year=end_date.year,
            month=end_date.month,
            day=end_date.day,
            hour=random.randint(0, 23),
            minute=random.randint(0, 59),
            second=random.randint(0, 59),
        )

        filename = f"{base}_{start_date.strftime('%Y-%m-%d')}_{end_date.strftime('%Y-%m-%d')}_{generation_time.strftime('%H-%M-%S')}.parquet"
        files.append(filename)

    return files


def get_control_and_generation_ts(filename: str) -> tuple[date, datetime]:
    match = EXTRACTION_PATTERN.search(filename)
    if not match:
        raise ValueError(
            f"No match for control_date or generation_ts found for {filename=}"
        )

    control_date = datetime.strptime(match.group(1), "%Y-%m-%d").date()
    gen_ts = datetime.strptime(match.group(2), "%Y-%m-%d_%H-%M-%S")
    return control_date, gen_ts


def filter_by_latest_generation_ts_df(files: list[str]) -> pl.DataFrame:
    """
    Return a Polars DataFrame where, for each control_date, only the file
    with the highest generation_ts is kept.
    """
    best_per_date: dict[date, tuple[str, date, datetime]] = {}

    for fn in files:
        ctrl_date, gen_ts = get_control_and_generation_ts(fn)
        # if first time seeing this date, or this file is newer, keep it
        if ctrl_date not in best_per_date or gen_ts > best_per_date[ctrl_date][2]:
            best_per_date[ctrl_date] = (fn, ctrl_date, gen_ts)

    # build list of row‑dicts
    rows = [
        {"filename": fn, "control_date": ctrl_date, "generation_timestamp": gen_ts}
        for fn, ctrl_date, gen_ts in best_per_date.values()
    ]

    # create and return DataFrame
    return pl.DataFrame(rows)


def filter_by_control_date(
    df: pl.DataFrame, year: int, month: int | None = None
) -> pl.DataFrame:
    """
    Filter rows by control_date’s year (and optionally month).

    Args:
      df: DataFrame with a `control_date` Date column.
      year: keep rows where control_date.year == year.
      month: if given, also require control_date.month == month.

    Returns:
      Filtered DataFrame.
    """
    # Base predicate: same year
    mask = pl.col("control_date").dt.year() == year

    # If month specified, add that condition
    if month is not None:
        mask &= pl.col("control_date").dt.month() == month

    return df.filter(mask)

df: pl.DataFrame = filter_by_latest_generation_ts_df(files).pipe(
    filter_by_control_date, year=2025
)
print(df["filename"].to_list())
