import config
import sys
import sqlite3
import shmbot
import gspread
import time
import datetime
import operator
import xlsxwriter

client = gspread.authorize(config.creds)

spreadsheet = client.open("Sheares Media Inventory")
camera_bodies_list = spreadsheet.worksheet("Camera Bodies")
lens_list = spreadsheet.worksheet("Lens")
batteries_list = spreadsheet.worksheet("Batteries")
memory_card_list = spreadsheet.worksheet("Memory Card")
camera_equipments_list = spreadsheet.worksheet("Camera Equipments")
#loan = spreadsheet.worksheet("Loan")
#loan_history = spreadsheet.worksheet("Loan_history")

def save_to_db(user_id, column_name, value):
    try:
        command = "UPDATE users SET {} = ? WHERE user_id = ?".format(column_name)
        sqlite_db = sqlite3.connect(config.db)
        cur = sqlite_db.cursor()
        cur.execute(command, (str(value), str(user_id)))
        sqlite_db.commit()
        sqlite_db.close()
    except:
        shmbot.bot.send_message(chat_id = user_id, text = "Error saving data to database.")

def get_from_db(user_id, column_name):
    try:
        command = "SELECT {} FROM users WHERE user_id = {}".format(column_name, str(user_id))
        sqlite_db = sqlite3.connect(config.db)
        cur = sqlite_db.cursor()
        cur.execute(command)
        result = cur.fetchall()
        sqlite_db.close()
        return result[0][0]
    except Exception as e:
        print(e)

def clear_fields(user_id):
    try:
        command = """UPDATE users
                     SET name = "", 
                        block = "",
                        item = "", 
                        start_date = "", 
                        end_date = "", 
                        purpose = "",  
                        temp_items = "", 
                        temp_category = "",
                        temp_row = "",
                        temp_field = "",
                        items_to_add = "",
                        items_to_remove = ""
                        WHERE user_id = {}""".format(user_id)
        sqlite_db = sqlite3.connect(config.db)
        cur = sqlite_db.cursor()
        cur.execute(command,)
        sqlite_db.commit()
        sqlite_db.close()
    except Exception as e:
        shmbot.bot.send_message(chat_id = user_id, text = str(e))

def initialize_user(message, value):
    try:
        exist_user_command = 'SELECT user_id FROM users'
        command = '''INSERT INTO users VALUES(?, ?, ?, "", "", "", "", "", "", "", "", "", "", "", "")'''
        sqlite_db = sqlite3.connect(config.db)
        cur = sqlite_db.cursor()
        cur.execute(exist_user_command)
        users = cur.fetchall()
        user_list = []
        for user in users:
            user_list.append(user[0])
        if str(message.chat.id) in user_list:
            return False
        else:
            cur.execute(command, (str(message.from_user.username), str(message.chat.id), str(value)))
            sqlite_db.commit()
            sqlite_db.close()
            return True
    except:
        print("Initialization error")

def get_current_state(user_id):
    try:
        command = '''SELECT state FROM users WHERE user_id = {}'''.format(str(user_id))
        sqlite_db = sqlite3.connect(config.db)
        cur = sqlite_db.cursor()
        cur.execute(command)
        state = cur.fetchall()
        sqlite_db.close()
        return state[0][0]
    except Exception as e:
        print(e)
    
        
def get_entry(user_id):
    try:
        command = 'SELECT * FROM users where user_id = {}'.format(str(user_id))
        sqlite_db = sqlite3.connect(config.db)
        cur = sqlite_db.cursor()
        cur.execute(command)
        entries = cur.fetchall()
        sqlite_db.close()
        return entries[0]
    except:
        print("Get entry error")

def save_items_temp(user_id, item_name, quantity):
    try:
        command = 'SELECT temp_items from users WHERE user_id = {}'.format(user_id)
        command_1 = 'UPDATE users SET temp_items = ? WHERE user_id = ?'
        sqlite_db = sqlite3.connect(config.db)
        cur = sqlite_db.cursor()
        cur.execute(command)
        existing_items = cur.fetchall()[0][0]
        new_items = existing_items + "\n" + item_name + " " + quantity + "x"
        cur.execute(command_1, (new_items, str(user_id)))
        sqlite_db.commit()
        sqlite_db.close()
        return new_items
    except:
        print("Error saving items")

