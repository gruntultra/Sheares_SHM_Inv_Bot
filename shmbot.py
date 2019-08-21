import telebot
import config
import dbworker
import time
import operator
import re
import markups as markup
import datetime

bot = telebot.TeleBot(config.token)

@bot.message_handler(commands=["test"])
def cmd_test(message):
    clear(message)

@bot.message_handler(commands=["state"])
def cmd_state(message):
    state = dbworker.get_current_state(message.chat.id)
    print("State : " + state + " (" + str(message.chat.id) + ")")

@bot.message_handler(commands=["start"])
def cmd_initialize(message):
    clear(message)
    val = dbworker.initialize_user(message, config.States.S_START.value)
    if val is True:
        msg  = "Welcome " + str(message.from_user.username) + " !"
    else:
        msg = "You have been initialized before"
    bot.send_message(chat_id = message.chat.id, text = msg)

@bot.message_handler(commands=["menu"])
def cmd_menu(message):
    clear(message)
    try:
        bot.edit_message_text(message_id = message.message_id,
                                chat_id = message.chat.id,
                                text = "Hi! What would you like to do?",
                                reply_markup = markup.main_menu())
    except:
        bot.send_message(message.chat.id, "Hi! What would you like to do?", reply_markup = markup.main_menu())
    dbworker.save_to_db(message.chat.id, "state", config.States.S_MAIN_MENU.value)

def clear(message):
    try:
        state = dbworker.get_current_state(message.chat.id)
        if state == "2.3":
            items = dbworker.get_from_db(message.chat.id, "temp_items")[1:].split("\n")
        else:
            items = dbworker.get_from_db(message.chat.id, "item")[1:].split("\n")
        for item in items:
            if not item:
                dbworker.clear_fields(message.chat.id)
                return
            if item:
                item_name = item.split(" ")[0]
                quantity = item.split(" ")[1].replace("x", "")
                category = dbworker.find_category(item_name)
                dbworker.stock_taking(category, item_name, quantity, False)
        dbworker.clear_fields(message.chat.id)
    except:
        pass

#------------------Create Loan Process-------------
@bot.message_handler(commands=["createloan"])
def cmd_createloan(message):
    clear(message)
    try:
        bot.edit_message_text(message_id= message.message_id, 
                            chat_id=message.chat.id, 
                            parse_mode="Markdown", 
                            text="Would you like to create a loan?", 
                            reply_markup = markup.create_loan_sub_menu())
    except:
        bot.send_message(message.chat.id, "Would you like to create a loan?", reply_markup = markup.create_loan_sub_menu())
    dbworker.save_to_db(message.chat.id, "state", config.States.S_CREATE_LOAN.value)

def proceed_to_create_loan(message):
    bot.send_message(message.chat.id, "Enter Name:")
    dbworker.save_to_db(message.chat.id, "state", config.States.S_CREATE_LOAN_ENTER_NAME.value)

@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_CREATE_LOAN_ENTER_NAME.value)
def user_entering_name(message):
    dbworker.save_to_db(message.chat.id, "name", message.text)
    bot.send_message(message.chat.id, "Nice. Enter Block:")
    dbworker.save_to_db(message.chat.id, "state", config.States.S_CREATE_LOAN_ENTER_BLOCK.value)

@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_CREATE_LOAN_ENTER_BLOCK.value)
def user_entering_block(message):
    dbworker.save_to_db(message.chat.id, "block", message.text)
    user_entering_item(message, True)
    dbworker.save_to_db(message.chat.id, "state", config.States.S_CREATE_LOAN_ENTER_ITEM.value)

# Item Choosing Process
def user_entering_item(message, send_msg):
    if send_msg is True:
        bot.send_message(chat_id = message.chat.id, text = "Select items:\n\n🏠 Home", reply_markup = markup.main_category_menu())
    else:
        list_of_items = dbworker.get_from_db(message.chat.id, "temp_items")
        bot.edit_message_text(message_id = message.message_id,
                            chat_id = message.chat.id,
                            text = "Select items:\n\n🏠 Home\n\nYour Items 👇\n" + list_of_items,
                            reply_markup = markup.main_category_menu())

