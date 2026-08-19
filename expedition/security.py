"""Small security primitives for the public-prototype HTTP boundary.

The module is deliberately independent of :mod:`expedition.ui.serve` so the
controls can be unit tested and reused by another stdlib HTTP handler.  It
does not load provider credentials and never includes bearer-token values in
errors or representations.
"""

from __future__ import annotations

import hmac
import ipaddress
import math
import os
import secrets
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass
from http.cookies import CookieError, SimpleCookie
from typing import Callable, Mapping
from urllib.parse import urlsplit

DEFAULT_BODY_LIMIT = 256 * 1024
DEFAULT_RATE_LIMIT = 120
DEFAULT_RATE_WINDOW_SECONDS = 60.0
DEFAULT_MAX_TRACKED_IPS = 4096
BEARER_TOKEN_ENV = "EXPEDITION_BEARER_TOKEN"
FORWARDED_SCHEMES = frozenset({"http", "https"})

# Keep this synchronized with the checked-in UI.  ``unsafe-inline`` is
# limited to styles because the scorecard currently renders a dynamic width
# style and both third-party widget stylesheets use inline styling.  Scripts
# do not receive ``unsafe-inline`` or ``unsafe-eval``.
DEFAULT_CONTENT_SECURITY_POLICY = "; ".join(
    (
        "default-src 'self'",
        "base-uri 'none'",
        "object-src 'none'",
        "frame-ancestors 'none'",
        "form-action 'self'",
        "script-src 'self' 'wasm-unsafe-eval' https://ajax.googleapis.com https://unpkg.com",
        "style-src 'self' 'unsafe-inline' https://ajax.googleapis.com https://unpkg.com",
        "font-src 'self' data:",
        (
            "img-src 'self' data: blob: https://ajax.googleapis.com "
            "https://unpkg.com https://tile.openstreetmap.org "
            "https://*.tile.openstreetmap.org"
        ),
        (
            "connect-src 'self' https://ajax.googleapis.com "
            "https://tile.openstreetmap.org https://*.tile.openstreetmap.org "
            "https://*.googleapis.com https://*.googleusercontent.com"
        ),
        "media-src 'self' blob: https:",
        "worker-src 'self' blob: https://ajax.googleapis.com",
        "child-src 'self' blob:",
        "manifest-src 'self'",
    )
)


def security_headers(
    *, content_security_policy: str = DEFAULT_CONTENT_SECURITY_POLICY
) -> dict[str, str]:
    """Return restrictive headers that are safe for the current board.

    A new dictionary is returned each time so callers may extend it without
    mutating process-global state.  CORS headers are intentionally absent;
    same-origin browser requests do not need them and a wildcard would expose
    the provider-backed proxy surface.
    """

    return {
        "Content-Security-Policy": content_security_policy,
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "no-referrer",
        "X-Frame-Options": "DENY",
        "Permissions-Policy": (
            "camera=(), microphone=(), geolocation=(), payment=(), usb=(), "
            "browsing-topics=()"
        ),
    }


class SecurityHeadersMixin:
    """``BaseHTTPRequestHandler`` mixin that adds prototype response headers.

    Put the mixin before ``BaseHTTPRequestHandler`` (or the existing handler)
    in the class bases so this ``end_headers`` method participates in the MRO.
    """

    content_security_policy = DEFAULT_CONTENT_SECURITY_POLICY

    def end_headers(self) -> None:
        for name, value in security_headers(
            content_security_policy=self.content_security_policy
        ).items():
            self.send_header(name, value)
        super().end_headers()


def _canonical_origin(scheme: str, host: str) -> tuple[str, str, int | None] | None:
    """Canonicalize an HTTP origin without accepting paths or credentials."""

    try:
        parsed = urlsplit(f"{scheme.lower()}://{host}")
        port = parsed.port
    except (TypeError, ValueError):
        return None
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return None
    if parsed.username is not None or parsed.password is not None:
        return None
    if parsed.path or parsed.query or parsed.fragment:
        return None
    if port == (80 if parsed.scheme == "http" else 443):
        port = None
    return parsed.scheme, parsed.hostname.rstrip(".").lower(), port


