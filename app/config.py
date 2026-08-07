import os
from dotenv import load_dotenv

load_dotenv()

class Config:  
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
    QDRANT_ENDPOINT = os.getenv('QDRANT_CLUSTER_ENDPOINT')


    QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "docs_collection")

    # Har folder ka naam -> uski file extension (category label folder_key hi rahega)
    DATA_FOLDERS = {
        "noisy_data": ".txt",
        "core_docs": ".md",
        "advanced_docs": ".md",
        "model_docs": ".md"
    }
    
    PORTKEY_EMBED_CONFIG_ID=os.getenv("PORTKEY_EMBED_CONFIG_ID")
    PORTKEY_CHAT_CONFIG_ID=os.getenv("PORTKEY_CHAT_CONFIG_ID")
    PORTKEY_API_KEY=os.getenv("PORTKEY_API_KEY")
    
    
    CHAT_MODEL=os.getenv("CHAT_MODEL","gpt-4o-mini")
    EMBEDDING_MODEL=os.getenv("EMBEDDING_MODEL","text-embedding-3-small")

settings = Config()