import subprocess
from pathlib import Path
from typing import List, Optional, Union

# We avoid using logging here because the Django app logger
# may not have been initialized yet.


class CommandManager:
    def run(
        self,
        cmd: List[str],
        check: bool = True,
        timeout: Optional[int] = None,
        text: bool = True,
        shell: bool = False,
        cwd: Optional[Union[str, Path]] = None,
        show_cmd: bool = False,
        env: Optional[dict] = None,
    ) -> subprocess.CompletedProcess:

        try:
            if not cmd:
                raise ValueError("no cmd specified")
            if show_cmd:
                print(f"Running command: {' '.join(cmd)} in {cwd or Path.cwd()}")

            results = subprocess.run(
                cmd,
                check=check,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=text,  # Process streams as text
                timeout=timeout,
                shell=shell,
                cwd=cwd,
                env=env,
            )
            return results

        except subprocess.CalledProcessError as call_error:
            print(
                f"Command '{' '.join(cmd)}' failed with exit code {call_error.returncode}."
            )
            if call_error.stdout:
                print(f"STDOUT:\n{call_error.stdout}")
            if call_error.stderr:
                print(f"STDERR:\n{call_error.stderr}")
            raise call_error

        except FileNotFoundError:
            print(f"Command not found: {cmd[0]}")
            raise

        except Exception as e:
            print(
                f"An unexpected error occurred while running command '{' '.join(cmd)}': {e}"
            )
            raise


class GitCommandManager(CommandManager):
    error_tag: str = "v0.0.0-error"

    def run_git_tag(self, debug_mode: bool = False) -> str:
        try:
            results = self.run(["git", "describe"], text=True)
        except Exception:
            raise

        return results.stdout.strip()


class VersionManager:
    cmd_manager: CommandManager
    version_fpath_root: Optional[Path] = None
    app_ver_filename: str = "app_version.txt"
    app_ver_filepath: Optional[Path] = None
    version: str = "v0.0.0-error"

    def __init__(
        self,
        folder_mode: str = "app_bundles",
        app_ver_filename: str = "app_version.txt",
    ) -> None:
        self.gcm = GitCommandManager()
        self.version_fpath_root = self.init_root_folder_for_appversion_file(folder_mode)
        self.app_ver_filename = app_ver_filename
        self.app_ver_filepath = self.version_fpath_root / self.app_ver_filename

    def init_root_folder_for_appversion_file(self, folder_mode: str = "") -> Path:
        """Initializes the root folder for the app version file based on the specified mode."""
        # Determine the root directory of the script for relative path calculations
        script_dir = Path(__file__).parent

        match folder_mode.lower():
            case "app_bundles":
                f_root = script_dir / "bundles"
            case "django":
                f_root = script_dir
                locate_managepy = f_root.parent / "manage.py"
                if not locate_managepy.is_file():
                    # Try another common Django structure: manage.py in the script's parent's parent
                    # e.g. myproject/myapp/utils/version_script.py -> myproject/manage.py
                    locate_managepy_alt = script_dir.parent.parent / "manage.py"
                    if not locate_managepy_alt.is_file():
                        raise RuntimeError(
                            f"VersionManager(folder_mode='{folder_mode}') unable to locate django manage.py "
                            f"at {locate_managepy} or {locate_managepy_alt}"
                        )
            case _:
                f_root = script_dir

        f_root.mkdir(parents=True, exist_ok=True)
        return f_root

    def write_app_version_file(self, version: str = "") -> Path:
        # This method uses print statements, not logger because
        # the Django app logger may not have been initialized yet.
        with open(self.app_ver_filepath, "w") as fwriter:
            fwriter.write(version)
        print(f"app_version={version} updated > {self.app_ver_filepath}")
        return self.app_ver_filepath

    def get_app_version_from_file(self) -> str:
        if not self.app_ver_filepath.is_file():
            print(f"Version file not found: {self.app_ver_filepath}")
            return self.version
        with open(self.app_ver_filepath, "r") as fr:
            version = fr.read().strip()
        self.version = version
        return self.version

    def get_app_version(self, run_git_tag: bool = False) -> str:
        """Retrieves the application version either from a git tag or from a file."""
        if run_git_tag:
            try:
                version = self.update_app_version_from_git()
                return version
            except subprocess.CalledProcessError:
                raise
        else:
            return self.get_app_version_from_file()

    def update_app_version_from_git(self) -> str:
        """Runs `git tag` command to get the latest version tag,
        then writes it to the app version file."""
        self.version = self.gcm.run_git_tag()
        self.write_app_version_file(self.version)
        return self.version

    def version_file_exists(self) -> bool:
        """Checks if the app version file exists."""
        return self.app_ver_filepath.is_file()


class GenericAppVersionManager(VersionManager):
    def __init__(self, folder_mode="app_bundles", app_ver_filename="app_version.txt"):
        super().__init__(folder_mode, app_ver_filename)


class DjangoVersionManager(VersionManager):
    def __init__(self, folder_mode="django", app_ver_filename="app_version.txt"):
        super().__init__(folder_mode, app_ver_filename)
