import base64
import hashlib
from urllib.parse import urlparse

import requests

BASE_URL = "https://docs.numerique.gouv.fr"


def docs_session():
    """Crée une session requests utilisant la session Firefox courante."""

    import browser_cookie3

    cookies = browser_cookie3.firefox(
        domain_name="docs.numerique.gouv.fr"
    )

    session = requests.Session()
    session.cookies.update(cookies)

    session.headers.update({
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0",
    })

    return session


def get_document(session, doc_id):
    url = (
        f"{BASE_URL}/api/v1.0/"
        f"documents/{doc_id}/formatted-content/"
    )
    print(f"Fetching document {doc_id} from {url}")

    response = session.get(url, timeout=30)
    response.raise_for_status()

    return response.json()


def download_image(session, url):
    if isinstance(url, str) and url.startswith("data:"):
        print("Decoding image from data URI")
        try:
            header, data = url.split(",", 1)
        except ValueError as exc:
            raise ValueError("Malformed data URI image") from exc

        if ";base64" in header:
            return base64.b64decode(data)

        return data.encode("utf-8")

    print(f"Downloading image from {url}")
    
    response = session.get(url, timeout=30)
    response.raise_for_status()
    return response.content


def get_document_children(session, doc_id):
    url = (
        "https://docs.numerique.gouv.fr/api/v1.0/"
        f"documents/{doc_id}/children/"
    )

    r = session.get(url, timeout=30)

    r.raise_for_status()
    return r.json()


def build_document_tree(session, root_id):
    root_doc = get_document(session, root_id)
    root = {
        "id": root_id,
        "title": root_doc["title"],
        "children": [],
    }

    def walk(node):
        children = get_document_children(session, node["id"])["results"]
        for child in children:
            child_node = {
                "id": child["id"],
                "title": child["title"],
                "children": [],
            }
            node["children"].append(child_node)
            walk(child_node)

    walk(root)
    return root


def iter_tree_ids(tree):
    yield tree["id"]
    for child in tree["children"]:
        yield from iter_tree_ids(child)


def iter_image_urls(blocks):
    if not isinstance(blocks, list):
        return

    for block in blocks:
        if not isinstance(block, dict):
            continue

        if block.get("type") == "image":
            props = block.get("props") or {}
            url = props.get("url")
            if isinstance(url, str) and url:
                yield url

        children = block.get("children")
        if isinstance(children, list):
            for child_url in iter_image_urls(children):
                yield child_url


def image_id_from_url(url):
    if isinstance(url, str) and url.startswith("data:"):
        digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
        return f"data-{digest[:24]}"

    name = urlparse(url).path.split("/")[-1]
    return name.rsplit(".", 1)[0]