from openai import OpenAI
from dotenv import load_dotenv
import os

import chromadb

load_dotenv()

API_KEY = os.getenv("PERPLEXITY_API_KEY")



def search(message="", context=""):

    #print(query)
    query = """
    Provide me with the latest news on the crypto market
    I'm particulary interested in the following topics:
    - Most interesting news or announcements related to DeFi in the last 24 hours ? (primarily interested in the Ethereum ecosystem & Layer 2 ecosystem)
    - Most interesting news related to specific projects / companies ? (primarily interested in the Ethereum ecosystem & Layer 2 ecosystem)
    - Any news related to Ethereum technology / development ? (for example deep dives into the Ethereum protocol, EIPs, Based Sequencing, Gas limits etc)
    - Any news related to upcoming chains (i.e. MegaETH, RISE Chain, Monad, Sonic, etc)
    - Any news related to crypto regulation ? (primarily interested in the US & EU / SEC & FED)


    """

    messages = [
        {
            "role": "system",
            "content": (
                """You are an assistant who's goal is to provide up to date information on a given topic. You are also able to provide context on a given topic if requested. 
                The information will primarily be related to the cryptocurrency market & technology 
                The information should be detailed & include relevant technical information
                The information should be focussed on news & events in the last 24 hours - last 7 days 
                You will often be asked multiple questions at once - when doing this list each answer seperately i.e. as a list of answers
                Responses should include specific statistics / data along with relevant quotes (i.e. if a prominent figure is mentioned in the context provide this or if a specific event / companyis mentioned provide this)
                Also make sure to include relevant up to date data (for example if asked about the crypto market or a current asset provide data on changes over last 24 hours / 7 days along with market cap / volume / price changes)
                """
            ),
        },
        {   
            "role": "user",
            "content": (
                query
            ),
        },
    ]

    client = OpenAI(api_key=API_KEY, base_url="https://api.perplexity.ai")

    # chat completion without streaming
    response = client.chat.completions.create(
        model="llama-3.1-sonar-large-128k-online",
        messages=messages,
    )

    out = response.choices[0].message.content

    return out


news = search()
print(news)