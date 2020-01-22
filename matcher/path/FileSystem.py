import os
from pathlib import Path


def create_directories_for(file_path: str) -> None:
    dir_path = os.path.dirname(file_path)
    if dir_path:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
