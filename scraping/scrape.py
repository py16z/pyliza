from firecrawl import FirecrawlApp

import os
from dotenv import load_dotenv
load_dotenv()

FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")

app = FirecrawlApp(api_key=FIRECRAWL_API_KEY)

url = "https://docs.blast.io/tokenomics"

def getInfo(url):
    scrape_result = app.scrape_url(url, params={'formats': ['markdown']})
    return scrape_result
    #print(scrape_result)

