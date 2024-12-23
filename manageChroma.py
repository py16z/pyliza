import chromadb
import os

from chromadb.config import Settings
from dotenv import load_dotenv
load_dotenv()

from helpers import getChromaClient

#DELETE ALL RECORDS
deleteCollection = "docs"
chromaClient = getChromaClient()
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

