import chromadb
import os 

from helpers import addTxt, addTxtList
import json
import config

chroma_db_path = os.path.join(os.getcwd(), "data/chromadb")
client = chromadb.PersistentClient(path=chroma_db_path)

addDocs = True
addInnerThoughts = False

### Load all .txt files from docs folder and add to vector DB
if addDocs:
   for file in os.listdir("docs"): 
      if file.endswith(".txt"): 
         inputTxt = open(os.path.join("docs", file), "r").read()
         print("Adding " + file)
         print("Length: " + str(len(inputTxt)))
         addTxt(client, "docs", inputTxt, file)

if addInnerThoughts:
   for file in os.listdir("innerThoughts"):
      if file.endswith(".json"):
            print("Adding " + file)
            file = json.load(open(os.path.join("innerThoughts", file), "r"))
            addTxtList(client, "innerThoughts", file["messages"], "innerThougts")
