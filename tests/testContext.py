from helpers import prepareContext
import chromadb
import os
client = chromadb.PersistentClient(path=os.path.join(os.getcwd(), "chromadb"))

message = "Hello, how are you?"

context = prepareContext(message, client)
print(context)