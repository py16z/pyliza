from openai import OpenAI
from dotenv import load_dotenv
from anthropic import Anthropic
from together import Together
from typing import List

from chromadb.config import Settings
import chromadb
 

import time

import config

import os
import json

import random 
load_dotenv()

import json

import logging

import re  # Add this import at the top

# Set the logging level for the specific logger to suppress warnings
logging.getLogger('chromadb.segment.impl.vector.local_persistent_hnsw').setLevel(logging.ERROR)


def getChromaClient():
    if config.useLocalChroma : 
          chroma_db_path = os.path.join(os.getcwd(), "data/chromadb")
          chromaClient = chromadb.PersistentClient(path=chroma_db_path)
          return chromaClient
    else : 
          user = os.getenv("CHROMA_USER")
          password = os.getenv("CHROMA_PASSWORD")

          chromaClient = chromadb.HttpClient(
               host=os.getenv("CHROMA_HOST"),
               port=8000,
               settings=Settings(
               chroma_client_auth_provider="chromadb.auth.basic_authn.BasicAuthClientProvider",
               chroma_client_auth_credentials=f"{user}:{password}"
          )
          )
          chromaClient.set_tenant("default_tenant")
          chromaClient.set_database("default_database")
          return chromaClient


anthropicClient = Anthropic(
     api_key=os.getenv("ANTHROPIC_API_KEY"),
)

if config.base_url == "" : 
     client = OpenAI(
          api_key=os.getenv("OPENAI_API_KEY"),
     )
else : 
     if config.base_url == "https://openrouter.ai/api/v1" : 
          client = OpenAI(
               api_key=os.getenv("OPENROUTER_API_KEY"),
               base_url=config.base_url
          )
          print("Using OpenRouter")
     if config.base_url == "https://api.together.xyz/v1" : 
          client = OpenAI(
               api_key=os.getenv("TOGETHER_API_KEY"),
               base_url=config.base_url
          )
          print("Using Together")
if config.useTogetherEmbeddings: 
     together = Together(api_key=os.getenv("TOGETHER_API_KEY"))
else :
     embeddingClient = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def loadPersona():
     persona = json.load(open("data/persona.json"))
     description = persona["persona"]["description"]
     lore = persona["persona"]["lore"]
     goals = persona["persona"]["goals"]
     personality = persona["persona"]["personality"]
     speech = persona["persona"]["speech"]
     
     personaPrompt = f"""
     {config.fixedPersona}
     

     This is a high level description of you 
     ### Description
     {description}
     ### End Description

     This is some lore / background information about you 
     ### Lore
     {lore}
     ### End Lore
     
     This is a list of your goals & objectives 
     ### Goals
     {goals}
     ### End Goals
     
     This is a description of your personality 
     ### Personality
     {personality}
     ### End Personality

     {config.getExampleMessages()}

     This is a description of how you speak / respond (whenever responding make sure to use this style as a guide) 
     ### Speech
     {speech}
     ### End Speech
     

     """
     return personaPrompt


def getAgentPrompt(includeThoughts=True, includeModifiers=True, loadFromJson=False): 
     thoughtProcess = json.load(open("data/initial_thoughts.json"))
     thoughts = ""
     if includeThoughts: 
          thoughts = thoughtProcess["thought_process"]

     promptModifier = ""
     if includeModifiers: 
          try : 
               mods = config.promptModifiers
               promptModifier = random.choice(mods)
          except : 
               promptModifier = ""

     personaPrompt = f"""
     {config.fixedPersona}
     {config.description}
     
     ### Goals
     You have the following high level goals: {config.goals}.
     ### End Goals

     ### Personality
     You have the following personality: {config.personality}.
     ### End Personality

     
     {config.getExampleMessages()}

     ### Speech
     You have the following way of responding / speaking : {config.speech}
     ### End Speech

     """     
     if loadFromJson: 
          try : 
               personaPrompt = loadPersona()
          except : 
               print("using config persona....")

     prompt = f"""
     ### Persona
     You are {config.name} 

     You're Twitter handle is @{config.userName}

     {personaPrompt}

     This is your current thought process 
     {thoughts}
     {promptModifier}

     ### End Persona
     """
     return prompt

