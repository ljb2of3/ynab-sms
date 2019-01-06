# Intro
Do you use YNAB with mutliple people? use `ynab-sms.py` to send text messages to other users of your budget to keep everyone in the loop! The script uses flag colors to identify who's transaction it is. For instance, I mark my transactions with a blue flag, and my wife marks hers with a purple flag. The script will also alert all users if a category's budgeted amount gets changed.
# Getting started
## Install Requirements
The script requires python 3. Install the required python packages with `pip install -r requirements.txt`
## Configure
Copy `settings.json.example` to `settings.json` and then modify with your settings. You'll need a Personal Access Token from your [YNAB Develop Settings](https://app.youneedabudget.com/settings/developer), and a [Twilio](https://www.twilio.com/sms) Programmable SMS account.
#### Sample Config
The configuration is broken up into three sections.

In the `ynab` section you'll need to fill in your budget ID, which can be found in the url bar when you're editing your budget: `https://app.youneedabudget.com/THIS IS YOUR BUDGET ID/budget`
```json
    "ynab": {
        "budget": "h1347489-2b23-6dcf-feb9-6204ba34a4fe",
        "token": "44b913a04a2f3c898d498a22b34a236205664ba97d68585446dcff6c04feb6"
    },
```
In the `twilio` section you'll need your Account SID, auth token, and your programmable sms number.
```json
    "twilio": {
        "sid": "ee5a1a322e6415d68cAC4fef0bf61899ed",
        "token": "5eb13d609b7edf2fd7b4c48ceef81923",
        "number": "+12135552560"
    },
```
Finally, in the `users` section add each person you want to get SMS alerts, and the flag color for the transactions they enter.
```json
    "users": [
        {            
            "name": "Alice",
            "number": "+16615557189",
            "flag": "purple"
        },
        {            
            "name": "Bob",
            "number": "+13235557167",
            "flag": "blue"
        }
    ]
}
```
## Run
Once configured, run `python3 ynab-sms.py` using cron or some other task scheduler as often as you want. Keep in mind the YNAB API call limits, which are currently 200 calls per hour.

# Improvements
Currently this script grabs all possible transactions. A future version should use the delta api instead. The payee list should be cached as well.