import argparse
import json
from pathlib import Path
import time
import re

import requests

from doc_md import document_to_markdown
from md_pdf import markdown_to_pdf
from assises_log import configure_logging, get_logger


logger = get_logger(__name__)


def data_paths(root_id):
    base = Path("data") / root_id
    return {
        "base": base,
        "tree": base / "tree.json",
        "docs": base / "docs",
        "img": base / "img",
        "md": base / "md",
        "document_md": base / "document.md",
        "document_pdf": base / "document.pdf",
    }


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def read_json(path):
    return json.loads(path.read_text())


def require_file(path):
    if not path.is_file():
        raise FileNotFoundError(path)


def normalize_tree_titles(tree):
    node_id = tree.get("id", "unknown")
    title = tree.get("title")

    if not isinstance(title, str) or not title.strip():
        fallback_title = f"Document {node_id}"
        logger.warning(
            "Document %s sans titre dans l'arbre; titre de secours applique: %s",
            node_id,
            fallback_title,
        )
        tree["title"] = fallback_title

    for child in tree.get("children", []):
        if isinstance(child, dict):
            normalize_tree_titles(child)


def retrieve_tree(root_id):
    from doc_api import build_document_tree, docs_session

    paths = data_paths(root_id)
    session = docs_session()
    tree = build_document_tree(session, root_id)
    normalize_tree_titles(tree)
    write_json(paths["tree"], tree)


def retrieve_docs(root_id, mode="all", doc_ids=None):
    from doc_api import docs_session, get_document, iter_tree_ids

    paths = data_paths(root_id)
    require_file(paths["tree"])

    tree = read_json(paths["tree"])
    session = docs_session()
    paths["docs"].mkdir(parents=True, exist_ok=True)

    tree_doc_ids = list(iter_tree_ids(tree))
    if doc_ids:
        requested_ids = set(doc_ids)
        missing_ids = sorted(requested_ids.difference(tree_doc_ids))
        for missing_id in missing_ids:
            logger.warning(
                "Document %s demande avec --retrieve-docs mais absent de l'arbre",
                missing_id,
            )

        target_doc_ids = [doc_id for doc_id in tree_doc_ids if doc_id in requested_ids]
    else:
        target_doc_ids = tree_doc_ids

    for index, doc_id in enumerate(target_doc_ids):
        if mode == "resume":
            existing = paths["docs"] / f"{doc_id}.json"
            if existing.exists():
                continue

        if index > 0:
            time.sleep(0.5)

        retry_delay = 0.5
        for attempt in range(1, 10):
            try:
                doc = get_document(session, doc_id)
                write_json(paths["docs"] / f"{doc_id}.json", doc)
                break
            except requests.exceptions.HTTPError as exc:
                response = getattr(exc, "response", None)
                if getattr(response, "status_code", None) != 429:
                    logger.error(
                        "Erreur lors de la récupération du document %s: %s",
                        doc_id,
                        str(exc),
                    )
                    break

                if attempt >= 5:
                    logger.error(
                        "Document %s abandonne après 429 sur 5 tentatives: %s",
                        doc_id,
                        str(exc),
                    )
                    break

                logger.warning(
                    "429 Too Many Requests pour %s (tentative %s/5), retry dans %.1fs",
                    doc_id,
                    attempt,
                    retry_delay,
                )
                time.sleep(retry_delay)
                retry_delay *= 2
            except Exception as exc:
                logger.error(
                    "Erreur lors de la récupération du document %s: %s",
                    doc_id,
                    str(exc),
                )
                break


def retrieve_images(root_id):
    from doc_api import (
        docs_session,
        download_image,
        image_id_from_url,
        iter_image_urls,
        iter_tree_ids,
    )

    paths = data_paths(root_id)
    require_file(paths["tree"])

    tree = read_json(paths["tree"])
    paths["img"].mkdir(parents=True, exist_ok=True)
    session = docs_session()

    for doc_id in iter_tree_ids(tree):
        doc_path = paths["docs"] / f"{doc_id}.json"
        require_file(doc_path)

        document = read_json(doc_path)
        content = document.get("content")
        if not isinstance(content, list):
            logger.warning(
                "Document %s ignore pour les images: content invalide (%s)",
                doc_id,
                type(content).__name__,
            )
            continue

        for url in iter_image_urls(content):
            img_id = image_id_from_url(url)
            img_path = paths["img"] / f"{img_id}.png"
            if not img_path.exists():
                img_path.write_bytes(download_image(session, url))


def convert_docs_to_md(root_id):
    from doc_api import image_id_from_url, iter_tree_ids

    paths = data_paths(root_id)
    require_file(paths["tree"])

    tree = read_json(paths["tree"])
    paths["md"].mkdir(parents=True, exist_ok=True)

    def map_image_url(url):
        img_id = image_id_from_url(url)
        img_path = paths["img"] / f"{img_id}.png"
        require_file(img_path)
        return f"../img/{img_id}.png"

    for doc_id in iter_tree_ids(tree):
        doc_path = paths["docs"] / f"{doc_id}.json"
        require_file(doc_path)

        document = read_json(doc_path)
        md = document_to_markdown(
            document,
            image_url_mapper=map_image_url,
            include_title=False,
        )
        (paths["md"] / f"{doc_id}.md").write_text(md)



def convert_pdf(root_id):
    paths = data_paths(root_id)
    require_file(paths["document_md"])
    metadata_path = Path(__file__).with_name("assises.yaml")
    require_file(metadata_path)

    markdown_to_pdf(
        paths["document_md"],
        paths["document_pdf"],
        metadata_file=metadata_path,
    )


def parse_retrieve_docs_args(values):
    if values is None:
        return None, []

    mode = "all"
    doc_ids = list(values)
    if doc_ids and doc_ids[0] in {"all", "resume"}:
        mode = doc_ids.pop(0)

    return mode, doc_ids


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("root_id")
    parser.add_argument("--retrieve-tree", action="store_true")
    parser.add_argument(
        "--retrieve-docs",
        nargs="*",
        help="telecharge tous les documents, ou seulement les ids fournis; premier argument optionnel: all|resume",
    )
    parser.add_argument("--retrieve-images", action="store_true")
    parser.add_argument("--md", action="store_true")
    parser.add_argument("--concat-md", action="store_true")
    parser.add_argument("--pdf", action="store_true")
    return parser.parse_args()


def main():
    configure_logging()
    args = parse_args()
    retrieve_docs_mode, retrieve_docs_ids = parse_retrieve_docs_args(
        args.retrieve_docs
    )

    if args.retrieve_tree:
        retrieve_tree(args.root_id)
    if retrieve_docs_mode:
        retrieve_docs(
            args.root_id,
            mode=retrieve_docs_mode,
            doc_ids=retrieve_docs_ids,
        )
    if args.retrieve_images:
        retrieve_images(args.root_id)
    if args.md:
        convert_docs_to_md(args.root_id)
    if args.concat_md:
        from concat_md import concat_md

        concat_md(args.root_id)
    if args.pdf:
        convert_pdf(args.root_id)


if __name__ == "__main__":
    main()


