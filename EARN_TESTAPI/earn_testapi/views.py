__author__ = 'Phil Jay'

from pyramid.response import Response
from pyramid.view import view_config
from cornice import Service
from sqlalchemy.exc import DBAPIError
from lxml import etree
import datetime
import collections
import io
from sqlalchemy import desc

from .models import (
    DBSession,
    Institutions,
    Addresses,
    Keys,
    Credentials,
    Logins,
    Accounts,
    Transactions,
    CustomerAccounts,
    )

# Using Pyramid Framework to test initializations

@view_config(route_name='home', renderer='templates/mytemplate.pt')
def my_view(request):
    try:
        one = DBSession.query(Institutions).all()
    except DBAPIError:
        return Response(conn_err_msg, content_type='text/plain', status_int=404)
    return {'one': one, 'project': 'EARN_TESTAPI'}

# Using Cornice Framework

def _addtoData(root, table):
    """ Iterates through requested xml file and adds values to _data dict.

    """
    _data = {}
    for column in table.__table__.columns._data.keys():
        expr = "//*[local-name() = '%s']" % column
        col = root.xpath(expr)
        if len(col) > 1 and column != "status":
            return Response(status_code=400, body="Found multiple values for one column.\n")
        if column == "status":
            if col[0].getparent().tag == "Institution":
                _data[column] = col[0].text
        if col and column not in [ "status", "institutionId" ]:
            _data[column] = col[0].text
    return _data

all_institutions = Service(name='all_institutions', path='/institutions')

@all_institutions.post(content_type="application/xml")
def add_institution(request):
    """This call adds an institution to the list of institutions
    """
    root = etree.parse(io.BytesIO(request.body))
    _data = _addtoData(root, Institutions)
    if len(_data) == 0:
        return Response(status_code=400, body="Empty request\n")
    columns = tuple([col for col in _data.keys()])
    values = tuple([val for val in _data.values()])
    clause = "insert into institutions %s values %s" % (str(columns).replace("'", ""), str(values))
    DBSession.execute(clause)
    DBSession.execute("commit")
    _data.clear()

    # Adding address
    this_institutionId = DBSession.query(Institutions).order_by(desc(Institutions.institutionId)).first().institutionId
    _data = _addtoData(root, Addresses)
    if len(_data) != 0:
        columns = tuple([col for col in _data.keys()]) + ('institutionId',)
        values = tuple([val for val in _data.values()]) + (int(this_institutionId),)
        clause = "insert into addresses %s values %s" % (str(columns).replace("'", ""), str(values))
        DBSession.execute(clause)
        DBSession.execute("commit")
    _data.clear()

    # Adding key
    expr = "//*[local-name() = 'key']"
    keys = root.xpath(expr)
    
    if len(keys) != 0:
        for key in keys:
            for child in key.getchildren():
                if child.tag in Keys.__table__.columns._data.keys():
                    _data[child.tag] = child.text
            if len(_data) != 0:
                columns = tuple([col for col in _data.keys()]) + ('institutionId',)
                values = tuple([val for val in _data.values()]) + (int(this_institutionId),)
                clause = "insert into inst_keys %s values %s" % (str(columns).replace("'", ""), str(values))
                DBSession.execute(clause)
                DBSession.execute("commit")  
                _data.clear()
   
    # Return the generated institution ID
    response = etree.Element("Institution_ID")
    response.text = str(this_institutionId)

    return Response(status_code=200, body=etree.tostring(response)+"\n")

@all_institutions.get()
def get_institutions(request):
    """This call returns a list of institutions supported for data acquisition.

    """
    if len(DBSession.query(Institutions).all()) == 0:
        return Response(status_code=200, body='')
    inst_body = etree.Element("Institutions")
    for institution in DBSession.query(Institutions).order_by(Institutions.institutionId):
        INST = etree.SubElement(inst_body, "institution")
        if institution.institutionId is not None:
            INST_ID = etree.SubElement(INST, "institutionId")
            INST_ID.text = str(institution.institutionId)
        if institution.institutionName is not None:
            INST_NAME = etree.SubElement(INST, "institutionName")
            INST_NAME.text = institution.institutionName
        if institution.homeUrl is not None:
            HOME_URL = etree.SubElement(INST, "homeUrl")
            HOME_URL.text = institution.homeUrl
        if institution.phoneNumber is not None:
            PHONE = etree.SubElement(INST, "phoneNumber")
            PHONE.text = str(institution.phoneNumber).zfill(10)
        if institution.virtual is not None:
            VIRTUAL = etree.SubElement(INST, "virtual")
            VIRTUAL.text = str(True).lower() if (institution.virtual == 1) else str(False).lower()
    return Response(status_code=200, body=etree.tostring(inst_body, pretty_print=True))