def check_overlap(user_id, item_name):
    command = 'SELECT temp_items from users WHERE user_id = {}'.format(user_id)
    sqlite_db = sqlite3.connect(config.db)
    cur = sqlite_db.cursor()
    cur.execute(command)
    existing_items = cur.fetchall()[0][0].split("\n")
    if any(item_name in s for s in existing_items):
        return True
    else:
        return False

def edit_quantity(user_id, item_name, quantity):
    command = 'SELECT temp_items from users WHERE user_id = {}'.format(user_id)
    command_1 = 'UPDATE users SET temp_items = ? WHERE user_id = {}'.format(user_id)
    sqlite_db = sqlite3.connect(config.db)
    cur = sqlite_db.cursor()
    cur.execute(command)
    existing_items = cur.fetchall()[0][0].split("\n")
    for items in existing_items:
        if item_name in items:
            splitted_items = items.split(" ")
            existing_quantity = splitted_items[1].replace("x", "")
            new_quantity = int(quantity) + int(existing_quantity)
            updated_item = item_name + " " + str(new_quantity) + "x"
            index = existing_items.index(items)
            existing_items[index] = updated_item
            updated_list = "\n".join(existing_items)
            cur.execute(command_1, (updated_list,))
            sqlite_db.commit()
            sqlite_db.close()
            return updated_list
        else:
            continue
        return None

def if_empty(user_id):
    try:
        command = 'SELECT temp_items from users WHERE user_id = {}'.format(user_id)
        sqlite_db = sqlite3.connect(config.db)
        cur = sqlite_db.cursor()
        cur.execute(command)
        value = cur.fetchall()
        sqlite_db.close()
        if value[0][0] == "":
            return True
        else:
            return False
    except Exception as e:
        print("If empty error")