def user_finish_entering_item(message):
    bot.send_message(message.chat.id, "Enter Start Date:\n\nIn this format: dd/mm/yy")
    dbworker.save_to_db(message.chat.id, "state", config.States.S_CREATE_LOAN_ENTER_SDATE.value)

@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_CREATE_LOAN_ENTER_SDATE.value)
def user_entering_sdate(message): 
    pattern = re.compile(r'^(3[01]|[12][0-9]|0?[1-9])/(1[0-2]|0?[1-9])/[0-9]{2}$')
    date_criteria = re.match(pattern, message.text)
    if date_criteria:
        dbworker.save_to_db(message.chat.id, "start_date", message.text)
    else:
        bot.send_message(message.chat.id, text="Wrong format. Enter Start Date:\n\nIn this format: dd/mm/yy")
        return
    bot.send_message(message.chat.id, "Enter End Date:\n\nIn this format: dd/mm/yy")
    dbworker.save_to_db(message.chat.id, "state", config.States.S_CREATE_LOAN_ENTER_EDATE.value)

@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_CREATE_LOAN_ENTER_EDATE.value)
def user_entering_edate(message):
    pattern = re.compile(r'^(3[01]|[12][0-9]|0?[1-9])/(1[0-2]|0?[1-9])/[0-9]{2}$')
    date_criteria = re.match(pattern, message.text)
    if date_criteria:
        dbworker.save_to_db(message.chat.id, "end_date", message.text)
    else:
        bot.send_message(message.chat.id, text="Wrong format. Enter end Date:\n\nIn this format: dd/mm/yy")
        return
    bot.send_message(message.chat.id, "Enter Purpose:")
    dbworker.save_to_db(message.chat.id, "state", config.States.S_CREATE_LOAN_ENTER_PURPOSE.value)

@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_CREATE_LOAN_ENTER_PURPOSE.value)
def user_entering_purpose(message):
    dbworker.save_to_db(message.chat.id, "purpose", message.text)
    dbworker.save_to_db(message.chat.id, "state", config.States.S_CREATE_LOAN_VERIFICATION.value)
    loan_verification(message, True)

def loan_verification(message, send_msg):
    entries = dbworker.get_entry(message.chat.id)
    verify_msg = "*Please verify that the entries are correct!*\n\n" + "*Name:* {}\n" + "*Block:* {}\n" + "*Item:* {}\n" + "*Start Date:* {}\n" + "*End Date:* {}\n" + "*Purpose:* {}\n\n"
    if send_msg is True:
        bot.send_message(chat_id = message.chat.id, 
                        parse_mode = "Markdown", 
                        text  =verify_msg.format(entries[3], entries[4], entries[5][1:], entries[6], entries[7], entries[8]),
                        reply_markup = markup.submit_loan_sub_menu())
    else:
        bot.edit_message_text(message_id = message.message_id,
                            chat_id = message.chat.id, 
                            parse_mode = "Markdown", 
                            text  =verify_msg.format(entries[3], entries[4], entries[5], entries[6], entries[7], entries[8]),
                            reply_markup = markup.submit_loan_sub_menu())

def entry_submission(message):
    entries = dbworker.get_entry(message.chat.id)
    entry_list = [entries[3], entries[4], entries[5][1:], entries[6], entries[7], entries[8], entries[0]]
    result = dbworker.submit_loan_gsheets(entry_list)
    if result is True:
        msg = "<b>Loan created successfully!</b>\n\n" + "<b>Name:</b> {}\n" + "<b>Block:</b> {}\n" + "<b>Item:</b> {}\n" + "<b>Start Date:</b> {}\n" + "<b>End Date:</b> {}\n" + "<b>Purpose:</b> {}\n\n" + "<i>by {}</i>" 
        bot.edit_message_text(message_id = message.message_id ,
                            chat_id = message.chat.id, 
                            parse_mode= 'HTML',
                            text = msg.format(entries[3], entries[4], entries[5][1:], entries[6], entries[7], entries[8], entries[0]))
        dbworker.clear_fields(message.chat.id)
        dbworker.save_to_db(message.chat.id, "state", config.States.S_CREATE_LOAN_COMPLETE.value)
    else:
        bot.send_message(chat_id = message.chat.id, text = "Failed to create loan")
