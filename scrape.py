import json

from scraping.scrape import getInfo
from scraping.getContext import getContext

import config


def updateContext():
    context = []
    for link in config.links : 
        try : 
            info = getInfo(link)
            context.append(getContext(str(info), ""))
        except Exception as e:
            print(e)

    ### save context to file
    with open("context.json", "w") as f:
        # indent = 4 for pretty printing
        json.dump({"context" : context}, f, indent=4)

#updateContext()