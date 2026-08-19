import io
import unittest

from expedition.security import (
    DEFAULT_CONTENT_SECURITY_POLICY,
    BrowserSessionGate,
    InvalidRequestBody,
    OptionalBearerTokenGate,
    PerIpRateLimiter,
    RequestBodyTooLarge,
    SecurityHeadersMixin,
    client_ip,
    content_length,
    cors_response_headers,
    origin_allowed,
    read_limited_body,
    request_origin_allowed,
    request_scheme,
    security_headers,
)


class SecurityHeaderTests(unittest.TestCase):
    def test_headers_are_restrictive_and_support_current_dependencies(self):
        headers = security_headers()
        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(headers["Referrer-Policy"], "no-referrer")
        self.assertEqual(headers["X-Frame-Options"], "DENY")
        csp = headers["Content-Security-Policy"]
        self.assertIn("frame-ancestors 'none'", csp)
        self.assertIn("object-src 'none'", csp)
        self.assertIn("https://ajax.googleapis.com", csp)
        self.assertIn("font-src 'self'", csp)
        self.assertNotIn("https://fonts.googleapis.com", csp)
        self.assertNotIn("https://fonts.gstatic.com", csp)
        self.assertIn("https://unpkg.com", csp)
        self.assertIn("https://*.tile.openstreetmap.org", csp)
        self.assertIn("worker-src 'self' blob:", csp)
        self.assertIn("media-src 'self' blob: https:", csp)
        self.assertNotIn("script-src 'self' 'unsafe-inline'", csp)
        self.assertNotIn("'unsafe-eval'", csp)
        self.assertIn("'wasm-unsafe-eval'", csp)
        self.assertNotIn("Access-Control-Allow-Origin", headers)

    def test_mixin_adds_headers_before_finishing(self):
        class Parent:
            def __init__(self):
                self.sent = []
                self.finished = False

            def send_header(self, name, value):
                self.sent.append((name, value))

            def end_headers(self):
                self.finished = True

        class Handler(SecurityHeadersMixin, Parent):
            pass

        handler = Handler()
        handler.end_headers()
        self.assertTrue(handler.finished)
        self.assertIn(("Content-Security-Policy", DEFAULT_CONTENT_SECURITY_POLICY), handler.sent)


class OriginTests(unittest.TestCase):
    def test_same_origin_normalizes_case_and_default_port(self):
        self.assertTrue(origin_allowed("http://LOCALHOST:80", "localhost", request_scheme="http"))
        self.assertTrue(origin_allowed("https://example.test", "example.test:443", request_scheme="https"))

    def test_cross_origin_and_wildcard_are_rejected(self):
        self.assertFalse(origin_allowed("https://evil.test", "localhost:8030"))
        self.assertFalse(
            origin_allowed(
                "https://evil.test",
                "localhost:8030",
                allowed_origins=("*",),
            )
        )

    def test_explicit_origin_allowlist_is_exact(self):
        self.assertTrue(
            origin_allowed(
                "https://demo.example",
                "localhost:8030",
                allowed_origins=("https://demo.example",),
            )
        )
        self.assertFalse(
            origin_allowed(
                "https://sub.demo.example",
                "localhost:8030",
                allowed_origins=("https://demo.example",),
            )
        )

    def test_malformed_and_null_origins_are_rejected(self):
        self.assertFalse(origin_allowed("null", "localhost:8030"))
        self.assertFalse(origin_allowed("https://user@localhost:8030", "localhost:8030"))
        self.assertFalse(origin_allowed("https://localhost:8030/path", "localhost:8030"))
        self.assertFalse(origin_allowed("http://localhost", "localhost/path"))

    def test_missing_origin_allows_cli_but_cross_site_fetch_signal_does_not(self):
        self.assertTrue(request_origin_allowed({"Host": "localhost:8030"}))
        self.assertFalse(
            request_origin_allowed(
                {"Host": "localhost:8030", "Sec-Fetch-Site": "cross-site"}
            )
        )

    def test_cors_response_echoes_only_an_accepted_exact_origin(self):
        self.assertEqual(
            cors_response_headers("http://localhost:8030", "localhost:8030"),
            {
                "Access-Control-Allow-Origin": "http://localhost:8030",
                "Vary": "Origin",
            },
        )

    def test_forwarded_scheme_is_explicitly_opt_in(self):
        headers = {"X-Forwarded-Proto": "https"}
        self.assertEqual("http", request_scheme(headers))
        self.assertEqual("https", request_scheme(headers, trust_proxy=True))
        self.assertEqual(
            "http",
            request_scheme({"X-Forwarded-Proto": "javascript"}, trust_proxy=True),
        )
        self.assertEqual(
            cors_response_headers(
                "https://evil.test", "localhost:8030", allowed_origins=("*",)
            ),
            {},
        )


class MutableClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


