from pathlib import Path
from typing import List, Tuple
import yaml

from app.schemas.documents import Document, DocumentMetadata


def parse_front_matter(text: str) -> Tuple[dict, str]:
    if not text.startswith("---"):
        raise ValueError("Document is missing front matter.")

    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError("Invalid front matter format.")

    metadata_text = parts[1]
    content = parts[2].strip()
    metadata = yaml.safe_load(metadata_text)
    return metadata, content


def load_markdown_documents(data_dir: str) -> List[Document]:
    documents: List[Document] = []
    base_path = Path(data_dir)

    for file_path in base_path.rglob("*.md"):
        raw_text = file_path.read_text(encoding="utf-8")
        metadata_dict, content = parse_front_matter(raw_text)

        metadata = DocumentMetadata(**metadata_dict)
        document = Document(metadata=metadata, content=content)
        documents.append(document)

    return documents
