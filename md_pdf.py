from pathlib import Path
import subprocess


TMP_DIR = Path(__file__).resolve().parent / "tmp"


def markdown_to_latex(
    markdown_file,
    latex_file,
    metadata_file=None,
    template_file=None,
):
    markdown_file = Path(markdown_file).resolve()
    latex_file = Path(latex_file).resolve()
    style_file = Path(__file__).resolve().parent / "style.tex"
    titlepage_file = Path(__file__).resolve().parent / "titlepage.tex"
    lua_filter_file = Path(__file__).resolve().parent / "chapter-author.lua"

    cmd = [
        "pandoc",
        str(markdown_file),
        "--metadata-file",
        str(metadata_file),
        "--include-in-header",
        str(style_file),
        "--include-before-body",
        str(titlepage_file),
        "--lua-filter",
        str(lua_filter_file),
        "--top-level-division=part",
        "-V lang=fr",
        "-o",
        str(latex_file)
    ]

    if metadata_file:
        metadata_file = Path(metadata_file).resolve()
        cmd += [
            "--metadata-file",
            str(metadata_file),
        ]

    if template_file:
        template_file = Path(template_file).resolve()
        cmd += [
            "--template",
            str(template_file),
        ]

    subprocess.run(
        cmd,
        check=True,
        cwd=markdown_file.parent,
    )


def latex_to_pdf(latex_file, pdf_file, working_dir):
    latex_file = Path(latex_file).resolve()
    pdf_file = Path(pdf_file).resolve()
    working_dir = Path(working_dir).resolve()

    cmd = [
        "lualatex",
        "-interaction=nonstopmode",
        "-halt-on-error",
        "-V lang=fr",
        f"-output-directory={TMP_DIR}",
        str(latex_file),
    ]

    subprocess.run(
        cmd,
        check=True,
        cwd=working_dir,
    )
    subprocess.run(
        cmd,
        check=True,
        cwd=working_dir,
    )

    built_pdf = TMP_DIR / f"{latex_file.stem}.pdf"
    pdf_file.write_bytes(built_pdf.read_bytes())


def markdown_to_pdf(
    markdown_file,
    pdf_file,
    metadata_file=None,
    template_file=None,
):
    markdown_file = Path(markdown_file).resolve()
    pdf_file = Path(pdf_file).resolve()
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    latex_file = TMP_DIR / f"{pdf_file.stem}.tex"

    markdown_to_latex(
        markdown_file,
        latex_file,
        metadata_file=metadata_file,
        template_file=template_file,
    )
    latex_to_pdf(
        latex_file,
        pdf_file,
        working_dir=markdown_file.parent,
    )



def markdown_to_pdf_direct(
    markdown_file,
    pdf_file,
    metadata_file=None,
    template_file=None,
):
    markdown_file = Path(markdown_file).resolve()
    pdf_file = Path(pdf_file).resolve()
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    latex_file = TMP_DIR / f"{pdf_file.stem}.tex"

    common = [
        "pandoc",
        str(markdown_file),
        "--metadata-file", str(metadata_file),
        "--top-level-division=part"
    ]

    # Garde le LaTeX pour inspection
    latex_file = str(pdf_file).removesuffix(".pdf") + ".tex"

    subprocess.run(
        common + ["-o", latex_file],
        check=True,
    )

    # Produit réellement le PDF
    subprocess.run(
        common + [
            "--pdf-engine=lualatex",
            "-o", str(pdf_file),
        ],
        check=True,
    )

	