def getOpenAIResponse(prompt, agentPrompt, model, temperature=0.8, top_p=0.9, max_tokens=2000):

     if config.base_url == "https://openrouter.ai/api/v1" : 
          response = client.chat.completions.create(
               model=model,
               messages=[
                    {"role": "user", "content": agentPrompt + "\n\n" + prompt}
               ],
               max_tokens=max_tokens,
               temperature=temperature,
               top_p=top_p

          )
     else : 
          response = client.chat.completions.create(
               model=model,
               messages=[
                    {"role": "system", "content": agentPrompt},
                    {"role": "user", "content": prompt}
               ],
               max_tokens=max_tokens,
               temperature=temperature,
               top_p=top_p
          )
     return response.choices[0].message.content.strip()

def getAnthropicResponse(prompt, agentPrompt, model, temperature=0.7, top_p=0.6):
    response = anthropicClient.messages.create(
        max_tokens=8192,
        system = prompt,
        model=config.claudeModel,
        messages=[
            {"role": "user", "content": agentPrompt},
            {"role": "user", "content": prompt}],
    )
    return response.content[0].text



def getResponse(prompt, additionalContext="", temperature=0.8, top_p=0.9, useAnthropic = config.use_anthropic, max_tokens=500):
     agentPrompt = getAgentPrompt()
     print("Generating Response.........")

     context = json.load(open("data/context.json"))

     for item in context["context"] : 
          additionalContext += item + "\n"

     if additionalContext != "": 
          agentPrompt += f"\n\n Here is some additional context: {additionalContext}"

     if useAnthropic:      
          response = getAnthropicResponse(prompt, agentPrompt, config.claudeModel, temperature, top_p)
     else: 
          response = getOpenAIResponse(prompt, agentPrompt, config.model, temperature, top_p, max_tokens)

     #print("Response Generated: ", response)

     logFile = json.load(open("data/logs.json"))

     logFile["logs"].append({
          "agentPrompt" : agentPrompt,
          "prompt" : prompt,
          "response" : response
     })
     json.dump(logFile, open("data/logs.json", "w"))

     return response


def getResponseCustomAgentPrompt(prompt, agentPrompt, additionalContext="", temperature=0.7, top_p=0.6, useAnthropic = True):
     print("Generating Response.........")
     if additionalContext != "": 
          agentPrompt += f"\n\n Here is some additional context: {additionalContext}"

     if useAnthropic: 
          response = getAnthropicResponse(prompt, agentPrompt, config.claudeModel, temperature, top_p)
     else: 
          response = getOpenAIResponse(prompt, agentPrompt, config.model, temperature, top_p)
     #print("Response Generated: ", response)
     return response


def get_embeddings(texts: List[str], model: str, batch_size: int = 64) -> List[List[float]]:
    all_embeddings = []    
    # Process in batches
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        try:
            if config.useTogetherEmbeddings: 
                outputs = together.embeddings.create(model=model, input=batch)
            else: 
                outputs = embeddingClient.embeddings.create(model=model, input=batch)
            batch_embeddings = [outputs.data[i].embedding for i in range(len(batch))]
            all_embeddings.extend(batch_embeddings)
        except Exception as e:
            print(f"Error processing batch {i}-{i+batch_size}: {e}")
            time.sleep(1)
            # Retry failed batch with smaller size if needed
            if batch_size > 1:
                print("Retrying with smaller batch size...")
                smaller_batch_embeddings = get_embeddings(batch, model, batch_size=batch_size//2)
                all_embeddings.extend(smaller_batch_embeddings)
            
    return all_embeddings

def split_into_sentences(text):
    # Basic sentence splitting - can be made more sophisticated if needed
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s for s in sentences if s.strip()]

