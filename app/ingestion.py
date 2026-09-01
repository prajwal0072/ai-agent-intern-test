from pathlib import Path
import re
import yaml

from app.models import Document, Chunk


KNOWLEDGE_BASE_DIR = Path("knowledge-base")


def parse_markdown_file(file_path: Path) -> tuple[dict, str]:
    """
    Read a Markdown file and separate YAML front matter from the body.
    """

    content = file_path.read_text(encoding="utf-8")

    # Front matter must appear at the beginning of the file.
    match = re.match(
        r"^\s*---\s*\n(.*?)\n---\s*\n(.*)$",
        content,
        re.DOTALL,
    )

    if not match:
        raise ValueError(
            f"Missing or invalid front matter in {file_path}"
        )

    front_matter_text = match.group(1)
    body = match.group(2).strip()

    metadata = yaml.safe_load(front_matter_text) or {}

    return metadata, body


def extract_headings(body: str) -> list[tuple[str, str]]:
    """
    Split a Markdown document into sections based on ## headings.

    Returns:
        [(heading, section_text), ...]
    """

    pattern = r"(?m)^##\s+(.+?)\s*$"

    matches = list(re.finditer(pattern, body))

    sections = []

    for index, match in enumerate(matches):
        heading = match.group(1).strip()

        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)

        text = body[start:end].strip()

        if text:
            sections.append((heading, text))

    return sections


def load_documents(
    knowledge_base_dir: Path = KNOWLEDGE_BASE_DIR,
) -> list[Document]:

    documents = []

    for file_path in sorted(knowledge_base_dir.glob("*.md")):

        metadata, _ = parse_markdown_file(file_path)

        document = Document(
            document_id=metadata.get("document_id", ""),
            title=metadata.get("title", ""),
            status=metadata.get("status", ""),
            effective_date=metadata.get("effective_date"),
            last_reviewed=metadata.get("last_reviewed"),
            audience=metadata.get("audience"),
            policy_authority=metadata.get("policy_authority"),
            filename=file_path.name,
            metadata=metadata,
        )

        documents.append(document)

    return documents


def create_chunks(
    knowledge_base_dir: Path = KNOWLEDGE_BASE_DIR,
) -> list[Chunk]:

    chunks = []

    for file_path in sorted(knowledge_base_dir.glob("*.md")):

        metadata, body = parse_markdown_file(file_path)

        sections = extract_headings(body)

        for heading, text in sections:

            chunk = Chunk(
                text=text,
                filename=file_path.name,
                document_id=metadata.get("document_id", ""),
                title=metadata.get("title", ""),
                heading=heading,
                metadata=metadata,
            )

            chunks.append(chunk)

    return chunks


if __name__ == "__main__":

    documents = load_documents()
    chunks = create_chunks()

    print(f"Loaded {len(documents)} documents")
    print(f"Created {len(chunks)} chunks")

    print("\nDocuments:")

    for document in documents:
        print(
            f"- {document.filename} | "
            f"{document.document_id} | "
            f"{document.status} | "
            f"{document.policy_authority}"
        )

    print("\nFirst 10 chunks:")

    for chunk in chunks[:10]:
        print(
            f"- {chunk.filename} "
            f"→ {chunk.heading}"
        )