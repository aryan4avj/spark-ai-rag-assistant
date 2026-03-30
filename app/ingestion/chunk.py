import re
from typing import List, Tuple

from app.schemas.documents import Chunk, ChunkMetadata, Document


def split_markdown_sections(content: str) -> List[Tuple[str, str]]:
    """
    Split markdown content into sections based on headings.
    Returns a list of tuples: (section_title, section_content)
    """
    lines = content.splitlines()
    sections: List[Tuple[str, List[str]]] = []
    current_section = "Introduction"
    current_lines: List[str] = []

    heading_pattern = re.compile(r"^(#{1,3})\s+(.*)$")

    for line in lines:
        match = heading_pattern.match(line.strip())
        if match:
            if current_lines:
                sections.append((current_section, current_lines))
            current_section = match.group(2).strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        sections.append((current_section, current_lines))

    return [
        (section_title, "\n".join(section_lines).strip())
        for section_title, section_lines in sections
        if "\n".join(section_lines).strip()
    ]


def split_text_with_overlap(
    text: str,
    max_chars: int = 500,
    overlap: int = 100,
) -> List[str]:
    """
    Split long text into smaller overlapping chunks.
    """
    if len(text) <= max_chars:
        return [text]

    chunks: List[str] = []
    start = 0

    while start < len(text):
        end = start + max_chars
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = max(end - overlap, start + 1)

    return chunks


def chunk_document(
    document: Document,
    max_chars: int = 500,
    overlap: int = 100,
) -> List[Chunk]:
    """
    Convert a Document into retrieval-ready chunks.
    """
    sections = split_markdown_sections(document.content)
    chunks: List[Chunk] = []
    chunk_index = 0

    for section_title, section_content in sections:
        subchunks = split_text_with_overlap(
            section_content,
            max_chars=max_chars,
            overlap=overlap,
        )

        for subchunk in subchunks:
            chunk_metadata = ChunkMetadata(
                chunk_id=f"{document.metadata.doc_id}-chunk-{chunk_index}",
                doc_id=document.metadata.doc_id,
                title=document.metadata.title,
                source=document.metadata.source,
                source_type=document.metadata.source_type,
                space=document.metadata.space,
                section=section_title,
                chunk_index=chunk_index,
                tags=document.metadata.tags,
                url=document.metadata.url,
            )
            chunks.append(
                Chunk(
                    metadata=chunk_metadata,
                    content=subchunk,
                )
            )
            chunk_index += 1

    return chunks


def chunk_documents(
    documents: List[Document],
    max_chars: int = 500,
    overlap: int = 100,
) -> List[Chunk]:
    """
    Chunk multiple documents into a flat list of chunks.
    """
    all_chunks: List[Chunk] = []

    for document in documents:
        all_chunks.extend(
            chunk_document(
                document=document,
                max_chars=max_chars,
                overlap=overlap,
            )
        )

    return all_chunks