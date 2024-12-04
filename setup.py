import chromadb
import os 


chroma_db_path = os.path.join(os.getcwd(), "chromadb")
client = chromadb.PersistentClient(path=chroma_db_path)