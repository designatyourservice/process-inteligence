#!/usr/bin/env python3
"""
merge_to_pdf.py — Mescla arquivos de uma pasta em um único PDF.

Formatos suportados:
  .pdf   — mesclados diretamente via pypdf
  .jpg / .jpeg / .png — convertidos para PDF via Pillow
  .docx  — texto extraído e renderizado em PDF via reportlab

Uso:
  python3 merge_to_pdf.py <pasta_entrada> [--output <arquivo.pdf>]
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path


def convert_image_to_pdf(image_path: Path) -> bytes:
    """Converte uma imagem (JPG/PNG) para bytes de PDF."""
    from PIL import Image
    import io

    img = Image.open(image_path).convert("RGB")
    pdf_bytes = io.BytesIO()
    img.save(pdf_bytes, format="PDF", resolution=150)
    return pdf_bytes.getvalue()


def convert_docx_to_pdf(docx_path: Path) -> bytes:
    """Extrai texto de um .docx e renderiza como PDF via reportlab."""
    from docx import Document
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
    import io

    doc = Document(docx_path)
    pdf_bytes = io.BytesIO()
    pdf_doc = SimpleDocTemplate(
        pdf_bytes,
        pagesize=A4,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm,
    )
    styles = getSampleStyleSheet()
    story = []

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            story.append(Spacer(1, 0.3 * cm))
            continue
        style = styles["Heading1"] if para.style.name.startswith("Heading") else styles["Normal"]
        story.append(Paragraph(text, style))
        story.append(Spacer(1, 0.2 * cm))

    if not story:
        story.append(Paragraph("(documento sem conteúdo de texto)", styles["Normal"]))

    pdf_doc.build(story)
    return pdf_bytes.getvalue()


def merge_files_to_pdf(folder: Path, output_path: Path) -> list[str]:
    """
    Mescla todos os arquivos suportados da pasta em um único PDF.
    Retorna lista de arquivos que não puderam ser processados.
    """
    import pypdf
    import io

    supported_extensions = {".pdf", ".jpg", ".jpeg", ".png", ".docx"}
    files = sorted(
        [f for f in folder.iterdir() if f.is_file() and f.suffix.lower() in supported_extensions]
    )

    if not files:
        print(f"ERRO: Nenhum arquivo suportado encontrado em '{folder}'")
        print(f"Formatos aceitos: {', '.join(sorted(supported_extensions))}")
        sys.exit(1)

    print(f"\nArquivos encontrados ({len(files)}):")
    for f in files:
        print(f"  - {f.name}")

    writer = pypdf.PdfWriter()
    failed = []

    for file in files:
        ext = file.suffix.lower()
        print(f"\nProcessando: {file.name} ...", end=" ")
        try:
            if ext == ".pdf":
                reader = pypdf.PdfReader(str(file))
                for page in reader.pages:
                    writer.add_page(page)
                print(f"OK ({len(reader.pages)} página(s))")

            elif ext in {".jpg", ".jpeg", ".png"}:
                pdf_bytes = convert_image_to_pdf(file)
                reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
                for page in reader.pages:
                    writer.add_page(page)
                print("OK (imagem convertida)")

            elif ext == ".docx":
                pdf_bytes = convert_docx_to_pdf(file)
                reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
                for page in reader.pages:
                    writer.add_page(page)
                print(f"OK ({len(reader.pages)} página(s) do Word)")

        except Exception as e:
            print(f"FALHOU — {e}")
            failed.append(str(file.name))

    if len(writer.pages) == 0:
        print("\nERRO: Nenhuma página pôde ser adicionada ao PDF.")
        sys.exit(1)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        writer.write(f)

    print(f"\n✅ PDF gerado: {output_path}")
    print(f"   Total de páginas: {len(writer.pages)}")

    return failed


def main():
    parser = argparse.ArgumentParser(description="Mescla arquivos em um único PDF")
    parser.add_argument("folder", help="Pasta com os arquivos a mesclar")
    parser.add_argument(
        "--output",
        help="Caminho do PDF de saída (padrão: output/merged_YYYYMMDD_HHMMSS.pdf)",
        default=None,
    )
    args = parser.parse_args()

    folder = Path(args.folder)
    if not folder.exists() or not folder.is_dir():
        print(f"ERRO: A pasta '{folder}' não existe.")
        sys.exit(1)

    if args.output:
        output_path = Path(args.output)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path("output") / f"merged_{timestamp}.pdf"

    failed = merge_files_to_pdf(folder, output_path)

    if failed:
        print(f"\n⚠️  Arquivos que não puderam ser convertidos ({len(failed)}):")
        for f in failed:
            print(f"  - {f}")

    # Imprime o caminho do arquivo para ser capturado por outros scripts
    print(f"\nOUTPUT_PDF={output_path}")


if __name__ == "__main__":
    main()