def submit_loan_gsheets(entry):
    try:
        sqlite_db = sqlite3.connect(config.loan_db)
        cur = sqlite_db.cursor()
        command = 'INSERT INTO loan VALUES(?, ?, ?, ?, ?, ?, ?)'
        cur.execute(command, (str(entry[0]), str(entry[1]), str(entry[2]), str(entry[3]), str(entry[4]), str(entry[5]), str(entry[6])))
        sqlite_db.commit()
        sqlite_db.close()
        return True
        # client.login()
        # loan.append_row(entry)
        # items = entry[2].split("\n")
        # for item in items:
            # item_name = item.split(" ")[0]
            # if camera_bodies_list.findall(item_name):
                # command = "SELECT In_Stock, On_Loan FROM 'Camera Bodies' WHERE Equipment = '{}'".format(item_name)
                # sqlite_db = sqlite3.connect(config.inv_db)
                # cur = sqlite_db.cursor()
                # cur.execute(command)
                # existing_quantity = cur.fetchall()
                # in_stock_qty = existing_quantity[0][0]
                # on_loan_qty = existing_quantity[0][1]
                # item = camera_bodies_list.findall(item_name)[0]
                # camera_bodies_list.update_cell(item.row, 4, in_stock_qty)
                # camera_bodies_list.update_cell(item.row, 5, on_loan_qty)
            # elif camera_equipments_list.findall(item_name):
                # command = "SELECT In_Stock, On_Loan FROM 'Camera Equipments' WHERE Equipment = '{}'".format(item_name)
                # sqlite_db = sqlite3.connect(config.inv_db)
                # cur = sqlite_db.cursor()
                # cur.execute(command)
                # existing_quantity = cur.fetchall()
                # in_stock_qty = existing_quantity[0][0]
                # on_loan_qty = existing_quantity[0][1]
                # item = camera_equipments_list.findall(item_name)[0]
                # camera_equipments_list.update_cell(item.row, 4, in_stock_qty)
                # camera_equipments_list.update_cell(item.row, 5, on_loan_qty)
            # elif lens_list.findall(item_name):
                # command = "SELECT In_Stock, On_Loan FROM 'Lens' WHERE Equipment = '{}'".format(item_name)
                # sqlite_db = sqlite3.connect(config.inv_db)
                # cur = sqlite_db.cursor()
                # cur.execute(command)
                # existing_quantity = cur.fetchall()
                # in_stock_qty = existing_quantity[0][0]
                # on_loan_qty = existing_quantity[0][1]
                # item = lens_list.findall(item_name)[0]
                # lens_list.update_cell(item.row, 4, in_stock_qty)
                # lens_list.update_cell(item.row, 5, on_loan_qty)
            # elif batteries_list.findall(item_name):
                # command = "SELECT In_Stock, On_Loan FROM 'Batteries' WHERE Equipment = '{}'".format(item_name)
                # sqlite_db = sqlite3.connect(config.inv_db)
                # cur = sqlite_db.cursor()
                # cur.execute(command)
                # existing_quantity = cur.fetchall()
                # in_stock_qty = existing_quantity[0][0]
                # on_loan_qty = existing_quantity[0][1]
                # item = batteries_list.findall(item_name)[0]
                # batteries_list.update_cell(item.row, 4, in_stock_qty)
                # batteries_list.update_cell(item.row, 5, on_loan_qty)
            # elif memory_card_list.findall(item_name): 
                # command = "SELECT In_Stock, On_Loan FROM 'Memory Cards' WHERE Equipment = '{}'".format(item_name)
                # sqlite_db = sqlite3.connect(config.inv_db)
                # cur = sqlite_db.cursor()
                # cur.execute(command)
                # existing_quantity = cur.fetchall()
                # in_stock_qty = existing_quantity[0][0]
                # on_loan_qty = existing_quantity[0][1]
                # item = memory_card_list.findall(item_name)[0]
                # memory_card_list.update_cell(item.row, 4, in_stock_qty)
                # memory_card_list.update_cell(item.row, 5, on_loan_qty)
        # return True
    except Exception as e:
        print(e)
        return False

def update_loan_gsheets(category, item, quantity, in_stock_operator, on_loan_operator):
    pass
    # client.login()
    # if category == "Camera Equipments":
        # cell = camera_equipments_list.findall(item)[0]
        # in_stock = camera_equipments_list.cell(cell.row, 4)
        # on_loan = camera_equipments_list.cell(cell.row, 5)
        # new_in_stock_val = in_stock_operator(int(in_stock.value), int(quantity))
        # new_on_loan_val = on_loan_operator(int(on_loan.value), int(quantity))
        # camera_equipments_list.update_cell(cell.row, 4, str(new_in_stock_val))
        # camera_equipments_list.update_cell(cell.row, 5, str(new_on_loan_val))
    # elif category == "Camera Bodies":
        # cell = camera_bodies_list.findall(item)[0]
        # in_stock = camera_bodies_list.cell(cell.row, 4)
        # on_loan = camera_bodies_list.cell(cell.row, 5)
        # new_in_stock_val = in_stock_operator(int(in_stock.value), int(quantity))
        # new_on_loan_val = on_loan_operator(int(on_loan.value), int(quantity))
        # camera_bodies_list.update_cell(cell.row, 4, str(new_in_stock_val))
        # camera_bodies_list.update_cell(cell.row, 5, str(new_on_loan_val))
    # elif category == "Lens":
        # cell = lens_list.findall(item)[0]
        # in_stock = lens_list.cell(cell.row, 4)
        # on_loan = lens_list.cell(cell.row, 5)
        # new_in_stock_val = in_stock_operator(int(in_stock.value), int(quantity))
        # new_on_loan_val = on_loan_operator(int(on_loan.value), int(quantity))
        # lens_list.update_cell(cell.row, 4, str(new_in_stock_val))
        # lens_list.update_cell(cell.row, 5, str(new_on_loan_val))
    # elif category == "Batteries":
        # cell = batteries_list.findall(item)[0]
        # in_stock = batteries_list.cell(cell.row, 4)
        # on_loan = batteries_list.cell(cell.row, 5)
        # new_in_stock_val = in_stock_operator(int(in_stock.value), int(quantity))
        # new_on_loan_val = on_loan_operator(int(on_loan.value), int(quantity))
        # batteries_list.update_cell(cell.row, 4, str(new_in_stock_val))
        # batteries_list.update_cell(cell.row, 5, str(new_on_loan_val))
    # elif category == "Memory Cards":
        # cell = memory_card_list.findall(item)[0]
        # in_stock = memory_card_list.cell(cell.row, 4)
        # on_loan = memory_card_list.cell(cell.row, 5)
        # new_in_stock_val = in_stock_operator(int(in_stock.value), int(quantity))
        # new_on_loan_val = on_loan_operator(int(on_loan.value), int(quantity))
        # memory_card_list.update_cell(cell.row, 4, str(new_in_stock_val))
        # memory_card_list.update_cell(cell.row, 5, str(new_on_loan_val))

