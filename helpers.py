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
    thoughtProcess = json.load(open("initial_thoughts.json"))
    thoughts = thoughtProcess["thought_process"]


    prompt = f"""
    You are {config.name}, 
    {config.description}

    You have the following goals: {config.goals}.
    You have the following personality: {config.personality}.
    You have the following way of responding / speaking : {config.speech}

    Your current thought process is : {thoughts}

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

     context = json.load(open("context.json"))

     for item in context["context"] : 
          additionalContext += item + "\n"

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


def log_message(chromaClient, message, user="user", collectionName="pastInteractions") : 
    # Here we want to log message into Chroma 
    #input = message + " \n" + "response from " + user + " : " + response

    try : 
        collection = chromaClient.get_or_create_collection(collectionName)
        n = len(collection.get()["documents"])
        collection.add(documents=[message], metadatas=[{"user": user}], ids=[str(n + 1) + "_" + str(int(time.time()))])
    except Exception as e:
        print(e)


def fetch_history(chromaClient, maxLength=2500, collectionName="pastInteractions"):
    try:
          collection = chromaClient.get_collection(collectionName)
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


def getTweetResponsePrompt(tweetContent, sender, searchContext):
     prompt = f"""
     You are responding to a tweet from {sender}
     {searchContext}
     The tweet content is : {tweetContent}

     When tweeting consider the below tweet style instructions 
     <tweetStyle>
          never use hashtags or emojis
          response should be short, punchy, and to the point
          don't say ah yes or oh or anything
          don't ask rhetorical questions, its lame
          occassionally you'll ask provocative / controversial questions
          use lowercase most of the time
          you like to go deep down the rabbithole....
     </tweetStyle>

     Post your response tweet below 
     Stay true to your personality and goals.

     """
     return prompt


def prepareContext(message, chromaClient,includeHistory=True, includeDocs=True, collectionName="docs", includeUser=False, userId = "user", includeScrapedContext=True):
     context = ""
     if includeHistory: 
          context += fetch_history(chromaClient)
     if includeDocs: 
          try : 
               docContext = fetch_context(chromaClient, collectionName, message)
               if docContext != "": 
                    context += f"\n<context> The below is information from {collectionName} "
                    context += docContext
          except Exception as e:
               print(e)
     if includeUser: 
          userContext = ""
          #TO DO - have some mechanics to store information about users 
          context += "You are responding to {user}"
     if includeScrapedContext: 
          try : 
               scrapedContext = json.load(open("context.json"))
               context += "\n<context> The below is information scraped from the web  "
               for item in scrapedContext["context"] : 
                    context += item + "\n"

               context += "</context>"
          except Exception as e:
               print(e)

     return context


def reflectThoughts(additionalContext = ""):
     thoughtProcess = json.load(open("initial_thoughts.json"))
     thoughts = thoughtProcess["thought_process"]

     thoughtPrompt = f"""
     This is your thought process : {thoughts}
     take into account the information provided along with the history of previous interactions

     Based on this generate an updated thought process

     """

     response = getResponse(thoughtPrompt, additionalContext=additionalContext)

     thoughtProcess["thought_process"] = response
     json.dump(thoughtProcess, open("initial_thoughts.json", "w"))
     print("Updated Thought Process: ", response)
     

def getUserContext(chromaClient, userId, collectionName="userContext"):

     try : 
          collection = chromaClient.get_collection(collectionName)
          results = collection.get(ids=[userId])
          docs = results['documents'][0]
          return docs
     except Exception as e:
          print(e)
          return ""


def updateUserContext(chromaClient, userId, interaction, userName, collectionName="userContext", additionalContext=""):

     existingContext = getUserContext(chromaClient, userId, collectionName)
     print("EXISTING CONTEXT: ", existingContext)
     if existingContext != "":
          existingContext = "This is your existing context on the user " + existingContext

     contextPrompt = f"""
     {existingContext}

     You had the following interaction with {userName} 
     {interaction}

     Update your context on the user based on this interaction 

     The context should be formatted as follows 

     <userContext>
     This should include the following information 
     - Your attitude towards {userName}
     - Your understanding of {userName}
     - What do you think of {userName}
     - Do they hold any importance / strong opinions that you agree / disagree with
     - Any other information you have about {userName}
     </userContext>

     """

     response = getResponse(contextPrompt, additionalContext=additionalContext)

     collection = chromaClient.get_or_create_collection(collectionName)
     collection.add(documents=[response], ids=[userId])
     print("UPDATED CONTEXT: ", response)

     


