import chromadb
import os

chroma_db_path = os.path.join(os.getcwd(), "chromadb")
chromaClient = chromadb.PersistentClient(path=chroma_db_path)

# DELETE ALL RECORDS
deleteCollection = "pastInteractions"

collection = chromaClient.get_or_create_collection(deleteCollection)
chromaClient.delete_collection(deleteCollection)
collection = chromaClient.get_or_create_collection(deleteCollection)

print(collection.count())