def get_expiry_loans():
    command = "SELECT * FROM loan"
    sqlite_db = sqlite3.connect(config.loan_db)
    cur = sqlite_db.cursor()
    cur.execute(command)
    all_loans = cur.fetchall()
    count = len(all_loans)
    expired_loans = []
    row = []
    counter = 1
    for single_data in all_loans:
        msg = str(single_data[0]) + ", Expires On " + str(single_data[4])
        expired_loans.append(msg)
        row.append(counter)
        counter += 1   
    # client.login()
    # list_of_lists = loan.get_all_values()
    # count = len(list_of_lists)
    # counter = 1
    # expired_loans = []
    # row = []
    # while counter < count:
        # format_str = '%d/%m/%y' # The format
        # todays_date = time.strftime("%d/%m/%y")
        # todays_date = datetime.datetime.strptime(todays_date, format_str)
        # enddate = list_of_lists[counter][4]
        # end_date = datetime.datetime.strptime(enddate, format_str)
        # #if end_date < todays_date:
        # msg = str(list_of_lists[counter][0]) + ", Expires On " + list_of_lists[counter][4]
        # expired_loans.append(msg)
        # row.append(counter)
        # counter += 1
    return expired_loans, row

def move_expired_to_history(row: int):
    command = 'SELECT * FROM loan WHERE ROWID = {}'.format(row)
    sqlite_db = sqlite3.connect(config.loan_db)
    cur = sqlite_db.cursor()
    cur.execute(command)
    data = cur.fetchall()[0]
    mv_command = 'INSERT INTO loan_history VALUES(?,?,?,?,?,?,?)'
    cur.execute(mv_command, (data[0], data[1], data[2], data[3], data[4], data[5], data[6]))
    del_command = 'DELETE FROM loan WHERE ROWID = {}'.format(row)
    end_command = 'end transaction'
    vacuum_command = 'vacuum'
    cur.execute(del_command)
    cur.execute(end_command)
    cur.execute(vacuum_command)
    sqlite_db.commit()
    sqlite_db.close()
    pass
    # client.login()
    # list_of_lists = loan.get_all_values()
    # loan_history.append_row(list_of_lists[row])
    # item_pair = list_of_lists[row][2]
    # list_of_items = item_pair.split("\n")
    # for items in list_of_items:
        # split_item = items.split(" ")
        # if split_item[0] == "":
            # continue
        # item = split_item[0]
        # quantity = split_item[1].replace("x", "")
        # category = find_category(item)
    # loan.delete_row(row + 1)

def get_expired_user_detail(row):
    command = "SELECT * FROM loan"
    sqlite_db = sqlite3.connect(config.loan_db)
    cur = sqlite_db.cursor()
    cur.execute(command)
    all_loans = cur.fetchall()
    print(row)
    user_details = all_loans[int(row) - 1]
    return user_details
    # client.login()
    # row = int(row) + 1
    # user_details = loan.row_values(row)
    # return user_details

