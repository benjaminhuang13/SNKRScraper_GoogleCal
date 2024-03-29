### Update 2022-07-17: SNKR website has been updated to include anti-scrapping properties and prevent the bot from scrapping for data.

# SNKRScraper-GoogleCal
Bot that scrapes SNKR.com's upcoming drops and searches for selling price data on stockX.com to determine if drops are worth re-selling. If a drop is found to be profitable, the bot will create a Google calendar invite using the Google calendar API. Beautifulsoup library is used to parse scraped data. Comments are left within the code to indicate where to fill in necessary data.

## "Security Feature" (Actually a bug):
- Sometimes when token expires, it needs to be deleted in order to run the program again and it will refresh the token.

## Results
![img of cal event](https://github.com/benjaminhuang13/SNKRScraper-GoogleCal/blob/main/google_cal_event.png?raw=true)
![img of cal event](https://github.com/benjaminhuang13/SNKRScraper-GoogleCal/blob/main/imageOfcmdOutput.png?raw=true)

## Resources:
https://developers.google.com/calendar/api/guides/overview
