from web3 import Web3
from dotenv import load_dotenv
import os
import json

load_dotenv()

abi = json.load(open("onchain/MyContract.json"))



def loadContract(rpc):
    w3 = Web3(Web3.HTTPProvider(rpc))
    contract = w3.eth.contract(address=os.getenv("CONTRACT_ADDRESS"), abi=abi)
    current_block = w3.eth.block_number
    return contract, current_block


def getLogs(from_block):
    contract, current_block = loadContract(os.getenv("RPC"))
    logs = contract.events.Logmessage().get_logs(from_block=from_block)

    return logs, current_block

    


