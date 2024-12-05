import chromadb
import os

chroma_db_path = os.path.join(os.getcwd(), "chromadb")
chromaClient = chromadb.PersistentClient(path=chroma_db_path)

# DELETE ALL RECORDS
collection = chromaClient.get_or_create_collection("tweet_responses")

chromaClient.delete_collection("tweet_responses")

collection = chromaClient.get_or_create_collection("tweet_responses")

print(collection.count())
