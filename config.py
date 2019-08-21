from enum import Enum
import gspread
from oauth2client.service_account import ServiceAccountCredentials

token = "780727315:AAENaPZrq2FzTjHtHPuXn870WIvoMP_zl9c"
db = "user.db"
inv_db = "inventory.db"
loan_db = "loans.db"

scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)

class States(Enum):
    S_START = "0"
    S_MAIN_MENU = "1"
    S_CREATE_LOAN = "2"
    S_CREATE_LOAN_ENTER_NAME = "2.1"
    S_CREATE_LOAN_ENTER_BLOCK = "2.2"
    S_CREATE_LOAN_ENTER_ITEM = "2.3"
    S_CREATE_LOAN_ENTER_SDATE = "2.4"
    S_CREATE_LOAN_ENTER_EDATE = "2.5"
    S_CREATE_LOAN_ENTER_PURPOSE = "2.6"
    S_CREATE_LOAN_VERIFICATION = "2.9"
    S_CREATE_LOAN_COMPLETE = "3"
    S_RETURN_LOAN = "4"
    S_RETURN_LOAN_COMPLETE = "4.1"
    S_VIEW_LOAN = "5"
    S_EDIT_LOAN = "6"
    S_DO_NOTHING = "11"