def _parse_origin(origin: str) -> tuple[str, str, int | None] | None:
    try:
        parsed = urlsplit(origin)
        port = parsed.port
    except (TypeError, ValueError):
        return None
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return None
    if parsed.username is not None or parsed.password is not None:
        return None
    if parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
        return None
    if port == (80 if parsed.scheme == "http" else 443):
        port = None
    return parsed.scheme, parsed.hostname.rstrip(".").lower(), port


def origin_allowed(
    origin: str | None,
    host: str | None,
    *,
    request_scheme: str = "http",
    allowed_origins: tuple[str, ...] = (),
) -> bool:
    """Return whether an Origin is same-origin or explicitly allowlisted.

    Missing ``Origin`` is allowed for non-browser clients and normal GETs.
    The browser's ``Sec-Fetch-Site`` signal can be checked by
    :func:`request_origin_allowed` as an additional defense.  Wildcard
    allowlist entries are ignored rather than becoming permissive.
    """

    if not origin:
        return True
    candidate = _parse_origin(origin)
    if candidate is None or not host:
        return False
    expected = _canonical_origin(request_scheme, host)
    if candidate == expected:
        return True
    for item in allowed_origins:
        if item == "*":
            continue
        parsed = _parse_origin(item)
        if parsed is not None and candidate == parsed:
            return True
    return False


def request_origin_allowed(
    headers: Mapping[str, str],
    *,
    request_scheme: str = "http",
    allowed_origins: tuple[str, ...] = (),
) -> bool:
    """Apply same-origin checks to an HTTP request's browser headers."""

    fetch_site = (headers.get("Sec-Fetch-Site") or "").strip().lower()
    if fetch_site in {"cross-site", "same-site"} and not headers.get("Origin"):
        return False
    return origin_allowed(
        headers.get("Origin"),
        headers.get("Host"),
        request_scheme=request_scheme,
        allowed_origins=allowed_origins,
    )


def request_scheme(headers: Mapping[str, str], *, trust_proxy: bool = False) -> str:
    """Return the effective HTTP scheme without trusting proxy data by default.

    Cloudflare and conventional reverse proxies send ``X-Forwarded-Proto``.
    The header is security-sensitive, so deployments must opt in explicitly;
    direct/local traffic remains HTTP when proxy trust is disabled.
    """

    if not trust_proxy:
        return "http"
    forwarded = (headers.get("X-Forwarded-Proto") or "").split(",", 1)[0]
    forwarded = forwarded.strip().lower()
    return forwarded if forwarded in FORWARDED_SCHEMES else "http"


def cors_response_headers(
    origin: str | None,
    host: str | None,
    *,
    request_scheme: str = "http",
    allowed_origins: tuple[str, ...] = (),
) -> dict[str, str]:
    """Return a non-wildcard CORS response only for an accepted Origin.

    The local board is same-origin and does not require these headers.  This
    helper exists for a deliberately configured cross-origin deployment; it
    never turns ``*`` into an allow-all response and never enables credential
    sharing.
    """

    if not origin or not origin_allowed(
        origin,
        host,
        request_scheme=request_scheme,
        allowed_origins=allowed_origins,
    ):
        return {}
    return {"Access-Control-Allow-Origin": origin, "Vary": "Origin"}


@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    remaining: int
    retry_after: int


@dataclass
class _RateWindow:
    count: int
    resets_at: float


