"""
File name   : intuit_wrapper.py
Author      : Ravichandra
Description : Functionality to access savers accounts and transaction data
              using Intuit API
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

class Rewardplans(BASE):
    __table__ = Table('reward_plans', METADATA, autoload=True)

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
        """
        self.client = AggcatClient(
            configuration.INTUIT_OAUTH_CONSUMER_KEY,
            configuration.INTUIT_OATH_CONSUMER_SECRET,
            configuration.INTUIT_SAML_IDENTITY_PROVIDER_ID,
            str(user_id),
            configuration.INTUIT_KEY_PATH
        )
        """
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
            return self.client.get_account(account_id)
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
            **credentials)
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
            account_object = self.client.get_account(account_id)
            if configuration.MOCK_ENABLED == 0:
                account_content = account_object.content
            else:
                if hasattr(account_object.content,"BankingAccount"):
                    account_content = account_object.content.BankingAccount
                else:
                    account_content = account_object.content

            account_balance = account_content.balance_amount
            if hasattr(account_content,"account_number"):
                account_real_number = account_content.account_number
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
        if configuration.MOCK_ENABLED == 0:
            account = account.content
        else:
            if hasattr(account.content,"BankingAccount"):
                account = account.content.BankingAccount
            else:
                account = account.content

        current_account_balance=Decimal(account.balance_amount)

        if type(account)==tuple and account[0] == False:
            return False, account.aggr_status_code

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
            # Delete all the values from transactions table and get the latest
            # data for current user since transactions are retrieved
            # successfully
            DB_SESSION.query(IntuitTransaction).\
            filter(IntuitTransaction.account_id == account_id).delete()
       
            for txn in transaction_list:
                        
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
                """
                Notify User if txn type is withdrawal(otherthan FEE,SERVICE
                CHARGES etc.,)
                """
                if float(txn.amount) < 0.0 and txn.pending.lower() == 'false':
                    verify_txn_and_notify_saver(user_id, txn.amount,\
                        txn.posted_date[:10], txn.payee_name)

            # Get the processed transactions for this account
            running_balance=current_account_balance
            trxns=DB_SESSION.query(\
            IntuitTransaction.transaction_id,IntuitTransaction.amount).\
            filter(IntuitTransaction.account_id==account_id,\
            IntuitTransaction.posted_date!=None).order_by(\
            IntuitTransaction.posted_date.desc(),
            IntuitTransaction.transaction_id.desc()).all()

            if len(trxns)!=0:
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

def get_inst_url(inst_id=None):
    """
    Description : 
    Input       : 
    """
    try:
        inst_url = DB_SESSION.query(IntuitInstitution.home_url).\
                      filter(IntuitInstitution.institution_id\
                      ==inst_id).one()[0]

        return inst_url
    except DBAPIError as exn:
        print exn
        return False,exn

def get_inst_name(inst_id=None):
    """
    Description : 
    Input       : 
    """
    try:
        inst_name = DB_SESSION.query(IntuitInstitution.institution_name).\
                      filter(IntuitInstitution.institution_id\
                      ==inst_id).one()[0]

        return inst_name
    except DBAPIError as exn:
        print exn
        return False,exn

def verify_txn_and_notify_saver(user_id, amount, posted_date, description):

    """
    Description : Verify withdrawal transactions and notify the Saver
                  regarding program restart.
    """

    try:
        word_list = [word.strip() for word in configuration.fee_phrases.split(',')]

        for word in word_list:
            if word in description.lower():
                return
        if  (posted_date == (datetime.datetime.today()-\
               datetime.timedelta(days=1)).strftime("%Y-%m-%d")) or\
                (posted_date ==\
                        (datetime.datetime.today().strftime("%Y-%m-%d"))):

            #Check no_of_restarts and if it exceeds threshold, exit from the
            #program
            no_of_restarts, reward_plan_id  =  DB_SESSION.query(
                User.no_of_restarts, User.reward_plan_id).filter(
                User.id == user_id).one()
            no_of_allowed_restarts = DB_SESSION.query(
                Rewardplans.no_of_allowed_restarts).filter(
                Rewardplans.id==reward_plan_id).first()[0]

            time_stamp_now = datetime.datetime.today()
            if no_of_restarts == no_of_allowed_restarts:
                DB_SESSION.query(User).filter(User.id ==
                        user_id).update({User.user_status:'exited',
                        User.exit_reason:'withdrawal',
                        User.user_status_updated_at:time_stamp_now})
                transaction.commit()
                user = DB_SESSION.query(User).filter(User.id
                                                  == user_id).one()
                notifications.Notification.alert_user_about_program_exit(user)
            else:
                #Saver made a withdrawal. Change user_status in DB to 'closed'
                DB_SESSION.query(User).filter(User.id ==
                    user_id).update({User.no_of_restarts: no_of_restarts + 1,
                    User.user_status:'closed',
                    User.exit_reason:'withdrawal',
                    User.user_status_updated_at:time_stamp_now})
                transaction.commit()
                user = DB_SESSION.query(User).filter(User.id
                                                  == user_id).one()
                notifications.Notification.alert_user_about_program_restart(user)

    except Exception as exn:
        print exn
