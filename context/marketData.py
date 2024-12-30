

### Get data from coingetcko API 

import requests
import os
from dotenv import load_dotenv
import pandas as pd
import json
load_dotenv()

### get price of a coin 

def get_price(coin_ids, vs_currency="usd"):
    url = "https://api.coingecko.com/api/v3/simple/price"

    params = {
        "ids": coin_ids,
        "vs_currencies": vs_currency,
        "include_market_cap": "true",
        "include_24hr_vol": "true",
        "include_24hr_change": "true",
        "include_last_updated_at": "true",
    'x-cg-demo-api-key' : os.getenv("COINGECKO_API_KEY")
}

    response = requests.get(url, params=params)
    return response.json()

def get_market_cap():
    url = "https://api.coingecko.com/api/v3/global"
    params = {
        'x-cg-demo-api-key' : os.getenv("COINGECKO_API_KEY")
    }
    response = requests.get(url, params=params)
    response = response.json()

    data = response["data"]


    #print(response)

    marketCap = data
    #print(marketCap)
    #print(type(marketCap))

    return marketCap




prices = get_price("bitcoin,ethereum")

def format_prices(prices):
    formatted_prices = []
    for coin_id, data in prices.items():
        formatted_prices.append({
            "chain" : coin_id,
            "usd_price": f"${data['usd']:.2f}",
            "usd_market_cap": f"${data['usd_market_cap']/1e9:.2f} Billion",
            "usd_24h_vol": f"${data['usd_24h_vol']/1e6:.2f} Million",
            "usd_24h_change": f"{data['usd_24h_change']:.2f}%"
        })
    
    df = pd.DataFrame(formatted_prices)
    return df

def get_chains():
    url = "https://api.llama.fi/v2/chains"
    response = requests.get(url)

    df = pd.DataFrame(response.json())

    ### Get top 10 chains by market cap
    top_chains = df.sort_values(by="tvl", ascending=False).head(10)
    ### Format TVL 
    top_chains["tvl"] = top_chains["tvl"].apply(lambda x: f"${x/1e9:.2f}B")
    includeCols = ["name", "tvl"]
    return top_chains[includeCols]

def get_protocols():
    url = "https://api.llama.fi/v2/protocols"
    response = requests.get(url)
    df = pd.DataFrame(response.json())

    ### Get top 10 protocols by tvl

    ### Exclude if "parent" is not null
    df = df[df["parent"].isnull()]
    top_protocols = df.sort_values(by="tvl", ascending=False).head(10)

    includeCols = ["name", "tvl"]

    top_protocols["tvl"] = top_protocols["tvl"].apply(lambda x: f"${x/1e9:.2f}B")
    top_protocols = top_protocols[includeCols]

    return top_protocols

def getMarketData():

    assetlist = ["bitcoin", "ethereum", "solana", "optimism", "arbitrum", "blast", "tether", "usdc","ethena-usde","dai"]
    
    assetIn = ""
    for asset in assetlist:
        assetIn += f"{asset},"
    assetIn = assetIn[:-1]

    prices = get_price(assetIn)
    formatted_prices = format_prices(prices)
    chains = get_chains()
    protocols = get_protocols()

    marketData = f"""
    ### Market Data
    Below is current cryptocurrency market data 

    ### Price Data (including market cap, 24h volume, and 24h change, price in USD)
    {formatted_prices.to_string(index=False)}

    ### Top 10 Chains by TVL
    {chains.to_string(index=False)}

    ### Top 10 Protocols by TVL
    {protocols.to_string(index=False)}

    ### End of Market Data
    """

    return marketData