class RateLimitTests(unittest.TestCase):
    def test_per_ip_limit_and_reset_are_deterministic(self):
        clock = MutableClock()
        limiter = PerIpRateLimiter(2, 10, clock=clock)
        self.assertTrue(limiter.check("192.0.2.1").allowed)
        second = limiter.check("192.0.2.1")
        self.assertTrue(second.allowed)
        self.assertEqual(second.remaining, 0)
        denied = limiter.check("192.0.2.1")
        self.assertFalse(denied.allowed)
        self.assertEqual(denied.retry_after, 10)

        clock.now = 10
        reset = limiter.check("192.0.2.1")
        self.assertTrue(reset.allowed)
        self.assertEqual(reset.remaining, 1)

    def test_ips_are_independent_and_table_is_bounded(self):
        limiter = PerIpRateLimiter(1, 60, max_clients=2, clock=lambda: 0)
        self.assertTrue(limiter.check("192.0.2.1").allowed)
        self.assertTrue(limiter.check("192.0.2.2").allowed)
        self.assertTrue(limiter.check("192.0.2.3").allowed)
        self.assertEqual(limiter.tracked_clients, 2)
        # .1 was the least-recently-used entry and receives a fresh window.
        self.assertTrue(limiter.check("192.0.2.1").allowed)
        self.assertEqual(limiter.tracked_clients, 2)

    def test_forwarded_ip_is_never_trusted_by_default(self):
        class Handler:
            headers = {"X-Forwarded-For": "203.0.113.9, 10.0.0.1"}
            client_address = ("127.0.0.1", 1234)

        self.assertEqual(client_ip(Handler()), "127.0.0.1")
        self.assertEqual(client_ip(Handler(), trust_proxy=True), "203.0.113.9")


class BodyLimitTests(unittest.TestCase):
    def test_body_is_read_within_limit(self):
        class Handler:
            headers = {"Content-Length": "5"}
            rfile = io.BytesIO(b"hello")

        self.assertEqual(read_limited_body(Handler(), max_bytes=5), b"hello")

    def test_oversize_is_rejected_before_read(self):
        class Handler:
            headers = {"Content-Length": "6"}
            rfile = io.BytesIO(b"secret")

        handler = Handler()
        with self.assertRaises(RequestBodyTooLarge):
            read_limited_body(handler, max_bytes=5)
        self.assertEqual(handler.rfile.tell(), 0)

    def test_invalid_framing_is_rejected(self):
        for headers in (
            {"Content-Length": "-1"},
            {"Content-Length": "nope"},
            {"Transfer-Encoding": "chunked"},
        ):
            with self.subTest(headers=headers):
                with self.assertRaises(InvalidRequestBody):
                    content_length(headers, max_bytes=10)

    def test_incomplete_body_is_rejected(self):
        class Handler:
            headers = {"Content-Length": "5"}
            rfile = io.BytesIO(b"abc")

        with self.assertRaises(InvalidRequestBody):
            read_limited_body(Handler(), max_bytes=5)


class BearerGateTests(unittest.TestCase):
    def test_empty_env_keeps_local_board_open(self):
        gate = OptionalBearerTokenGate.from_env({})
        self.assertFalse(gate.enabled)
        self.assertTrue(gate.allows({}))

    def test_configured_token_is_required_and_never_repr_exposed(self):
        gate = OptionalBearerTokenGate.from_env(
            {"EXPEDITION_BEARER_TOKEN": "do-not-print-this"}
        )
        self.assertTrue(gate.enabled)
        self.assertFalse(gate.allows({}))
        self.assertFalse(gate.allows({"Authorization": "Basic nope"}))
        self.assertFalse(gate.allows({"Authorization": "Bearer wrong"}))
        self.assertTrue(
            gate.allows({"Authorization": "Bearer do-not-print-this"})
        )
        self.assertNotIn("do-not-print-this", repr(gate))
        self.assertEqual(
            gate.challenge_headers(),
            {"WWW-Authenticate": 'Bearer realm="expedition"'},
        )


class BrowserSessionGateTests(unittest.TestCase):
    def test_bearer_exchange_issues_an_expiring_http_only_session(self):
        clock = MutableClock()
        gate = BrowserSessionGate(
            OptionalBearerTokenGate("deployment-secret"),
            ttl_seconds=60,
            clock=clock,
            token_factory=lambda: "opaque-session-id",
        )
        self.assertIsNone(gate.issue("wrong"))
        session_id = gate.issue("deployment-secret")
        self.assertEqual("opaque-session-id", session_id)
        cookie = gate.cookie_header(session_id, secure=True)
        self.assertIn("HttpOnly", cookie)
        self.assertIn("SameSite=Strict", cookie)
        self.assertIn("Secure", cookie)
        headers = {"Cookie": "expedition_session=opaque-session-id"}
        self.assertTrue(gate.allows(headers))
        clock.now = 61
        self.assertFalse(gate.allows(headers))

    def test_direct_bearer_clients_remain_supported(self):
        gate = BrowserSessionGate(OptionalBearerTokenGate("deployment-secret"))
        self.assertTrue(
            gate.allows({"Authorization": "Bearer deployment-secret"})
        )
        self.assertFalse(gate.allows({}))


if __name__ == "__main__":
    unittest.main()