def find_category(item):
    categories = get_table_name()
    command = "SELECT * FROM '{}' WHERE Equipment = ?"
    sqlite_db = sqlite3.connect(config.inv_db)
    cur = sqlite_db.cursor()
    for category in categories:
        new_command = command.format(category[0])
        cur.execute(new_command, (item,))
        data = cur.fetchall()
        if data:
            break
        else:
            continue
    return category[0]

def get_loan_names():
    command = "SELECT * FROM loan"
    sqlite_db = sqlite3.connect(config.loan_db)
    cur = sqlite_db.cursor()
    cur.execute(command)
    all_loans = cur.fetchall()
    name_list = [name[0] for name in all_loans]
    start_date = [date[3] for date in all_loans]
    #client.login()
    #name_list = loan.col_values(1)[1:]
    #start_date = loan.col_values(4)[1:]
    a = len(name_list) + 2
    return name_list, start_date, list(range(2, a))

def view_loan(user_row):
    command = "SELECT * FROM loan"
    sqlite_db = sqlite3.connect(config.loan_db)
    cur = sqlite_db.cursor()
    cur.execute(command)
    all_loans = cur.fetchall()
    try:
        user_details = all_loans[int(user_row) - 2]
        return user_details
    except:
        user_details = ''
        return user_details
    #client.login()
    #user_details = loan.row_values(user_row)
    

def delete_loan(user_row):
    sqlite_db = sqlite3.connect(config.loan_db)
    cur = sqlite_db.cursor()
    delete_command = "DELETE FROM loan WHERE ROWID = {}".format(int(user_row) - 1)
    end_command = 'end transaction'
    vacuum_command = 'vacuum'
    cur.execute(delete_command)
    cur.execute(end_command)
    cur.execute(vacuum_command)
    sqlite_db.commit()
    sqlite_db.close()
    # client.login()
    # loan.delete_row(int(user_row))
    # pass

def update_editted_data(row, col, new_data):
    try:
        command = "SELECT * FROM loan"
        sqlite_db = sqlite3.connect(config.loan_db)
        cur = sqlite_db.cursor()
        cur.execute(command)
        all_loans = cur.fetchall()
        user_details = all_loans[int(row) - 2]
        update_command = "UPDATE loan SET {} = ? WHERE ROWID = ?".format(col)
        print(update_command)
        cur.execute(update_command, (str(new_data), int(row) - 1))
        sqlite_db.commit()
        sqlite_db.close()
    except Exception as e:
        print("something wrong with" + row)
        print(e)
    # client.login()
    # my_dict = {"name":1, "block":2, "startdate":4, "enddate":5, "purpose":6}
    # loan.update_cell(row, my_dict[col], new_data)

def update_items(row, new_data):
    command = "SELECT * FROM loan"
    sqlite_db = sqlite3.connect(config.loan_db)
    cur = sqlite_db.cursor()
    cur.execute(command)
    all_loans = cur.fetchall()
    user_details = all_loans[int(row) - 2]
    update_command = "UPDATE loan SET item = ? WHERE ROWID = ?"
    cur.execute(update_command, (str(new_data), int(row) - 1))
    sqlite_db.commit()
    sqlite_db.close()
    # client.login()
    # loan.update_cell(row, 3, new_data)

def get_table_name():
    try:
        command = "SELECT name FROM sqlite_master WHERE type = 'table';"
        sqlite_db = sqlite3.connect(config.inv_db)
        cur = sqlite_db.cursor()
        cur.execute(command)
        categories = cur.fetchall()
        return categories
    except:
        print("Error while quering database")

def get_from_inv_db(category):
    command = "SELECT Equipment, In_Stock FROM '{}'".format(category)
    sqlite_db = sqlite3.connect(config.inv_db)
    cur = sqlite_db.cursor()
    cur.execute(command)
    items = cur.fetchall()
    return items

