#!/usr/bin/env python

import matplotlib

matplotlib.use('TkAgg')

import matplotlib.pyplot as plt
import urllib.parse

import getpass
import sys

from common import scraper

import pandas as pd


def display_daily_graph(davg, mean_average):
    y_pos = range(len(davg["Date and Time"]))
    only_dates = pd.to_datetime(davg["Date and Time"]).dt.date

    plt.bar(y_pos, davg["Amount"], align='center', alpha=0.5)
    plt.xticks(y_pos, only_dates, rotation=90)
    plt.ylabel('Dollars Spent')
    plt.title('Dollars Spent Per Day')
    plt.axhline(y=mean_average, color='r', linestyle='-')
    plt.savefig('daily_spending.png', bbox_inches='tight')
    plt.show()


def display_cumulative_spending_graph(df):
    df.plot(y=['Cumulative Spending'])
    plt.savefig('cumulative_spending.png', bbox_inches='tight')
    plt.show()


if __name__ == "__main__":
    if len(sys.argv) == 1:
        username = urllib.parse.quote(input("Username: "), safe='')
        password = urllib.parse.quote(getpass.getpass(), safe='')

    # write transactions to csv
    user_transactions = scraper.get_user_transactions(username, password)

    date_amount = user_transactions["Amount"]
    daily_average = date_amount.resample('D').sum().reset_index()
    daily_average = daily_average.fillna(0)
    mean_average = daily_average["Amount"].mean()

    display_daily_graph(daily_average, mean_average)
    display_cumulative_spending_graph(user_transactions)
