from typing import List
import re

import logfire


def split_large_paragraph(paragraph: str, chunk_size: int) -> List[str]:
    """
    Split a large paragraph into smaller chunks.

    The paragraph is first divided into sentences. If a sentence is still
    longer than the chunk size, it is split by characters.
    """
    chunks: List[str] = []
    current = ""

    sentences = re.split(r"(?<=[.!?])\s+", paragraph)

    for sentence in sentences:

        # Add the sentence if it fits
        if len(current) + len(sentence) + 1 <= chunk_size:
            current = f"{current} {sentence}".strip()

        else:
            # Save the current chunk
            if current:
                chunks.append(current)

            # Handle very long sentences
            if len(sentence) > chunk_size:
                for i in range(0, len(sentence), chunk_size):
                    chunks.append(sentence[i:i + chunk_size].strip())
                current = ""
            else:
                current = sentence

    if current:
        chunks.append(current)

    return chunks


def chunk_text(text: str, chunk_size: int = 800) -> List[str]:
    """
    Split text into chunks using Structural Chunking.

    Small paragraphs are merged together until the chunk size is reached.
    Large paragraphs are split into smaller pieces based on sentences.

    Args:
        text (str): Input document.
        chunk_size (int, optional): Maximum chunk size. Defaults to 800.

    Returns:
        List[str]: List of text chunks.
    """

    with logfire.span("Text Chunking", text_length=len(text)):

        if not text.strip():
            return []

        # Normalize line endings
        text = text.replace("\r\n", "\n").strip()

        # Split into paragraphs
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        chunks: List[str] = []
        current_chunk = ""

        for paragraph in paragraphs:

            # Merge paragraph if it fits
            if len(current_chunk) + len(paragraph) + 2 <= chunk_size:
                current_chunk = (
                    f"{current_chunk}\n\n{paragraph}".strip()
                    if current_chunk
                    else paragraph
                )
                continue

            # Save the current chunk
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""

            # Split oversized paragraphs
            if len(paragraph) > chunk_size:
                chunks.extend(split_large_paragraph(paragraph, chunk_size))
            else:
                current_chunk = paragraph

        # Save the final chunk
        if current_chunk:
            chunks.append(current_chunk)

        logfire.info(
            "Chunking completed",
            total_chunks=len(chunks),
            average_chunk_size=(
                sum(len(chunk) for chunk in chunks) // len(chunks)
                if chunks else 0
            ),
        )

        return chunks