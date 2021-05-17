from collections import defaultdict
import pandas as pd
import requests
import uncurl
from bs4 import BeautifulSoup
import urllib.parse
from datetime import datetime


def get_user_transactions(username, password):
    session = requests.Session()

    def parsed_context_to_dict(parsed_context):
        res = {}
        for key in ["url", "method", "headers", "data", "cookies", "auth"]:
            res[key] = getattr(parsed_context, key)
        return res

    # GET LOGIN PAGE --------------------------------------------------------------------------------------------------
    response = session.request(**parsed_context_to_dict(uncurl.parse_context(
        '''curl 'https://onecard.mcgill.ca/LogIn.aspx' 

        -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:69.0) Gecko/20100101 Firefox/69.0' 
        -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8' 
        -H 'Accept-Language: en-US,en;q=0.5' --compressed 
        -H 'DNT: 1' 
        -H 'Connection: keep-alive' 
        -H 'Upgrade-Insecure-Requests: 1' 
        -H 'Cache-Control: max-age=0' '''
    )))

    # get body parameters
    soup = BeautifulSoup(response.text, "html.parser")

    viewstate = urllib.parse.quote(soup.find(id="__VIEWSTATE")['value'], safe='')
    generator = urllib.parse.quote(soup.find(id="__VIEWSTATEGENERATOR")['value'], safe='')
    validation = urllib.parse.quote(soup.find(id="__EVENTVALIDATION")['value'], safe='')

    # LOGIN WITH BODY PARAMETERS --------------------------------------------------------------------------------------
    response = session.request(**parsed_context_to_dict(uncurl.parse_context(
        '''curl 'https://onecard.mcgill.ca/LogIn.aspx' 
           -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:69.0) Gecko/20100101 Firefox/69.0' 
           -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8' 
           -H 'Accept-Language: en-US,en;q=0.5' --compressed 
           -H 'Content-Type: application/x-www-form-urlencoded' 
           -H 'DNT: 1' 
           -H 'Connection: keep-alive' 
           -H 'Referer: https://onecard.mcgill.ca/LogIn.aspx' 
           -H 'Upgrade-Insecure-Requests: 1' --data '__VIEWSTATE=''' + viewstate + '''&__VIEWSTATEGENERATOR=''' + generator + '''&__EVENTVALIDATION=''' + validation + '''&tbUserName=''' + username + '''&tbPassword=''' + password + '''&Button1=Log+In' '''
    )))

    # GET FIRST TRANSACTIONS PAGE -------------------------------------------------------------------------------------
    response = session.request(**parsed_context_to_dict(uncurl.parse_context(
        '''curl 'https://onecard.mcgill.ca/Consumption.aspx' 
           -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:69.0) Gecko/20100101 Firefox/69.0' 
           -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8' 
           -H 'Accept-Language: en-US,en;q=0.5' --compressed 
           -H 'DNT: 1' 
           -H 'Connection: keep-alive' 
           -H 'Referer: https://onecard.mcgill.ca/Default.aspx' 
           -H 'Upgrade-Insecure-Requests: 1' '''
    )))

    # get body parameters
    soup = BeautifulSoup(response.text, "html.parser")

    viewstate = urllib.parse.quote(soup.find(id="__VIEWSTATE")['value'], safe='')
    generator = urllib.parse.quote(soup.find(id="__VIEWSTATEGENERATOR")['value'], safe='')
    validation = urllib.parse.quote(soup.find(id="__EVENTVALIDATION")['value'], safe='')

    account_balances = []
    account_table = soup.find(id="cphConsumption_gvAccounts")
    for i, table_row in enumerate(account_table.findAll('tr')[1:]):
        account_balances.append([column.text for column in table_row.findAll('td')])

    account_balances = list(map(lambda row: {"account_name": row[0], "balance": row[1]}, account_balances))

    output_rows = []
    # write to csv
    table = soup.find(id="cphConsumption_gvTransDetail")
    for i, table_row in enumerate(table.findAll('tr')):
        if 2 < i < (len(table.findAll('tr')) - 2):
            output_rows.append([column.text for column in table_row.findAll('td')])

    # check if there is next page
    hasnext = ("Next" in response.text)

    while hasnext:

        response = session.request(**parsed_context_to_dict(uncurl.parse_context(
            '''curl 'https://onecard.mcgill.ca/Consumption.aspx' 
            -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:69.0) Gecko/20100101 Firefox/69.0' -H 'Accept: */*' 
            -H 'Accept-Language: en-US,en;q=0.5' --compressed -H 'X-Requested-With: XMLHttpRequest' 
            -H 'X-MicrosoftAjax: Delta=true' -H 'Cache-Control: no-cache' 
            -H 'Content-Type: application/x-www-form-urlencoded; charset=utf-8' -H 'DNT: 1' 
            -H 'Connection: keep-alive' -H 'Referer: https://onecard.mcgill.ca/Consumption.aspx' --data 'ctl00%24cphConsumption%24ScriptManager1=ctl00%24cphConsumption%24upDetails%7Cctl00%24cphConsumption%24gvTransDetail&__EVENTTARGET=ctl00%24cphConsumption%24gvTransDetail&__EVENTARGUMENT=Page%24Next&__VIEWSTATE=''' + viewstate + '''&__VIEWSTATEGENERATOR=''' + generator + '''&__EVENTVALIDATION=''' + validation + '''&__ASYNCPOST=true&' '''
        )))

        soup = BeautifulSoup(response.text, "html.parser")
        starting = (soup.text[soup.text.index("__VIEWSTATE") + 12:])
        broken_up = (starting.split("|"))
        viewstate = urllib.parse.quote(broken_up[0], safe='')
        generator = urllib.parse.quote(broken_up[4], safe='')
        validation = urllib.parse.quote(broken_up[8], safe='')

        table = soup.find(id="cphConsumption_gvTransDetail")
        for i, table_row in enumerate(table.findAll('tr')):
            if 2 < i < (len(table.findAll('tr')) - 2):
                output_rows.append([column.text for column in table_row.findAll('td')])

        hasnext = ("Next" in response.text)

    df = pd.DataFrame(output_rows,
                      columns=["transaction_id", "datetime", "amount", "location", "device", "account"])

    # reverse the transactions
    df = df.reindex(index=df.index[::-1])

    # convert Date and Time column to datetime objects
    df["datetime"] = pd.to_datetime(df["datetime"])

    # set the index to the Date and Time column
    df = df.set_index("datetime")

    # convert the amount column to float
    df["amount"] = df["amount"].replace(["\\$", "\\(", "\\)"], '', regex=True).astype(float)

    return df, account_balances


