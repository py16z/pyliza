from together import Together
from dotenv import load_dotenv
import json

import config

from helpers import getResponseCustomAgentPrompt

load_dotenv()

thoughts = json.load(open("thoughtProcess.json"))
thoughtProcess = thoughts["thoughtProcess"]

PROMPT = """
<rules>
META_PROMPT1: Follow the prompt instructions laid out below. 

1. follow the conventions always.

2. Your primary objective is in <mission> & the expected output is in <expected output>

</rules>
"""

task = """
You are given raw output from a website that has been scraped using a webscraper.

Additionally if available you are given a previous analysis of the same topic - build on this analysis & add to it using the information provided
This information is provided in the <context> tag

Make sure to keep all the information in the <context> tag in mind when you are writing your analysis unless it is repeated / updated in the new content

You are to analyze the output together with any previous analysis and give a summary
The summary should be in markdown format 
Ensure you also include the existing context in the summary along with any new information you have found

You should seperate each section with a header 

Your current thought process is : 
{thoughtProcess}

Key sections to include in the summary are 
# Introduction
Key summary of the content in question i.e. what is being discussed in the content  
# Key Insights:
-> list out key insights from the content 
(if there are particular headlines / topics list them out & make sure to include the details)

"""


summary = """
You are given analysis from various articles 

Summarise the analysis into one coherent summary 

You should seperate each section with a header 

Once you've analysed the articles decide which headers are most relevant to include in the summary 
Do this in your <thought process> section 

"""

output = """
Below is an example of how the output from the above tasks should be formatted

<analysis>

Analysis in markdown format

</analysis>

"""



TASK = f"""
<mission>
This is your TASK : 
{task}
</mission>
"""

SUMMARY_TASK = f"""
<mission>
This is your TASK : 
{summary}
</mission>
"""

EXPECTED_OUTPUT = f"""
<expected output>
{output}
</expected output>
"""


import time

def getContext(results, additionalContext="", useClaude=True):
    togetherModel = "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo"
    model = "claude-3-5-sonnet-20240620"
    contextStr = "\n<context> Additionally the following context has been provided from previous analysis conducted - build on this & add to it using the information provided : "
    sysPrompt = PROMPT + TASK + EXPECTED_OUTPUT

    out = getResponseCustomAgentPrompt(results, sysPrompt, additionalContext=additionalContext)
    return out

    
def getSummary(results, additionalContext="", useClaude=True):
    togetherModel = "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo"
    model = "claude-3-5-sonnet-20240620"
    contextStr = "\n<context> The below is information specically about Rise Chain - use this to help guide your response :  "

    sysPrompt = PROMPT + SUMMARY_TASK + EXPECTED_OUTPUT
    out = getResponseCustomAgentPrompt(results, sysPrompt, additionalContext=additionalContext)


    return out




    