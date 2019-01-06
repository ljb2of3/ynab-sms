from twilio.rest import Client
import requests
import json


# Load config data
try:
	with open('settings.json', 'r') as f:
		settings = json.load(f)
except:
	print("Error loading settings. Verify that settings.json exists and contains valid json!")
	exit(-1)

flags = {}

for user in settings['users']:
	flags[user['flag']] = user['name']

# Load previous transactions
try:
	with open('known-transactions.json', 'r') as f:
		knownTransactions = json.load(f)
except:
	knownTransactions = []


# Load previous budget amounts
try:
	with open('budgeted-amounts.json', 'r') as f:
		budgetedAmounts = json.load(f)
except:
	budgetedAmounts = {}


def sendSMS(who, message):
	print('To: ' + who)
	print('  ' + message)
	print()

	twilio = Client(settings['twilio']['sid'], settings['twilio']['token'])
	twilio.messages.create(to=who, from_=settings['twilio']['number'], body=message)


def processTransaction(id, doc, balance):
	if id not in knownTransactions:
		knownTransactions.append(id)
		if doc['flag'] in flags and doc['outflow'] > 0:			
			for user in settings['users']:
				if user['flag'] not in doc['flag']:
					text = flags[doc['flag']] + ' spent $' + '{:01.2f}'.format(doc['outflow']) + ' @ ' + doc['payee'] + ' from ' + doc['category'] + '. $' + '{:01.2f}'.format(balance) + ' remaining. (' + doc['memo'] + ')'
					sendSMS(user['number'], text)


# Grab the current data from the YNAB API
headers = {
	'accept': 'application/json',
	'Authorization': 'Bearer ' + settings['ynab']['token']
}

ynabURL = 'https://api.youneedabudget.com/v1'
budgetURL = ynabURL + '/budgets/' + settings['ynab']['budget']

data = None

r = requests.get(budgetURL + '/transactions', headers=headers)
r.raise_for_status()
data = r.json()

transactions = data['data']['transactions']

# Get the Category list
r = requests.get(budgetURL + '/categories', headers=headers)
r.raise_for_status()
data = r.json()

categories = {}
for g in data['data']['category_groups']:
	for c in g['categories']:
		if c['id'] in budgetedAmounts:
			if c['budgeted'] != budgetedAmounts[c['id']]:				
				if c['budgeted'] > budgetedAmounts[c['id']]: 
					amount = (c['budgeted'] - budgetedAmounts[c['id']]) / 1000.0
					text = 'The amount budgeted for ' + c['name'] + ' has increased by $' + '{:01.2f}'.format(amount) + '. There is now $' + '{:01.2f}'.format(c['balance'] / 1000.0) + ' remaining.'
				else:
					amount = (budgetedAmounts[c['id']] - c['budgeted']) / 1000.0
					text = 'The amount budgeted for ' + c['name'] + ' has decreased by $' + '{:01.2f}'.format(amount) + '. There is now $' + '{:01.2f}'.format(c['balance'] / 1000.0) + ' remaining.'
				for user in settings['users']:
					sendSMS(user['number'], text)
		
		budgetedAmounts[c['id']] = c['budgeted']
		
		categories[c['id']] = {}
		categories[c['id']]['name'] = c['name']
		categories[c['id']]['balance'] = c['balance'] / 1000.0
		categories[c['id']]['budgeted'] = c['budgeted'] / 1000.0
		categories[c['id']]['group'] = g['name']

# Get the Payee list
r = requests.get(budgetURL + '/payees', headers=headers)
r.raise_for_status()
data = r.json()

payees = {}
for p in data['data']['payees']:
	payees[p['id']] = p['name']

# Process Transactions
for t in transactions:
	# Check to see if this is a split transaction
	if len(t['subtransactions']) > 0:
		for s in t['subtransactions']:
			id = s['id']			
			doc = {}
			doc['date'] = t['date']
			doc['amount'] = s['amount'] / 1000.0
			if doc['amount'] < 0:
				doc['outflow'] = doc['amount'] * -1
				doc['inflow'] = 0
			else:
				doc['outflow'] = 0
				doc['inflow'] = doc['amount']
			if s['memo'] is not None:
				doc['memo'] = s['memo']
			elif t['memo'] is not None:
				doc['memo'] = t['memo']
			else:
				doc['memo'] = ''
			doc['status'] = t['cleared']
			doc['approved'] = t['approved']
			doc['flag'] = t['flag_color']
			doc['account'] = t['account_name']
			if s['payee_id'] is not None:
				doc['payee'] = payees[s['payee_id']]
			elif t['payee_id'] is not None:
				doc['payee'] = payees[t['payee_id']]
			doc['category'] = None
			doc['group'] = None
			catBalance = None
			if s['category_id'] is not None:
				doc['category'] = categories[s['category_id']]['name']
				doc['group'] = categories[s['category_id']]['group']
				catBalance = categories[s['category_id']]['balance']
			elif t['category_id'] is not None:
				doc['category'] = categories[t['category_id']]['name']
				doc['group'] = categories[t['category_id']]['group']
				catBalance = categories[t['category_id']]['balance']            
			processTransaction(id, doc, catBalance)
	else:
		id = t['id']
		doc = {}
		doc['date'] = t['date']
		doc['amount'] = t['amount'] / 1000.0
		if doc['amount'] < 0:
			doc['outflow'] = doc['amount'] * -1
			doc['inflow'] = 0
		else:
			doc['outflow'] = 0
			doc['inflow'] = doc['amount']
		if t['memo'] is not None:
			doc['memo'] = t['memo']
		else:
			doc['memo'] = ''
		doc['status'] = t['cleared']
		doc['approved'] = t['approved']
		doc['flag'] = t['flag_color']
		doc['account'] = t['account_name']
		if t['payee_id'] is not None:
			doc['payee'] = payees[t['payee_id']]
		doc['category'] = None
		doc['group'] = None
		catBalance = None
		if t['category_id'] is not None:
			doc['category'] = categories[t['category_id']]['name']
			doc['group'] = categories[t['category_id']]['group']
			catBalance = categories[t['category_id']]['balance']
		processTransaction(id, doc, catBalance)

with open('known-transactions.json', 'w') as f:
	json.dump(knownTransactions, f, indent=4, sort_keys=True, ensure_ascii = False)

with open('budgeted-amounts.json', 'w') as f:
	json.dump(budgetedAmounts, f, indent=4, sort_keys=True, ensure_ascii = False)