def summarize_user_transactions_df(df):
    user_transactions_summary = defaultdict(lambda: defaultdict(lambda: {"cumulative_spending": 0, "count": 0}))

    for index, row in df.iterrows():
        user_transactions_summary[row["account"]][row["device"]]["count"] += 1
        user_transactions_summary[row["account"]][row["device"]]["cumulative_spending"] = \
            round(user_transactions_summary[row["account"]][row["device"]]["cumulative_spending"] + row["amount"], 2)

    return user_transactions_summary


def get_timeseries_data_from_df(df):
    timeseries_data = defaultdict(list)
    cumulative_spending_data = defaultdict(int)

    # these are supposed to be datetimes, but not working
    timestamps = df.index.array
    earliest_timestamp = timestamps[0]
    latest_timestamp = timestamps[-1]

    for index, row in df.iterrows():
        cumulative_spending_data[row["account"]] = round(cumulative_spending_data[row["account"]] + row["amount"], 2)
        timeseries_data[row["account"]].append({"datetime": index, "amount": row["amount"],
                                                "cumulative_spending": cumulative_spending_data[row["account"]]})

    # add beginning and ending transactions to make the datetimes align
    for key, value in timeseries_data.items():
        if timeseries_data[key][0]["datetime"] != earliest_timestamp:
            timeseries_data[key].insert(0, {"datetime": earliest_timestamp, "amount": 0,
                                            "cumulative_spending": 0})

        if timeseries_data[key][-1]["datetime"] != latest_timestamp:
            timeseries_data[key].append({"datetime": latest_timestamp, "amount": 0,
                                         "cumulative_spending": cumulative_spending_data[key]})

    return timeseries_data
