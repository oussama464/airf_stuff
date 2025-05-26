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
