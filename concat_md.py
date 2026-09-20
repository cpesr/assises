from pathlib import Path
import re

from assises_doc_maker import data_paths, require_file, read_json
from assises_log import get_logger


logger = get_logger(__name__)

def concat_md(root_id):
    paths = data_paths(root_id)
    require_file(paths["tree"])

    tree = read_json(paths["tree"])
    chunks = []

    heading_pattern = re.compile(r"^(#{1,6})(\s+.*)$")
    title_line_pattern = re.compile(r"^#\s+(.+?)\s*$")
    author_line_pattern = re.compile(
        r"^(?:\*\*|\*|__|_)?\s*[Pp]ar\s+(.+?)\s*(?:\*\*|\*|__|_)?\s*$"
    )

    def split_doc_title(raw_title):
        title = (raw_title or "").strip()
        if not title:
            return "", ""

        parts = re.split(r"\s+-\s+", title, maxsplit=1)
        if len(parts) == 2:
            author, main_title = parts[0].strip(), parts[1].strip()
            return author, main_title

        return "", title

    def normalize_first_lines(markdown, doc_id, doc_title):
        lines = markdown.splitlines()
        fallback_author, fallback_title = split_doc_title(doc_title)

        extracted_title = ""
        extracted_author = ""

        consume_heading = False
        consume_author = False
        title_idx = None
        author_idx = None

        def next_non_empty_index(start):
            for idx in range(start, len(lines)):
                if lines[idx].strip():
                    return idx
            return None

        title_idx = next_non_empty_index(0)
        if title_idx is not None:
            first_match = title_line_pattern.match(lines[title_idx])
            if first_match:
                extracted_title = first_match.group(1).strip()
                consume_heading = True
            else:
                logger.warning(
                    "Document %s: premiere ligne invalide; fallback titre depuis le titre du document",
                    doc_id,
                )

        author_search_start = (title_idx + 1) if (consume_heading and title_idx is not None) else 0
        author_idx = next_non_empty_index(author_search_start)
        if author_idx is not None:
            author_match = author_line_pattern.match(lines[author_idx])
            if author_match:
                extracted_author = author_match.group(1).strip()
                consume_author = True
            else:
                logger.warning(
                    "Document %s: seconde ligne invalide; fallback auteur depuis le titre du document",
                    doc_id,
                )

        if not extracted_title:
            extracted_title = fallback_title or (doc_title or "").strip() or "Sans titre"
        if not extracted_author:
            extracted_author = fallback_author or None

        body_start = 0
        if consume_heading and title_idx is not None:
            body_start = title_idx + 1
        if consume_author and author_idx is not None:
            body_start = author_idx + 1

        body = "\n".join(lines[body_start:]).lstrip("\n")
        body = body.replace("# Références","# Références {.unnumbered}",)        
        
        return f"""
# {extracted_title}{f' {{author="{extracted_author}"}}' if extracted_author else ""}

{body}
"""

    def shift_headings(markdown, depth):
        if depth == 0:
            return markdown

        lines = []
        in_code_block = False

        for line in markdown.splitlines():
            stripped = line.lstrip()
            if stripped.startswith("```") or stripped.startswith("~~~"):
                in_code_block = not in_code_block
                lines.append(line)
                continue

            if not in_code_block:
                match = heading_pattern.match(line)
                if match:
                    level = min(6, len(match.group(1)) + depth)
                    lines.append("#" * level + match.group(2))
                    continue

            lines.append(line)

        return "\n".join(lines)

    def walk(node, depth=0, is_root=False):
        doc_id = node["id"]
        md_path = paths["md"] / f"{doc_id}.md"
        require_file(md_path)

        content = md_path.read_text().strip()
        content = content.replace("](../img/", "](img/")
        if not is_root:
            content = normalize_first_lines(content, doc_id, node.get("title", ""))
        if is_root:
            chunks.append(content)
        else:
            chunks.append(shift_headings(content, depth))

        for child in node["children"]:
            walk(child, 0 if is_root else depth + 1, is_root=False)

    walk(tree, depth=0, is_root=True)

    paths["document_md"].write_text("\n\n".join(chunks) + "\n")