from pathlib import Path
import subprocess


TMP_DIR = Path(__file__).resolve().parent / "tmp"


def markdown_to_latex(
    markdown_file,
    latex_file,
    metadata_file=None,
    template_file=None,
    style_file="style.tex",
    titlepage_file="titlepage.tex",
    lua_filter_file="chapter-author.lua"
):
    markdown_file = Path(markdown_file).resolve()
    latex_file = Path(latex_file).resolve()
    style_file = Path(__file__).resolve().parent / style_file
    titlepage_file = Path(__file__).resolve().parent / titlepage_file
    lua_filter_file = Path(__file__).resolve().parent / lua_filter_file

    cmd = [
        "pandoc",
        str(markdown_file),
        "--metadata-file",
        str(metadata_file),
        #"--include-in-header",
        #str(style_file),
        #"--include-before-body",
        #str(titlepage_file),
        #"--lua-filter",
        #str(lua_filter_file),
        #"--top-level-division=part",
        #"-V lang=fr",
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
        #"-V lang=fr",
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
    base_dir = Path(__file__).resolve().parent

    markdown_file = Path(markdown_file).resolve()
    pdf_file = Path(pdf_file).resolve()

    document_dir = markdown_file.parent

    cmd = [
        "pandoc",
        str(markdown_file),
        "--pdf-engine=lualatex",
        "--resource-path",
        str(document_dir),
    ]

    if metadata_file:
        metadata_file = Path(metadata_file)

        if not metadata_file.is_absolute():
            metadata_file = base_dir / metadata_file

        cmd += [
            "--defaults",
            str(metadata_file.resolve()),
        ]

    if template_file:
        template_file = Path(template_file)

        if not template_file.is_absolute():
            template_file = base_dir / template_file

        cmd += [
            "--template",
            str(template_file.resolve()),
        ]

    cmd += [
        "-o",
        str(pdf_file),
    ]

    subprocess.run(
        cmd,
        check=True,
        cwd=base_dir,
    )