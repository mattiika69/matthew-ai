#!/usr/bin/env python3
"""Record a completed publication review of catalog metadata and every skill file.

Use only after inspecting the exact content for public distribution. This tool
records hashes; it does not perform the human/agent review, clear source flags,
or establish answer-quality acceptance. Any changed/added/removed package file
or changed catalog invalidates this review.
"""
import argparse
import subprocess
from pathlib import Path

from package_skill import record_review

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reviewer", required=True, help="Actual reviewer; do not imply Matthew approval unless he reviewed it.")
    parser.add_argument("--note", required=True, help="Completed publication review scope and basis; avoid private details in this public note.")
    args = parser.parse_args()
    try:
        path = record_review(ROOT, args.reviewer, args.note)
    except (ValueError, OSError, KeyError, subprocess.CalledProcessError) as error:
        parser.error(str(error))
    print(f"Recorded {path.relative_to(ROOT)}. This records publication review, not behavioral acceptance.")


if __name__ == "__main__":
    main()
