import logging
from pathlib import Path

# Use the standard library tomllib for reading TOML
import tomllib

# The standard library does not include a TOML writer, so we implement a robust manual writer.

logger = logging.getLogger("django")

CONFIG_FILE = Path("config.toml")

# FIX: Changed outermost braces from {} (set) to [] (list) for flow_default.
# I also cleaned up the flow list to have unique, sequential indices and removed duplicates.
DEFAULT_CONFIG = {
    "default": {
        "key": "value",
    },
}


class ConfigHelper:
    default_config: dict = DEFAULT_CONFIG
    config: dict = {}

    def __init__(self, filepath: Path = CONFIG_FILE):
        self.filepath = filepath
        if not filepath.exists():
            logger.info("Configuration file not found.")
            logger.info("Writing default configuration..")
            # Write config must be called before load_config() attempts to read it
            self.write_config(self.default_config)

        # Ensure that if writing failed or something went wrong, we fall back to defaults
        loaded_config = self.load_config()
        # If load_config returns None (due to an error), use default_config as fallback
        self.config = (
            loaded_config if loaded_config is not None else self.default_config
        )

    def _format_toml_value(self, value):
        """Formats a Python value into its TOML string representation."""
        if isinstance(value, str):
            # Strings must be quoted in TOML
            return f'"{value}"'
        elif isinstance(value, (int, float, bool)):
            # Numbers and booleans are unquoted
            return str(value)
        else:
            # Fallback for unexpected types (or for robustness)
            return f'"{str(value)}"'

    def dict_to_toml_string(self, data: dict) -> str:
        """
        Manually formats a nested dictionary, supporting standard tables and
        Arrays of Tables, into a valid TOML string.
        """
        toml_str = ""
        for section, content in data.items():
            if isinstance(content, list) and all(
                isinstance(item, dict) for item in content
            ):
                # Handle Array of Tables (like 'flow_default')
                # In TOML, these require double brackets: [[section]]
                for item in content:
                    toml_str += f"[[{section}]]\n"
                    for key, value in item.items():
                        toml_str += f"{key} = {self._format_toml_value(value)}\n"
                    toml_str += "\n"  # Add a newline after each table in the array
            elif isinstance(content, dict):
                # Handle standard TOML table (like 'unit_of_measurements')
                # In TOML, these require single brackets: [section]
                toml_str += f"[{section}]\n"
                for key, value in content.items():
                    toml_str += f"{key} = {self._format_toml_value(value)}\n"
                toml_str += "\n"  # Add a newline for separation
        return toml_str

    def load_config(self) -> dict | None:
        """
        Reads configuration using tomllib.
        Returns dict or None on failure.
        """
        try:
            # tomllib requires reading the file in binary mode ("rb")
            with open(self.filepath, "rb") as f:
                config = tomllib.load(f)
            logger.debug("Configuration loaded successfully.")
            return config
        except tomllib.TOMLDecodeError as e:
            logger.error(f"TOML decoding error in {self.filepath}: {e}")
            logger.warning("Using default configuration...")
            return None
        except Exception as e:
            logger.error(f"File read error in {self.filepath}: {e}")
            logger.warning("Using default configuration...")
            return None

    def write_config(self, config: dict) -> None:
        try:
            toml_content = self.dict_to_toml_string(config)
            with open(self.filepath, "w") as f:
                f.write(toml_content)
            logger.info("Default configuration written successfully.")
        except Exception as e:
            logger.info("Error writing configuration file")
            raise e
