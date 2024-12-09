from onchain.loadContract import loadContract, getLogs
import json

startingBlock = 105062472

def monitorChain():
    print("Monitoring chain.....")
    try : 
        startBlock = json.load(open("startBlock.json"))
        startBlock = startBlock["block"]
    except : 
        startBlock = startingBlock

    logs, current_block = getLogs(startBlock)
    print(logs)
    print(type(logs))


    json.dump({"block" : current_block}, open("startBlock.json", "w"))

    return logs


def processLogs(logs): 
    print("Processing logs.....")

    for log in logs: 
        
        message = log["args"]["message"]
        context = log["args"]["context"]
        takeAction(message, context)
        print(message)

        ### TO DO -> each message should map to a function that also takes in context as an argument 
        ### i.e. update description / speech / personality / etc. 

    return

def takeAction(action, context):

    persona = json.load(open("persona.json"))

    if action == "Tweet":
        try : 
            queuedTweets = json.load(open("queuedTweets.json"))
            queuedTweets["tweets"].append(context)
            json.dump(queuedTweets, open("queuedTweets.json", "w"))
        except : 
            json.dump({"tweets" : [context]}, open("queuedTweets.json", "w"))
        ### TO DO -> add tweet instructions to schedule 
        pass

    # elif action == "UpdatePersonality":
    #     persona["persona"]["personality"] = context
    #     json.dump(persona, open("persona.json", "w"))
    # elif action == "UpdateLore":
    #     persona["persona"]["lore"] = context
    #     json.dump(persona, open("persona.json", "w"))
    # elif action == "UpdateSpeech":
    #     persona["persona"]["speech"] = context
    #     json.dump(persona, open("persona.json", "w"))
    # elif action == "UpdateDescription":
    #     persona["persona"]["description"] = context
    #     json.dump(persona, open("persona.json", "w"))
    # elif action == "UpdateGoals":
    #     persona["persona"]["goals"] = context
    #     json.dump(persona, open("persona.json", "w"))
    # elif action == "ResearchLink":
    #     ### TO DO -> add research link instructions to schedule 
    #     pass

    
        