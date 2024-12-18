from openai import OpenAI
from dotenv import load_dotenv
import os

from helpers import getResponse, getResponseCustomAgentPrompt, prepareContext

import chromadb

load_dotenv()
chroma_db_path = os.path.join(os.getcwd(), "data/chromadb")


API_KEY = os.getenv("PERPLEXITY_API_KEY")

def search(chromaClient, message="", context=""):
    agentPrompt = """
    You are an assistant who's goal is to reflect on previous interactions along with additional context provided i.e. an agents thought process 
    Based on this you will produce a list of questions 
    This list of questions will be passed to an AI agent search engine who will provide results with details information 

    Keep your questions specific, provide as much detail as possible in addition to asking for what information you need 

    I.e. an example question could be 
    "What is the current price of Bitcoin?" 
    This is too vague, a better question would be 
    "What is the current price of Bitcoin in USD & how has it changed over the last 24 hours - what are the key drivers of this change" 
    This is more specific & will provide a more relevant answer 

"""
    
    
    getQueryInstructions = """
    Reflect on the context provided in addition to historical information 
    (note are there any recurring themes coming up in the past interactions / or are there specific pieces of information that will help you better clarrify your thoughts)

    Based on this is there any additional information that could help you better respond in the future 

    If so provide a list of questions that could help you better respond in the future 

    
    """

    if message != "":
        getQueryInstructions = """
        ### Instructions

        Note You have been given the following instruction - based on this is there any additional information that could you better complete the following task 
        ### Task
        {message}
        List out any questions that could help you better complete the task
        """
        




    query = getResponseCustomAgentPrompt(prompt = getQueryInstructions, agentPrompt = agentPrompt, additionalContext=  context)

    

    #print(query)

    messages = [
        {
            "role": "system",
            "content": (
                """You are an assistant who's goal is to provide up to date information on a given topic. You are also able to provide context on a given topic if requested. 
                The information will primarily be related to the cryptocurrency market & technology 
                The information should be detailed & include relevant technical information
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

    return query, out