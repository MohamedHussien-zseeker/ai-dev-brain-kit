"""PyInstaller entry point for Windows cross-compilation.

Invoked by scripts/build-windows.sh via wine.
"""
import sys
import site

# Ensure site-packages is on sys.path (Wine Python may not add it correctly)
sp = [d for d in site.getsitepackages() if d.endswith("site-packages")]
for d in sp:
    if d not in sys.path:
        sys.path.insert(0, d)

import PyInstaller.__main__  # noqa: E402


def main() -> int:
    spec = r"C:\brain-build\brain.spec"
    dist = r"C:\brain-build\dist"
    work = r"C:\brain-build\build"

    PyInstaller.__main__.run([
        "--clean",
        "--distpath", dist,
        "--workpath", work,
        spec,
    ])
    return 0


if __name__ == "__main__":
    sys.exit(main())
