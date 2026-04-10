# Python Brute Force Attack Tools

A universal brute force tool with CSRF bypass support for both traditional form-based and JSON API logins.

## Features

- Form-based login (traditional HTML forms)
- JSON API login (modern SPA/React/Vue/Angular sites)
- Universal CSRF bypass (hidden inputs, meta tags, cookies, headers)
- Auto-detection of login type, field names, and API endpoints
- Multi-threaded with progress bar
- Beautiful Rich-styled terminal output with hacker theme

---

## Installation

```bash
pip install -r requirements.txt
```

## **Note**: This version uses the Rich library for enhanced terminal UI. Make sure Rich is installed (included in requirements.txt).

## Usage

```bash
python3 bruteforce.py
```

The tool walks you through 3 steps:

### Step 1 — Target Info

You'll be asked for:

- **Login page URL** — e.g. `https://example.com/login`
- **Username / email** — the account to test
- **Wrong password error message** — log in with a wrong password in your browser, copy the exact error text (check DevTools → Network → response body if needed)

### Step 2 — Review & Adjust

The tool auto-detects field names, login mode, and API endpoint by fetching the page. Review what it found and press Enter to accept, or type a new value to override.

```
  Username field name [email]:
  Password field name [password]:
  API endpoint [https://example.com/api/login]:
  Login mode [auto]:
```

Login mode options: `auto` (use detected), `form` (HTML form POST), `api` (JSON POST).

### Step 3 — Attack Settings

- **Workers** — number of concurrent threads (default 10)
- **Password file** — path to your wordlist (default `passwords.txt`)

A summary is shown before starting. Confirm with `Y` to begin.

### Example

```
  Target login page URL: https://example.com/login
  Target username / email: admin
  Wrong password error message: Invalid email or password

  ──────────────────────────────────────────────────────────
  AUTO-DETECTING TARGET
  ──────────────────────────────────────────────────────────
  [*] Fetching login page...
  [*] Detecting login type...
  [+] Detected: JSON API login (modern/SPA site)
  [+] Username field: email
  [+] Password field: password
  [+] API endpoint: https://example.com/api/login
  [+] CSRF token: csrfmiddlewaretoken
  [+] Auto-detection complete!

  ──────────────────────────────────────────────────────────
  RESULTS
  ──────────────────────────────────────────────────────────

  PASSWORD FOUND!

  Username             admin
  Password             admin123
```

---

## Finding the Error Message

If you're not sure what to enter for the error message:

1. Open the login page in your browser
2. Open DevTools (F12) → **Network** tab
3. Submit a wrong password
4. Click the login request → **Response** tab
5. Copy the exact error text from the response

---

## CSRF Bypass

The tool automatically handles these CSRF protection methods:

| Method       | Example                                   | Frameworks             |
| ------------ | ----------------------------------------- | ---------------------- |
| Hidden Input | `<input type="hidden" name="csrf_token">` | Django, Laravel, Rails |
| Meta Tags    | `<meta name="csrf-token" content="...">`  | Rails, Laravel         |
| Cookies      | `XSRF-TOKEN` cookie                       | Express, Spring        |
| Headers      | `X-CSRFToken` header                      | Django REST Framework  |
| JavaScript   | `var csrfToken = "..."`                   | Custom implementations |

---

## Legal Disclaimer

**Only use this tool on systems you own or have explicit permission to test.**

Unauthorized access to computer systems is illegal. This tool is for:

- Security researchers
- Penetration testers
- CTF players
- Educational purposes

---

## Resources

- [Medium Article](https://medium.com/@textmeantu/brute-force-attack-with-python-c1d70fcba607)
- [Password Lists](https://github.com/Antu7/password-generator)

## Recent Updates

### v1.1.0 - UI Enhancement

- **Rich Library Integration**: Upgraded terminal output with beautiful, modern UI using the Rich library.
- **Hacker Theme**: Applied a Matrix-style green color scheme for all outputs, tables, and progress bars.
- **Enhanced Tables**: Configuration and results now displayed in styled tables for better readability.
- **Improved Panels**: Banner and success messages use Rich panels with borders.
- **Better Progress Display**: Progress bar with green styling and real-time updates.
- **Fixed Prompts**: Input prompts now display hints and defaults correctly without markup leakage.

## Contributing

Pull requests are welcome. For major changes, please open an issue first.

### Happy Hacking 🔥🔥
