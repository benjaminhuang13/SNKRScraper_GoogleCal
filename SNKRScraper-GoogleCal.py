from math import prod
import os
import requests
from requests import HTTPError, get
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
#calendar
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from datetime import datetime
from datetime import date
from pytz import timezone
from apscheduler.schedulers.background import BackgroundScheduler

class SnkrProd:
    def __init__(self, name, style, prodSKU, month, day, retailPrice, prodURL):
        self.name = name
        self.style = style
        self.prodSKU = prodSKU
        self.month = month
        self.day = day
        self.retailPrice = retailPrice
        self.prodURL = prodURL
stockx_url = 'https://stockx.com/search?s='
#headers are needed for the get request to get a RESPONSE 200 instead of RESPONSE 403, you will need to get your own cookies from Inspect I > Application > cookies
headers = {
    'User-Agent': 
     'you can get this from browser\'s inspect (crtl + shift + i) > Network tab',
    'accept': 'you can get this from browser\'s inspect (crtl + shift + i) > Network tab ',
    'cookie': 'you can get a cookie by going onto stockX.com and then browser\'s inspect (crtl + shift + i) > Application tab > cookies'
}
#method for converting list into dictionary
def convertToDict(list):
    res_dct = {list[i]: list[i + 1] for i in range(0, len(list), 2)}
    return res_dct
#gets and processes data from SNKR website
snkr_url = 'https://www.nike.com/launch?s=upcoming'
content = requests.get(snkr_url)
soup = BeautifulSoup(content.text, 'html.parser')
prodList = []
print("fetching...", end = '')
try:
    gridOfProducts = soup.find('section', {'class': 'upcoming-section bg-white ncss-row prl2-md prl5-lg pb4-md pb6-lg'})
    for product in gridOfProducts.find_all('div', {'class': 'product-card ncss-row mr0-sm ml0-sm'}):
        print(".", end = '')
        prodMonth = product.find('p', {'data-qa': 'test-startDate'}).text.strip()
        prodDay = product.find('p', {'data-qa': 'test-day'}).text.strip()
        prodName = product.find('h3', {'class': 'headline-5'}).text.strip()
        prodStyle = product.find('h6', {'class': 'headline-3'}).text.strip()
        prodURL = "https://www.nike.com/"+ product.find('a', {'data-qa': 'product-card-link'}).get('href')
        # Gets retail price
        prodContent = requests.get(prodURL)
        prodSoup = BeautifulSoup(prodContent.text, 'html.parser')
        retailPrice = prodSoup.find('div', {'class': 'headline-5'}).text.strip()
        prodSKU = prodSoup.find('p').text.strip()
        prodSKU = prodSKU.rpartition('SKU')[2][2:(len(prodSKU))]
        excludeProd = ["Tees", "Apparel", "Accessories", "Bottoms", "Outerwear", "Brand"]
        if not any(word in prodStyle for word in excludeProd):
            prodList.append(SnkrProd(prodName, prodStyle, prodSKU, prodMonth, prodDay, retailPrice, prodURL))
except AttributeError as error:
    print('An error occurred: %s' % error+ ". Probably requested from this website too many times too quickly")
print()
# Iterate through each product from SNKR 
for productX in prodList:
    stockxContent = requests.get(stockx_url + productX.prodSKU, headers=headers)
    stockxSoup = BeautifulSoup(stockxContent.text, 'html.parser')
    stockxProd = stockxSoup.find('div', {'class': 'css-1ibvugw-GridProductTileContainer'})
    stockxLink = "https://stockx.com" + stockxProd.find('a').get("href")
    # finds all the scripts and only takes the 12th one that contains information we want and cleans data
    sXScriptSoup = str(stockxSoup.findAll('script'))
    sXScriptSoup = sXScriptSoup[sXScriptSoup.find('window.preLoadedBrowseProps'):(sXScriptSoup.find("selling_countries"))]
    imageUrlIndex = sXScriptSoup.find("imageUrl")
    imageUrlIndexEnd = sXScriptSoup.find("jpg?")
    sXimageURL = (sXScriptSoup[imageUrlIndex-1:imageUrlIndexEnd+4:1].replace("\"", ""))
    lowestAskIndex = sXScriptSoup.find("lowestAsk")
    changePercentageIndex = sXScriptSoup.find("changePercentage")
    # Array of products details prices and cleans out empty elements
    productDetails = sXScriptSoup[lowestAskIndex:changePercentageIndex:1].replace("\"", "").split(',')
    for x in productDetails:
        if x == "":
            productDetails.remove(x)
    # Creates dictionary for product details
    prodDetailDict = []
    for i in productDetails:
        start = i.find(":")
        prodDetailDict.append(i[:start])
        prodDetailDict.append(i[start+1:])
    detailDict = convertToDict(prodDetailDict)
    # Goes through each products and compare retail to highest bid and last sale prices to see if profitable
    listOfDetails = ["highestBid", "lastSale"]

    if not (float(detailDict["highestBid"]) < int(retailPrice[1:])*1.20 or float(detailDict["lastSale"]) < int(retailPrice[1:])*1.20):
        eventDesc = productX.name + ' ' + productX.style + " -----DROPS: "+ productX.month + " " + productX.day + " ----RETAIL: " + productX.retailPrice + "\n\t" + productX.prodURL + "\n\t" + stockxLink
        print(eventDesc)
        for x in productDetails:
            if any(word in x for word in listOfDetails):
                print("\t" + x)   
                eventDesc = eventDesc + "\n\t" + x + ", "
        month_name = productX.month

        datetime_object = datetime.strptime(month_name, "%b")
        month_number = datetime_object.month
        strt_date_time_str = str(date.today().year) + "-"+ str(month_number) + "-" + str(productX.day) + "T10:00:00-04" #-04 is the timezone difference
        end_date_time_str = str(date.today().year) + "-" + str(month_number) + "-" + str(productX.day) + "T10:05:00-04"

        #create calendar event
        event = {
            'summary': 'SNKR ' + productX.name,
            'location': '',
            'description': eventDesc,
            'start': {
                'dateTime': strt_date_time_str,
                'timeZone': 'America/New_York',
            },
            'end': {
                'dateTime': end_date_time_str,
                'timeZone': 'America/New_York',
            },
            'attendees': [
                {'email': 'email1@gmail.com'},
                {'email': 'email2@gmail.com'},
                {'email': 'email3@gmail.com'},
                {'email': 'email4@gmail.com'},
            ],
            'reminders': {
                'useDefault': True,
            },
        }
        SCOPES = 'https://www.googleapis.com/auth/calendar'
        creds = None
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
                
        #Search through next 50 events in the calendar and add any events that are not there yet
        try:
            service = build('calendar', 'v3', credentials=creds)
            tz = timezone('EST')
            now = datetime.now(tz).replace(hour=0).isoformat()
            events_result = service.events().list(calendarId='primary', timeMin=now,
            maxResults=50, singleEvents=True,orderBy='startTime').execute()
            eventsearch = events_result.get('items', [])
            listOfSummary = []
            for x in eventsearch:       
                listOfSummary.append(x["summary"][5:])
            if not productX.name in listOfSummary:
                event = service.events().insert(calendarId='primary', body=event).execute()
                print('Event created: %s' % (event.get('htmlLink')))
        except HTTPError as error:
            print('An error occurred: %s' % error)
    else:
        print(productX.name + " NO PROFIT!\t" + stockxLink)


