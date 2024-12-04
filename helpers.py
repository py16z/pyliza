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


if config.use_anthropic:
        client = Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY"),
    )
else : 
     if config.base_url == "" : 
          client = OpenAI(
               api_key=os.getenv("OPENAI_API_KEY"),
          )
     else : 
          client = OpenAI(
               api_key=os.getenv("OPENROUTER_API_KEY"),
               base_url=config.base_url
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
        model=config.claudeModel,
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

     if config.use_anthropic: 
          response = getAnthropicResponse(prompt, agentPrompt, config.claudeModel, temperature, top_p)
     else: 
          response = getOpenAIResponse(prompt, agentPrompt, config.model, temperature, top_p)

     #print("Response Generated: ", response)
     return response


def getResponseCustomAgentPrompt(prompt, agentPrompt, additionalContext="", temperature=0.7, top_p=0.6):
     print("Generating Response.........")
     if additionalContext != "": 
          agentPrompt += f"\n\n Here is some additional context: {additionalContext}"

     if config.use_anthropic: 
          response = getAnthropicResponse(prompt, agentPrompt, config.claudeModel, temperature, top_p)
     else: 
          response = getOpenAIResponse(prompt, agentPrompt, config.model, temperature, top_p)
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


def log_message(chromaClient, message, response, user="user") : 
    # Here we want to log message into Chroma 
    #input = message + " \n" + "response from " + user + " : " + response
    input = response

    try : 
        collection = chromaClient.get_collection("pastInteractions")
        n = len(collection.get()["documents"])
        collection.add(documents=[input], metadatas=[{"user": user}], ids=[str(n + 1) + "_" + str(int(time.time()))])
    except Exception as e:
        print(e)


def fetch_history(chromaClient, maxLength=2500):
    try:
          collection = chromaClient.get_collection("pastInteractions")
          # Get all documents from the collection
          info = collection.get()
          documents = info["documents"]
          n = len(documents)
          if (n == 0):
               return ""
          # Concatenate all documents into a single string
          chat_history_string = ""

          for i in range(n) :
               doc = documents[n - i]

               while len(chat_history_string) + len(doc) < maxLength:
                    chat_history_string = doc + "\n" + chat_history_string


          histInstr = "\nUse this history to help inform your response. "
          chat_history_string = "History of previous interactions " + histInstr + " : \n" + chat_history_string
               
          print("HISTORY FETCHED......")
               
          return chat_history_string
    except:
        return ""
