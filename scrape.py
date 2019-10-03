#!/usr/bin/env python

import requests
import uncurl
from bs4 import BeautifulSoup
import urllib.parse
import csv
import pandas as pd
import matplotlib.pyplot as plt
import getpass

username = urllib.parse.quote(input("Username: "), safe='')
password = urllib.parse.quote(getpass.getpass(), safe='')

# clear output.csv file
open('output.csv', 'w').close()

session = requests.Session()

def get_uncurled(curl):
    return "session" + (uncurl.parse(curl))[8:]

# GET LOGIN PAGE -------------------------------------------------------------------------------------------------------------------------
uncurled = get_uncurled('''curl 'https://onecard.mcgill.ca/LogIn.aspx' -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:69.0) Gecko/20100101 Firefox/69.0' -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8' -H 'Accept-Language: en-US,en;q=0.5' --compressed -H 'DNT: 1' -H 'Connection: keep-alive' -H 'Upgrade-Insecure-Requests: 1' -H 'Cache-Control: max-age=0' ''')
exec("response = " + uncurled)


# get body parameters
soup = BeautifulSoup(response.text, "html.parser")

viewstate = urllib.parse.quote(soup.find(id="__VIEWSTATE")['value'], safe='')
generator = urllib.parse.quote(soup.find(id="__VIEWSTATEGENERATOR")['value'], safe='')
validation = urllib.parse.quote(soup.find(id="__EVENTVALIDATION")['value'], safe='')

# LOGIN WITH BODY PARAMETERS -------------------------------------------------------------------------------------------------------------------------
uncurled = get_uncurled('''curl 'https://onecard.mcgill.ca/LogIn.aspx' -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:69.0) Gecko/20100101 Firefox/69.0' -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8' -H 'Accept-Language: en-US,en;q=0.5' --compressed -H 'Content-Type: application/x-www-form-urlencoded' -H 'DNT: 1' -H 'Connection: keep-alive' -H 'Referer: https://onecard.mcgill.ca/LogIn.aspx' -H 'Upgrade-Insecure-Requests: 1' --data '__VIEWSTATE=''' + viewstate + '''&__VIEWSTATEGENERATOR=''' + generator + '''&__EVENTVALIDATION=''' + validation + '''&tbUserName=''' + username + '''&tbPassword=''' + password + '''&Button1=Log+In' ''')
exec("response = " + uncurled)


# GET FIRST TRANSACTIONS PAGE -------------------------------------------------------------------------------------------------------------------------
uncurled = "session" + (uncurl.parse('''curl 'https://onecard.mcgill.ca/Consumption.aspx' -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:69.0) Gecko/20100101 Firefox/69.0' -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8' -H 'Accept-Language: en-US,en;q=0.5' --compressed -H 'DNT: 1' -H 'Connection: keep-alive' -H 'Referer: https://onecard.mcgill.ca/Default.aspx' -H 'Upgrade-Insecure-Requests: 1' '''))[8:]
exec("response = " + uncurled)

# get body parameters
soup = BeautifulSoup(response.text, "html.parser")

viewstate = urllib.parse.quote(soup.find(id="__VIEWSTATE")['value'], safe='')
generator = urllib.parse.quote(soup.find(id="__VIEWSTATEGENERATOR")['value'], safe='')
validation = urllib.parse.quote(soup.find(id="__EVENTVALIDATION")['value'], safe='')

# write to csv
table = soup.find(id="cphConsumption_gvTransDetail")
output_rows = []
for i, table_row in enumerate(table.findAll('tr')):
    if i > 2 and i < (len(table.findAll('tr')) - 2):
        columns = table_row.findAll('td')
        output_row = []
        for column in columns:
            output_row.append(column.text)
        output_rows.append(output_row)
    
with open('output.csv', 'a') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerows(output_rows)

# check if there is next page
hasnext = ("Next" in response.text)

while (hasnext):

    uncurled = "session" + (uncurl.parse('''curl 'https://onecard.mcgill.ca/Consumption.aspx' -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:69.0) Gecko/20100101 Firefox/69.0' -H 'Accept: */*' -H 'Accept-Language: en-US,en;q=0.5' --compressed -H 'X-Requested-With: XMLHttpRequest' -H 'X-MicrosoftAjax: Delta=true' -H 'Cache-Control: no-cache' -H 'Content-Type: application/x-www-form-urlencoded; charset=utf-8' -H 'DNT: 1' -H 'Connection: keep-alive' -H 'Referer: https://onecard.mcgill.ca/Consumption.aspx' --data 'ctl00%24cphConsumption%24ScriptManager1=ctl00%24cphConsumption%24upDetails%7Cctl00%24cphConsumption%24gvTransDetail&__EVENTTARGET=ctl00%24cphConsumption%24gvTransDetail&__EVENTARGUMENT=Page%24Next&__VIEWSTATE=''' + viewstate + '''&__VIEWSTATEGENERATOR=''' + generator + '''&__EVENTVALIDATION=''' + validation + '''&__ASYNCPOST=true&' '''))[8:]
    exec("response = " + uncurled)

    soup = BeautifulSoup(response.text, "html.parser")
    starting = (soup.text[soup.text.index("__VIEWSTATE") + 12:])
    broken_up = (starting.split("|"))
    # print(starting[:starting.index("|")])
    viewstate = urllib.parse.quote(broken_up[0], safe='')
    generator = urllib.parse.quote(broken_up[4], safe='')
    validation = urllib.parse.quote(broken_up[8], safe='')

    table = soup.find(id="cphConsumption_gvTransDetail")

    output_rows = []
    for i, table_row in enumerate(table.findAll('tr')):
        if i > 2 and i < (len(table.findAll('tr')) - 2):
            columns = table_row.findAll('td')
            output_row = []
            for column in columns:
                output_row.append(column.text)
            output_rows.append(output_row)
        
    with open('output.csv', 'a') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(output_rows)

    hasnext = ("Next" in response.text)

df = pd.read_csv("output.csv", names=["Transaction Number", "Date and Time", "Amount", "Location", "Device", "Plan/Account"])

df = df.reindex(index=df.index[::-1])
df["Amount"] = df["Amount"].replace('\$', '', regex=True).astype(float)
df["Date and Time"] = pd.to_datetime(df["Date and Time"])
df["Cummulative Spending"] = df['Amount'].cumsum()

df.plot(x='Date and Time',y=['Cummulative Spending'])
plt.show()
