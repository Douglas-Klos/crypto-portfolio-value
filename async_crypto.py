#!/usr/bin/env python3
""" Async queries api.cryptowat.ch and calculates the value of your portfolio """

import asyncio
import json
import csv
from functools import reduce
from operator import add
from datetime import datetime
import aiohttp


class Crytpowatch:
    """ Generates cryptowatch api url's """

    def __init__(self):
        self.base_url = "https://api.cryptowat.ch/"
        self.market = "binance"
        self.paircoin = "btc"

    def get_market_price_url(self, **kwargs):
        """ Returns the market price url for a specified pair """
        return (
            self.base_url + "markets/" + self.market + "/" + kwargs["pair"] + "/price"
        )

    def get_market_url(self):
        """ Returns the base market url """
        return self.base_url + "markets/" + self.market


async def fetch(session, url):
    """ Async call to get data from url """
    async with session.get(url) as response:
        return await response.text()


def load_currency_file(filename="currency.txt"):
    """ Loads currency file into memory for processing """
    with open(filename) as file:
        reader = csv.reader(file, skipinitialspace=True)
        crypto_currency = list(reader)

    return crypto_currency


def get_coin_pair(coin, pair):
    """ Returns the coin par used in the URL """
    return coin.lower() + pair


def calculate_portfolio_total(portfolio):
    """ Calculates the total value of the portfolio in specified paircoin """
    return reduce(add, [item["value"] for item in portfolio])


def display_portfolio(portfolio, client):
    """ Display the portfolio """
    print("-----------------------------------------------------------------------")
    print(
        f"Coin\t Quantity\t {client.paircoin.upper()} value\t Total Value \t Location"
    )
    print("-----------------------------------------------------------------------")
    for item in portfolio:
        print(
            f'{item["coin"]}\t {item["quantity"]:10}\t {item["price"]:.8f}\t '
            f'{item["value"]:.8f}\t {item["storage"]}'
        )
    print("-----------------------------------------------------------------------")


def add_to_portfolio(portfolio, **kwargs):
    """ Adds a record to the portfolio """
    return portfolio.append(kwargs)


async def calculate_btc_equivalent(session, client, coin):
    """
        When a coin pair is not found on the market, we first convert it to btc
        and then to the desired coin to generate an approximate value
    """
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


async def calculate_usd_value(client):
    """ Uses the total portfolio value to estimate a USD value """
    async with aiohttp.ClientSession() as session:
        coin_data = json.loads(
            await (
                fetch(
                    session, client.get_market_price_url(pair=client.paircoin + "usdt")
                )
            )
        )

    return coin_data["result"]["price"]


async def calculate_portfolio(crypto_currency, client):
    """ Our main async loop.  Calculates the value of each coin in the portfolio """
    portfolio = []
    insertion = {}

    async with aiohttp.ClientSession() as session:
        for coin in crypto_currency:

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


async def main():
    """ Main """
    client = Crytpowatch()
    crypto_currency = load_currency_file()

    portfolio = await calculate_portfolio(crypto_currency, client)
    usd_value = await calculate_usd_value(client)

    display_portfolio(portfolio, client)
    print(f"Date: {datetime.now()}")
    print(f"Total {client.paircoin} value: {calculate_portfolio_total(portfolio)}\t")
    print(f"USD Value: {usd_value * calculate_portfolio_total(portfolio)}")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