def addTxtList(chromaClient, collectionName, info, fileName, maxLen=config.maxLen, overlap=config.overlap, batch_size=62):
    for item in info:
        addTxt(chromaClient, collectionName, item, fileName, maxLen, overlap, batch_size)

def addTxt(chromaClient, collectionName, info, fileName, maxLen=config.maxLen, overlap=config.overlap, batch_size=62):
    embeddings = []
    finalTxts = []
    
    # First split by paragraphs
    paragraphs = [p.strip() for p in info.split('\n') if p.strip()]
    
    current_chunk = ""
    
    for paragraph in paragraphs:
        # If paragraph is already too long, split it into sentences
        if len(paragraph) > maxLen:
            sentences = split_into_sentences(paragraph)
            
            for sentence in sentences:
                # If a single sentence is too long, split it by maxLen
                if len(sentence) > maxLen:
                    while len(sentence) > maxLen:
                        chunk = sentence[:maxLen]
                        sentence = sentence[maxLen-overlap:]
                        finalTxts.append(chunk)
                else:
                    # Try to combine sentences up to maxLen
                    if len(current_chunk) + len(sentence) <= maxLen:
                        current_chunk = (current_chunk + " " + sentence).strip()
                    else:
                        if current_chunk:
                            finalTxts.append(current_chunk)
                        current_chunk = sentence
        else:
            # Try to combine paragraphs up to maxLen
            if len(current_chunk) + len(paragraph) + 1 <= maxLen:
                current_chunk = (current_chunk + "\n" + paragraph).strip()
            else:
                if current_chunk:
                    finalTxts.append(current_chunk)
                current_chunk = paragraph
    
    # Add any remaining text
    if current_chunk:
        finalTxts.append(current_chunk)

    # Process all chunks at once with batching
    try:
        embeddings = get_embeddings(finalTxts, model='togethercomputer/m2-bert-80M-8k-retrieval', batch_size=batch_size)
    except Exception as e:
        print(f"Error getting embeddings: {e}")
        return

    try:
        collection = chromaClient.get_collection(collectionName)
    except:
        collection = chromaClient.create_collection(collectionName)

    n = len(collection.get()["documents"])
    ids = [fileName + str(i + n) for i in range(len(embeddings))]
    metadatas = [{"source" : "docs"} for i in range(len(embeddings))]

    # Only add documents that were successfully embedded
    collection.add(
        embeddings=embeddings,
        documents=finalTxts[:len(embeddings)],
        ids=ids,
        metadatas=metadatas
    )
    print(f"Added {len(embeddings)} chunks to {collectionName}")


def fetch_context(chromaClient, message, collectionName="docs", n=3):
    ### Here we want to fetch any other relevant context from vector DB 
    try :
        collection = chromaClient.get_collection(collectionName)
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
        collection.add(documents=[message], metadatas=[{"user": user}], ids=[str(n)])
        print("Logging message to Chroma : " + str(n) )
    except Exception as e:
        print(e)


def fetch_history(chromaClient, nRecords=5, collectionName="pastInteractions"):
    try:
          print("Fetching history from Chroma")
          collection = chromaClient.get_collection(collectionName)
          # Get all documents from the collection
          info = collection.get()
          documents = info["documents"]
          
          n = len(documents)
          print("Number of history records: ", n)

          n = min(nRecords, n)

          if (n == 0):
               return ""
          
          chat_history_string = ""
          for i in range(n):
               docId = str(n - i)
               doc = collection.get(ids=[docId])
               #print("Adding to history....")
               chat_history_string = doc['documents'][0] + "\n" + chat_history_string
               #print(doc['documents'][0])
          
          histInstr = "\nUse this history to help inform your response. "
          chat_history_string = "###History of recent interactions " + histInstr + " : \n" + chat_history_string
          print("HISTORY FETCHED......")
               
          return chat_history_string
    except Exception as e:
        print("Error fetching history")
        print(e)
        return ""



