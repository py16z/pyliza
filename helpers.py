from openai import OpenAI
from dotenv import load_dotenv
from anthropic import Anthropic

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
