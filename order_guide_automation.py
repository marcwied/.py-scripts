import requests
import csv
import json
import pyodbc
from itertools import groupby
import itertools
import pandas as pd
import xlwt

def azure_connect(dbserver: str, db: str, dbuser: str) -> object:
    """Connect to Azure database
​
    Args:
        dbserver (str): database server to connect to
        db (str): The database on the server
        dbuser (str): The database user making the connection
​
    Returns:
        object: The pyodbc database connection object
    """
    return pyodbc.connect("Driver={ODBC Driver 17 for SQL Server};"
                          "Server=tcp:" + dbserver + ",1433;"
                                                     "Database=" + db + ";"
                                                                        "UID=" + dbuser + ";"
                                                                                          "EncryptionMethod=SSL;"
                                                                                          "MultipleActiveResultSets=False;"
                                                                                          "Encrypt=yes;"
                                                                                          "TrustServerCertificate=yes;"
                                                                                          "hostNameInCertificate=*.database.windows.net;"
                                                                                          "Connection Timeout=45;"
                                                                                          "ApplicationIntent=ReadOnly;"
                                                                                          "Authentication=ActiveDirectoryInteractive")


def get_auth_token(key=None):
    """

    Args:
        key: defaulted to none, client_id & secret prompted during runtime

    Returns:
        API authorization token required for various API calls

    """
    if key is None:
        key = {'client_id': api_key, 'client_secret': api_secret}
    dest_token = requests.get('server url/endpoint', params=key)
    dest_access_token = dest_token.json()
    type(dest_access_token)
    return dest_access_token['access_token']


def get_og(og_id: str):
    """
    utilizes API GET call for against specified order guide ID
    Args:
        og_id: string ID passed into function from loop in build_og_dict()

    Returns:
        JSON containing all data from specific order guide ID

    """
    headers = {'content-type': 'application/json', 'Authorization': 'Bearer ' + str(get_auth_token())}
    get_response = requests.get('server url/endpoint/' + str(og_id) + '?details=true',
                                headers=headers)
    return get_response.json()


def build_og_dict():
    """
    loops through list of order guides IDs, adds order guide name as key, and the data for the order guide as the value

    Returns:
        dictionary containing order guide info key

    """
    # initialize order guide dictionary
    ogdict = {}

    # iterates over list of order guides, compiled based on user prompts.  Assigns order guide name (key) to order guide data (value)
    for og in og_list:
        ogdict[og[1]] = get_og(og[0])
    return ogdict

def put_og(og_json):
    """
    sends data file through API post function to update order guide information with new data

    Args:
        og_json: takes data in json format

    Returns:
        body of json sent through the API

    """
    headers = {'content-type': 'application/json', 'Authorization': 'Bearer ' + str(get_auth_token())}
    get_response = requests.post('server url/endpoint', data=og_json,
                                headers=headers)
    print(get_response.status_code)
    # if item fails to update against an order guide, the item and order guide are added to a list for later processing
    if get_response.status_code == 500:
        failed_updates.append(json.loads(og_json))
    return get_response.request.body


