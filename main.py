import asyncio
import json
from typing import Optional

import aiohttp
import websockets
from fastapi import FastAPI, Query

storage = {}

app = FastAPI()


async def binance_ws():
    uri = "wss://stream.binance.com:9443/ws/!ticker@arr"

    async with websockets.connect(uri) as websocket:

        while True:

            response = await websocket.recv()
            response = json.loads(response)

            data = {}

            for pair in response:

                try:
                    price_buy = float(pair['b'])
                    price_sell = float(pair['a'])
                    price = (price_buy + price_sell) / 2

                    price = '%.6f' % price
                    data[pair['s']] = price

                    storage.setdefault('binance', {})[pair['s']] = price

                except Exception as e:
                    print(e)


async def fetch_all_trading_pairs():
    url = "https://api.kraken.com/0/public/AssetPairs"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response_text = await response.text()
            trading_pairs = json.loads(response_text)
            trading_pairs = trading_pairs.get("result", {})

            data = []

            for pair in trading_pairs:
                data.append(trading_pairs[pair]['wsname'])

            return data


async def kraken_ws(pairs):
    uri = "wss://ws.kraken.com/"

    subscribe_message = {
        "event": "subscribe",
        "pair": list(pairs),
        "subscription": {"name": "ticker"}
    }

    async with websockets.connect(uri) as websocket:
        await websocket.send(json.dumps(subscribe_message))

        while True:
            response = await websocket.recv()
            response = json.loads(response)

            if isinstance(response, list) and "ticker" in response[-2]:
                pair_name = response[-1].replace('/', '')
                price_data1 = float(response[1]['a'][0])
                price_data2 = float(response[1]['b'][0])
                price = (price_data1 + price_data2) / 2
                price = '%.6f' % price
                storage.setdefault('kraken', {})[pair_name] = price


@app.on_event('startup')
async def binance_updator():
    asyncio.create_task(binance_ws())


@app.on_event('startup')
async def kraken_updator():
    trading_pairs = await fetch_all_trading_pairs()

    asyncio.create_task(kraken_ws(trading_pairs))


@app.get("/prices")
async def get_prices(pair: Optional[str] = Query(None), exchange: Optional[str] = Query(None)):
    print(exchange, pair)

    if exchange == 'binance':

        if not pair:
            data = storage.get("binance", None)
            return {"success": True, "data": data}

        data = storage.get("binance", None).get(pair)

        return {"success": True, "data": [{"pair": pair, "price": data}]}

    if exchange == 'kraken':

        if not pair:
            data = storage.get("kraken", None)
            return {"success": True, "data": data}

        data = storage.get("kraken", None).get(pair)

        return {"success": True, "data": [{"pair": pair, "price": data}]}

    if not exchange and not pair:
        return {"success": True, "data": storage}

    return {"success": False, "error": "Wrong exchange"}