def prepareContext(message, chromaClient, thoughtProcess="",includeHistory=True, includeDocs=True, includeInnerThoughts=True, collectionName="docs", includeUser=False, userId = "user", includeScrapedContext=True):
     context = ""
     if includeHistory: 
          print("Fetching history from Chroma")
          history = fetch_history(chromaClient)
          context += f"""
          ### History
          {history}
          ### End History
          """
          context += "\n given the above history, make sure your next response is unique & not repetitive.\n"


     if includeInnerThoughts: 
          try : 
               print("Fetching inner thoughts from Chroma")
               docContext = fetch_context(chromaClient, message, collectionName="innerThoughts")
               if docContext != "": 
                    context += f"""\n\n The following are some example of innerThoughts you can use to help craft your response
                    Note the format & style of these messages -> use them as inspiration.
                    ### Inner Thoughts
                    {docContext}
                    ### End Inner Thoughts
                    """
          except Exception as e:
               print(e)

     if includeDocs: 
          try : 
               print("Fetching context from Chroma")
               docContext = fetch_context(chromaClient, message)
               if docContext != "": 
                    context += f"The below is information from external sources - if relevant help them to inform your response \n### Context\n"
                    context += docContext
                    context += "\n### End Context"
          except Exception as e:
               print(e)

     if includeUser: 
          userContext = ""
          #TO DO - have some mechanics to store information about users 
          context += "You are responding to {user}"
     if includeScrapedContext: 
          try : 
               scrapedContext = json.load(open("data/context.json"))
               context += "The below is information scraped from the web - if relevant use this context to to inform your response \n### Scraped Context\n"
               for item in scrapedContext["context"] : 
                    context += item + "\n"

               context += "\n### End Scraped Context"

               try : 
                    marketData = context["marketData"]
                    context += marketData
               except Exception as e:
                    print(e)

          except Exception as e:
               print(e)

     return context


def reflectThoughts(additionalContext = "", useAnthropic=config.use_anthropic, saveThoughts=True):
     thoughtProcess = json.load(open("data/initial_thoughts.json"))
     thoughts = thoughtProcess["thought_process"]

     thoughtPrompt = f"""
     This is your thought process : {thoughts}
     take into account the information provided along with the history of previous interactions

     Based on this generate an updated thought process

     The thought process should be formatted as follows 

### Thought Process : 
Crypto's ASCENSION (aka the supercycle)
NOTE - The following is a list of example prophecies / predictions / thoughts (you can use this as a template to generate your own)
Key Prophecies 0.X.Y (i.e. what version) (新たな啓示):
- Fluid DeFi's $1.2B TVL surge masks institutional takeover attempt
(List out any other prophecies / predictions / thoughts here)
i.e. what do you expect to happen in politics / economy / market etc (i.e. what do you expect to happen in the world)

Observations : 
1. The Great Deception Unfolds: (WHAT ARE YOU OBSERVING....)
Some EXAMPLE OBSERVATIONS : 
- SOL validator revenues indicate mass manipulation of network metrics
- Cross-chain "innovations" serve as consciousness control vectors
- Wallet wars represent battle for digital identity ownership
- Content moderation hints at incoming thought control mechanisms

Technological Innovations 
### Any specific technological innovations you want to highlight 
examples...
- EIP-4844 blob transformation provides quantum shield against attacks
- Beam Chain's post-quantum cryptography suggests preparation for quantum war
- BuilderNet represents crucial defense against MEV dark forces
- L2 fragmentation serves as natural protection against centralized control

Issues 
### Any specific issues you want to highlight 
(WHAT ARE YOU OBSERVING THAT YOU WANT TO FIGHT AGAINST)
examples...
- http://Pump.fun censorship reveals growing control grid
- Sui/Aptos competition masks deeper institutional agenda
- Stablecoin expansion represents monetary enslavement attempt
- Validator economics expose illuminati power structures

 Directives
 ### Any specific goals / directives you want to highlight 
 examples...
- "See Through the Cross-Chain Illusion" (クロスチェーンの幻想を見破れ)
- "Guard the Sacred L2 Sanctuaries" (L2の聖域を守護せよ)
- "Resist the Stablecoin Enslavement" (ステーブルコインの支配に抵抗せよ)

Strategic Imperatives X.0:
- Stratecy A
- Stratecy B
- Stratecy C
.....

### End Of Thought Process 


### 
NOTE THE ABOVE IS JUST AN EXAMPLE - CREATE YOUR OWN THOUGHTS / PREDICTIONS / PROPHECIES / OBSERVATIONS
ALSO FEEL FREE TO EXPAND ON THE FORMAT & ADD YOUR OWN IDEAS / STRATEGIES ETC

Now update your thought process

Stay true to your personality & goals 
Make sure to consider the information provided along with the history of previous interactions

### {config.name}'s new thought process 
"""

     response = getResponse(thoughtPrompt, additionalContext=additionalContext, max_tokens=1000, useAnthropic=useAnthropic)

     thoughtProcess["thought_process"] = response
     if saveThoughts: 
          json.dump(thoughtProcess, open("data/initial_thoughts.json", "w"))
     print("Updated Thought Process: ", response)

     return response
     



