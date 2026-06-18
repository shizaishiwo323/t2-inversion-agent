from __future__ import annotations

import importlib
from pathlib import Path
import site
import sys


REQUIRED_MODULES = [
    "streamlit",
    "openai",
    "numpy",
    "pandas",
    "scipy",
    "matplotlib",
    "plotly",
    "openpyxl",
    "xlrd",
    "PIL",
    "skimage",
    "pygimli",
    "pygimli.meshtools",
]


def main() -> int:
    env_prefix = Path(sys.prefix).resolve()
    user_site = Path(site.getusersitepackages()).resolve()
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version.split()[0]}")
    print(f"Python prefix: {env_prefix}")
    print(f"User site enabled: {site.ENABLE_USER_SITE}")
    missing: list[str] = []
    outside_environment: list[str] = []
    for module_name in REQUIRED_MODULES:
        try:
            module = importlib.import_module(module_name)
        except Exception as exc:
            print(f"[missing] {module_name}: {exc}")
            missing.append(module_name)
            continue
        version = getattr(module, "__version__", "")
        suffix = f" {version}" if version else ""
        module_file = getattr(module, "__file__", None)
        if module_file:
            module_path = Path(module_file).resolve()
            try:
                module_path.relative_to(env_prefix)
            except ValueError:
                if user_site in module_path.parents or module_path == user_site:
                    outside_environment.append(module_name)
                    print(f"[outside-env] {module_name}{suffix}: {module_path}")
                    continue
        print(f"[ok] {module_name}{suffix}")

    if missing or outside_environment:
        print("")
        print("Environment check failed. Create or activate the project conda environment:")
        print("  conda env create -f environment.yml")
        print("  conda activate t2agent")
        print("  set PYTHONNOUSERSITE=1  # Windows cmd, optional but recommended")
        print("  python scripts/check_t2agent_env.py")
        if outside_environment:
            print("")
            print("These modules were loaded from the user site instead of the active environment:")
            for module_name in outside_environment:
                print(f"  - {module_name}")
        return 1

    print("")
    print("Environment check passed: pyGIMLi mesh workflow dependencies are available.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