def build_payload(item_id, prod_items):
    """
    This function utilizes the API get to write menu item and production item info against an order guide to a .csv

    Args:
        item_id: takes a single item id to process against a list of order guides
        prod_items: variable to hold boolean for including/exluding production items in the export

    Returns:
        writes item info for specific item_id and order guide prices for all order guides item is available for to a single line in .csv

    """
    # initialize payload (menu items) and sub-payload (production items) dictionaries.  ititialize production item list
    payload = {}
    sub_payload = {}
    prod_item_list = []

    # iterates over current order guide dictionary from build_og_dict()
    for key, value in og_prices.items():
        categories = value['menus'][0]['categories']
        for cat_data in categories:
            groups = cat_data['groups']
            for group in groups:
                items = group['items']['item']
                for item in items or []:

                    # checks if the current item from the Order Guide JSON matches the item id variable.  On a match, payload is updated with name of order guide (key) and the price for that item (value)
                    if item['id'] == item_id:

                        dict = {key: item['price']}
                        payload.update(dict)
                        print(f'{item_id} has been processed against {key}')

                        # checks if user has opted to include production items, if yes, script iterates over all prod item data and adds to the production item list
                        if prod_items == 'y':

                            selectionGroups = item['selectionGroups']
                            for selectionGroup in selectionGroups or []:
                                subItems = selectionGroup['subItems']
                                for prodItem in subItems:
                                    if selectionGroups == 'None':

                                        prod_dict = {'menu': '', 'category': 'Production Item', 'group': '',
                                                     'menu_item_id': item['id'],
                                                     'production_item_id': prodItem['id'], 'item': prodItem['name']}

                                        prod_dict.update({key: prodItem['price']})
                                        prod_item_list.append(prod_dict)


                                    else:
                                        print(selectionGroup)
                                        prod_dict = {'menu': '', 'category': 'Production Item', 'group': '',
                                                     'menu_item_id': item['id'],
                                                     'production_item_id': prodItem['id'], 'item': prodItem['name'],
                                                     'max_quantity': selectionGroup['maxQuanity'],
                                                     'input_type': selectionGroup['inputType']}

                                        if selectionGroup['disallowFrontEnd'] == 0:
                                            prod_dict.update({'available_frontEnd': 'yes'})
                                        else:
                                            prod_dict.update({'available_frontEnd': 'no'})

                                        if selectionGroup['disallowBackEnd'] == 0:
                                            prod_dict.update({'available_admin': 'yes'})
                                        else:
                                            prod_dict.update({'available_admin': 'no'})

                                        prod_dict.update({key: prodItem['price']})
                                        prod_item_list.append(prod_dict)


                    else:
                        continue

                # iterates over parent item nodes
                parent_items = group['items']['parent']
                for item2 in parent_items or []:
                    child_items = item2['items']
                    for child in child_items:

                        # if child item id matches item_id variable, payload is updated with name of order guide (key) and the price for that item (value)
                        if child['id'] == item_id:
                            dict = {key: child['price']}
                            payload.update(dict)
                            print(f'{item_id} has been processed against {key}')

                            # checks if user has opted to include production items, if yes, script iterates over all prod item data and adds to the production item list
                            # includes data for prod items such as, basic item info and menu mapping configuration including FE/BE visibility, quantity limitations and input type
                            if prod_items == 'y':

                                selectionGroups = child['selectionGroups']
                                for selectionGroup in selectionGroups or []:
                                    subItems = selectionGroup['subItems']
                                    for prodItem in subItems:
                                        if selectionGroups == 'None':

                                            prod_dict = {'menu': '', 'category': 'Production Item', 'group': '',
                                                         'menu_item_id': child['id'],
                                                         'production_item_id': prodItem['id'], 'item': prodItem['name']}

                                            prod_dict.update({key: prodItem['price']})
                                            prod_item_list.append(prod_dict)


                                        else:
                                            print(selectionGroup)
                                            prod_dict = {'menu': '', 'category': 'Production Item', 'group': '',
                                                         'menu_item_id': child['id'],
                                                         'production_item_id': prodItem['id'], 'item': prodItem['name'],
                                                         'max_quantity': selectionGroup['maxQuanity'],
                                                         'input_type': selectionGroup['inputType']}

                                            if selectionGroup['disallowFrontEnd'] == 0:
                                                prod_dict.update({'available_frontEnd': 'yes'})
                                            else:
                                                prod_dict.update({'available_frontEnd': 'no'})

                                            if selectionGroup['disallowBackEnd'] == 0:
                                                prod_dict.update({'available_admin': 'yes'})
                                            else:
                                                prod_dict.update({'available_admin': 'no'})

                                            prod_dict.update({key: prodItem['price']})
                                            prod_item_list.append(prod_dict)

                        else:
                            continue

        # queries DB for default info on specific menu item based on item_id, needed for payload headers
        default_info = cursor.execute(
            "select product_class_name, product_group_name, product_name, product_sub_id, product_sub_name from dbo.product_sub_real psr JOIN dbo.product_real pr ON psr.product_id = pr.product_id JOIN dbo.product_group_real pgr ON pr.product_group_id = pgr.product_group_id JOIN dbo.product_class_real pcr ON pgr.product_class_id = pcr.product_class_id WHERE product_sub_id =" + str(
                item_id))
        for y in default_info:

            # assigns values to .csv headers based on query results
            payload['menu'] = y[0]
            payload['category'] = y[1]
            payload['group'] = y[2]
            payload['menu_item_id'] = item_id
            payload['item'] = y[4]

        default_price = cursor.execute(
            "SELECT product_sub_price from dbo.product_sub_real where product_sub_id =" + str(
                item_id))
        for x in default_price:
            payload['defaultPrice'] = x[0]

    print(payload)

    # writes the payload to the .csv after item_id has been processed against all order guides being iterated over
    w.writerow(payload)

    # checks if user opted for production items, if yes, the production item list is processed and final data added to final_prod_list
    if prod_items == 'y':
        final_prod_list = []
        #iterates over the range of the prod item list
        for i in range(len(prod_item_list)):
            # removes duplicate entries and adds to final list
            if prod_item_list[i] not in prod_item_list[i + 1:]:
                final_prod_list.append(prod_item_list[i])

        # groupby requires the container to be sorted by the key
        sortkey = lambda x: x['production_item_id']
        final_prod_list.sort(key=sortkey)

        # "key" is the common key for the items
        # "items" is an iterator of the common items
        for key, items2 in groupby(final_prod_list, key=sortkey):
            # empty dict for each common key
            dct = {}
            for ii in items2:

                # add all key/value pairs for each common key item to the dict
                dct.update(ii)
            # update sub_payload with dct
            sub_payload.update(dct)
            print(sub_payload)

            # writes sub_payload to a single line
            w.writerow(sub_payload)

    print(f'Menu Item ID:{item_id} Processed')