def stock_taking(category, item, quantity, lending):
    try:
        select_command = "SELECT In_Stock, On_Loan FROM '{}' WHERE Equipment = '{}'".format(category, item)
        update_command = "UPDATE '{}' set In_Stock = ?, On_Loan = ? WHERE Equipment = '{}'".format(category, item)
        sqlite_db = sqlite3.connect(config.inv_db)
        cur = sqlite_db.cursor()
        cur.execute(select_command)
        existing_quantity = cur.fetchall()
        in_stock_qty = existing_quantity[0][0]
        on_loan_qty = existing_quantity[0][1]
        if lending:
            new_in_stock = int(in_stock_qty) - int(quantity)
            new_on_loan = int(on_loan_qty) + int(quantity)
        else:
            new_in_stock = int(in_stock_qty) + int(quantity)
            new_on_loan = int(on_loan_qty) - int(quantity)
        cur.execute(update_command, (new_in_stock, new_on_loan,))
        sqlite_db.commit()
        sqlite_db.close()
    except:
        print("database error")

def add_or_remove(user_id, category, item, quantity, add):
    if add:
        select_command = "SELECT items_to_add FROM users WHERE user_id = {}".format(user_id)
        update_command = "UPDATE users SET items_to_add = ? WHERE user_id = {}".format(user_id)
    else:
        select_command = "SELECT items_to_remove FROM users WHERE user_id = {}".format(user_id)
        update_command = "UPDATE users SET items_to_remove = ? WHERE user_id = {}".format(user_id)
    data = category + "," + item + "," + quantity
    sqlite_db = sqlite3.connect(config.db)
    cur = sqlite_db.cursor()
    cur.execute(select_command)
    existing_items = cur.fetchall()[0][0]
    new_items = existing_items + "\n" + category + "," + item + "," + quantity
    cur.execute(update_command, (new_items,))
    sqlite_db.commit()
    sqlite_db.close()

def produce_worksheet():
    command = 'SELECT * FROM loan'
    hist_command = 'SELECT * FROM loan_history'
    sqlite_db = sqlite3.connect(config.loan_db)
    cur = sqlite_db.cursor()
    cur.execute(command)
    all_loans = cur.fetchall()
    cur.execute(hist_command)
    hist_loan = cur.fetchall()
    now = datetime.datetime.now()
    timing = 'Updated on {}'.format(now.strftime("%Y-%m-%d"))
    name = 'SHM_loans.xlsx'
    workbook = xlsxwriter.Workbook(name)
    worksheet = workbook.add_worksheet('loans')
    worksheet2 = workbook.add_worksheet('loan history')
    bold = workbook.add_format({'bold': 1})
    worksheet.write('A1', 'Name', bold)
    worksheet.write('B1', 'Block', bold)
    worksheet.write('C1', 'Item', bold)
    worksheet.write('D1', 'Start Date', bold)
    worksheet.write('E1', 'End Date', bold)
    worksheet.write('F1', 'Purpose', bold)
    worksheet.write('G1', 'Telegram Username', bold)
    worksheet.write('J1', timing, bold)
    worksheet2.write('A1', 'Name', bold)
    worksheet2.write('B1', 'Block', bold)
    worksheet2.write('C1', 'Item', bold)
    worksheet2.write('D1', 'Start Date', bold)
    worksheet2.write('E1', 'End Date', bold)
    worksheet2.write('F1', 'Purpose', bold)
    worksheet2.write('G1', 'Telegram Username', bold)
    row = 1
    col = 0
    for name, block, item, start_date, end_date, purpose, telegram_username in (all_loans):
        worksheet.write_string(row, col, name)
        worksheet.write_string(row, col + 1, block)
        worksheet.write_string(row, col + 2, item)
        worksheet.write_string(row, col + 3, start_date)
        worksheet.write_string(row, col + 4, end_date)
        worksheet.write_string(row, col + 5, purpose)
        worksheet.write_string(row, col + 6, telegram_username)
        row += 1
    row = 1
    col = 0
    for name, block, item, start_date, end_date, purpose, telegram_username in (hist_loan):
        worksheet2.write_string(row, col, name)
        worksheet2.write_string(row, col + 1, block)
        worksheet2.write_string(row, col + 2, item)
        worksheet2.write_string(row, col + 3, start_date)
        worksheet2.write_string(row, col + 4, end_date)
        worksheet2.write_string(row, col + 5, purpose)
        worksheet2.write_string(row, col + 6, telegram_username)
        row += 1
    workbook.close()
    sqlite_db.close()
    return True

