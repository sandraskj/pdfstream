"""Used in release procedure."""
import shutil
import subprocess
import sys
from pathlib import Path

import pkg_resources
import yaml

PACKAGE = "pdfstream"
REVER_DIR = Path("rever")
REQUIREMENTS = Path("requirements")
LICENSE = Path("LICENSE")
CONDA_CHANNEL_SOURCES = ["defaults", "diffpy", "conda-forge"]
CONDA_CHANNEL_TARGETS = ["st3107"]


def conda_recipe() -> None:
    """Make conda recipe."""
    # create a new director
    recipe_dir = REVER_DIR / "recipe"
    if not recipe_dir.is_dir():
        recipe_dir.mkdir()
    # create conda_build_config.yaml
    conda_build_config_yaml = recipe_dir / "conda_build_config.yaml"
    with conda_build_config_yaml.open("w") as f:
        yaml.safe_dump(conda_build_config(), f, sort_keys=False)
    # create meta.yaml
    meta_yaml = recipe_dir / "meta.yaml"
    with meta_yaml.open("w") as f:
        yaml.safe_dump(conda_meta(), f, sort_keys=False)
    # copy license
    shutil.copy(LICENSE, recipe_dir / LICENSE.name)
    return


def conda_build_config() -> dict:
    """Make the dictionary of conda build configuration."""
    return {
        "channel_sources": CONDA_CHANNEL_SOURCES,
        "channel_targets": CONDA_CHANNEL_TARGETS
    }


def conda_meta() -> dict:
    """Make the dictionary of conda meta information."""
    package = pkg_resources.require(PACKAGE)[0]
    name = package.project_name
    version = package.version
    host = read_dependencies(REQUIREMENTS / "build.txt")
    build = read_dependencies(REQUIREMENTS / "run.txt")
    tar_file_name = rf"{name}-{version}.tar.gz"
    sha256 = get_hash(REVER_DIR / tar_file_name)
    return {
        "package": {
            "name": name.lower(),
            "version": version
        },
        "source": {
            "url": rf"http://github.com/st3107/{name}/releases/download/{version}/{tar_file_name}",
            "sha256": sha256
        },
        "build": {
            "noarch": "python",
            "number": 0,
            "script": r"{{ PYTHON }} -m pip install . --no-deps -vv"
        },
        "requirements": {
            "host": host,
            "build": build
        },
        "test": {
            "imports": [name]
        },
        "about": {
            "home": rf"https://st3107.github.io/{name}/",
            "license": r"BSD-3-Clause",
            "license_file": str(LICENSE),
            "summary": r"The data analysis toolbox for the study on pair distribution function (PDF).",
            "dev_url": r"https://github.com/st3107/pdfstream/tree/master",
            "doc_url": r"https://st3107.github.io/pdfstream/"
        }
    }


def get_hash(file_path: Path, hash_type: str = "sha256") -> str:
    """Use openssl to get the hash of a file."""
    cp = subprocess.run(
        ["openssl", "dgst", rf"-{hash_type}", str(file_path)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    if cp.returncode != 0:
        sys.exit(cp.stderr)
    return cp.stdout.decode('utf-8').split("= ")[1].strip('\n')


def read_dependencies(txt_file: Path) -> list:
    """Read name of the required packages."""
    with txt_file.open("r") as f:
        dependencies = [
            line for line in f.read().splitlines()
            if not line.startswith('#')
        ]
    return dependencies


if __name__ == "__main__":
    conda_recipe()
