
import uuid
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
import logfire
from app.config import settings
from app.ingestion.loaders.documents_loader import load_documents
from app.ingestion.chunking.splitter import chunk_text
from app.services.retrieval.embeddings import embed_batch, BATCH_SIZE
from qdrant_client.http import models

# Initialize clients
logfire.configure()
qdrant_client = QdrantClient(url=settings.QDRANT_ENDPOINT, api_key=settings.QDRANT_API_KEY, timeout=300.0)


# Fixed vector size for "text-embedding-3-small" default output (no custom "dimensions" param set via Portkey)
def init_qdrant_collection(collection_name: str, vector_size: int = 1536):
    """Create collection and payload index in Qdrant if it doesn't exist."""
    if not qdrant_client.collection_exists(collection_name):
        logfire.info(f"Creating Qdrant collection: {collection_name}")
        qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )

    # Only create the payload index once (skip if it already exists, so re-runs don't error)
    try:
        existing = qdrant_client.get_collection(collection_name)
        has_index = "category" in (existing.payload_schema or {})
    except Exception:
        has_index = False

    if not has_index:
        qdrant_client.create_payload_index(
            collection_name=collection_name,
            field_name="category",
            field_schema=models.PayloadSchemaType.KEYWORD,
        )
        logfire.info(f"Payload index on 'category' created for {collection_name}")
    else:
        logfire.info(f"Payload index on 'category' already exists for {collection_name}")


def delete_category_points(collection_name: str, category: str):
    """Delete all existing points for a category before re-ingesting.

    This prevents stale/orphaned points from staying in Qdrant when a file
    is removed or shrinks (fewer chunks than before).
    """
    logfire.info(f"Clearing old points for category '{category}' before re-ingest")
    qdrant_client.delete(
        collection_name=collection_name,
        points_selector=Filter(
            must=[FieldCondition(key="category", match=MatchValue(value=category))]
        ),
        wait=True,
    )


def process_and_ingest_all(base_data_dir: str = "Data"):
    """Main pipeline for processing all subfolders into a single Qdrant collection. Instead of creating separate collections for each category, all data is stored in one collection. Each point includes a category field in its payload, which is used for filtering during retrieval.
    """
    base_path = Path(base_data_dir)
    collection_name = settings.QDRANT_COLLECTION_NAME

    with logfire.span("Starting Total Ingestion Pipeline"):

        # 1. Setup Qdrant Collection 
        init_qdrant_collection(collection_name)

        # Iterate over the mapping to see which folders we need to process
        for folder_key, ext in settings.DATA_FOLDERS.items():

            # Find the path dynamically (e.g., Data/noisy_data or Data/true_data/core_docs)
            target_folder = None
            for p in base_path.rglob(folder_key):
                if p.is_dir():
                    target_folder = p
                    break

            if not target_folder:
                logfire.warning(f"Folder matching '{folder_key}' not found in {base_data_dir}. Skipping.")
                continue

            with logfire.span(f"Processing Category: {folder_key}", collection=collection_name):

                # 2. Load documents (guarded so one bad category doesn't kill the whole run)
                try:
                    raw_docs = load_documents(str(target_folder), extension=ext)
                except Exception as e:
                    logfire.error(f"Failed to load documents for '{folder_key}': {e}")
                    continue

                if not raw_docs:
                    logfire.warning(f"No documents found for category '{folder_key}'. Skipping.")
                    continue

                logfire.info(f"Loaded {len(raw_docs)} documents for category '{folder_key}'")

                # 3. Loop through docs, chunk them 
                pending = []  # list of (unique_id, chunk_text, payload)

                for doc in raw_docs:
                    try:
                        chunks = chunk_text(doc["content"], chunk_size=800)
                    except Exception as e:
                        logfire.error(f"Failed to chunk document '{doc.get('file_name')}': {e}")
                        continue

                    for chunk_index, chunk in enumerate(chunks):
                        payload = {
                            "source": doc["source"],
                            "file_name": doc["file_name"],
                            "chunk_index": chunk_index,
                            "content": chunk,
                            "category": folder_key,
                        }

                        # Generate a unique ID using the full source path instead of just the file name.
                        # This prevents ID collisions when different subfolders contain files with the same name.
                        unique_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{doc['source']}_{chunk_index}"))

                        pending.append((unique_id, chunk, payload))

                if not pending:
                    logfire.warning(f"No chunks produced for category '{folder_key}'. Skipping.")
                    continue

                logfire.info(f"Created {len(pending)} chunks for category '{folder_key}'")

                # 4. Clear old points for this category first, so deleted/shrunk files
                # don't leave stale points behind.
                try:
                    delete_category_points(collection_name, folder_key)
                except Exception as e:
                    logfire.error(f"Failed to clear old points for '{folder_key}': {e}")
                    # Continue anyway - worst case some old points remain, but we still
                    # want fresh data to go in.

                # 5. Embed in batches and upload immediately (avoids holding everything in RAM)
                UPLOAD_BATCH_SIZE = 100
                total_uploaded = 0
                total_batches = (len(pending) + BATCH_SIZE - 1) // BATCH_SIZE

                for batch_num, i in enumerate(range(0, len(pending), BATCH_SIZE), start=1):
                    batch = pending[i:i + BATCH_SIZE]
                    texts = [item[1] for item in batch]

                    try:
                        vectors = embed_batch(texts)
                    except Exception as e:
                        logfire.error(
                            f"Embedding failed for batch {batch_num}/{total_batches} "
                            f"in category '{folder_key}': {e}"
                        )
                        continue  # skip this batch, keep going with the rest

                    points = [
                        PointStruct(id=unique_id, vector=vector, payload=payload)
                        for (unique_id, _, payload), vector in zip(batch, vectors)
                    ]

                    # Upload this batch straight away in sub-batches of UPLOAD_BATCH_SIZE
                    for j in range(0, len(points), UPLOAD_BATCH_SIZE):
                        upload_chunk = points[j:j + UPLOAD_BATCH_SIZE]
                        try:
                            qdrant_client.upsert(
                                collection_name=collection_name,
                                points=upload_chunk,
                                wait=True,
                            )
                            total_uploaded += len(upload_chunk)
                            logfire.info(
                                f"Uploaded {len(upload_chunk)} points "
                                f"(embed batch {batch_num}/{total_batches}) for '{folder_key}'"
                            )
                        except Exception as e:
                            logfire.error(
                                f"Upload failed for a batch in category '{folder_key}': {e}"
                            )

                logfire.info(
                    f"Finished category '{folder_key}': {total_uploaded}/{len(pending)} points ingested"
                )


if __name__ == "__main__":
    # running the full pipeline
    process_and_ingest_all()