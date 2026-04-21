import argparse
import re
from pathlib import Path


WATERMARK_PATTERNS = [
    r"^感谢您下载包图网平台上提供的PPT作品",
    r"^为了您和包图网以及原创作者的利益",
    r"^请勿复制、传播、销售",
    r"^包图网将对作品进行维权",
    r"^ibaotu\.com$",
    r"^Object Oriented\s+Programming",
]


def should_drop(line: str) -> bool:
    s = line.strip()
    if not s:
        return False
    for p in WATERMARK_PATTERNS:
        if re.search(p, s, flags=re.IGNORECASE):
            return True
    return False


def clean_markdown(text: str) -> str:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    cleaned = []

    for line in lines:
        if should_drop(line):
            continue

        # Remove repeated single-page headers like "## Page 23" if desired for cleaner retrieval.
        if re.match(r"^##\s*Page\s*\d+\s*$", line.strip()):
            continue

        cleaned.append(line.rstrip())

    # Collapse >2 blank lines.
    out = "\n".join(cleaned)
    out = re.sub(r"\n{3,}", "\n\n", out)
    return out.strip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean noisy markdown extracted from PDF for RAG ingestion")
    parser.add_argument("--input", required=True, help="Input markdown path")
    parser.add_argument("--output", required=True, help="Output cleaned markdown path")
    args = parser.parse_args()

    inp = Path(args.input)
    out = Path(args.output)
    if not inp.exists():
        raise FileNotFoundError(f"Input markdown not found: {inp}")

    text = inp.read_text(encoding="utf-8")
    cleaned = clean_markdown(text)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(cleaned, encoding="utf-8")

    print(f"Input chars: {len(text)}")
    print(f"Output chars: {len(cleaned)}")
    print(f"Output file: {out}")


if __name__ == "__main__":
    main()
