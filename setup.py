import chromadb
import os 

from helpers import addTxt
import json
import config

chroma_db_path = os.path.join(os.getcwd(), "chromadb")
client = chromadb.PersistentClient(path=chroma_db_path)


### Load all .txt files from docs folder and add to vector DB
for file in os.listdir("docs"): 
     if file.endswith(".txt"): 
        inputTxt = open(os.path.join("docs", file), "r").read()
        print("Adding " + file)
        print("Length: " + str(len(inputTxt)))
        addTxt(client, "docs", inputTxt, file)


### Add initial thoughts to jsonn
with open("initial_thoughts.json", "w") as f: 
     json.dump({"thought_process": config.initial_thoughts}, f)