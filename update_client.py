import requests
import json
import csv




# API Work
############################################################################################################
#required credentials to get auth token assigned to variables
api_key = input("Enter the Client API Key: ")
type(api_key)
api_secret = input("Enter the Client API Secret: ")
type(api_secret)

"""
function to get API auth token
args: none
returns: access token string
"""
def get_auth_token(key=None):
    if key is None:
        key = {'client_id': api_key, 'client_secret': api_secret}
    dest_token = requests.get('https://monkeyconnect.mnkysoft.com/monkeytoken', params=key)
    dest_access_token = dest_token.json()
    type(dest_access_token)
    return dest_access_token['access_token']

# Test Function
print(get_auth_token())

"""
function to put(send) client information
args: cleaned json file, member(from .csv)
returns: Response Status Code, 200 = Success
"""
def put_clients(data_file,member_id):
    headers = {'content-type': 'application/json', 'Authorization': 'Bearer ' + str(get_auth_token())}
    put_response = requests.put('https://monkeyconnect.mnkysoft.com/clients/' + str(member_id),
                                data=data_file, headers=headers)
    return put_response

# Test Function
# print(put_clients(clientID))


"""
function to get(retrieve) client loyalty information
args: member(from .csv)
returns: client loyalty information as a list[Dictionary]
"""
def get_clients(member_id):
    headers = {'content-type': 'application/json', 'Authorization': 'Bearer ' + str(get_auth_token())}
    get_response = requests.get('https://monkeyconnect.mnkysoft.com/clients/' + str(member_id), headers=headers)
    return get_response.json()['loyaltyPrograms']

#Test Function
#print(get_clients(240178))

############################################################################################################

# .csv work - script engine
############################################################################################################
'''
Script Considerations: 

1. .csv must include id column
2. script engines are split between loyalty/non loyalty integrated brands - will prompt at start of program
3. if your brand is integrated with loyalty but your not updating a loyaltyCardNumber for a client, leave the field blank in the .csv

'''

# prompts for loyalty status of brand
loyalty_integration = input("Does the brand have loyalty integration? (Y/N): ").lower()

# non-loyalty engine
if loyalty_integration == 'n':

    def setup_data(file):  # wrapper function

        with open(file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                member_id = row['id']

                prelim_json = row
                del prelim_json['id']
                for key, values in list(prelim_json.items()):
                    if values == '':
                        del prelim_json[key]

                print(json.dumps(prelim_json))

                print(put_clients(json.dumps(prelim_json), member_id))


    setup_data('temp_test.csv')

#loyalty engine
elif loyalty_integration == 'y':


    def setup_data(file):
        with open(file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                prelim_json = row
                member_id = prelim_json['id']

                if prelim_json['loyaltyCardNumber'] == '':
                    prelim_json['loyaltyPrograms'] = get_clients(member_id)

                else:
                    prelim_json['loyaltyPrograms'] = get_clients(member_id)
                    prelim_json['loyaltyPrograms'][0]['loyaltyCardNumber'] = row['loyaltyCardNumber']
                    del prelim_json['loyaltyCardNumber']


                for key, values in list(prelim_json.items()):
                    if values == '':
                        del prelim_json[key]

                del prelim_json['id']

                payload = json.dumps(prelim_json)

                print(f'{member_id} updated with values {payload}')
                print(f'{put_clients(payload, member_id)}      Success!')

    setup_data('temp_test.csv')


###########################################################################################################


# DB Connection
#
# ###########################################################################################################
#
# dbserver = 'server goes here'
# db = "db name here"
# dbuser = 'username here'
# driver = 'ODBC Driver 17 for SQL Server'
# dbpass = 'pwgoeshere'
#
#
# print(pyodbc.drivers())
#
# connection string using pypyodbc, added ssl encryption, and server certificate exemptions - still gives login timeout error
#
# conn_string = 'Driver={ODBC Driver 17 for SQL Server};Server=' + dbserver + ';Database=' + db + ';UID=' + dbuser + ';' + 'EncryptionMethod=SSL;' + 'Encrypt=yes;' + 'TrustServerCertificate=yes;' + 'hostNameInCertificate=*.database.windows.net;' + 'Connection Timeout=30;' + 'Authentication=ActiveDirectoryInteractive;'
# cnct = pypyodbc.connect(conn_string)
#
#
# connection string using pyodbc gives login timeout
#
# cnxn = pyodbc.connect("driver={ODBC Driver 17 for SQL Server};"
#                       "Server="+dbserver+";"
#                       "Database="+db+";"
#                       "UID="+dbuser+";"
#                       #"PWD="+dbpass+";"
#                       "TrustServerCertificate=yes;"
#                       "Authentication=ActiveDirectoryInteractive;")
# cursor = cnxn.cursor()
# cursor.execute("SELECT TOP 10 * FROM dbo.orders")
# row = cursor.fetchone()
# while row:
#     print (str(row[0]) + " " + str(row[1]))
#     row = cursor.fetchone()
#
#
# connection string using mnkyfunctions (pypyodbc) - doesnt work, login timeout
#
# connection = monkeyFunctions.DBConnections(dbserver, dbuser, dbpass).azure_connect('DBnameGoesHere')

###########################################################################################################
