"""Small working-tree pattern scan; not a substitute for a history/security audit."""
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = [
    re.compile(r"AI" + r"za[0-9A-Za-z_-]{35}"),
    re.compile(r"gh[pousr]" + r"_[A-Za-z0-9]{36,}"),
    re.compile(r"AK" + r"IA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN " + r"(?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
]


def main() -> int:
    try:
        output = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT, stderr=subprocess.DEVNULL)
        paths = [ROOT / item for item in output.decode().split("\0") if item]
    except (OSError, subprocess.CalledProcessError):
        paths = [p for p in ROOT.rglob("*") if p.is_file() and not any(
            part in {".venv", ".git", "artifacts", "__pycache__", ".pytest_cache"} for part in p.parts)]
    findings = []
    for path in paths:
        if not path.is_file():
            continue
        if path.name == ".env":
            findings.append(f"{path.relative_to(ROOT)}: environment file must not be tracked")
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for line_number, line in enumerate(text.splitlines(), 1):
            if any(pattern.search(line) for pattern in PATTERNS):
                findings.append(f"{path.relative_to(ROOT)}:{line_number}: possible credential (value withheld)")
    print("\n".join(findings) if findings else "No credential patterns found in scanned working-tree text files.")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
