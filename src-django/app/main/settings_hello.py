import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class HelloConfig:
    INPUT_DIRNAME = "jetforge_inputs_hello/"
    OUTPUT_DIRNAME = "jetforge_outputs_hello/"

    INPUT_ALLOWED_EXTENSIONS = (".txt", "")

    def __init__(self, media_root: str | Path):
        self.INPUT_DIRPATH = Path(media_root) / self.INPUT_DIRNAME
        self.INPUT_DIRPATH.mkdir(parents=True, exist_ok=True)
        self.OUTPUT_DIRPATH = Path(media_root) / self.OUTPUT_DIRNAME
        self.OUTPUT_DIRPATH.mkdir(parents=True, exist_ok=True)
        self.validate_config_values()

    def validate_config_values(self) -> None:
        pass
