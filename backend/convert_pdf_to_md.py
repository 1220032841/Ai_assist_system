import argparse
from pathlib import Path

from pypdf import PdfReader


def convert_pdf_to_md(input_pdf: Path, output_md: Path) -> None:
    reader = PdfReader(str(input_pdf))
    sections = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        sections.append(f"## Page {i + 1}\n\n{text}")

    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text("\n\n".join(sections), encoding="utf-8")

    print(f"Converted pages: {len(reader.pages)}")
    print(f"Output file: {output_md}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert PDF file to Markdown text")
    parser.add_argument("--input", required=True, help="Path to source PDF")
    parser.add_argument("--output", required=True, help="Path to output Markdown")
    args = parser.parse_args()

    input_pdf = Path(args.input)
    output_md = Path(args.output)

    if not input_pdf.exists():
        raise FileNotFoundError(f"Input PDF not found: {input_pdf}")

    convert_pdf_to_md(input_pdf, output_md)


if __name__ == "__main__":
    main()