#------------------Create Loan Process-------------

#------------------View Loan Process---------------
@bot.message_handler(commands=["viewloan"])
def cmd_viewloan(message):
    clear(message)
    name_list, start_date, row = dbworker.get_loan_names()
    try:
        bot.edit_message_text(message_id = message.message_id ,
                            chat_id = message.chat.id,
                            text='Which one would you like to view?', 
                            reply_markup = markup.view_loan_menu(name_list, start_date, row))
    except:
        bot.send_message(message.chat.id, "Which one would you like to view?", reply_markup = markup.view_loan_menu(name_list, start_date, row))
    dbworker.save_to_db(message.chat.id, "state", config.States.S_VIEW_LOAN.value)

@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_EDIT_LOAN.value)
def edit_loan(message):
    try:
        new_data = message.text
        row = dbworker.get_from_db(message.chat.id, "temp_row")
        col = dbworker.get_from_db(message.chat.id, "temp_field")
        dbworker.update_editted_data(row, col, new_data)
        user_details = dbworker.view_loan(int(row))
        msg = "<b>Name:</b> {}\n<b>Block:</b> {}\n<b>Item:</b> {}\n<b>Start Date:</b> {}\n<b>End Date:</b> {}\n<b>Purpose:</b> {}\n\n<i>by {}</i>"
        bot.send_message(chat_id = message.chat.id,
                        parse_mode = "HTML",
                        text = msg.format(user_details[0], user_details[1], user_details[2], user_details[3], user_details[4], user_details[5], user_details[6]), 
                        reply_markup = markup.edit_loan_sub_menu())
    except:
        print("Error here")
#------------------View Loan Process---------------

#------------------Return Loan Process---------------
@bot.message_handler(commands=["returnloan"])
def cmd_returnloan(message):
    clear(message)
    expired_loans, row = dbworker.get_expiry_loans()
    try:
        bot.edit_message_text(message_id = message.message_id ,
                            chat_id = message.chat.id,
                            text="Select any to return loan:", 
                            reply_markup = markup.return_loan_menu(expired_loans, row))
    except:
        bot.send_message(message.chat.id, "Select any to return loan:?", reply_markup = markup.return_loan_menu(expired_loans, row))
    dbworker.save_to_db(message.chat.id, "state", config.States.S_RETURN_LOAN.value)
#------------------Return Loan Process---------------

#------------------Update Code-----------------------
@bot.message_handler(commands=["updatetheentiredatabase"])
def update(message):
    try:
        bot.send_message(chat_id = message.chat.id, text = "Update In progress...")
        dbworker.update_gsheet_inv()    
        bot.edit_message_text(message_id = message.message_id ,
                            chat_id = message.chat.id,
                            text="Update successful:")
    except:
        bot.send_message(chat_id = message.chat.id, text = "Update Failed...")
#-----------------------------------------------------

#------------------Print out loan Process-------------
@bot.message_handler(commands=["printloan"])
def printloan(message):
    try:
        done = dbworker.produce_worksheet()
        bot.send_message(chat_id = message.chat.id, text = "File is being prepared...")
        if done == True:
            #now = datetime.datetime.now()
            name = 'SHM_loans.xlsx'
            doc = open(name,'rb')
            bot.send_document(message.chat.id, doc)
    except:
        bot.send_message(chat_id = message.chat.id, text = "File could not be generated...")

#------------------Print out loan Process-------------

