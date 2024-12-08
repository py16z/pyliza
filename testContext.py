from helpers import prepareContext, updatePersona
from tweetLogic import getCurrentThoughts
import chromadb
import os
client = chromadb.PersistentClient(path=os.path.join(os.getcwd(), "chromadb"))

message = "Hello, how are you?"

context = prepareContext(message, client, thoughtProcess=getCurrentThoughts())
print(context)

updatePersona(client,additionalContext=context)