def check_query(table, param, keys=False, creds=False, accounts=False):
    """ Checks the query given parameter and table to determine if it's empty

    :param table: Table name
    :param param: institutionId or LoginId
    :param keys: Designated for table inst_keys
    :param creds: Designated for table user_credentials
    :param accounts: Designated for table accounts
    :return: "" if not empty, else a non-empty err_msg
    """
    err_msg = ""
    try:
        if accounts:
            try_query = DBSession.query(table).filter_by(institutionLoginId = int(param))
        else:
            try_query = DBSession.query(table).filter_by(institutionId = int(param))
        try_inst = try_query.all()
        if len(try_inst) == 0:
            raise Exception("ID NOT FOUND")
    except Exception:
        if keys:
            err_msg = "Keys were not found for Institution ID.\n"
        elif creds:
            err_msg = "Credentials were not found for Institution ID.\n"
        elif accounts:
            err_msg = "Accounts were not found for Institution ID.\n"
        else:
            err_msg = "Given Institution ID was not found.\n"
    except ValueError:
        err_msg = "Give Institution ID was not an integer.\n"
    return err_msg

institution_details = Service(name='institution_details', path='/institutions/{institution_id}')

@institution_details.get()
def get_inst_details(request):
    """ This call returns detailed information for the supplied institution ID

    """
    inst_id = request.matchdict['institution_id']
    err_msg = "" + check_query(Institutions, inst_id)
    if err_msg != "":
        return Response(status_code=404, body=err_msg)
    inst_query = DBSession.query(Institutions).filter_by(institutionId = int(inst_id))
    institution = inst_query.first()
    inst_body = etree.Element("InstitutionDetail")
    for column in institution.__table__.columns:
        value = getattr(institution, column.name)
        if value != None and column.name not in ["emailAddress, specialText", "currencyCode"]:
            label = etree.SubElement(inst_body, column.name)
            if column.name == "phoneNumber":
                label.text = str(value).zfill(10)
            elif column.name == "virtual":
                label.text = str(True).lower() if (value == 1) else str(False).lower()
            else:
                label.text = str(value)
    address_query = DBSession.query(Addresses).filter_by(institutionId = int(inst_id))
    num = address_query.all()
    if len(num) != 0:
        address = address_query.first()
        address_body = etree.SubElement(inst_body, "address")
        no_address = True
        for column in address.__table__.columns:
            value = getattr(address, column.name)
            if value != None and column.name != "institutionId":
                label = etree.SubElement(address_body, column.name)
                label.text = str(value)
                no_address = False
        if no_address:
            inst_body.remove(address_body)
    for column in institution.__table__.columns:
        value = getattr(institution, column.name)
        if value != None and column.name in ["emailAddress, specialText", "currencyCode"]:
            label = etree.SubElement(inst_body, column.name)
            if column.name == "currencyCode":
                label.text = str(value).upper()
            else:
                label.text = str(value)
    key_query = DBSession.query(Keys).filter_by(institutionId = int(inst_id)).order_by(Keys.displayOrder)
    if len(key_query.all()) == 0:
        return Response(status_code=200, body=etree.tostring(inst_body, pretty_print=True))
    keys_body = etree.SubElement(inst_body, "keys")
    no_keys = True
    for key in key_query:
        key_body = etree.SubElement(keys_body, "key")
        no_key = True
        for column in key.__table__.columns:
            value = getattr(key, column.name)
            if value != None and column.name != "institutionId" and column.name != "id":
                label = etree.SubElement(key_body, column.name)
                if column.name == "displayFlag":
                    label.text = str(True).lower() if (value == 1) else str(False).lower()
                else:
                    label.text = str(value)
                no_key = False
        if no_key:
            keys_body.remove(key_body)
        else:
            no_keys = False
    if no_keys:
        inst_body.remove(keys_body)
    return Response(status_code=200, body=etree.tostring(inst_body, pretty_print=True))


