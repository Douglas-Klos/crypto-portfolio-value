#!/usr/bin/env python3

import aiohttp
import asyncio
import json
import csv
from functools import reduce
from operator import add
from loguru import logger
from datetime import datetime


class Crytpowatch:
    def __init__(self):
        self.base_url = "https://api.cryptowat.ch/"
        self.market = "binance"
        self.paircoin = "xlm"
        self.pairusd = 0

    def get_market_price_url(self, **kwargs):

        return (
            self.base_url + "markets/" + self.market + "/" + kwargs["pair"] + "/price"
        )


async def fetch(session, url):
    async with session.get(url) as response:
        return await response.text()


def load_currency_file(filename="currency.txt"):
    with open(filename) as file:
        reader = csv.reader(file, skipinitialspace=True)
        cryptoCurrency = list(reader)

    return cryptoCurrency


def get_coin_pair(coin, pair):
    return coin.lower() + pair


def calculate_portfolio_total(portfolio):
    return reduce(add, [item["value"] for item in portfolio])


def display_portfolio(portfolio, client):
    print("-----------------------------------------------------------------------")
    print(
        f"Coin\t Quantity\t {client.paircoin.upper()} value\t Total Value \t Location"
    )
    print("-----------------------------------------------------------------------")
    for item in portfolio:
        print(
            f'{item["coin"]}\t {item["quantity"]:10}\t {item["price"]:.8f}\t {item["value"]:.8f}\t {item["storage"]}'
        )
    print("-----------------------------------------------------------------------")


def add_to_portfolio(portfolio, **kwargs):
    return portfolio.append(kwargs)


async def calculate_btc_equivalent(session, client, coin):

    coin_data = json.loads(
        await (
            fetch(
                session, client.get_market_price_url(pair=get_coin_pair(coin[0], "btc"))
            )
        )
    )

    equivalent = json.loads(
        await (
            fetch(
                session,
                client.get_market_price_url(pair=get_coin_pair(client.paircoin, "btc")),
            )
        )
    )

    return {
        "coin": coin[0],
        "quantity": float(coin[1]),
        "price": (coin_data["result"]["price"]) * (1 / equivalent["result"]["price"]),
        "value": (float(coin[1]) * coin_data["result"]["price"])
        * (1 / equivalent["result"]["price"]),
        "storage": coin[2],
    }


async def calculate_usd_value(total_coin_value, client):
    async with aiohttp.ClientSession() as session:
        coin_data = json.loads(
            await (
                fetch(
                    session, client.get_market_price_url(pair=client.paircoin + "usdt")
                )
            )
        )

    return coin_data["result"]["price"]


async def calculate_portfolio(cryptoCurrency, client):
    portfolio = []
    insertion = {}

    async with aiohttp.ClientSession() as session:
        for coin in cryptoCurrency:

            insertion["coin"] = coin[0]
            insertion["quantity"] = float(coin[1])
            insertion["storage"] = coin[2]

            pair = get_coin_pair(coin[0], client.paircoin)

            if pair == coin[0].lower() + coin[0].lower():
                insertion["price"] = 1.0
                insertion["value"] = float(coin[1])

            else:
                coin_data = json.loads(
                    await fetch(session, client.get_market_price_url(pair=pair))
                )

                if "error" in coin_data:
                    insertion = await calculate_btc_equivalent(session, client, coin)
                else:
                    insertion["price"] = coin_data["result"]["price"]
                    insertion["value"] = coin_data["result"]["price"] * float(coin[1])

            add_to_portfolio(portfolio, **insertion)

    return portfolio


def main():
    client = Crytpowatch()
    cryptoCurrency = load_currency_file()

    loop = asyncio.get_event_loop()
    portfolio = loop.run_until_complete(calculate_portfolio(cryptoCurrency, client))

    display_portfolio(portfolio, client)
    print(f"Date: {datetime.now()}")
    print(f"Total {client.paircoin} value: {calculate_portfolio_total(portfolio)}\t")

    usd_value = loop.run_until_complete(
        calculate_usd_value(calculate_portfolio_total(portfolio), client)
    )

    print(f"USD Value: {usd_value * calculate_portfolio_total(portfolio)}")


if __name__ == "__main__":
    main()
