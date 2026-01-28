import datetime
import hashlib
import logging
import re
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import pandas as pd

logger = logging.getLogger("django")


def timing_decorator(func):
    """A decorator to measure the execution time of a function."""

    def wrapper(*args, **kwargs):
        # args[0] will be 'self' when decorating a method
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        logger.info(
            f"method '{func.__name__}' executed in {execution_time:.4f} seconds"
        )
        return result

    return wrapper


def date_extractor(v: str) -> datetime.datetime | None:
    # Regular expression to find date patterns
    # (e.g., DD_MMM_YYYY, DD MMM YYYY, DDMMMYYYY, DDMMYYYY, DD/MM/YYYY)
    date_obj = None
    match = re.search(
        r"(\d{1,2})\s*[_ ]?(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|\d{1,2})\s*[_ /]?(\d{4})",
        v,
        re.IGNORECASE,
    )
    if match:
        day = int(match.group(1))
        month_str = match.group(2)
        year = int(match.group(3))

        try:
            if month_str.isdigit():
                month = int(month_str)
                date_obj = datetime.datetime(year, month, day).date()
            else:
                date_obj = datetime.datetime.strptime(
                    f"{day} {month_str} {year}", "%d %b %Y"
                ).date()
        except ValueError as ve:
            raise (f"bad date format [{v=}]; error @1, {ve=}")

    else:
        match = re.search(
            r"(\d{1,2})(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|\d{1,2})(\d{4})",
            v,
            re.IGNORECASE,
        )
        if match:
            day = int(match.group(1))
            month_str = match.group(2)
            year = int(match.group(3))
            try:
                if month_str.isdigit():
                    month = int(month_str)
                    date_obj = datetime.datetime(year, month, day).date()
                else:
                    date_obj = datetime.datetime.strptime(
                        f"{day} {month_str} {year}", "%d %b %Y"
                    ).date()
            except ValueError as ve:
                raise (f"bad date format [{v=}]; error @2, {ve=}")
        else:
            raise (f"bad date format [{v=}]; error @3")

    return datetime.datetime.combine(date_obj, datetime.datetime.min.time()).replace(
        microsecond=0
    )


def chunked(
    iterable: List[Dict[str, Any]], size: int
) -> Iterable[List[Dict[str, Any]]]:
    """Yield successive chunks of given size from a list."""
    for i in range(0, len(iterable), size):
        yield iterable[i : i + size]


def get_resource_folder(dirname: str = "resources", cwd: Optional[Path] = None) -> Path:
    """
    Get the resource folder path.
    The resource folder is located in the same directory as this script.
    """
    if cwd is None:
        current_file = Path(__file__).resolve()
        resource_folder = current_file.parent / dirname
    else:
        resource_folder = cwd / dirname
    if not resource_folder.exists():
        resource_folder = resource_folder.parent / dirname
        if not resource_folder.exists():
            raise FileNotFoundError(
                f"Resource folder {resource_folder} does not exist."
            )
    return resource_folder


def get_resource_file(
    resource_name: str,
    dirname: str = "resources",
    allow_multiple: bool = False,
    recursive: bool = False,
    cwd: Optional[Path] = None,
) -> Path | List[Path]:
    """
    Get the path(s) to a resource file within the resource folder.

    Supports wildcard patterns such as 'sample-*.csv'. By default, enforces
    a single match to preserve existing behavior.

    Args:
        resource_name: File name or glob pattern (e.g., 'sample-*.csv', '**/*.csv' if recursive=True).
        dirname: Name of the resource directory.
        allow_multiple: If True, returns a list of all matching files.
                        If False, requires exactly one match and returns a single Path.
        recursive: If True, uses recursive globbing (Path.rglob) to match patterns in subdirectories.
                   If False, matches only in the top-level resource folder (Path.glob).

    Returns:
        Path if allow_multiple=False and exactly one match is found,
        List[Path] if allow_multiple=True and one or more matches are found.

    Raises:
        FileNotFoundError: If no files match the given name/pattern.
        FileExistsError: If multiple files match but allow_multiple=False.
    """
    resource_folder = get_resource_folder(dirname, cwd=cwd)

    # If the string contains glob characters, treat as pattern.
    has_wildcards = any(ch in resource_name for ch in ["*", "?", "["])

    if not has_wildcards:
        # Original behavior for exact file names.
        resource_file = resource_folder / resource_name
        if not resource_file.exists():
            raise FileNotFoundError(f"Resource file {resource_file} does not exist.")
        return resource_file

    # Glob matching branch.
    if recursive:
        matches = list(resource_folder.rglob(resource_name))
    else:
        matches = list(resource_folder.glob(resource_name))

    if not matches:
        raise FileNotFoundError(
            f"No files matched pattern '{resource_name}' in {resource_folder} "
            f"(recursive={recursive})."
        )

    # Enforce single vs multiple matches based on flag.
    if allow_multiple:
        # Return sorted for determinism.
        return sorted(matches)
    else:
        if len(matches) > 1:
            # Helpful diagnostic.
            preview = ", ".join(str(p) for p in sorted(matches[:5]))
            more = "" if len(matches) <= 5 else f" (+{len(matches) - 5} more)"
            raise FileExistsError(
                f"Multiple files matched pattern '{resource_name}' in {resource_folder}: "
                f"{preview}{more}. Set allow_multiple=True to return all matches."
            )
        return matches[0]


def generate_row_hash_from_pdseries(
    row: pd.Series, precision: int = 8, hash_algorithm: str = "sha256"
) -> str:
    """
    Generates a cryptographic hash (SHA256 by default) for a single pandas Series (row).

    The function serializes the row's values into a canonical string format,
    handling different data types, especially standardizing floating-point numbers,
    before hashing. This ensures consistent hashing for identical rows.

    Args:
        row (pd.Series): The pandas Series representing a row of the DataFrame.
        precision (int): The number of decimal places to use for floating-point numbers
                         to ensure consistent hashing. Defaults to 8.
        hash_algorithm (str): The hash algorithm to use (e.g., 'sha256', 'md5').
                              Defaults to 'sha256'.

    Returns:
        str: The hexadecimal digest of the row's hash.
    """
    # 1. Standardize and convert values to strings
    # Handle floats by rounding to specified precision for consistency.
    # Handle NaNs/None by converting them to a consistent string representation (e.g., 'NaN').

    serialized_values = []

    for value in row.values:
        if pd.isna(value):
            str_value = "NaN"
        elif isinstance(value, float):
            # Format float with fixed precision
            str_value = f"{value:.{precision}f}"
        else:
            # Convert all other types (int, str, bool, datetime) to string
            str_value = str(value)

        serialized_values.append(str_value)

    # 2. Join all serialized values into a single canonical string using a separator
    canonical_string = "|".join(serialized_values)

    # 3. Encode the string to bytes
    encoded_bytes = canonical_string.encode("utf-8")

    # 4. Calculate and return the hash
    hasher = hashlib.new(hash_algorithm)
    hasher.update(encoded_bytes)

    return hasher.hexdigest()
