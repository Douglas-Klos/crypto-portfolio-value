#!/usr/bin/env python3

import requests
from functools import reduce
from operator import add
import csv


class Crytpowatch:
    def __init__(self):
        self.base_url = "https://api.cryptowat.ch/"

    def get_market(self, market):
        return requests.get(self.base_url + "markets/" + market)

    def get_market_price(self, market, pair):
        return requests.get(self.base_url + "markets/" + market + "/" + pair + "/price")


pair = "btc"
market = "binance"


def load_currency_file(filename="currency.txt"):
    with open(filename) as file:
        reader = csv.reader(file, skipinitialspace=True)
        cryptoCurrency = list(reader)

    return cryptoCurrency


def get_coin_pair(coin):
    return coin.lower() + pair


def calculate_portfolio(client, cryptoCurrency):
    portfolio = []

    for coin in cryptoCurrency:
        coin_data = client.get_market_price(market, get_coin_pair(coin[0])).json()

        portfolio.append(
            {
                "coin": coin[0],
                "quantity": float(coin[1]),
                "price": coin_data["result"]["price"],
                "value": coin_data["result"]["price"] * float(coin[1]),
            }
        )

    return portfolio


def display_portfolio(portfolio):
    print("---------------------------------------------------")
    for item in portfolio:
        print(
            f'{item["coin"]}\t {item["quantity"]:10}\t {item["price"]:.8f}\t {item["value"]:.8f}'
        )
    print("---------------------------------------------------")


def calculate_portfolio_total(portfolio):
    return (reduce(add, [item["value"] for item in portfolio]))


def main():
    client = Crytpowatch()

    cryptoCurrency = load_currency_file()

    portfolio = calculate_portfolio(client, cryptoCurrency)
    display_portfolio(portfolio)

    print(f"Total {pair} value = {calculate_portfolio_total(portfolio)}")


if __name__ == "__main__":
    main()
