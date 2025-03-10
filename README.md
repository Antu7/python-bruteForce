# Simple Brute Force Attack Tools Using Python


## Simple Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install requests.

```bash
pip install requests
pip install beautifulsoup4
```

## Run

```bash
python3 bruteforce.py
```
For more please check this Medium [Link](https://medium.com/@textmeantu/brute-force-attack-with-python-c1d70fcba607)
 
### Example Image

![Screenshot from 2025-03-10 13-30-57](https://github.com/user-attachments/assets/de606bfd-1fe8-4a1a-b8dd-3a48470c5755)


For more password List check This [Git Repo](https://github.com/Antu7/password-generator)

### CSRF Token Bypass Summary

CSRF tokens protect websites from automated attacks by requiring unique, unpredictable values with each form submission. To handle these tokens in authorized security testing:

1. **Session Management**: Use a persistent session to maintain cookies between requests.

2. **Token Extraction**: Extract the CSRF token from the login page's HTML before each attempt. Look for it in hidden form fields, meta tags, or JavaScript variables.

3. **Token Inclusion**: Include the extracted token in your login request alongside username and password credentials.

4. **Fresh Tokens**: Some sites invalidate tokens after each request - always fetch a new token before each login attempt.

5. **Token Naming**: Be aware that token field names vary (csrf_token, _token, __RequestVerificationToken, etc.) and adapt your extraction method accordingly.

This technique works by mimicking legitimate browser behavior rather than truly "bypassing" the protection. Remember to only use these methods on systems you own or have permission to test.

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.


### Happy Hacking 🔥🔥