# All the buttons handler
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    # Main Menu buttons
    if call.data == "cb_createloan":
        bot.answer_callback_query(call.id)
        cmd_createloan(call.message)
    elif call.data == "cb_viewloan":
        bot.answer_callback_query(call.id)
        cmd_viewloan(call.message)
    elif call.data == "cb_returnloan":
        bot.answer_callback_query(call.id)
        cmd_returnloan(call.message)
    # Back to Main Menu button
    elif call.data == "cb_mainmenu":
        bot.answer_callback_query(call.id)
        cmd_menu(call.message)
    elif call.data == "cb_printloan":
        bot.answer_callback_query(call.id)
        printloan(call.message)
    # Let's Create Loan Button
    elif call.data == "cb_letscreate":
        bot.answer_callback_query(call.id)
        proceed_to_create_loan(call.message)
    # Submit or Cancel loan buttons in Create Loan
    elif call.data == "cb_cancelloan_cl":
        bot.answer_callback_query(call.id)
        bot.edit_message_text(message_id = call.message.message_id,
                            chat_id = call.message.chat.id,
                            text = "Are you sure you want to cancel and delete the current loan?",
                            reply_markup = markup.cancel_loan_confirmation())
    elif call.data == "cb_submitloan_cl":
        bot.answer_callback_query(call.id)
        bot.edit_message_text(message_id = call.message.message_id, chat_id = call.message.chat.id, text = "Submitting...")
        entry_submission(call.message)
    elif call.data == "yes_cancelloan":
        bot.answer_callback_query(call.id, text = "Cancelling...")
        items_list = dbworker.get_from_db(call.message.chat.id, "item")[1:].split("\n")
        for i in items_list:
            item = i.split(" ")[0]
            quantity = i.split(" ")[1].replace("x", "")
            category = dbworker.find_category(item)
            dbworker.stock_taking(category, item, quantity, False)
            dbworker.update_loan_gsheets(category, item, int(quantity), operator.__add__, operator.__sub__)
        dbworker.clear_fields(call.message.chat.id)
        bot.edit_message_text(message_id = call.message.message_id,
                            chat_id = call.message.chat.id,
                            text = "Loan has cancelled")
    elif call.data == "no_cancelloan":
        bot.answer_callback_query(call.id)
        loan_verification(call.message, False)
    # Item Choosing
    elif call.data.startswith("cat_"):
        bot.answer_callback_query(call.id)
        category = call.data.split("_")[1]
        dbworker.save_to_db(call.message.chat.id, "temp_category", category)
        list_of_items = dbworker.get_from_db(call.message.chat.id, "temp_items")
        bot.edit_message_text(message_id = call.message.message_id,
                            chat_id = call.message.chat.id,
                            text = "🏠 > " + category + "\n\nYour Items:\n" + list_of_items,
                            reply_markup = markup.items_menu(category))
    elif call.data.startswith("item_"):
        bot.answer_callback_query(call.id)
        item = call.data.split("_")[1]
        quantity = call.data.split("_")[2]
        if(int(quantity) == 1):
            bot.answer_callback_query(call.id, text = "Adding your items...")
            category = dbworker.get_from_db(call.message.chat.id, "temp_category")
            dbworker.stock_taking(category, item, 1, True)
            list_of_items = dbworker.save_items_temp(call.message.chat.id, item, quantity)
            bot.edit_message_text(message_id = call.message.message_id,
                                    chat_id = call.message.chat.id,
                                    text = "🏠 > " + category + "\n\nYour Items:\n" + list_of_items,
                                    reply_markup = markup.items_menu(category))
        else:
            bot.edit_message_reply_markup(message_id = call.message.message_id,
                                        chat_id = call.message.chat.id,
                                        reply_markup = markup.quantity_choosing(quantity, item))
    elif call.data.startswith("q_"):
        bot.answer_callback_query(call.id, text = "Adding your items...")
        quantity = call.data.split("_")[1]
        item = call.data.split("_")[2]
        category = dbworker.get_from_db(call.message.chat.id, "temp_category")
        dbworker.stock_taking(category, item, quantity, True)
        if dbworker.get_current_state(call.message.chat.id) == config.States.S_EDIT_LOAN.value:
            dbworker.add_or_remove(call.message.chat.id, category, item, quantity, True)
        if category == "Batteries" or category == "Memory Cards":
            result = False
        else:
            result = dbworker.check_overlap(call.message.chat.id, item)
        if result is True:
            updated_list = dbworker.edit_quantity(call.message.chat.id, item, quantity)
            bot.edit_message_text(message_id = call.message.message_id,
                                    chat_id = call.message.chat.id,
                                    text = "🏠 > " + category + "\n\nYour Items:\n" + updated_list,
                                    reply_markup = markup.items_menu(category))
        else:
            list_of_items = dbworker.save_items_temp(call.message.chat.id, item, quantity)
            bot.edit_message_text(message_id = call.message.message_id,
                                    chat_id = call.message.chat.id,
                                    text = "🏠 > " + category + "\n\nYour Items:\n" + list_of_items,
                                    reply_markup = markup.items_menu(category))
    elif call.data == "back_to_main_cat":
        bot.answer_callback_query(call.id)
        user_entering_item(call.message, False)
    elif call.data == "back_to_items":
        bot.answer_callback_query(call.id)
        category = dbworker.get_from_db(call.message.chat.id, "temp_category")
        list_of_items = dbworker.get_from_db(call.message.chat.id, "temp_items")
        bot.edit_message_text(message_id = call.message.message_id,
                            chat_id = call.message.chat.id,
                            text = "🏠 > " + category + "\n\nYour Items:\n" + list_of_items,
                            reply_markup = markup.items_menu(category))
    elif call.data == "cb_remove_items":
        bot.answer_callback_query(call.id)
        list_of_existing_items = dbworker.get_from_db(call.message.chat.id, "temp_items")
        bot.edit_message_text(message_id = call.message.message_id,
                            chat_id = call.message.chat.id,
                            text = "Select the items that you want to remove:\n" + list_of_existing_items,
                            reply_markup = markup.item_removal(call.message.chat.id, list_of_existing_items))
    elif call.data.startswith("remove_"):
        bot.answer_callback_query(call.id, text = "Removing items...")
        item_to_be_removed = call.data.split("_")[1]
        item = item_to_be_removed.split(" ")[0]
        quantity = item_to_be_removed.split(" ")[1].replace("x", "")
        existing_items = dbworker.get_from_db(call.message.chat.id, "temp_items")
        list_of_existing_items = existing_items.split("\n")
        if item_to_be_removed in list_of_existing_items:
            list_of_existing_items.remove(item_to_be_removed)
        new_list = "\n".join(list_of_existing_items)
        category = dbworker.find_category(item)
        dbworker.stock_taking(category, item, quantity, False)
        if dbworker.get_current_state(call.message.chat.id) == config.States.S_EDIT_LOAN.value:
            dbworker.add_or_remove(call.message.chat.id, category, item, quantity, False)
        dbworker.save_to_db(call.message.chat.id, "temp_items", new_list)
        bot.edit_message_text(message_id = call.message.message_id,
                            chat_id = call.message.chat.id,
                            text = "Select the items that you want to remove:\n" + new_list,
                            reply_markup = markup.item_removal(call.message.chat.id, new_list))
    elif call.data == "cb_submit_items":
        bot.answer_callback_query(call.id, text = "Submitting...")
        is_empty = dbworker.if_empty(call.message.chat.id)
        if is_empty:
            bot.send_message(chat_id = call.message.chat.id, text = "You have not selected any items yet")
        else:
            list_of_items = dbworker.get_from_db(call.message.chat.id, "temp_items")
            if dbworker.get_current_state(call.message.chat.id) == config.States.S_CREATE_LOAN_ENTER_ITEM.value:
                dbworker.save_to_db(call.message.chat.id, "item", list_of_items)
                user_finish_entering_item(call.message)
                bot.edit_message_text(message_id = call.message.message_id,
                                    chat_id = call.message.chat.id,
                                    text = "Submitted Successfully!")
                dbworker.save_to_db(call.message.chat.id, "state", config.States.S_CREATE_LOAN_ENTER_SDATE.value)
            else:
                bot.edit_message_text(message_id = call.message.message_id,
                                chat_id = call.message.chat.id,
                                text = "Submitting updated data...Please wait...")
                row = dbworker.get_from_db(call.message.chat.id, "temp_row")
                new_items = dbworker.get_from_db(call.message.chat.id, "temp_items")
                dbworker.update_items(row, new_items)
                dbworker.save_to_db(call.message.chat.id, "temp_items", "")
                items_to_add = dbworker.get_from_db(call.message.chat.id, "items_to_add").split("\n")[1:]
                items_to_remove = dbworker.get_from_db(call.message.chat.id, "items_to_remove").split("\n")[1:]
                for item_to_add in items_to_add:
                    category = item_to_add.split(",")[0]
                    item_name = item_to_add.split(",")[1]
                    quantity = item_to_add.split(",")[2]
                    dbworker.update_loan_gsheets(category, item_name, quantity, operator.__sub__, operator.__add__)
                for item_to_remove in items_to_remove:
                    category = item_to_remove.split(",")[0]
                    item_name = item_to_remove.split(",")[1]
                    quantity = item_to_remove.split(",")[2]
                    dbworker.update_loan_gsheets(category, item_name, quantity, operator.__add__, operator.__sub__)
                dbworker.save_to_db(call.message.chat.id, "items_to_add", "")
                dbworker.save_to_db(call.message.chat.id, "items_to_remove", "")
                user_details = dbworker.view_loan(row)
                msg = "<b>Name:</b> {}\n<b>Block:</b> {}\n<b>Item:</b> {}\n<b>Start Date:</b> {}\n<b>End Date:</b> {}\n<b>Purpose:</b> {}\n\n<i>by {}</i>"
                bot.edit_message_text(message_id = call.message.message_id,
                                chat_id = call.message.chat.id,
                                parse_mode = "HTML",
                                text = msg.format(user_details[0], user_details[1], user_details[2], user_details[3], user_details[4], user_details[5], user_details[6]),
                                reply_markup = markup.edit_loan_sub_menu())     
    # Return Loan
    elif call.data.startswith("return_"):
        bot.answer_callback_query(call.id)
        row = call.data.split("_")[1]
        user_details = dbworker.get_expired_user_detail(row)
        msg = "<b>User Details:</b>\n\n" + "<b>Name:</b> {}\n" + "<b>Block:</b> {}\n" + "<b>Item:</b> {}\n" + "<b>Start Date:</b> {}\n" + "<b>End Date:</b> {}\n" + "<b>Purpose:</b> {}\n\nDo you want to return this?"
        bot.edit_message_text(message_id = call.message.message_id,
                                chat_id = call.message.chat.id,
                                parse_mode = "HTML",
                                text = msg.format(user_details[0], user_details[1], user_details[2], user_details[3], user_details[4], user_details[5]),
                                reply_markup = markup.return_loan_confirmation(row))
    elif call.data.startswith("ryes_"):
        bot.answer_callback_query(call.id, text = "Returning...")
        bot.edit_message_text(message_id = call.message.message_id,
                                chat_id = call.message.chat.id,
                                text = "Returning... Please wait!")
        row = call.data.split("_")[1]
        user_details = dbworker.get_expired_user_detail(row)
        items_list = user_details[2].split("\n")
        for items in items_list:
            item = items.split(" ")[0]
            quantity = items.split(" ")[1].replace("x", "")
            category = dbworker.find_category(item)
            dbworker.stock_taking(category, item, quantity, False)
        dbworker.move_expired_to_history(int(row))
        expired_loans, rows = dbworker.get_expiry_loans()
        bot.edit_message_text(message_id = call.message.message_id,
                                chat_id = call.message.chat.id,
                                text = "Select any to return loan:",
                                reply_markup = markup.return_loan_menu(expired_loans, rows))
    elif call.data == "rno":
        bot.answer_callback_query(call.id)
        cmd_returnloan(call.message)
    # View Loan
    elif call.data.startswith("view_"):
        bot.answer_callback_query(call.id, text = "Loading loans...")
        user_row = call.data.split("_")[2]
        user_details = dbworker.view_loan(user_row)
        msg = "<b>Name:</b> {}\n<b>Block:</b> {}\n<b>Item:</b> {}\n<b>Start Date:</b> {}\n<b>End Date:</b> {}\n<b>Purpose:</b> {}\n\n<i>by {}</i>"
        dbworker.save_to_db(call.message.chat.id, "temp_row", user_row)
        bot.edit_message_text(message_id = call.message.message_id,
                                chat_id = call.message.chat.id,
                                parse_mode = "HTML",
                                text = msg.format(user_details[0], user_details[1], user_details[2], user_details[3], user_details[4], user_details[5], user_details[6]),
                                reply_markup = markup.view_loan_sub_menu())
    # View Loan - Edit Loan
    elif call.data == "editloan":
        bot.answer_callback_query(call.id)
        row = dbworker.get_from_db(call.message.chat.id, "temp_row")
        user_details = dbworker.view_loan(int(row))
        msg = "<b>Name:</b> {}\n<b>Block:</b> {}\n<b>Item:</b> {}\n<b>Start Date:</b> {}\n<b>End Date:</b> {}\n<b>Purpose:</b> {}\n\n<i>by {}</i>"
        bot.edit_message_text(message_id = call.message.message_id,
                                chat_id = call.message.chat.id,
                                parse_mode = "HTML",
                                text = msg.format(user_details[0], user_details[1], user_details[2], user_details[3], user_details[4], user_details[5], user_details[6]),
                                reply_markup = markup.edit_loan_sub_menu())
    elif call.data.startswith("edit_"):
        bot.answer_callback_query(call.id)
        field_to_edit = call.data.split("_")[1]
        if field_to_edit == "item":
            row = dbworker.get_from_db(call.message.chat.id, "temp_row")
            existing_items =  dbworker.view_loan(int(row))[2]
            dbworker.save_to_db(call.message.chat.id, "temp_items", existing_items)
            user_entering_item(call.message, False)
        else:
            bot.edit_message_text(message_id = call.message.message_id,
                                    chat_id = call.message.chat.id,
                                    text = "OK. Send me the new " + field_to_edit + ".")
            dbworker.save_to_db(call.message.chat.id, "temp_field", field_to_edit)
        dbworker.save_to_db(call.message.chat.id, "state", config.States.S_EDIT_LOAN.value)
    # View Loan - Delete Loan
    elif call.data == "deleteloan":
        bot.answer_callback_query(call.id)
        bot.edit_message_text(message_id = call.message.message_id,
                                chat_id = call.message.chat.id,
                                text = "Are you sure you want to delete?",
                                reply_markup = markup.delete_loan_sub_menu())
    elif call.data == "back_to_user":
        bot.answer_callback_query(call.id)
        row = dbworker.get_from_db(call.message.chat.id, "temp_row")
        user_details = dbworker.view_loan(int(row))
        msg = "<b>Name:</b> {}\n<b>Block:</b> {}\n<b>Item:</b> {}\n<b>Start Date:</b> {}\n<b>End Date:</b> {}\n<b>Purpose:</b> {}\n\n<i>by {}</i>"
        bot.edit_message_text(message_id = call.message.message_id,
                                chat_id = call.message.chat.id,
                                parse_mode = "HTML",
                                text = msg.format(user_details[0], user_details[1], user_details[2], user_details[3], user_details[4], user_details[5], user_details[6]),
                                reply_markup = markup.view_loan_sub_menu())
    elif call.data == "yes_delete":
        bot.answer_callback_query(call.id)
        bot.edit_message_text(message_id = call.message.message_id,
                                chat_id = call.message.chat.id,
                                parse_mode = "Markdown",
                                text = "Deleting...Please wait...")
        row = dbworker.get_from_db(call.message.chat.id, "temp_row")
        items_list = dbworker.view_loan(row)[2].split("\n")
        for items in items_list:
            item = items.split(" ")[0]
            quantity = items.split(" ")[1].replace("x", "")
            category = dbworker.find_category(item)
            dbworker.stock_taking(category, item, quantity, False)
            dbworker.update_loan_gsheets(category, item, int(quantity), operator.__add__, operator.__sub__)
        dbworker.delete_loan(row)
        bot.edit_message_text(message_id = call.message.message_id,
                                chat_id = call.message.chat.id,
                                parse_mode = "Markdown",
                                text = "Deleted Successfully.")
    # View Loan - Back to view loan
    elif call.data == "backtoviewloan":
        bot.answer_callback_query(call.id)
        cmd_viewloan(call.message)


if __name__ == "__main__":
    bot.polling(none_stop=True)
