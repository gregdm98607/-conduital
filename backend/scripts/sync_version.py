"""
Version sync script — reads version from pyproject.toml (SSoT) and updates:
  - frontend/package.json
  - installer/conduital.iss
  - backend/app/core/config.py fallback

Usage:
    python backend/scripts/sync_version.py
    python backend/scripts/sync_version.py --check   (verify all files match, exit 1 if not)

BACKLOG-116 / DEBT-080: Version single source of truth
"""

import json
import re
import sys
from pathlib import Path


def get_project_root() -> Path:
    """Get project root (parent of backend/)."""
    return Path(__file__).resolve().parent.parent.parent


def read_version_from_pyproject(root: Path) -> str:
    """Read version from pyproject.toml."""
    pyproject = root / "backend" / "pyproject.toml"
    text = pyproject.read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if not match:
        print("ERROR: Could not find version in pyproject.toml")
        sys.exit(1)
    return match.group(1)


def sync_package_json(root: Path, version: str) -> bool:
    """Update version in frontend/package.json."""
    pkg_path = root / "frontend" / "package.json"
    if not pkg_path.exists():
        return False
    data = json.loads(pkg_path.read_text(encoding="utf-8"))
    if data.get("version") == version:
        return False
    data["version"] = version
    pkg_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return True


def sync_installer(root: Path, version: str) -> bool:
    """Update version in installer/conduital.iss."""
    iss_path = root / "installer" / "conduital.iss"
    if not iss_path.exists():
        return False
    text = iss_path.read_text(encoding="utf-8")
    new_text = re.sub(
        r'#define MyAppVersion ".*?"',
        f'#define MyAppVersion "{version}"',
        text,
    )
    # Also update the output filename reference in the header comment
    new_text = re.sub(
        r"ConduitalSetup-[\d.]+[-\w]*\.exe",
        f"ConduitalSetup-{version}.exe",
        new_text,
    )
    if new_text == text:
        return False
    iss_path.write_text(new_text, encoding="utf-8")
    return True


def sync_config_fallback(root: Path, version: str) -> bool:
    """Update the fallback version in config.py."""
    config_path = root / "backend" / "app" / "core" / "config.py"
    text = config_path.read_text(encoding="utf-8")
    new_text = re.sub(
        r'_FALLBACK_VERSION = ".*?"',
        f'_FALLBACK_VERSION = "{version}"',
        text,
    )
    if new_text == text:
        return False
    config_path.write_text(new_text, encoding="utf-8")
    return True


def check_all(root: Path, version: str) -> bool:
    """Check that all files match the canonical version. Returns True if all match."""
    all_match = True

    # frontend/package.json
    pkg_path = root / "frontend" / "package.json"
    if pkg_path.exists():
        data = json.loads(pkg_path.read_text(encoding="utf-8"))
        if data.get("version") != version:
            print(f"  MISMATCH: frontend/package.json has '{data.get('version')}' (expected '{version}')")
            all_match = False

    # installer/conduital.iss
    iss_path = root / "installer" / "conduital.iss"
    if iss_path.exists():
        text = iss_path.read_text(encoding="utf-8")
        match = re.search(r'#define MyAppVersion "([^"]+)"', text)
        if match and match.group(1) != version:
            print(f"  MISMATCH: installer/conduital.iss has '{match.group(1)}' (expected '{version}')")
            all_match = False

    # config.py fallback
    config_path = root / "backend" / "app" / "core" / "config.py"
    text = config_path.read_text(encoding="utf-8")
    match = re.search(r'_FALLBACK_VERSION = "([^"]+)"', text)
    if match and match.group(1) != version:
        print(f"  MISMATCH: config.py fallback has '{match.group(1)}' (expected '{version}')")
        all_match = False

    return all_match


def main():
    root = get_project_root()
    version = read_version_from_pyproject(root)
    print(f"Canonical version (pyproject.toml): {version}")

    if "--check" in sys.argv:
        print("Checking version consistency...")
        if check_all(root, version):
            print("All files match.")
            sys.exit(0)
        else:
            print("Version mismatch detected! Run this script without --check to sync.")
            sys.exit(1)

    updated = []
    if sync_package_json(root, version):
        updated.append("frontend/package.json")
    if sync_installer(root, version):
        updated.append("installer/conduital.iss")
    if sync_config_fallback(root, version):
        updated.append("backend/app/core/config.py")

    if updated:
        print(f"Updated {len(updated)} file(s):")
        for f in updated:
            print(f"  - {f}")
    else:
        print("All files already in sync.")


if __name__ == "__main__":
    main()