institution_login = Service(name='Add Login', path='/institutions/{institution_id}/login')

@institution_login.post(content_type="application/xml")
def add_login_credentials(request):
    """ This call adds a login ID and assigns the given credentials to it.
    """
    inst_id = request.matchdict['institution_id']
    
    # Add a login ID
    clause = "insert into logins (institutionId) values (%d)" % int(inst_id)
    DBSession.execute(clause)
    DBSession.execute("commit")
    this_loginId = DBSession.query(Logins).order_by(desc(Logins.loginId)).first().loginId
    
    # Add credentials
    required_creds = [key.name for key in DBSession.query(Keys).filter_by(institutionId = int(inst_id)).order_by(Keys.displayOrder)]
    root = etree.parse(io.BytesIO(request.body))
    expr = "//*[local-name() = 'credential']"
    creds = root.xpath(expr)
    if len(creds) != len(required_creds):
        return Response(status_code=400, body="Badly formed request.\n")
    _data = {}
    for cred in creds:
        for child in cred.getchildren():
            if child.tag == "name":
                if child.text not in required_creds:
                    return Response(status_code=400, body="Badly formed request. Given fields do not match required keys\n")
            _data[child.tag] = child.text
        columns = tuple([col for col in _data.keys()]) + ('institutionId', 'institutionLoginId')
        values = tuple([val for val in _data.values()]) + (int(inst_id), int(this_loginId))
        clause = "insert into user_credentials %s values %s" %(str(columns).replace("'", ""), str(values))
        DBSession.execute(clause)
        _data.clear()
    DBSession.execute("commit")
    
    # returns an auto-generated login ID
    response = etree.Element("Login_ID")
    response.text = str(this_loginId)

    return Response(status_code=200, body=etree.tostring(response)+"\n")

def create_accounts_tree(value=None, id=False, cid=None):
    """ Creates a etree of accounts filtered by login ID

    :param value: Value at the login ID
    :return: a tree that has not been formatted to a string
    """
    accountList = etree.Element("AccountList")
    if value == None:
        accounts_query = DBSession.query(Accounts)
    elif id:
        accounts_query = DBSession.query(Accounts).filter_by(accountId = value)
    elif cid:
        cust_accts = [i.accountId for i in DBSession.query(CustomerAccounts).filter_by(customerId = cid).all()]
        accounts_query = DBSession.query(Accounts).filter(Accounts.accountId.in_(cust_accts))
    else:
        accounts_query = DBSession.query(Accounts).filter_by(institutionLoginId = value)
    for account in accounts_query:
         account_body = etree.SubElement(accountList, "BankingAccount")
         for column in account.__table__.columns:
             val= getattr(account, column.name)
             if val != None:
                 label = etree.SubElement(account_body, column.name)
                 label.text = str(val)
    return accountList

discover_and_add = Service(name='discoverAndAddAccounts', path='/{customer_id}/institutions/{institution_id}/logins')