# ************************************************************
server = "server url"
devnum = input(str('Enter Dev Number: '))

database = 'dev' + str(devnum) + 'server url'
user = input('Enter Azure Username (including domain): ')

#initial DB connection object
cnxn = azure_connect(server, database, user)
cursor = cnxn.cursor()


# init list of order guides to process for GET or POST
og_list = []
# init .csv headers for GET
og_headers = ['menu', 'category', 'group', 'menu_item_id', 'production_item_id', 'item', 'max_quantity', 'input_type', 'available_admin', 'available_frontEnd', 'defaultPrice']

if devnum == '100':
    api_key = 'enter api key here'
    type(api_key)
    api_secret = 'enter api secret'
    type(api_secret)

if devnum != '100':
    api_key = 'monkey' + str(devnum)
    type(api_key)
    secret_container = cursor.execute("select replace (client_secret, '{noop}', '') as [client_secret] from dbo.api_auth where api_key = ? ", api_key)
    api_secret = ''
    for element in secret_container:
        api_secret = element[0]
    type(api_secret)

# prompts user for desired API function (GET or POST)
get_or_post = input('Get or Post? \n'
                    '1 - GET\n'
                    '2 - POST\n')

# GET ENGINE
if get_or_post == '1':

    # prompts user for the types of menu items they'd like to see (Catering or Takeout)
    menu_item_types = input("Please enter which of the following you'd like to process: \n"
                            "1 - Catering Menu Items\n"
                            "2 - Takeout Menu Items\n")
    # init menu items list
    menu_items = []

    # prompts user if they want to include Production items in the GET
    prod_items = input("Do you want to include production items? (Y/N) ").lower()

    # ENGINE for ONLY Catering Items
    if menu_item_types == '1':

        # prompts user for the Order Guides they would like to process the Menu Items against.
        # Options are to specify stores codes (which adds their OGs to the list)
        # specify order guides by ID, or process all order guides assigned to an active store
        og_selection = input(
            "Which Order Guides do you want to process?\n"
            "1 - All Active Stores/Order Guides\n"
            "2 - List of Order Guide IDs\n"
            "3 - List of Store Codes\n")

        # adds all current order guides for active stores to og_list
        if og_selection == '1':
            cursor.execute(
                "SELECT DISTINCT og_base_id, ogt.og_template_name "
                "FROM [dbo].[store_order_guides] sog  "
                "JOIN dbo.store s ON sog.store_id = s.store_id  "
                "JOIN dbo.order_guide_base ogb ON sog.og_template_id = ogb.og_template_id  "
                "JOIN dbo.order_guide_template ogt ON sog.og_template_id = ogt.og_template_id "
                "where sog.store_id IN (SELECT store_id from dbo.store where store_status = 1 AND ogb.[status] = 1)"
                "AND sog.product_class_id = 16")
            for row in cursor:
                og_list.append(row)

                # adds order guide name to .csv headers
                og_headers.append(row[1])

        # adds order guides to og_list based on order guide ids provided by user
        elif og_selection == '2':
            order_guide_list_entry = input("Enter Order Guide Base IDs separated by comma (no spaces): ")
            cursor.execute("SELECT DISTINCT ogb.og_base_id, ogt.og_template_name "
                           "FROM dbo.order_guide_base ogb "
                           "JOIN dbo.order_guide_template ogt ON ogb.og_template_id = ogt.og_template_id "
                           "where ogb.og_base_id IN" + '(' + str(order_guide_list_entry) + ')')
            for row in cursor:
                og_list.append(row)
                og_headers.append(row[1])

        # adds order guides to og_list based on store codes provided by user
        else:
            store_codes = input("Enter list of Store Codes separated by comma: ")
            stores = store_codes.split(',')
            for store_code in stores:
                cursor.execute("""SELECT DISTINCT og_base_id, ogt.og_template_name
                FROM [dbo].[store_order_guides] sog
                JOIN dbo.store s ON sog.store_id = s.store_id
                JOIN dbo.order_guide_base ogb ON sog.og_template_id = ogb.og_template_id
                JOIN dbo.order_guide_template ogt ON sog.og_template_id = ogt.og_template_id WHERE s.store_id IN (
                SELECT store_id FROM dbo.store WHERE store_code = ?)""", store_code)
                for row in cursor:
                    og_list.append(row)
                    og_headers.append(row[1])

        print(og_list)

        # queries DB for CATERING menu items that are currently active and NOT parent items, adds item_id to menu_items list
        cursor.execute(
            "select product_sub_id, product_sub_name "
            "from dbo.product_sub_real psr "
            "JOIN dbo.product_real pr ON psr.product_id = pr.product_id "
            "JOIN dbo.product_group_real pgr ON pr.product_group_id = pgr.product_group_id "
            "JOIN dbo.product_class_real pcr ON pgr.product_class_id = pcr.product_class_id "
            "where product_sub_status = 1 AND pcr.product_class_id IN (16) "
            "AND pr.product_status = 1 AND pgr.product_group_status = 1 AND psr.is_parent = 0 order by product_sub_id")

        for row in cursor:
            menu_items.append(row[0])

    # ENGINE for ONLY Takeout Items
    if menu_item_types == '2':

        # prompts user for the Order Guides they would like to process the Menu Items against.
        # Options are to specify stores codes (which adds their OGs to the list)
        # specify order guides by ID, or process all order guides assigned to an active store
        og_selection = input(
            "Which Order Guides do you want to process?\n"
            "1 - All Active Stores/Order Guides\n"
            "2 - List of Order Guide IDs\n"
            "3 - List of Store Codes\n")

        # adds all current order guides for active stores to og_list
        if og_selection == '1':
            cursor.execute(
                "SELECT DISTINCT og_base_id, ogt.og_template_name "
                "FROM [dbo].[store_order_guides] sog  "
                "JOIN dbo.store s ON sog.store_id = s.store_id  "
                "JOIN dbo.order_guide_base ogb ON sog.og_template_id = ogb.og_template_id  "
                "JOIN dbo.order_guide_template ogt ON sog.og_template_id = ogt.og_template_id "
                "where sog.store_id IN (SELECT store_id from dbo.store where store_status = 1 AND ogb.[status] = 1)"
                "AND sog.product_class_id = 24")
            for row in cursor:
                og_list.append(row)

                # adds order guide name to .csv headers
                og_headers.append(row[1])

        # adds order guides to og_list based on order guide ids provided by user
        elif og_selection == '2':
            order_guide_list_entry = input("Enter Order Guide Base IDs separated by comma (no spaces): ")
            cursor.execute("SELECT DISTINCT ogb.og_base_id, ogt.og_template_name "
                           "FROM dbo.order_guide_base ogb "
                           "JOIN dbo.order_guide_template ogt ON ogb.og_template_id = ogt.og_template_id "
                           "where ogb.og_base_id IN" + '(' + str(order_guide_list_entry) + ')')
            for row in cursor:
                og_list.append(row)

                # adds order guide name to .csv headers
                og_headers.append(row[1])

        # adds order guides to og_list based on store codes provided by user
        else:
            store_codes = input("Enter list of Store Codes separated by comma: ")
            stores = store_codes.split(',')
            for store_code in stores:
                cursor.execute("""SELECT DISTINCT og_base_id, ogt.og_template_name
                            FROM [dbo].[store_order_guides] sog
                            JOIN dbo.store s ON sog.store_id = s.store_id
                            JOIN dbo.order_guide_base ogb ON sog.og_template_id = ogb.og_template_id
                            JOIN dbo.order_guide_template ogt ON sog.og_template_id = ogt.og_template_id WHERE s.store_id IN (
                            SELECT store_id FROM dbo.store WHERE store_code = ?)""", store_code)
                for row in cursor:
                    og_list.append(row)
                    og_headers.append(row[1])

        print(og_list)

        # queries DB for TAKEOUT menu items that are currently active and NOT parent items, adds item_id to menu_items list
        cursor.execute(
            "select product_sub_id, product_sub_name "
            "from dbo.product_sub_real psr "
            "JOIN dbo.product_real pr ON psr.product_id = pr.product_id "
            "JOIN dbo.product_group_real pgr ON pr.product_group_id = pgr.product_group_id "
            "JOIN dbo.product_class_real pcr ON pgr.product_class_id = pcr.product_class_id "
            "where product_sub_status = 1 AND pcr.product_class_id IN (24) "
            "AND pr.product_status = 1 AND pgr.product_group_status = 1 AND psr.is_parent = 0 order by product_sub_id")

        for row in cursor:
            menu_items.append(row[0])

    # prompts user for file name the script should write to
    filename = input('What is the file name to write to? ')
    with open(filename, 'w') as f:

		# writer object
        w = csv.DictWriter(f, fieldnames=og_headers)
        w.writeheader()
        
        # list of order guides in header to iterate over
        updateOGs = og_headers[11:]
        
        #dict containing row 2 headers data - this row lists the order guide ID directly under the order guide name
        ogiddict = {'menu': '', 'category': '', 'group': '', 'menu_item_id': '',
                                     'production_item_id': '', 'item': '', 'max_quantity': '',
                                     'input_type': '', 'available_admin': '', 'available_frontEnd': '',
                                     'defaultPrice': 'OG Base ID:'}
		
		#dict containing row 3 headers data - this row lists call stores currently assigned to the order guide
        ogid_store_dict = {'menu': '', 'category': '', 'group': '', 'menu_item_id': '',
                    'production_item_id': '', 'item': '', 'max_quantity': '',
                    'input_type': '', 'available_admin': '', 'available_frontEnd': '',
                    'defaultPrice': 'Assigned Stores'}
        temp_store_list = []

        for ogname in updateOGs:
            for ogitem in og_list:
                if ogname == ogitem[1]:
                    ogiddict.update({ogname: ogitem[0]})

                else:
                    continue

			# queries db for store codes assigned to the current ogname
            cursor.execute(
                '''SELECT DISTINCT store_code
                    from dbo.store s
                    JOIN dbo.store_order_guides sog ON s.store_id = sog.store_id
                    JOIN dbo.order_guide_template ogt ON sog.og_template_id = ogt.og_template_id
                    where ogt.og_template_name = ?''', ogname)
            for rowx in cursor:
                temp_store_list.append(rowx[0])
            ogid_store_dict.update({ogname: temp_store_list})



        print(og_headers)
        w.writerow(ogiddict)
        w.writerow(ogid_store_dict)

    # once .csv is opened, og_prices is initialized with a list of dictionaries of order guides and their data
        og_prices = build_og_dict()

        # menu_items list is iterated over and build_payload is called for every menu item in the list
        for item in menu_items:
            build_payload(item, prod_items)
        file_reader = pd.read_csv(filename)
        file_reader.to_excel(filename + '.xls')

