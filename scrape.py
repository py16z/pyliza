import json

from scraping.scrape import getInfo
from scraping.getContext import getContext

import config
import random

def updateContext(thoughtProcess="", randomLink=True):
    context = []
    links = config.links
    if randomLink:
        links = random.sample(links, 1)

    
    for link in links : 
        try : 
            info = getInfo(link)
            print("Scraping info from ", link)
            context.append(getContext(str(info), thoughtProcess=thoughtProcess))
        except Exception as e:
            print(e)

    ### save context to file
    with open("context.json", "w") as f:
        # indent = 4 for pretty printing
        json.dump({"context" : context}, f, indent=4)

#updateContext()