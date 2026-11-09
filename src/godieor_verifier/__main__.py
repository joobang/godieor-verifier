import argparse
import json
import os
from pathlib import Path
import sys
import tempfile

from .engine import EXIT_CODES, markdown, report


def atomic_write(path, content):
    fd, temporary = tempfile.mkstemp(prefix=".report-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(content)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main():
    parser = argparse.ArgumentParser(description="GODIEOR evidence verdict (bootstrap)")
    parser.add_argument("--acceptance", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--require-schema-version", type=int, choices=(1, 2), default=1,
                        help="통합 실행은 2로 지정하여 앱 전용 v1 입력을 거부")
    args = parser.parse_args()
    try:
        acceptance_bytes, evidence_bytes = args.acceptance.read_bytes(), args.evidence.read_bytes()
        result = report(acceptance_bytes, evidence_bytes, args.require_schema_version)
        json_output = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        markdown_output = markdown(result)
        args.out.mkdir(parents=True, exist_ok=True)
        atomic_write(args.out / "report.json", json_output)
        atomic_write(args.out / "report.md", markdown_output)
    except (OSError, UnicodeError, ValueError, RecursionError) as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        return EXIT_CODES["ERROR"]
    print(result["verdict"] + ": " + str(args.out / "report.json"))
    return EXIT_CODES[result["verdict"]]


if __name__ == "__main__":
    sys.exit(main())
