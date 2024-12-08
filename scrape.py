import json

from scraping.scrape import getInfo
from scraping.getContext import getContext

from helpers import addTxt

import config
import random

def updateContext(ChromaClient, links=config.links, thoughtProcess="", randomLink=True, addText=True):
    context = []

    if randomLink:
        links = random.sample(links, 1)

    try : 
        existingContext = open("context.json", "r").read()
        additionalContext = json.loads(existingContext)["context"][0]
    except : 
        additionalContext = ""

    
    for link in links : 
        try : 
            info = getInfo(link)
            print("Scraping info from ", link)
            newContext = getContext(str(info), thoughtProcess=thoughtProcess, additionalContext=additionalContext)
            context.append(newContext)
            try : 
                addTxt(ChromaClient, collectionName="context", info=newContext, fileName="context")
            except Exception as e:
                print(e)
        except Exception as e:
            print(e)

    ### save context to file
    with open("context.json", "w") as f:
        # indent = 4 for pretty printing
        json.dump({"context" : context}, f, indent=4)

