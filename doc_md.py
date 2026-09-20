def inline_to_markdown(items, plain_text=False):
    """Convertit le contenu inline BlockNote en Markdown."""
    result = []

    for item in items or []:
        item_type = item.get("type")

        if item_type == "text":
            text = item.get("text", "")
            if not plain_text:
                styles = item.get("styles", {})

                if styles.get("code"):
                    text = f"`{text}`"
                if styles.get("bold"):
                    text = f"**{text}**"
                if styles.get("italic"):
                    text = f"*{text}*"
                if styles.get("strike"):
                    text = f"~~{text}~~"

            result.append(text)

        elif item_type == "link":
            href = item.get("href", "")

            # Le texte d'un lien peut lui-même être structuré
            content = item.get("content", [])

            if isinstance(content, list):
                label = inline_to_markdown(content, plain_text=plain_text)
            else:
                label = str(content)

            if not label:
                label = href

            result.append(f"[{label}]({href})")

    return "".join(result)


def blocks_to_markdown(blocks, indent=0, image_url_mapper=None):
    """Convertit récursivement des blocs BlockNote en Markdown."""
    output = []

    for block in blocks or []:
        block_type = block.get("type")
        children = block.get("children", [])
        content = inline_to_markdown(block.get("content", []))

        if block_type == "heading":
            content = inline_to_markdown(block.get("content", []), plain_text=True)
            level = block.get("props", {}).get("level", 1)
            level = max(1, min(level, 6))
            output.append(f'{"#" * level} {content}\n')

        elif block_type == "paragraph":
            if content:
                output.append(f"{content}\n")
            else:
                output.append("")

        elif block_type == "bulletListItem":
            prefix = "  " * indent
            output.append(f"{prefix}- {content}")

            if children:
                child_md = blocks_to_markdown(
                    children,
                    indent=indent + 1,
                    image_url_mapper=image_url_mapper,
                )
                output.append(child_md.rstrip())

        elif block_type == "numberedListItem":
            prefix = "  " * indent
            output.append(f"{prefix}1. {content}")

            if children:
                child_md = blocks_to_markdown(
                    children,
                    indent=indent + 1,
                    image_url_mapper=image_url_mapper,
                )
                output.append(child_md.rstrip())

        elif block_type == "divider":
            output.append("\n---\n")

        elif block_type == "quote":
            lines = content.splitlines() or [""]
            output.append("\n".join(f"> {line}" for line in lines))

        elif block_type == "image":
            props = block.get("props", {})

            url = props.get("url", "")
            caption = props.get("caption", "")
            name = props.get("name", "image")

            alt = caption or name

            if url:
                if image_url_mapper is not None:
                    url = image_url_mapper(url)

                output.append(f"![{alt}]({url})")

                if caption:
                    output.append(f"*{caption}*")            

        else:
            # Fallback : ne pas perdre le texte d'un bloc inconnu
            if content:
                output.append(content)

            if children:
                output.append(
                    blocks_to_markdown(
                        children,
                        indent=indent,
                        image_url_mapper=image_url_mapper,
                    )
                )

    return "\n".join(output)


def document_to_markdown(document, image_url_mapper=None, include_title=True):
    title = document.get("title", "")
    blocks = document.get("content", [])

    md = ""

    if include_title and title:
        md += f"# {title}\n\n"

    md += blocks_to_markdown(
        blocks,
        image_url_mapper=image_url_mapper,
    )

    return md.strip() + "\n"

def find_block_types(blocks, types=None):
    if types is None:
        types = set()

    for block in blocks or []:
        types.add(block.get("type"))

        find_block_types(
            block.get("children", []),
            types
        )

    return types


def print_document_blocks_types(session, root_id, max_documents=20):
    base_url = "https://docs.numerique.gouv.fr/api/v1.0/documents"
    block_types = set()
    visited = set()

    def walk(doc_id):
        if len(visited) >= max_documents:
            return

        if doc_id in visited:
            return

        visited.add(doc_id)

        # Récupère le contenu
        response = session.get(
            f"{base_url}/{doc_id}/formatted-content/",
            timeout=30,
        )
        response.raise_for_status()

        document = response.json()

        block_types.update(
            find_block_types(document.get("content", []))
        )

        # Arrêt immédiat si on a atteint la limite
        if len(visited) >= max_documents:
            return

        # Récupère les enfants
        response = session.get(
            f"{base_url}/{doc_id}/children/",
            timeout=30,
        )
        response.raise_for_status()

        for child in response.json().get("results", []):
            if len(visited) >= max_documents:
                break

            walk(child["id"])

    walk(root_id)

    print(sorted(block_types))