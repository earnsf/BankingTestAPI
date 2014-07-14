"""
File name   : intuit_wrapper.py
Author      : Ravichandra
Edited	    : Phil Jay Kwon 
Description : Functionality to access savers accounts and transaction data
              using EARN Test API
"""
# Import the required functions and modules
from aggcat import AggcatClient
from sqlalchemy import create_engine, MetaData, Table, and_,distinct
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import DBAPIError
from zope.sqlalchemy import ZopeTransactionExtension
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.orm import aliased
from sqlalchemy.sql import func
from ConfigParser import SafeConfigParser
from decimal import Decimal

import transaction
import datetime
import configuration
import sqlalchemy

# Create a database engine and session
DB_SESSION = scoped_session(sessionmaker(extension=\
ZopeTransactionExtension(), expire_on_commit=False))
BASE = declarative_base()
PARSER = SafeConfigParser()
PARSER.read(configuration.DEV_INI_FILE_PATH)
DB_URL = PARSER.get("app:main", "sqlalchemy.url")
ENGINE = create_engine(DB_URL, echo=False, pool_recycle=600)
DB_SESSION.configure(bind=ENGINE)
BASE.metadata.bind = ENGINE
METADATA = MetaData(bind=DB_SESSION.get_bind())


# TODO: Replace all print statements with logger
class User(BASE):
    __table__ = Table('users', METADATA, autoload=True)

class IntuitInstitution(BASE):
    """
    Description: Database table for Intuit transactions
    """
    __table__ = Table('intuit_institutions', METADATA, autoload=True)

class IntuitTransaction(BASE):
    """
    Description: Database table for Intuit transactions
    """
    __table__ = Table('intuit_transactions', METADATA, autoload=True)

class IntuitWrapper(object):
    """
    Description: Wrapper Class for Intuit API calls.
    """
    def __init__(self,user_id=None):
        # Create a client to connect to Intuit API
        self.client = AggcatClient(str(user_id))

    def get_institutions(self):
        """
        Description     : Get financial institution details.
        Input           : None.
        Output          : Financial institution details.
        """
        try:        
            return self.client.get_institutions().content
        except Exception as exn:
            print exn
            return False,exn

    def get_single_account(self,account_id=None):
        """
        Description : Get savings account details for the current customer.
        Input       : Account Id
        Output      : Various accounts linked to same institution.
        """
        try:
            return self.client.get_account(account_id).content
        except Exception as exn:
            print exn
            return False,exn

    def get_saver_transactions(self,account_id=None, txn_sdate=None, txn_edate=None):
        """
        Description : Get transaction details for an account linked to
                      an institution.
        Input       : Account Id, Transaction Start Date, Transaction End Date.
        Output      : Transactions for the selected period.
        """
        try:
            return self.client.get_account_transactions(account_id=account_id, \
                        start_date=txn_sdate, end_date=txn_edate).content
        except Exception as exn:
            print exn
            return False,exn

    def get_credential_fields(self,institution_id=None):
        """
        Description : Gets the credential fields for the institution
        Input       : Institution Id
        Output      : Credential fields
        """
        try:
            return self.client.get_credential_fields(institution_id=institution_id)
        except Exception as exn:
            print exn
            return False,exn

    def discover_and_add_accounts(self,institution_id=None, **credentials):
        """
        Description : Adds all the accounts associated with the login.
        Input       : Institution Id, Credentials
        Output      : All the accounts added.
        """
        try:
            return self.client.discover_and_add_accounts(institution_id,\
            **credentials).content
        except Exception as exn:
            print exn
            return False,exn

    def delete_account(self,account_id=None):
        """
        Description : Deletes an account given account id
        Input       : Account Id
        Output      : None
        """
        try:
            return self.client.delete_account(account_id)
        except Exception as exn:
            print exn
            return False,exn

    def get_customer_accounts(self):
        """
        Description : Get all the accounts linked to current Intuit customer 
        Input       : None
        Output      : all the accounts linked to current Intuit customer
        """
        try:
            return self.client.get_customer_accounts()
        except Exception as exn:
            print exn
            return False,exn

    def get_account_balance_and_real_number(self,account_id=None):
        """
        Description : Get account balance and and real account number. 
        Input       : Account Id
        Output      : Account balance and and real account number.
        """
        try:
            account_content = self.client.get_account(account_id).content
            account_balance = account_content.balance_amount
            if hasattr(account_content,"account_number_real"):
                account_real_number = account_content.account_number_real
                return account_balance,account_real_number
            return account_balance,False                
        except Exception as exn:
            print exn
            return False,exn

def get_savings_account_id(user_id=None):
    """
    Description : Get savings account id for the current user
                  This is just a stub right now.
    Input       : user_id from users table
    Output      : savings account id
    """
    try:
        account_id=DB_SESSION.query(User.intuit_account_id).\
                           filter_by(id=user_id).all()[0].intuit_account_id

        return account_id
    except Exception as exn:
        print exn
        return False,exn

def get_user_start_date(user_id=None):
    """
    Description : Get the date of registration for the current user
                  This is just a stub right now.
    Input       : user_id from users table
    Output      : date when the user registed in earn
    """
    try:
        start_date=DB_SESSION.query(User.intuit_linked_account_timestamp).\
                   filter_by(id=user_id).all()[0][0].strftime("%Y-%m-%d")

        return start_date
    except Exception as exn:
        print exn
        return False,exn

