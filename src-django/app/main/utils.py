import datetime
import logging
import os
import random
import re
import secrets
import string
import time
import uuid
from collections import namedtuple
from functools import wraps
from typing import Any, Callable, Dict, Optional, Tuple, Type, Union
from urllib.parse import urlparse

lg = logging.getLogger("django")


DbConnectionParam = namedtuple("DbConnectionParam", "db username password host port")

# Define a type hint for the exceptions parameter
ExceptionTypes = Union[Type[Exception], Tuple[Type[Exception], ...]]


def convert_to_snake_case(name: str) -> str:
    """
    Converts a column name into a PEP8-compliant snake_case variable name.

    ... (Update docstring to accurately reflect what is replaced)
    """

    # Replace all non-word characters (including symbols, spaces, etc.) with a space.
    # '\W' matches anything that is NOT a letter, number, or underscore.
    name = name.lower().strip()
    cleaned_name = re.sub(
        r"[\W_]+", " ", name
    )  # Use '+' to combine adjacent non-word/underscore into one space

    # Now replace spaces with an underscore
    snake_case_name = cleaned_name.replace(" ", "_")

    # Strip any leading or trailing underscores from the final string
    snake_case_name = snake_case_name.strip("_")

    return snake_case_name if snake_case_name else None


def retry_on_exception(
    func: Union[Callable[..., Any], None] = None,
    *,  # Enforce subsequent arguments to be keyword-only
    max_attempts: int = 3,
    base_delay: float = 2,
    max_delay: float = 60,  # New: Cap the maximum backoff delay
    exceptions_to_catch: ExceptionTypes = Exception,
) -> Union[Callable[..., Any], Callable[[Callable[..., Any]], Callable[..., Any]]]:
    """
    A decorator that retries the execution of a function if it raises a specified exception,
    using exponential backoff.

    Exponential backoff is required to work with Celery.

    Parameters:
        max_attempts (int): The maximum number of times to attempt the function execution.
        base_delay (float): The initial delay in seconds. Delay increases exponentially.
        max_delay (float): The maximum delay allowed between retries.
        exceptions_to_catch (ExceptionTypes): The exception or tuple of exceptions to catch and retry on.
    """

    def decorator(f: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(f)
        def wrapper(*args, **kwargs) -> Any:
            # We start counting attempts from 1
            for attempt in range(1, max_attempts + 1):
                try:
                    # 1. Attempt to call the original function
                    result = f(*args, **kwargs)
                    lg.info(f"[SUCCESS] Attempt {attempt}/{max_attempts} successful.")
                    return result

                except exceptions_to_catch as e:
                    # 2. Handle the caught exception

                    # If this was the last allowed attempt, re-raise the exception to fail hard
                    if attempt == max_attempts:
                        lg.warning(
                            f"[FAIL] Attempt {attempt}/{max_attempts} failed. Max retries reached. Raising final exception: {type(e).__name__}"
                        )
                        # Re-raise the original exception
                        raise e

                    # 3. Calculate exponential backoff delay (2^n-1 * base_delay)
                    # We add a small random jitter (0-1s) to prevent a thundering herd problem.
                    exponential_backoff = base_delay * (2 ** (attempt - 1))
                    jitter = random.uniform(0, 1)
                    current_delay = min(exponential_backoff + jitter, max_delay)

                    # Log the retry and wait for the delay
                    lg.warning(
                        f"[RETRY] Attempt {attempt}/{max_attempts} failed with error: {type(e).__name__}. Retrying in {current_delay:.2f}s..."
                    )
                    time.sleep(current_delay)

            # Safety net: This line should theoretically be unreachable if max_attempts > 0
            raise RuntimeError(
                "Retry decorator finished without success or re-raising a final exception."
            )

        return wrapper

    # This logic allows the decorator to be used with or without arguments
    if func is None:
        # Called as @retry_on_exception(args) -> return the decorator function
        return decorator
    else:
        # Called as @retry_on_exception without parentheses -> apply the decorator immediately
        return decorator(func)


def convert_str_to_bool(value):
    mapper = {
        "true": True,
        "false": False,
        "1": True,
        "0": False,
    }
    v = value.lower()
    if v in mapper:
        return mapper[v]
    else:
        return False


def get_utc_timestamp_now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def get_datetime_str(
    dtformat: str = "%Y%m%d_%H%M%S", append_microseconds: bool = False
) -> str:
    now = datetime.datetime.now()
    timestr = now.strftime(dtformat)
    if append_microseconds:
        ms = now.strftime("%f")[:2]
        timestr = f"{timestr}{ms}"
    return timestr


def get_today_date(format):
    today = datetime.datetime.today()
    return today.strftime(format)


def get_quarter(dt: datetime.datetime) -> Optional[str]:
    """
    Calculates the fiscal quarter (Q1, Q2, Q3, or Q4) for a given datetime object
    using a single arithmetic expression.

    Args:
        dt: The datetime object to check.

    Returns:
        A string representing the quarter (e.g., "Q1").
    """
    month = dt.month

    # The formula (month - 1) // 3 + 1 mathematically finds the ceiling of (month / 3).
    # Examples:
    # Month 1, 2, 3 -> (0, 1, 2) // 3 + 1 -> 0 + 1 = 1 (Q1)
    # Month 4, 5, 6 -> (3, 4, 5) // 3 + 1 -> 1 + 1 = 2 (Q2)
    # Month 10, 11, 12 -> (9, 10, 11) // 3 + 1 -> 3 + 1 = 4 (Q4)
    quarter_number = (month - 1) // 3 + 1
    return f"Q{quarter_number}"


def generate_password(length: int = 16) -> str:
    aset = string.ascii_letters + string.digits + string.punctuation
    pwd = "".join(secrets.choice(aset) for _ in range(16))
    return pwd


def generate_unique_id():
    return str(uuid.uuid4())


def create_random_string(size: int) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(size))


def sanitize_filename(input_string):
    """
    Converts any user input string into an alphanumeric name suitable for
    use as a filename in Windows or Linux operating systems.

    Args:
      input_string: The string to be converted.

    Returns:
      A new string containing only alphanumeric characters.
    """
    # Remove any characters that are not alphanumeric
    sanitized_string = re.sub(r"[^a-zA-Z0-9]", "", input_string)
    return sanitized_string


def natural_sort(mylist: list[str]) -> list[str]:
    def convert(text: str):
        return [int(c) if c.isdigit() else c for c in re.split(r"(\d+)", text)]

    return sorted(mylist, key=convert)


def get_boolean_env_var(var_name: str, default: bool = False) -> bool:
    """Retrieve a boolean environment variable."""
    return os.getenv(var_name, str(default)).lower() in ("true", "1", "t")


def parse_mongo_uri(uri: str) -> DbConnectionParam:
    if not uri:
        raise ValueError("invalid Mongo URI for parsing")
    parsed = urlparse(uri)
    database_name = parsed.path.lstrip("/")

    connection_details = DbConnectionParam(
        db=database_name if database_name else None,
        username=parsed.username,
        password=parsed.password,
        host=parsed.hostname,
        port=parsed.port,
    )

    return connection_details