@discover_and_add.post(content_type="application/xml", accept="text/html")
def discover_add_accounts(request):
    """ This call discovers a user's accounts at an external Financial Institution
    and adds them to the system.

    Unique key like "Username" must be the first in displayOrder
    """
    input_creds = {}
    root = etree.parse(io.BytesIO(request.body))
    expr = "//*[local-name() = 'name']"
    names = root.xpath(expr)
    expr = "//*[local-name() = 'value']"
    values = root.xpath(expr)
    if len(names) != len(values):
        return Response(status_code=400, body="Did not format XML file correctly. Could not find element.\n")
    for i in range(len(names)):
        try:
            input_creds[names[i].text] = values[i].text
        except AttributeError:
            return Response(status_code=400, body="Did not format XML file correctly. Could not find element.\n")
    inst_id = request.matchdict['institution_id']
    err_msg = check_query(Keys, inst_id, True)
    if err_msg != "":
        return Response(status_code=404, body=err_msg)
    key_query = DBSession.query(Keys).filter_by(institutionId = inst_id).order_by(Keys.displayOrder)
    inst_keys = []
    for key in key_query:
        inst_keys.append(key.name)
    try:
        if collections.Counter(inst_keys) != collections.Counter(list(input_creds.keys())):
            raise Exception("Does not match keys!")
    except Exception:
        try:
            return Response(status_code=401, body="Given credential fields do not match required keys.\n")
        except TypeError:
            return Response(status_code=401, body="Given credential fields do not match required keys.\n")
    err_msg = check_query(Credentials, inst_id, False, True)
    if err_msg != "":
        return Response(status_code=404, body=err_msg)
    unique_key = input_creds[inst_keys[0]] #unique_key = demo, inst_keys[0] = Username
    try:
        user_identifier = DBSession.query(Credentials).filter_by(institutionId = inst_id).\
            filter_by(name = inst_keys[0]).filter_by(value = unique_key).first().institutionLoginId
    except:
        err_msg = inst_keys[0] + " " + unique_key + " was not found. Try again. "
        return Response(status_code=401, body=err_msg)
    creds_query = DBSession.query(Credentials).filter_by(institutionId = inst_id).\
        filter_by(institutionLoginId = user_identifier)
    validation = True
    for cred in creds_query:
        if input_creds[cred.name] != cred.value:
            validation = False
    if not validation:
        return Response(status_code=401, body="VALIDATION HAS FAILED\n")
    err_msg = check_query(Accounts, user_identifier, False, False, True)
    if err_msg != "":
        return Response(status_code=201, body='')
    customer_id = int(request.matchdict['customer_id'])
    accounts_added = DBSession.query(Accounts.accountId).filter_by(institutionLoginId = user_identifier).all()
    for i in accounts_added:
	try:
	    clause= "insert into customer_accounts (customerId, accountId) values (%d,%d)" % (customer_id, int(i[0]))
	    DBSession.execute(clause)
	    DBSession.execute("commit")
	except:
      	    pass
    
    response = create_accounts_tree(user_identifier)
    return Response(status_code=201, body=etree.tostring(response, pretty_print=True))

customer_accounts = Service(name='Customer Accounts', path='/{customer_id}/accounts')

@customer_accounts.get()
def get_accounts(request):
    """ This call returns a list of all accounts belonging to the authenticated
    user making the call.

    """
    customer_id = request.matchdict['customer_id']
    accounts_query = DBSession.query(CustomerAccounts).filter_by(customerId = customer_id).all()
    if len(accounts_query) == 0:
        return Response(status_code=200, body="")
    response = create_accounts_tree(False,False,cid=customer_id)
    return Response(status_code=200, body=etree.tostring(response, pretty_print=True))

login_accounts = Service(name='Login Accounts', path='/logins/{login_id}/accounts')

@login_accounts.post()
def add_account(request):
    """ Adds an account to a list of accounts.
    """
    login_id = request.matchdict['login_id']
    login_query = DBSession.query(Logins).filter_by(loginId = login_id)
    if len(login_query.all()) == 0:
        return Response(status_code=404, body="Login ID not found\n")
    institution_id = login_query.first().institutionId
    root = etree.parse(io.BytesIO(request.body))
    _data = {}
    for column in Accounts.__table__.columns._data.keys():
        expr = "//*[local-name() = '%s']" % column
        col = root.xpath(expr)
        if len(col) > 1:
            return Response(status_code=400, body="Found multiple values for one column.\n")
        if col and column not in ["institutionId", "institutionLoginId", "accountId"]:
            _data[column] = col[0].text
    columns = tuple([col for col in _data.keys()]) + ('institutionId', 'institutionLoginId')
    values = tuple([val for val in _data.values()]) + (int(institution_id), int(login_id))
    clause = "insert into accounts %s values %s" % (str(columns).replace("'", ""), str(values))
    DBSession.execute(clause)
    DBSession.execute("commit")
    _data.clear()

    # Returns an auto-generated account_id
    this_accountId = DBSession.query(Accounts).order_by(desc(Accounts.accountId)).first().accountId
    response = etree.Element("Account_ID")
    response.text = str(this_accountId)

    return Response(status_code=200, body=etree.tostring(response)+"\n")

@login_accounts.get()
def get_login_accounts(request):
    """ This call returns a list of all accounts belonging to the Login_ID provided in the URI path.
    (Ex. Accounts belonging to just Chase or Bank Of America)

    """
    login_id = request.matchdict['login_id']
    try_logins = DBSession.query(Logins).filter_by(loginId = login_id).all()
    if len(try_logins) == 0:
        return Response(status_code=404, body="Login not found!\n")
    err_msg = check_query(Accounts, login_id, False, False, True)
    if err_msg != "":
        return Response(status_code=200, body="")
    response = create_accounts_tree(login_id)
    return Response(status_code=200, body=etree.tostring(response, pretty_print=True))