class PerIpRateLimiter:
    """Thread-safe fixed-window limiter with a bounded in-memory IP table."""

    def __init__(
        self,
        limit: int = DEFAULT_RATE_LIMIT,
        window_seconds: float = DEFAULT_RATE_WINDOW_SECONDS,
        *,
        max_clients: int = DEFAULT_MAX_TRACKED_IPS,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if limit <= 0:
            raise ValueError("limit must be positive")
        if window_seconds <= 0:
            raise ValueError("window_seconds must be positive")
        if max_clients <= 0:
            raise ValueError("max_clients must be positive")
        self.limit = limit
        self.window_seconds = float(window_seconds)
        self.max_clients = max_clients
        self._clock = clock
        self._clients: OrderedDict[str, _RateWindow] = OrderedDict()
        self._lock = threading.Lock()

    @property
    def tracked_clients(self) -> int:
        with self._lock:
            return len(self._clients)

    def check(self, ip: str, *, cost: int = 1) -> RateLimitDecision:
        if not ip:
            raise ValueError("ip must not be empty")
        if cost <= 0 or cost > self.limit:
            raise ValueError("cost must be between 1 and the configured limit")
        now = float(self._clock())
        with self._lock:
            # Expired entries cannot consume the bounded client table.
            for key, window in list(self._clients.items()):
                if now >= window.resets_at:
                    del self._clients[key]

            window = self._clients.get(ip)
            if window is None:
                if len(self._clients) >= self.max_clients:
                    self._clients.popitem(last=False)
                window = _RateWindow(count=0, resets_at=now + self.window_seconds)
                self._clients[ip] = window

            self._clients.move_to_end(ip)
            proposed = window.count + cost
            if proposed <= self.limit:
                window.count = proposed
                return RateLimitDecision(
                    allowed=True,
                    remaining=self.limit - window.count,
                    retry_after=0,
                )
            return RateLimitDecision(
                allowed=False,
                remaining=0,
                retry_after=max(1, math.ceil(window.resets_at - now)),
            )


def client_ip(handler: object, *, trust_proxy: bool = False) -> str:
    """Return a normalized peer IP; forwarded data is opt-in only."""

    headers = getattr(handler, "headers", {})
    if trust_proxy:
        forwarded = (headers.get("X-Forwarded-For") or "").split(",", 1)[0].strip()
        if forwarded:
            try:
                return ipaddress.ip_address(forwarded).compressed
            except ValueError:
                pass
    address = getattr(handler, "client_address", ("unknown", 0))[0]
    try:
        return ipaddress.ip_address(address).compressed
    except ValueError:
        return str(address)


class InvalidRequestBody(ValueError):
    """The request cannot be safely framed or read by the stdlib server."""


class RequestBodyTooLarge(InvalidRequestBody):
    """The declared request body exceeds the configured maximum."""


def content_length(headers: Mapping[str, str], *, max_bytes: int) -> int:
    """Validate request framing and return a bounded Content-Length."""

    if max_bytes < 0:
        raise ValueError("max_bytes must not be negative")
    transfer_encoding = (headers.get("Transfer-Encoding") or "").strip()
    if transfer_encoding:
        raise InvalidRequestBody("transfer encoding is not supported")
    raw = headers.get("Content-Length")
    if raw in {None, ""}:
        return 0
    try:
        length = int(raw, 10)
    except (TypeError, ValueError) as exc:
        raise InvalidRequestBody("invalid content length") from exc
    if length < 0:
        raise InvalidRequestBody("invalid content length")
    if length > max_bytes:
        raise RequestBodyTooLarge("request body exceeds configured limit")
    return length


def read_limited_body(handler: object, *, max_bytes: int = DEFAULT_BODY_LIMIT) -> bytes:
    """Read one body only after its declared length passes the size limit."""

    length = content_length(getattr(handler, "headers"), max_bytes=max_bytes)
    if length == 0:
        return b""
    body = getattr(handler, "rfile").read(length)
    if len(body) != length:
        raise InvalidRequestBody("incomplete request body")
    return body


class OptionalBearerTokenGate:
    """Bearer authentication that is disabled unless its env token is set."""

    __slots__ = ("_token",)

    def __init__(self, token: str | None = None) -> None:
        self._token = token.strip() if token and token.strip() else None

    @classmethod
    def from_env(
        cls,
        environ: Mapping[str, str] | None = None,
        *,
        variable: str = BEARER_TOKEN_ENV,
    ) -> "OptionalBearerTokenGate":
        values = os.environ if environ is None else environ
        return cls(values.get(variable))

    @property
    def enabled(self) -> bool:
        return self._token is not None

    def allows(self, headers: Mapping[str, str]) -> bool:
        if self._token is None:
            return True
        value = (headers.get("Authorization") or "").strip()
        pieces = value.split()
        if len(pieces) != 2 or pieces[0].lower() != "bearer":
            return False
        return hmac.compare_digest(pieces[1], self._token)

    def matches_token(self, token: str) -> bool:
        """Check a raw token for the browser-session exchange."""

        return self._token is not None and hmac.compare_digest(token, self._token)

    @staticmethod
    def challenge_headers() -> dict[str, str]:
        return {"WWW-Authenticate": 'Bearer realm="expedition"'}

    def __repr__(self) -> str:
        state = "enabled" if self.enabled else "disabled"
        return f"OptionalBearerTokenGate({state})"


class BrowserSessionGate:
    """Exchange a deployment bearer secret for a bounded HttpOnly session.

    Direct API clients may continue to send the bearer secret.  Browser code
    never stores or replays it: after a successful exchange the server keeps
    an opaque, expiring session id in memory and authenticates the cookie.
    """

    cookie_name = "expedition_session"

    def __init__(
        self,
        bearer: OptionalBearerTokenGate,
        *,
        ttl_seconds: int = 8 * 60 * 60,
        max_sessions: int = 64,
        clock: Callable[[], float] = time.monotonic,
        token_factory: Callable[[], str] | None = None,
    ) -> None:
        if ttl_seconds <= 0:
            raise ValueError("session ttl must be positive")
        if max_sessions <= 0:
            raise ValueError("max sessions must be positive")
        self._bearer = bearer
        self.ttl_seconds = int(ttl_seconds)
        self.max_sessions = int(max_sessions)
        self._clock = clock
        self._token_factory = token_factory or (lambda: secrets.token_urlsafe(32))
        self._sessions: OrderedDict[str, float] = OrderedDict()
        self._lock = threading.Lock()

    @property
    def enabled(self) -> bool:
        return self._bearer.enabled

    def issue(self, token: str) -> str | None:
        if not isinstance(token, str) or not self._bearer.matches_token(token):
            return None
        now = float(self._clock())
        session_id = self._token_factory()
        with self._lock:
            self._discard_expired(now)
            while len(self._sessions) >= self.max_sessions:
                self._sessions.popitem(last=False)
            self._sessions[session_id] = now + self.ttl_seconds
        return session_id

    def allows(self, headers: Mapping[str, str]) -> bool:
        if self._bearer.allows(headers):
            return True
        if not self.enabled:
            return False
        session_id = self._session_cookie(headers.get("Cookie") or "")
        if not session_id:
            return False
        now = float(self._clock())
        with self._lock:
            self._discard_expired(now)
            expires = self._sessions.get(session_id)
            if expires is None or now >= expires:
                self._sessions.pop(session_id, None)
                return False
            self._sessions.move_to_end(session_id)
            return True

    def cookie_header(self, session_id: str | None, *, secure: bool) -> str:
        if not session_id:
            raise ValueError("session id is required")
        attributes = [
            f"{self.cookie_name}={session_id}",
            "Path=/",
            "HttpOnly",
            "SameSite=Strict",
            f"Max-Age={self.ttl_seconds}",
        ]
        if secure:
            attributes.append("Secure")
        return "; ".join(attributes)

    def challenge_headers(self) -> dict[str, str]:
        return self._bearer.challenge_headers()

    def _discard_expired(self, now: float) -> None:
        for session_id, expires in list(self._sessions.items()):
            if now >= expires:
                del self._sessions[session_id]

    def _session_cookie(self, raw_cookie: str) -> str | None:
        try:
            parsed = SimpleCookie()
            parsed.load(raw_cookie)
        except CookieError:
            return None
        morsel = parsed.get(self.cookie_name)
        return morsel.value if morsel else None

    def __repr__(self) -> str:
        state = "enabled" if self.enabled else "disabled"
        return f"BrowserSessionGate({state})"
