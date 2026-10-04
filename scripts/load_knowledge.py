"""Chunk the files in knowledge/ and load them into PREDMACC_DB.APP.KNOWLEDGE_CHUNKS.

Usage:  python scripts/load_knowledge.py [--connection YRUZETZ-VG76067]

Reads .md / .txt / .pdf files (pdf needs `pip install pypdf`), writes a chunk CSV, uploads it
with the Snowflake CLI (via uvx) and reloads the table. The Cortex Search service
MAINTENANCE_KB_SEARCH refreshes itself from the table.
"""

import argparse
import csv
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = ROOT / "knowledge"
STAGE = "@PREDMACC_DB.APP.DATA_STAGE"
TABLE = "PREDMACC_DB.APP.KNOWLEDGE_CHUNKS"
MAX_CHARS = 1200


def read_text(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError:
            print(f"  skipping {path.name}: pip install pypdf to read PDFs")
            return ""
        return "\n\n".join((p.extract_text() or "") for p in PdfReader(str(path)).pages)
    return path.read_text(encoding="utf-8", errors="ignore")


def split_long(text: str) -> list:
    parts, current = [], ""
    for para in re.split(r"\n\s*\n", text):
        para = para.strip()
        if not para:
            continue
        if current and len(current) + len(para) > MAX_CHARS:
            parts.append(current)
            current = para
        else:
            current = f"{current}\n\n{para}" if current else para
    if current:
        parts.append(current)
    return parts


def chunk_file(path: Path) -> list:
    text = read_text(path)
    if not text.strip():
        return []
    m = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    title = m.group(1).strip() if m else path.stem
    sections = re.split(r"^##\s+", text, flags=re.MULTILINE)
    chunks = []
    for i, sec in enumerate(sections):
        sec = sec.strip()
        if not sec:
            continue
        heading = sec.split("\n", 1)[0] if i > 0 else "Overview"
        for part in split_long(sec):
            chunks.append((title, f"{title} - {heading}\n\n{part}"))
    return chunks


def run(cmd: list) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise SystemExit(f"Command failed: {' '.join(cmd)}\n{result.stdout}\n{result.stderr}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--connection", default="YRUZETZ-VG76067")
    args = ap.parse_args()

    files = sorted(
        p for p in KNOWLEDGE_DIR.rglob("*")
        if p.suffix.lower() in {".md", ".txt", ".pdf"} and p.name.lower() != "readme.md"
    )
    rows = []
    for p in files:
        for n, (title, content) in enumerate(chunk_file(p), start=1):
            rows.append((f"{p.stem}-{n}", p.name, title, content, f"knowledge/{p.name}"))
    print(f"{len(files)} files -> {len(rows)} chunks")
    if not rows:
        raise SystemExit("No chunks to load.")

    with tempfile.TemporaryDirectory() as tmp:
        csv_path = Path(tmp) / "knowledge_chunks.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["CHUNK_ID", "FILE_NAME", "TITLE", "CONTENT", "SOURCE_URL"])
            w.writerows(rows)
        base = ["uvx", "--from", "snowflake-cli", "snow"]
        run(base + ["stage", "copy", str(csv_path), STAGE, "--connection", args.connection, "--overwrite"])

    run(base + [
        "sql", "--connection", args.connection, "-q",
        f"TRUNCATE TABLE {TABLE}; COPY INTO {TABLE} FROM {STAGE}/knowledge_chunks.csv ON_ERROR = ABORT_STATEMENT;",
    ])
    print(f"Loaded {len(rows)} chunks into {TABLE}")


if __name__ == "__main__":
    main()