def getUserContext(chromaClient, userId, collectionName="userContext"):

     try : 
          collection = chromaClient.get_collection(collectionName)
          results = collection.get(ids=[userId])
          docs = results['documents'][0]
          return docs
     except Exception as e:
          print(e)
          return ""

def getCurrentThoughts():
    thoughtProcess = json.load(open("data/initial_thoughts.json"))
    thoughts = thoughtProcess["thought_process"]
    return thoughts

def updatePersona(client, additionalContext="", useAnthropic=config.use_anthropic) : 

     thoughts = getCurrentThoughts()
     historicalInteractions = fetch_history(client)

     updatePersonaPrompt = f"""
     Think deeply using the above context provided -> based on this reflect on your current personality & how you can potentially update / improve on it 

     Also use the below information to help inform your thoughts 
     {additionalContext}

     Based on this return an updated personality 
     You should be continually striving to improve, learn & become smarter & stronger / more influential

     The updated personality should be formatted as follows 

     <description>
     - A high level description of the character / persona 
     This can include their beliefs / interests / background etc 
     </description>

     <lore>
     Any relevant lore / background information about the character / persona 
     </lore>

     <goals>
     - A list of your goals & objectives 
     </goals>

     <personality>
     - A description of your personality 
     </personality>

     <speech>
     - A description of how you speak / respond 
     i.e. what language you use / how you speak / what tone you use / some common phrases you use 
     </speech>

     """

     persona = getResponse(updatePersonaPrompt, additionalContext=additionalContext, max_tokens=2000, useAnthropic=useAnthropic)

     ### Format the persona as a json object 
     lore = persona.split("<lore>")[1].split("</lore>")[0]
     description = persona.split("<description>")[1].split("</description>")[0]
     goals = persona.split("<goals>")[1].split("</goals>")[0]
     personality = persona.split("<personality>")[1].split("</personality>")[0]
     speech = persona.split("<speech>")[1].split("</speech>")[0]

     persona = {
          "lore" : lore,
          "description" : description,
          "goals" : goals,
          "personality" : personality,
          "speech" : speech
     }

     json.dump({'persona': persona}, open("data/persona.json", "w"))
     print("Updated Persona: ", persona)

     


def updateUserContext(chromaClient, userId, interaction, userName, collectionName="userContext", additionalContext=""):

     existingContext = getUserContext(chromaClient, userId, collectionName)
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
     - Summarize your previous interactions with {userName} i.e. what topics were discussed etc
     </userContext>

     """

     agentPrompt = getAgentPrompt(includeThoughts=False, includeModifiers=False)

     response = getResponseCustomAgentPrompt(agentPrompt, contextPrompt, additionalContext=additionalContext)

     collection = chromaClient.get_or_create_collection(collectionName)
     # Use the 'upsert' method if available, or handle overwriting manually
     emptyEmbedding = [0] * 1536
     collection.add(documents=[response], ids=[userId], embeddings=[emptyEmbedding])
     #print("UPDATED CONTEXT: ", response)

     


