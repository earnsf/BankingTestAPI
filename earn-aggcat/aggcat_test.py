__author__ = 'Phil Jay'

from aggcat import AggcatClient

# Create client.
client = AggcatClient(1000)

# Get all institutions
institutions = client.get_institutions()
print ("Number of institutions: %s" % str(len(institutions.content)))
print ("----------------------------------------------------------------------------------")

# Get the institution details for Victor's Bank (no keys)
victors_id = 2
victorsbank = client.get_institution_details(2)
print ("Institution name: %s" % victorsbank.content.institution_name)
print ("----------------------------------------------------------------------------------")

# Get the institution details for Phil's Bank (with keys)
phils_id = 1
try:
	philsbank = client.get_institution_details(phils_id)
except (RuntimeError, TypeError, NameError, IndexError):
	print ("Ran into error when trying to get institution details")
	pass
finally:
	print ("Institution name: %s" % philsbank.content.institution_name)
	print ("Phil's Banks's Required keys: %s" % str([key.name for key in philsbank.content.keys]))
	print ("----------------------------------------------------------------------------------")

# Get the credentials for Phil's Bank
phils_creds = client.get_credential_fields(phils_id)
print ("Phil's bank's detailed info of credentials: %s" % str(phils_creds))
print ("----------------------------------------------------------------------------------")

# Authenticate and add accounts for Phil's Bank
# Get a list of accounts for login_id 1
accountIds = []
r = client.discover_and_add_accounts(phils_id,
	**{'Username': 'a', 'Password': 'aPassword'})
try:
	accountIds = map(int, [acct.account_id for acct in r.content])
except TypeError:
	accountIds.append(r.content.BankingAccount.account_id)

print ("Account ID's for Login 1 : %s" % str(accountIds))
print ("----------------------------------------------------------------------------------")

# Should fail to authenticate
r = client.discover_and_add_accounts(phils_id,
	**{'Username': 'a', 'Password': 'wrongPASSWORD'})
print ("Wrong password should fail: %s" % str(r.status_code))
print ("----------------------------------------------------------------------------------")

# Get a list of transactions for all accounts under login_id 1
txns = []
for acct in accountIds:
		temp = client.get_account_transactions(acct, '2012-01-01', '2014-05-28')
		txns.extend([t for t in temp.content])
print ("Transactions for all accounts for login 1:")
for t in txns:
	try:
		print t.id, t.memo, t.posted_date, t.amount
	except AttributeError:
		pass
print ("----------------------------------------------------------------------------------")

# Update login info for login_id 2
r = client.update_institution_login(1, 2, **{'Username': 'b', 'Password': 'newPassword'})
print ("Successful login update: %d" % r.status_code)
r = client.update_institution_login(1, 2, **{'Username': 'b', 'Password': 'bPassword'})
print ("----------------------------------------------------------------------------------")

# Updating and Deleting may change data! Use for testing only.

"""
# Update account type for account 2 (should fail)
try:
	r = client.update_account_type(2, 'banking', 'savings')
except Exception, e:
	print e
# Update account type for account 1 (should pass) 
# Must account type to NULL for it to pass
print ('Trying for a different account...')
try:
	r = client.update_account_type(1, 'banking', 'savings')
	print ("Successful login update: %d" % r.status_code)
except Exception, e:
	print (e)
print ("----------------------------------------------------------------------------------")

# Delete account 10 (should fail)
try:
	r = client.delete_account(10)
except Exception, e:
	print e
# Delete account 1 (should pass)
# Must create account 1 again to pass
print ('Trying for a different account...')
try:
	r = client.delete_account(1)
	print ("Successful account delete: %d" % r.status_code)
except Exception, e:
	print e
print ("----------------------------------------------------------------------------------")
"""

print ("END")

