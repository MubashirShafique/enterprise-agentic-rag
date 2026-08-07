from pathlib import Path
import logfire

logfire.configure()


def load_documents(folder_path: str, extension: str = ".md") -> list[dict]:
    """
    Recursively loads non-empty files with the specified extension from a folder.

    Args:
        folder_path: Path to the root directory to search.
        extension: File extension to match (e.g., '.md'). Defaults to ".md".

    Returns:
        List of dicts, each containing 'source', 'file_name', and 'content'.

    Raises:
        FileNotFoundError: If the folder_path does not exist.
    """

    folder = Path(folder_path)
    documents = []

    with logfire.span(" Document Loading", folder_path=folder_path, extension=extension):

        # Validate that the folder actually exists before scanning it
        if not folder.exists():
            logfire.error(f" Folder not found: {folder_path}")
            raise FileNotFoundError(f"Folder not found: {folder_path}")

        # Recursively search for all matching files, including subfolders
        for file_path in folder.rglob(f"*{extension}"):
            with logfire.span(" File Parsing", file_path=str(file_path)):
                try:
                    text = file_path.read_text(encoding="utf-8")

                    # Skip files that are empty or contain only whitespace
                    if not text.strip():
                        logfire.warning(f" Skipping empty file: {file_path}")
                        continue

                    # Store the file content along with useful metadata
                    documents.append({
                        "source": str(file_path),
                        "file_name": file_path.name,
                        "content": text,
                    })

                    logfire.info(f" Successfully parsed {len(text)} characters from {file_path.name}")

                except UnicodeDecodeError:
                    logfire.error(f" Encoding error, skipping file: {file_path}")
                except Exception as e:
                    logfire.error(f" Error reading file {file_path}: {e}")

        logfire.info(f" Total {len(documents)} documents loaded from {folder_path}")

    return documents


