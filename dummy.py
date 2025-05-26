import argparse
import logging
import re
import shutil
from datetime import datetime, timedelta
from pathlib import Path

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
PATTERN = r"^OUSS_(\d{4}-\d{2}-\d{2})-.*$"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Delete folders older than one week based on their names."
    )
    parser.add_argument(
        "--date",
        required=True,
        help="Reference date in YYYY-MM-DD format (calculations are relative to this date).",
    )
    parser.add_argument(
        "--path",
        required=True,
        type=Path,
        help="Path to the directory containing folders to evaluate.",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting.",
    )
    return parser.parse_args()


def extract_date_from_name(name: str, pattern: str) -> datetime | None:
    match = re.match(pattern, name)
    if match:
        date_str = match.group(1)
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            logging.warning(f"Invalid date format in folder name: {name}")
    return None


def main():
    args = parse_args()

    try:
        ref_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    except ValueError:
        logging.error("Provided date is not in YYYY-MM-DD format.")
        return

    threshold = ref_date - timedelta(weeks=1)
    logging.info(f"Reference date: {ref_date}, threshold date: {threshold}")

    if not args.path.is_dir():
        logging.error(f"Provided path is not a directory: {args.path}")
        return

    for entry in args.path.iterdir():
        if not entry.is_dir():
            continue

        folder_date = extract_date_from_name(entry.name, PATTERN)
        if folder_date is None:
            logging.debug(f"Skipping folder with non-matching name: {entry.name}")
            continue

        if folder_date <= threshold:
            if args.dry_run:
                logging.info(f"[Dry run] Would delete: {entry}")
            else:
                try:
                    shutil.rmtree(entry)
                    logging.info(f"Deleted folder: {entry}")
                except Exception as e:
                    logging.error(f"Failed to delete {entry}: {e}")
        else:
            logging.debug(f"Keeping folder: {entry.name} (date {folder_date})")


if __name__ == "__main__":
    main()
=========================================tests========================================================
import sys
import pytest
from pathlib import Path
from datetime import date

import delete_old_folders_cli as cli


def test_extract_date_valid():
    name = "OUSS_2025-05-26-abc"
    result = cli.extract_date_from_name(name, cli.PATTERN)
    assert result == date(2025, 5, 26)


def test_extract_date_invalid_format(caplog):
    name = "OUSS_2025-13-01-abc"
    caplog.set_level("WARNING")
    result = cli.extract_date_from_name(name, cli.PATTERN)
    assert result is None
    assert any("Invalid date format in folder name" in rec.message for rec in caplog.records)


def test_extract_date_no_match():
    name = "OTHER_2025-05-26-abc"
    result = cli.extract_date_from_name(name, cli.PATTERN)
    assert result is None


def test_parse_args(tmp_path, monkeypatch):
    test_args = ["prog", "--date", "2025-05-26", "--path", str(tmp_path)]
    monkeypatch.setattr(sys, "argv", test_args)
    args = cli.parse_args()
    assert args.date == "2025-05-26"
    assert isinstance(args.path, Path) and args.path == tmp_path
    assert args.dry_run is False


def test_main_dry_run(tmp_path, caplog, monkeypatch):
    # Setup folders
    ref_date = date(2025, 5, 26)
    older = tmp_path / "OUSS_2025-05-18-aaa"
    newer = tmp_path / "OUSS_2025-05-20-bbb"
    older.mkdir()
    newer.mkdir()
    # Prepare args
    monkeypatch.setattr(sys, "argv", ["prog", "--date", ref_date.isoformat(), "--path", str(tmp_path), "--dry-run"])
    caplog.set_level("INFO")
    # Run
    cli.main()
    # Check logs
    assert any(f"[Dry run] Would delete: {older}" in rec.message for rec in caplog.records)
    assert not any(f"[Dry run] Would delete: {newer}" in rec.message for rec in caplog.records)
    # Ensure directories still exist
    assert older.exists()
    assert newer.exists()


def test_main_delete(tmp_path, caplog, monkeypatch):
    # Setup folders
    ref_date = date(2025, 5, 26)
    older = tmp_path / "OUSS_2025-05-18-xxx"
    newer = tmp_path / "OUSS_2025-05-20-yyy"
    older.mkdir()
    newer.mkdir()
    # Monkeypatch rmtree
    deleted = []
    def fake_rmtree(path):
        deleted.append(Path(path))
    monkeypatch.setattr(cli.shutil, "rmtree", fake_rmtree)
    monkeypatch.setattr(sys, "argv", ["prog", "--date", ref_date.isoformat(), "--path", str(tmp_path)])
    caplog.set_level("INFO")
    # Run
    cli.main()
    # Only older should be deleted
    assert older in deleted
    assert newer not in deleted


def test_main_invalid_date(tmp_path, caplog, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["prog", "--date", "invalid", "--path", str(tmp_path)])
    caplog.set_level("ERROR")
    cli.main()
    assert any("Provided date is not in YYYY-MM-DD format." in rec.message for rec in caplog.records)


def test_main_invalid_path(tmp_path, caplog, monkeypatch):
    # Create a file, not a dir
    file_path = tmp_path / "notadir"
    file_path.write_text("hello")
    monkeypatch.setattr(sys, "argv", ["prog", "--date", "2025-05-26", "--path", str(file_path)])
    caplog.set_level("ERROR")
    cli.main()
    assert any("Provided path is not a directory" in rec.message for rec in caplog.records)
