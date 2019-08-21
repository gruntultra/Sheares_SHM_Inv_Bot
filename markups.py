from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import config
import dbworker
import gspread

client = gspread.authorize(config.creds)

spreadsheet = client.open("Sheares Media Inventory")
camera_bodies_list = spreadsheet.worksheet("Camera Bodies")
lens_list = spreadsheet.worksheet("Lens")
camera_equipments_list = spreadsheet.worksheet("Camera Equipments")
batteries_list = spreadsheet.worksheet("Batteries")
memory_card_list = spreadsheet.worksheet("Memory Card")

# Main Menu
def main_menu():
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(InlineKeyboardButton("Create Loan", callback_data=f"cb_createloan"), 
                InlineKeyboardButton("View Loans", callback_data=f"cb_viewloan"),
                InlineKeyboardButton("Print Loans", callback_data=f"cb_printloan"),
                InlineKeyboardButton("Return Loans", callback_data=f"cb_returnloan"))
    return markup

# Createloan Sub Menu
def create_loan_sub_menu():
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(InlineKeyboardButton("Let's Create!", callback_data=f"cb_letscreate"), 
                InlineKeyboardButton("Main Menu", callback_data=f"cb_mainmenu"))
    return markup

# Submit Loan menu during createloan
def submit_loan_sub_menu():
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(InlineKeyboardButton("Cancel Loan", callback_data=f"cb_cancelloan_cl"),
                InlineKeyboardButton("Submit Loan", callback_data=f"cb_submitloan_cl"))
    return markup

def cancel_loan_confirmation():
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(InlineKeyboardButton("Yes", callback_data=f"yes_cancelloan"),
                InlineKeyboardButton("No", callback_data=f"no_cancelloan"))
    return markup

# Item menu
def main_category_menu():
    categories = dbworker.get_table_name()
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    for category in categories:
        markup.add(InlineKeyboardButton(text = category[0], callback_data = "cat_{}".format(category[0])))
    markup.add(InlineKeyboardButton(text = "Remove items", callback_data = f"cb_remove_items"))
    markup.add(InlineKeyboardButton(text = "Submit items", callback_data = f"cb_submit_items"))
    return markup

def items_menu(category):
    items = dbworker.get_from_inv_db(category)
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    for item in items:
        item_name = item[0]
        quantity = str(item[1])
        markup.add(InlineKeyboardButton(text = item_name + " " + quantity + "x", callback_data = "item_{}_{}".format(item_name, quantity)))
    markup.add(InlineKeyboardButton(text = "Back to 🏠", callback_data = f"back_to_main_cat"))
    return markup

def quantity_choosing(quantity, item_name):
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    i = 1
    while i <= int(quantity):
        markup.add(InlineKeyboardButton(text = i, callback_data = "q_{}_{}".format(i, item_name)))
        i += 1
    markup.add(InlineKeyboardButton(text = "Back to items", callback_data = f"back_to_items"))
    return markup

def item_removal(user_id, items):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    list_of_items = items.split("\n")
    for item in list_of_items:
        markup.add(InlineKeyboardButton(text = item, callback_data= "remove_{}".format(item)))
    markup.add(InlineKeyboardButton(text = "Back to 🏠", callback_data = f"back_to_main_cat"))
    return markup

def return_loan_menu(expired_loans, rows):
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    for loan, row in zip(expired_loans, rows):
        markup.add(InlineKeyboardButton(text = loan, callback_data = "return_{}".format(row)))
    markup.add(InlineKeyboardButton("Main Menu", callback_data=f"cb_mainmenu"))
    return markup

def return_loan_confirmation(row):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(InlineKeyboardButton(text = "No", callback_data = "rno"),
                InlineKeyboardButton(text = "Yes", callback_data = "ryes_{}".format(row)))
    return markup
    
# View Loan Menu
def view_loan_menu(name_list, start_date, rows):
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    for name, date, row in zip(name_list, start_date, rows):
        markup.add(InlineKeyboardButton(text = name + ", Created on " + date, callback_data = "view_{}_{}".format(name, row)))
    markup.add(InlineKeyboardButton("Main Menu", callback_data=f"cb_mainmenu"))
    return markup

def view_loan_sub_menu():
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(InlineKeyboardButton("Edit Loan", callback_data=f"editloan"),
                InlineKeyboardButton("Delete Loan", callback_data=f"deleteloan"),
                InlineKeyboardButton("Back", callback_data=f"backtoviewloan"))
    return markup

def delete_loan_sub_menu():
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(InlineKeyboardButton(text = "No", callback_data = f"back_to_user"),
                InlineKeyboardButton(text = "Yes", callback_data = f"yes_delete"))
    return markup

def edit_loan_sub_menu():
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(InlineKeyboardButton(text = "Edit Name", callback_data = f"edit_name"),
                InlineKeyboardButton(text = "Edit Block", callback_data = f"edit_block"),
                InlineKeyboardButton(text = "Edit Item", callback_data = f"edit_item"),
                InlineKeyboardButton(text = "Edit Start Date", callback_data = f"edit_startdate"),
                InlineKeyboardButton(text = "Edit End Date", callback_data = f"edit_enddate"),
                InlineKeyboardButton(text = "Edit Purpose", callback_data = f"edit_purpose"),
                InlineKeyboardButton(text = "Back", callback_data = f"back_to_user"))
    return markup

