# import getpass
import pyodbc
import pypyodbc
import monkeyFunctions as mnky
import sql
import csv
import os
import pandas as pd
import requests
import json




# API Work
############################################################################################################
# required credentials to get auth token assigned to variables
api_key = input("Enter the Client API Key: ")
type(api_key)
api_secret = input("Enter the Client API Secret: ")
type(api_secret)


def get_auth_token(key=None):                                                           # function to get API auth token
    if key is None:
        key = {'client_id': api_key, 'client_secret': api_secret}
    dest_token = requests.get('https://monkeyconnect.mnkysoft.com/monkeytoken', params=key)
    dest_access_token = dest_token.json()
    type(dest_access_token)
    return dest_access_token['access_token']                                            # returns a dictionary value for specific key 'access_token'
#
#
# print(get_auth_token())                         # Test Function
#
#
def put_clients(data_file,member_id):                                                    # Function to put (update) clients, requires loyaltyPrograms node
    headers = {'content-type': 'application/json', 'Authorization': 'Bearer ' + str(get_auth_token())}
    print(headers)
    put_response = requests.put('https://monkeyconnect.mnkysoft.com/clients/' + str(member_id),
                                data=data_file, headers=headers)
    return put_response                                                                 # returns status code of API request
#
# # print(put_clients(240178))                    # Test Function
#
#
def get_clients(member_id):                                                             # Function to get clients, only returns client loyalty Programs node
    headers = {'content-type': 'application/json', 'Authorization': 'Bearer ' + str(get_auth_token())}
    get_response = requests.get('https://monkeyconnect.mnkysoft.com/clients/' + str(member_id), headers=headers)
    return get_response.json()['loyaltyPrograms'][0]                                      # Returns dictionary {key: value} of selected columns
#
#print(get_clients(240178))                      # Test Function
############################################################################################################

# CSV work
############################################################################################################
from csv import DictReader

def setup_data(file):                                                                   # wrapper function

    with open(file,'r') as f:                                                           # opens .csv of data type "file", read only, aliased as f
        reader = DictReader(f)                                                          # creation of DictReader object (basically a cursor)
        for row in reader:                                                              # creation of variable that iterates through each line
            member_id = row['id']                                                       # variable assigned to Dict(Key) = 'id'
            prelim_json = row                                                           # assigns variable to current row (dictionary type)
            prelim_json['loyaltyPrograms'] = [get_clients(member_id)]                   # creates Dict(Key) loyaltyPrograms, assigns results of get_clients(current member_id) as value
            del prelim_json['id']                                                       # client_id not editable in API, removes from Dict

            print(json.dumps(prelim_json))                                              # prints raw data being sent in request

            print(put_clients(json.dumps(prelim_json), member_id))                      # sends request and prints result code


setup_data('temp_test.csv')                                                             # file for wrapper function


############################################################################################################


# DB Connection

############################################################################################################

# dbserver = 'server goes here'
# db = "db name here"
# dbuser = 'username here'
# driver = 'ODBC Driver 17 for SQL Server'
# dbpass = 'pwgoeshere'


# print(pyodbc.drivers())

# connection string using pypyodbc, added ssl encryption, and server certificate exemptions - still gives login timeout error

# conn_string = 'Driver={ODBC Driver 17 for SQL Server};Server=' + dbserver + ';Database=' + db + ';UID=' + dbuser + ';' + 'EncryptionMethod=SSL;' + 'Encrypt=yes;' + 'TrustServerCertificate=yes;' + 'hostNameInCertificate=*.database.windows.net;' + 'Connection Timeout=30;' + 'Authentication=ActiveDirectoryInteractive;'
# cnct = pypyodbc.connect(conn_string)


# connection string using pyodbc gives login timeout

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


# connection string using mnkyfunctions (pypyodbc) - doesnt work, login timeout

# connection = monkeyFunctions.DBConnections(dbserver, dbuser, dbpass).azure_connect('dev223_monkeymedia_ca_01')

############################################################################################################