customer_account = Service(name='Customer Account', path='/accounts/{account_id}')

@customer_account.get()
def get_account(request):
    """ This call returns all information about the account.

    """
    ac_id = request.matchdict['account_id']
    try:
        try_query = DBSession.query(Accounts).filter_by(accountId = ac_id).all()
        if len(try_query) == 0:
            raise Exception ("No Account Found")
    except Exception:
        return Response(status_code=404, body='No account with this ID was found!\n')
    response = create_accounts_tree(ac_id, True)
    return Response(status_code=200, body=etree.tostring(response, pretty_print=True))

transactions = Service(name='Transactions', path='/accounts/{account_id}/transactions')

@transactions.post()
def add_transaction(request):
    """ Adds a transaction to a list of transactions.
    """
    ac_id = request.matchdict['account_id']
    try:
        try_query = DBSession.query(Accounts).filter_by(accountId = int(ac_id)).all()
        if len(try_query) == 0:
            raise Exception ("No account found!")
    except Exception:
        return Response(status_code=404, body='No account with this ID was found!\n')
    root = etree.parse(io.BytesIO(request.body))
    _data = {}
    for column in Transactions.__table__.columns._data.keys():
        expr = "//*[local-name() = '%s']" % column
        col = root.xpath(expr)
        if len(col) > 1:
            return Response(status_code=400, body="Found multiple values for one column.\n")
        if col and column not in ["id", "accountId"]:
            _data[column] = col[0].text
    columns = tuple([col for col in _data.keys()]) + ('accountId',)
    if "postedDate" not in columns:
        return Response(status_code=400, body='Must have a posted date!\n')
    values = tuple([val for val in _data.values()]) + (int(ac_id),)
    clause = "insert into transactions %s values %s" % (str(columns).replace("'", ""), str(values))
    DBSession.execute(clause)
    DBSession.execute("commit")
    _data.clear()
    
    # Returns an auto-generated transaction ID
    trans_id = DBSession.query(Transactions).order_by(desc(Transactions.id)).first().id
    response = etree.Element("Transaction_ID")
    response.text = str(trans_id)

    return Response(status_code=200, body=etree.tostring(response)+"\n")

@transactions.get()
def get_transactions(request):
    """This call retrieves all transactions for an account over the specified date range.

    """
    ac_id = request.matchdict['account_id']
    try:
        try_query = DBSession.query(Accounts).filter_by(accountId = ac_id).all()
        if len(try_query) == 0:
            raise Exception ("No Account Found")
    except Exception:
        return Response(status_code=404, body='Account ID not found!\n')
    account_id = request.matchdict['account_id']
    request_dates = request.params
    txnStartDate, txnEndDate = "", ""
    try:
        txnStartDate = request_dates['txnStartDate']
        txnStartDate = datetime.datetime.strptime(txnStartDate, "%Y-%m-%d")
    except KeyError:
        return Response(status_code=400, body='No start date found!\n')
    except ValueError:
        return Response(status_code=400, body='Start date is not formatted correctly\n')
    try:
        txnEndDate = request_dates['txnEndDate']
        if txnEndDate != "":
            txnEndDate = datetime.datetime.strptime(txnEndDate, "%Y-%m-%d")
    except KeyError:
        pass
    except ValueError:
        return Response(status_code=400, body='End date is not formatted correctly\n')
    trans = DBSession.query(Transactions).filter_by(accountId = account_id)
    if len(trans.all()) == 0:
        return Response(status_code=200, body='')
    trans_body = etree.Element("TransactionList")
    matched = False
    for tran in trans:
        if (getattr(tran, 'postedDate')) >= txnStartDate:
            if (txnEndDate == "") or (txnEndDate != "" and getattr(tran, 'postedDate') <= txnEndDate):
                tran_body = etree.SubElement(trans_body, "Transaction")
                matched = True
                for column in tran.__table__.columns:
                    value = getattr(tran, column.name)
                    if value != None and column.name != "accountId":
                        label = etree.SubElement(tran_body, column.name)
                        if column.name == "originalCurrency" or column.name == "pending":
                            label.text = str(True).lower() if (value == 1) else str(False).lower()
                        else:
                            label.text = str(value)
    if not matched:
        return Response(status_code=200, body="No transactions within requested dates were found!\n")
    return Response(status_code=200, body=etree.tostring(trans_body, pretty_print=True))

