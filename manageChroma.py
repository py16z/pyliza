import chromadb
import os

chroma_db_path = os.path.join(os.getcwd(), "chromadb")
chromaClient = chromadb.PersistentClient(path=chroma_db_path)

# DELETE ALL RECORDS
collection = chromaClient.get_or_create_collection("pastInteractions")
chromaClient.delete_collection("pastInteractions")
collection = chromaClient.get_or_create_collection("pastInteractions")

print(collection.count())