def pull_store_transactions(user_id=None):
    """
    Description : Pull and store transactions of the saver.
    Input       : None.
    Output      : Returns True if successful else returns False.
    """
    try:    
        account_id = get_savings_account_id(user_id)
        account=IntuitWrapper(user_id).get_single_account(account_id)
        current_account_balance=Decimal(account.balance_amount)
        if type(account)==tuple and account[0] == False:
            print "Not a valid account"
            return False, "Not a valid account"
       
    except Exception as exn:
        print exn
        return False,exn

    if hasattr(account, "banking_account_type") and\
     account.banking_account_type == "SAVINGS":
        try:
            user_start_date = get_user_start_date(user_id)
            # Retrieve transactions from Intuit API for the
            # savings account of the saver
            transactions = IntuitWrapper(user_id).get_saver_transactions(\
                           account_id, user_start_date,\
                    datetime.datetime.today().strftime("%Y-%m-%d"))
            if hasattr(transactions,"institution_transaction_id"):
                transaction_list=[transactions]
            elif not hasattr(transactions,"_list") or\
            len(transactions._list) == 0:
                print "No transactions till now for this account"
                return True
            elif hasattr(transactions,"_list"):
                transaction_list=transactions._list
            else:
                print "Unknown error in pulling saver transactions"
                return False,"Unknown error in pulling saver transactions"
        except Exception as exn:
            print "Unable to pull saver transactions"
            print exn
            return False, exn

        try:
            for txn in transaction_list:
                # Check whether there is a row with same transaction id
                # present already
                transaction_present = len(DB_SESSION.query(\
                  IntuitTransaction.transaction_id,\
                  IntuitTransaction.account_id).\
                  filter(IntuitTransaction.transaction_id == txn.id, \
                  IntuitTransaction.account_id == account_id).all())

                if transaction_present == 0:
                            
                    if txn.pending.lower() == 'false':
                        # Convert pending value to an integer
                        pending = 0


                        # Create database object for completed transactions
                        transaction_database = IntuitTransaction(\
                          account_id=account_id,\
                          transaction_id=txn.id,\
                          payee_name=txn.payee_name,\
                          posted_date=txn.posted_date[:-6],\
                          pending=pending, amount=txn.amount,)

                    elif txn.pending.lower() == 'true':
                        # Convert pending value to an integer
                        pending = 1
                        # Create database object for pending transactions
                        transaction_database = IntuitTransaction(\
                          account_id=account_id,\
                          transaction_id=txn.id,\
                          payee_name=txn.payee_name,\
                          user_date=txn.user_date[:-6],\
                          pending=pending, amount=txn.amount,)

                    # Commit transaction to the database
                    DB_SESSION.add(transaction_database)
                    DB_SESSION.flush()
                    DB_SESSION.refresh(transaction_database)
                    transaction.commit()

            # Get the processed transactions for this account
            running_balance=current_account_balance
            trxns=DB_SESSION.query(\
            IntuitTransaction.transaction_id,IntuitTransaction.amount).\
            filter(IntuitTransaction.account_id==account_id,\
            IntuitTransaction.posted_date!=None).order_by(\
            IntuitTransaction.posted_date.desc(),
            IntuitTransaction.transaction_id.desc()).all()

            # Update the most recent transaction with current balance
            prev_amount=trxns[0][1]
            DB_SESSION.query(\
                IntuitTransaction.runningBalanceAmount).\
                filter(IntuitTransaction.transaction_id==\
                trxns[0][0]).\
                update({'runningBalanceAmount':running_balance})

            transaction.commit()                        

            # Compute balance after each transaction depending on the
            # order of posted date
            for trxn in trxns[1:]:
                running_balance=running_balance-prev_amount
                DB_SESSION.query(\
                        IntuitTransaction.runningBalanceAmount).\
                        filter(IntuitTransaction.transaction_id==\
                        trxn[0]).\
                        update({'runningBalanceAmount':running_balance})
                transaction.commit()
                prev_amount=trxn[1]

            # Get the pending transactions for this account
            running_balance=current_account_balance
            trxns=DB_SESSION.query(\
            IntuitTransaction.transaction_id,IntuitTransaction.amount).\
            filter(IntuitTransaction.account_id==account_id,\
            IntuitTransaction.user_date!=None).order_by(\
            IntuitTransaction.user_date.desc(),\
            IntuitTransaction.transaction_id).all()

            # Compute balance after each transaction depending on the
            # order of user date
            for trxn in trxns:
                current_amount=trxn[1]
           
                running_balance=running_balance+current_amount

                DB_SESSION.query(\
                        IntuitTransaction.runningBalanceAmount).\
                        filter(IntuitTransaction.transaction_id==\
                        trxn[0]).\
                        update({'runningBalanceAmount':running_balance})
                transaction.commit()
                       
            return True
        except Exception as exn:
            print "Insertion Not Successful"
            print exn
            return False, exn
    else:
        print "Account type is not savings"
        return False, "Account type is not savings"

def search_institutions(keyword=None):
    """
    Description : Search institutions depending on the key word
    Input       : keyword
    Output      : Returns institutions matching key word
                  in alphabetical order of the name
    """
    try:
        result = DB_SESSION.query(IntuitInstitution.institution_id,\
		      IntuitInstitution.institution_name).\
                      filter(IntuitInstitution.institution_name.\
                      like('%'+keyword+'%')).\
                      order_by(IntuitInstitution.institution_name).all()
        modified_result =[]
        for i in result:
            modified_result.append({'id':i[0],'name':i[1]})

        return modified_result
    except DBAPIError as exn:
        print exn
        return False,exn

