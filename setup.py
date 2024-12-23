import chromadb
import os 

from helpers import addTxt, addTxtList, getChromaClient
import json
import config


addDocs = True
addInnerThoughts = True

### Load all .txt files from docs folder and add to vector DB
if addDocs:
   for file in os.listdir("docs"): 
      if file.endswith(".txt"): 
         inputTxt = open(os.path.join("docs", file), "r").read()
         print("Adding " + file)
         print("Length: " + str(len(inputTxt)))
         addTxt(getChromaClient(), "docs", inputTxt, file)

if addInnerThoughts:
   for file in os.listdir("innerThoughts"):
      if file.endswith(".json"):
            print("Adding " + file)
            file = json.load(open(os.path.join("innerThoughts", file), "r"))
            addTxtList(getChromaClient(), "innerThoughts", file["messages"], "innerThougts")