# POST ENGINE
if get_or_post == '2':

    # prompts for filename to be processed for POST
    filename2 = input('What is the file name? ')

    # init list for items that fail to update
    failed_updates = []

    # opens .csv
    with open(filename2, 'r') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',')

        # init list of order guides based on .csv headers
        updateOGs = reader.fieldnames[11:]

        for row in reader:

            # iterates over list of order guides and appends their ids to og_list
            for og_item in updateOGs:
                cursor.execute("""
                SELECT DISTINCT og_base_id
                FROM order_guide_base ogb
                JOIN order_guide_template ogt ON ogb.og_template_id = ogt.og_template_id
                WHERE ogt.og_template_name = ?
                AND ogb.status = 1""", og_item)
                for row2 in cursor:
                    og_list.append(row2)
                og_list_list = list(itertools.chain(*og_list))

                # init post_payload which will hold JSON for the POST
                post_payload = {}

                # ENGINE for Production Items
                if row['category'] == 'Production Item':

                    # if yes, DB is queried for production item info and is appended to list item_info
                    item_info = []

                    cursor.execute("""
                                                                    SELECT pcr.product_class_id, pgr.product_group_id, pr.product_id
                                                                    from dbo.product_sub_real psr
                                                                    JOIN dbo.product_real pr ON psr.product_id = pr.product_id
                                                                    JOIN dbo.product_group_real pgr ON pr.product_group_id = pgr.product_group_id
                                                                    JOIN dbo.product_class_real pcr ON pgr.product_class_id = pcr.product_class_id
                                                                    where product_sub_id = ?""", row['menu_item_id'])
                    for row3 in cursor:
                        item_info.append(row3)
                    item_info_list = list(itertools.chain(*item_info))

                    # item_info is processed and its contents are passed to a final list
                    if row[og_item] != '':
                        for ogid in og_list_list:

                            # final list is iterated over and the data inside is used to build the json required for POST
                            post_payload.update({'id': ogid, 'menus': [{'id': item_info_list[0], 'categories': [{'id': item_info_list[1], 'groups': [{'id': item_info_list[2], 'items': {'item': [{'id': row['menu_item_id'], 'price': '', 'selectionGroups':[{'subItems':[{'id': row['production_item_id'], 'price': row[og_item]}]}]}]}}]}]}]})

                    elif row[og_item] == '':
                        for ogid in og_list_list:

                            # final list is iterated over and the data inside is used to build the json required for POST
                            post_payload.update({'id': ogid, 'menus': [{'id': item_info_list[0], 'categories': [
                                {'id': item_info_list[1], 'groups': [{'id': item_info_list[2], 'items': {'item': [
                                    {'id': row['menu_item_id'], 'price': '', 'selectionGroups': [{'subItems': [
                                        {'id': row['production_item_id'], 'price': 0}]}]}]}}]}]}]})

                # ENGINE for Menu Items
                else:
                    item_info = []

                    # DB queried for Item Info and appended to item_info list
                    cursor.execute("""
                                                                    SELECT pcr.product_class_id, pgr.product_group_id, pr.product_id
                                                                    from dbo.product_sub_real psr
                                                                    JOIN dbo.product_real pr ON psr.product_id = pr.product_id
                                                                    JOIN dbo.product_group_real pgr ON pr.product_group_id = pgr.product_group_id
                                                                    JOIN dbo.product_class_real pcr ON pgr.product_class_id = pcr.product_class_id
                                                                    where product_sub_id = ?""", row['menu_item_id'])
                    for row3 in cursor:
                        item_info.append(row3)
                    item_info_list = list(itertools.chain(*item_info))
                    for ogid in og_list_list:

                        # if menu item has null price in .csv, this disables item via days of the week availability
                        if row[og_item] == '':
                            post_payload.update({'id': ogid, 'menus': [{'id': item_info_list[0], 'categories': [
                                {'id': item_info_list[1], 'groups': [{'id': item_info_list[2], 'items': {'item': [
                                    {'id': row['menu_item_id'], 'price': row[og_item],
                                     'availability': []}]}}]}]}]})

                        # item is updated with price given in .csv
                        else:
                            post_payload.update({'id': ogid, 'menus': [{'id': item_info_list[0], 'categories': [
                                {'id': item_info_list[1], 'groups': [{'id': item_info_list[2], 'items': {'item': [
                                    {'id': row['menu_item_id'], 'price': row[og_item],
                                     'availability': ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday',
                                                      'saturday']}]}}]}]}]})

                # calls API POST and prints JSON that is sent
                print(put_og(json.dumps(post_payload)))

    # init vars for failed updates
    ogname = ''
    itemname = ''

    # opens new .csv to log failed updates
    with open('failed_updates.csv', 'w') as ff:

        # iterates over list of failed updates
        for failure in failed_updates:
            ogid = failure['id']
            itemid = failure['menus'][0]['categories'][0]['groups'][0]['items']['item'][0]['id']
            price = failure['menus'][0]['categories'][0]['groups'][0]['items']['item'][0]['price']
            cursor.execute(
                """select og_template_name
                    from order_guide_template ogt
                    JOIN order_guide_base ogb ON ogb.og_template_id = ogt.og_template_id
                    where og_base_id = ?""", ogid)
            for ogg in cursor:
                ogname = ogg[0]
                cursor.execute(
                    """select product_sub_name
                        from dbo.product_sub_real
                        where product_sub_id = ?""", itemid)
                for items in cursor:
                    itemname = items[0]
                    print([itemname, ogname])
                    w = csv.writer(ff, delimiter=',')

                    # writes menu item name, the order guide, and the price that failed to update
                    w.writerow([itemname, ogname, price])