update_login = Service('Update Login', path='/logins/{login_id}')

@update_login.put(content_type="application/xml", accept="text/html")
def update_login_info(request):
    """ This call is used to update the credentials (usually the password) associated with a login.

    """
    input_creds = {}
    root = etree.parse(io.BytesIO(request.body))
    expr = "//*[local-name() = 'name']"    
    names = root.xpath(expr)
    expr = "//*[local-name() = 'value']"
    values = root.xpath(expr)
    if len(names) != len(values):
        return Response(status_code=400, body="Did not format XML file correctly. Could not find element.\n")
    for i in range(len(names)):
        try:
            input_creds[names[i].text] = values[i].text
        except AttributeError:
            return Response(status_code=400, body="Did not format XML file correctly. Could not find element.\n")
    login_id = request.matchdict['login_id']
    err_msg = check_query(Credentials, login_id, False, True, True)
    if err_msg != "":
        return Response(status_code=404, body=err_msg)
    institution_identifier = DBSession.query(Credentials).filter_by(institutionLoginId = int(login_id)).\
        first().institutionId
    key_query = DBSession.query(Keys).filter_by(institutionId = int(institution_identifier))
    names = [getattr(key, "name") for key in key_query]
    validated = True
    for name in input_creds.keys():
        if name not in names:
            validated = False
    if not validated:
        return Response(status_code=404, body='Given wrong credential name(s) for this institution\n')
    for cred in input_creds.keys():
        cred_query = DBSession.query(Credentials).filter_by(institutionLoginId = int(login_id))\
            .filter_by(name = cred)
        if len(cred_query.all()) == 0:
            return Response(status_code=404, body='Given wrong credential name for this id. Does not " \
                                                            "exist in User_Credentials table\n')
        cred_query.update({"value" : input_creds[cred]})
    return Response(status_code=200)

@customer_account.put(content_type="application/xml", accept="text/html")
def update_account_type(request):
    """ This call is used to set the account type for an account where its type could not be determined
    during discovery or refresh.

    """
    account_id = request.matchdict['account_id']
    try:
        try_query = DBSession.query(Accounts).filter_by(accountId = int(account_id))
        if len(try_query.all()) == 0:
            raise Exception("ID NOT FOUND")
    except Exception:
        return Response(status_code=404, body='Account ID not found\n')
    account = DBSession.query(Accounts).filter_by(accountId = int(account_id))
    if account.first().bankingAccountType != None:
        return Response(status_code=403, body='Changing between concrete account types is not supported\n')
    try:
        root = etree.fromstring(request.body)
        accountType = (root.getchildren()[0].text).upper()
    except:
        return Response(status_code=400, body='Did not format XML file correctly. Could not find element.\n')
    try:
        account.update({"bankingAccountType" : accountType})
    except:
        return Response(status_code=400, body='Given account type is not one of the possible banking account types!\n')
    return Response(status_code=200)

delete_account = Service(name='deleteAccount', path='/{customer_id}/accounts/{account_id}')
def delete_account(request):
    """This call is used to delete a user's account.

    """
    account_id = request.matchdict['account_id']
    try:
        try_query = DBSession.query(CustomerAccounts).filter_by(accountId = int(account_id))
        if len(try_query.all()) == 0:
            raise Exception("ID NOT FOUND")
    except Exception:
        return Response(status_code=404, body='Account ID not found\n')
    transactions = DBSession.query(Transactions).filter_by(accountId = account_id)
    if (len(transactions.all())) != 0:
        transactions.delete()
    DBSession.query(CustomerAccounts).filter_by(accountId = int(account_id)).delete()
    return Response(status_code=200)

conn_err_msg = """\
Pyramid is having a problem using your SQL database.  The problem
might be caused by one of the following things:

1.  You may need to run the "initialize_EARN_TESTAPI_db" script
    to initialize your database tables.  Check your virtual
    environment's "bin" directory for this script and try to run it.

2.  Your database server may not be running.  Check that the
    database server referred to by the "sqlalchemy.url" setting in
    your "development.ini" file is running.

After you fix the problem, please restart the Pyramid application to
try it again.
"""
