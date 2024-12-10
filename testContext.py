from helpers import prepareContext, updatePersona, reflectThoughts, getResponse
from tweetLogic import getCurrentThoughts
import chromadb
import os
client = chromadb.PersistentClient(path=os.path.join(os.getcwd(), "chromadb"))

import config

message = "Hello, how are you?"

context = prepareContext(message, client, thoughtProcess=getCurrentThoughts())
#print(context)

instructions = ""

out = getResponse(config.getPostPrompt(instructions=instructions), additionalContext=context)

print(out)

# thoughts = reflectThoughts(context)
# print(thoughts)

# updatePersona(client,additionalContext=context)