def update_gsheet_inv():
    try:
        client.login()
        list_of_cam_bodies = camera_bodies_list.get_all_values()
        count_cam = len(list_of_cam_bodies)
        ct = count_cam + 1
        data1 = []
        for i in list_of_cam_bodies[1:]:
            data1.append((i[0], i[3], i[4]))
        category = 'Camera Bodies'
        del_command = "DELETE FROM '{}'".format(category)
        sqlite_db = sqlite3.connect(config.inv_db)
        cur = sqlite_db.cursor()
        cur.execute(del_command)
        for i in data1:
            ins_command = "INSERT INTO '{}' VALUES(?, ?, ?)".format(category)
            cur.execute(ins_command, (i[0], i[1], i[2]))
        sqlite_db.commit()
        sqlite_db.close() #done for cam bodies
        list_of_lens = lens_list.get_all_values()
        count_lens = len(list_of_lens)
        ct = count_lens + 1
        data1 = []
        for i in list_of_lens[1:]:
            data1.append((i[0], i[3], i[4]))
        print(data1)
        category = 'Lens'
        del_command = "DELETE FROM '{}'".format(category)
        sqlite_db = sqlite3.connect(config.inv_db)
        cur = sqlite_db.cursor()
        cur.execute(del_command)
        for i in data1:
            ins_command = "INSERT INTO '{}' VALUES(?, ?, ?)".format(category)
            cur.execute(ins_command, (i[0], i[1], i[2]))
        sqlite_db.commit()
        sqlite_db.close() # done for cam lens
        list_of_batt = batteries_list.get_all_values()
        count_batt = len(list_of_batt)
        ct = count_batt + 1
        data1 = []
        for i in list_of_batt[1:]:
            data1.append((i[0], i[3], i[4]))
        print(data1)
        category = 'Batteries'
        del_command = "DELETE FROM '{}'".format(category)
        sqlite_db = sqlite3.connect(config.inv_db)
        cur = sqlite_db.cursor()
        cur.execute(del_command)
        for i in data1:
            ins_command = "INSERT INTO '{}' VALUES(?, ?, ?)".format(category)
            cur.execute(ins_command, (i[0], i[1], i[2]))
        sqlite_db.commit()
        sqlite_db.close() # done for cam batt
        list_of_memorycard = memory_card_list.get_all_values()
        count_mem = len(list_of_memorycard)
        ct = count_mem + 1
        data1 = []
        for i in list_of_memorycard[1:]:
            data1.append((i[0], i[3], i[4]))
        print(data1)
        category = 'Memory Cards'
        del_command = "DELETE FROM '{}'".format(category)
        sqlite_db = sqlite3.connect(config.inv_db)
        cur = sqlite_db.cursor()
        cur.execute(del_command)
        for i in data1:
            ins_command = "INSERT INTO '{}' VALUES(?, ?, ?)".format(category)
            cur.execute(ins_command, (i[0], i[1], i[2]))
        sqlite_db.commit()
        sqlite_db.close() # done for cam mem
        list_of_cam_equip = camera_equipments_list.get_all_values()
        count_equ = len(list_of_cam_equip)
        ct = count_equ + 1
        data1 = []
        for i in list_of_cam_equip[1:]:
            data1.append((i[0], i[3], i[4]))
        print(data1)
        category = 'Camera Equipments'
        del_command = "DELETE FROM '{}'".format(category)
        sqlite_db = sqlite3.connect(config.inv_db)
        cur = sqlite_db.cursor()
        cur.execute(del_command)
        for i in data1:
            ins_command = "INSERT INTO '{}' VALUES(?, ?, ?)".format(category)
            cur.execute(ins_command, (i[0], i[1], i[2]))
        sqlite_db.commit()
        sqlite_db.close() # done for cam equp
    except Exception as e:
        print(e)
        pass
    
    
    

    
