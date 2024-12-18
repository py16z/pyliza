import chromadb
import os

chroma_db_path = os.path.join(os.getcwd(), "data/chromadb")
chromaClient = chromadb.PersistentClient(path=chroma_db_path)

#DELETE ALL RECORDS
deleteCollection = "pastInteractions"

collection = chromaClient.get_or_create_collection(deleteCollection)
chromaClient.delete_collection(deleteCollection)
collection = chromaClient.get_or_create_collection(deleteCollection)

print(collection.count())


# from helpers import getUserContext

# userCollection = "userContext"

# collection = chromaClient.get_or_create_collection(userCollection)
# userId = "user"


# existingContext = getUserContext(chromaClient, userId)
# print(existingContext)
# description = """

# """

# addDescription = False
# if addDescription :
#     collection.add(documents=[description], ids=[userId])

