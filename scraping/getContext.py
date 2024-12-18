from together import Together
from dotenv import load_dotenv
import json

from helpers import getResponseCustomAgentPrompt

load_dotenv()

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

Note : 
YOU ARE EXTREMELY OPEN TO CHANGING YOUR THOUGHTS / OPINIONS BASED ON THE INFORMATION PROVIDED 

Key sections to include in the summary are 
# Introduction
Key summary of the content in question i.e. what is being discussed in the content / how does it relate to your opinions / interests / thoughts  
# Key Insights:
-> list out key insights from the content 
(if there are particular headlines / topics list them out & make sure to include the details)
# Your reactions / thoughts
-> Any strong reactions to the information presented
-> Does the information conflict with any existing beliefs ? If so how should your thougt process be updated 
-> Are there any interesting terms / concepts you should aim to understand better 
-> Are there any quotes / statements you should aim to memorise (if so list them)
# Future questions / things to research
-> Based on this is there anything you should aim to research further 
# Future actions
-> Based on this what would you like to tweet about in the future ? (i.e. what topics / what things you should aim to discuss)

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

Analysis in markdown format

Notes on the analysis
i.e. what you learned from the analysis
i.e. what you would like to research further
i.e. what you would like to tweet about in the future

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

def getContext(results, additionalContext="", useClaude=True, thoughtProcess=""):
    togetherModel = "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo"
    model = "claude-3-5-sonnet-20240620"
    sysPrompt = PROMPT + thoughtProcess +TASK + EXPECTED_OUTPUT

    out = getResponseCustomAgentPrompt(results, sysPrompt, additionalContext=additionalContext, useAnthropic=useClaude)
    return out

    
def getSummary(results, additionalContext="", useClaude=True, thoughtProcess=""):
    togetherModel = "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo"
    model = "claude-3-5-sonnet-20240620"

    sysPrompt = PROMPT + thoughtProcess + SUMMARY_TASK + EXPECTED_OUTPUT
    out = getResponseCustomAgentPrompt(results, sysPrompt, additionalContext=additionalContext)


    return out




    