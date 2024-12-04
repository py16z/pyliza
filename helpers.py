from openai import OpenAI
from dotenv import load_dotenv
from anthropic import Anthropic
from together import Together
from typing import List

import time

import config

import os
import json

import random 
load_dotenv()

import json

claudeModel = "claude-3-5-sonnet-20241022"
model = "meta-llama/llama-3.1-70b-instruct"
use_anthropic = True
base_url = "https://api.together.xyz/v1"


if use_anthropic:
        client = Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY"),
    )
else : 
     if base_url == "" : 
          client = OpenAI(
               api_key=os.getenv("OPENAI_API_KEY"),
          )
     else : 
          client = OpenAI(
               api_key=os.getenv("OPENROUTER_API_KEY"),
               base_url=base_url
          )

if config.useTogetherEmbeddings: 
     together = Together(api_key=os.getenv("TOGETHER_API_KEY"))
else :
     embeddingClient = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def getAgentPrompt(): 

    prompt = f"""
    You are {config.name}, 
    {config.description}

    You have the following goals: {config.goals}.
    You have the following personality: {config.personality}.
    You have the following way of responding / speaking : {config.speech}
    """
    return prompt



def getOpenAIResponse(prompt, agentPrompt, model, temperature=0.7, top_p=0.6):


    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": agentPrompt},
            {"role": "user", "content": prompt}
        ],
    )
    return response.choices[0].message.content.strip()

def getAnthropicResponse(prompt, agentPrompt, model, temperature=0.7, top_p=0.6):
    response = client.messages.create(
        max_tokens=8192,
        system = prompt,
        model=claudeModel,
        messages=[
            {"role": "user", "content": agentPrompt},
            {"role": "user", "content": prompt}],
    )
    return response.content[0].text



def getResponse(prompt, additionalContext="", temperature=0.7, top_p=0.6):
     agentPrompt = getAgentPrompt()
     print("Generating Response.........")
     if additionalContext != "": 
          agentPrompt += f"\n\n Here is some additional context: {additionalContext}"

     if use_anthropic: 
          response = getAnthropicResponse(prompt, agentPrompt, model, temperature, top_p)
     else: 
          response = getOpenAIResponse(prompt, agentPrompt, model, temperature, top_p)

     #print("Response Generated: ", response)
     return response


def getResponseCustomAgentPrompt(prompt, agentPrompt, additionalContext="", temperature=0.7, top_p=0.6):
     print("Generating Response.........")
     if additionalContext != "": 
          agentPrompt += f"\n\n Here is some additional context: {additionalContext}"

     if use_anthropic: 
          response = getAnthropicResponse(prompt, agentPrompt, model, temperature, top_p)
     else: 
          response = getOpenAIResponse(prompt, agentPrompt, model, temperature, top_p)

     #print("Response Generated: ", response)
     return response


def get_embeddings(texts: List[str], model: str) -> List[List[float]]:
    texts = [text.replace("\n", " ") for text in texts]
    if config.useTogetherEmbeddings: 
          outputs = together.embeddings.create(model=model, input=texts)
    else : 
          outputs = embeddingClient.embeddings.create(model=model, input=texts)
    return [outputs.data[i].embedding for i in range(len(texts))]


def addTxt(chromaClient, collectionName, info, fileName): 
     maxLen = config.maxLen
     overlap = config.overlap

     embeddings = []
     inputTxts = []
     finalTxts = []

     while (len(info) > maxLen):
          inputTxts.append(info[0:maxLen])
          info = info[overlap:]

     for i in range(len(inputTxts)):
          try : 
               #print(txts[i]) 
               newEmbeddings = get_embeddings([inputTxts[i]], model='togethercomputer/m2-bert-80M-8k-retrieval')
               # Note some txts may fail to embed i.e. empty strings 
               #ids.append(fileName + str(i))
               embeddings = embeddings + newEmbeddings
               finalTxts.append(inputTxts[i])
          except : 
               time.sleep(1)
               print("API Failed")
               print(inputTxts[i])
               print("Retrying")

     ids = [fileName + str(i) for i in range(len(finalTxts))]
     try : 
          collection = chromaClient.get_collection(collectionName)
     except :
          collection = chromaClient.create_collection(collectionName)

     collection.add(
          embeddings=embeddings,
          documents=finalTxts,
          ids = ids
     )
     print("Added Data : " + collectionName)


def fetch_context(chromaClient, collection, message, n=3):
    ### Here we want to fetch any other relevant context from vector DB 
    try :
        collection = chromaClient.get_collection(collection)
        embedding = get_embeddings([message], model=config.embeddingModel)

        results = collection.query(query_embeddings=embedding, n_results=2)
        docs = results['documents'][0]
        
        context = ""
        for doc in docs: 
            context += doc + "\n"
            #print(doc)
        return context
    except Exception as e:
        print(e)
        return ""
