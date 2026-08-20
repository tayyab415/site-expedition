from concurrent.futures import ThreadPoolExecutor
import http.client
import json
import socket
import threading
import time
import unittest
import urllib.error
from http.server import BaseHTTPRequestHandler
from unittest.mock import patch

from expedition.security import (
    BrowserSessionGate,
    OptionalBearerTokenGate,
    PerIpRateLimiter,
)
from expedition.ui import serve


class HttpApiBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original_auth = serve.AUTH
        cls.original_api_limiter = serve.API_LIMITER
        cls.original_tile_limiter = serve.TILE_LIMITER
        cls.original_trust_proxy = getattr(serve, "TRUST_PROXY", False)
        serve.AUTH = BrowserSessionGate(
            OptionalBearerTokenGate("test-access-token"),
            token_factory=lambda: "test-browser-session",
        )
        serve.API_LIMITER = PerIpRateLimiter(limit=1000)
        serve.TILE_LIMITER = PerIpRateLimiter(limit=1000)
        serve.TRUST_PROXY = True
        cls.server = serve.ThreadingHTTPServer(("127.0.0.1", 0), serve.Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.port = cls.server.server_address[1]

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)
        serve.AUTH = cls.original_auth
        serve.API_LIMITER = cls.original_api_limiter
        serve.TILE_LIMITER = cls.original_tile_limiter
        serve.TRUST_PROXY = cls.original_trust_proxy

    def request(self, path, payload, *, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=2)
        body = payload if isinstance(payload, str) else json.dumps(payload)
        request_headers = {
            "Authorization": "Bearer test-access-token",
            "Content-Type": "application/json",
        }
        request_headers.update(headers or {})
        connection.request("POST", path, body=body, headers=request_headers)
        response = connection.getresponse()
        raw = response.read()
        connection.close()
        return response.status, json.loads(raw or b"{}")

    def test_browser_can_exchange_secret_for_http_only_session(self):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=2)
        connection.request("GET", "/api/session")
        response = connection.getresponse()
        anonymous = json.loads(response.read())
        connection.close()
        self.assertEqual(200, response.status)
        self.assertEqual({"authenticated": False}, anonymous)

        status, result, headers = self.request_with_headers(
            "/api/session",
            {"token": "test-access-token"},
            headers={"Authorization": ""},
        )
        self.assertEqual(200, status)
        self.assertEqual("authenticated", result["status"])
        cookie = headers.get("Set-Cookie")
        self.assertIn("expedition_session=test-browser-session", cookie)
        self.assertIn("HttpOnly", cookie)

        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=2)
        connection.request(
            "GET",
            "/api/credits",
            headers={"Cookie": "expedition_session=test-browser-session"},
        )
        response = connection.getresponse()
        authenticated = json.loads(response.read())
        connection.close()
        self.assertEqual(200, response.status)

        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=2)
        connection.request(
            "GET",
            "/api/session",
            headers={"Cookie": "expedition_session=test-browser-session"},
        )
        response = connection.getresponse()
        authenticated = json.loads(response.read())
        connection.close()
        self.assertEqual(200, response.status)
        self.assertEqual({"authenticated": True}, authenticated)

    def get_json(self, path):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=2)
        connection.request(
            "GET",
            path,
            headers={"Authorization": "Bearer test-access-token"},
        )
        response = connection.getresponse()
        raw = response.read()
        connection.close()
        return response.status, json.loads(raw or b"{}")

    def test_aerial_meta_requires_an_address_query(self):
        status, result = self.get_json("/api/aerial-meta")
        self.assertEqual(400, status)
        self.assertIn("address", result["error"])

    def test_aerial_meta_rejects_overlong_query(self):
        status, result = self.get_json("/api/aerial-meta?query=" + ("x" * 201))
        self.assertEqual(400, status)

    def test_aerial_meta_maps_google_404_to_not_found(self):
        error = urllib.error.HTTPError("url", 404, "not found", {}, None)
        with patch("expedition.ui.serve.maps_key", return_value="not-secret"):
            with patch(
                "expedition.adapters.aerial.lookup_metadata",
                side_effect=error,
            ):
                status, result = self.get_json("/api/aerial-meta?query=5801%20S%20Ellis%20Ave")
        self.assertEqual(200, status)
        self.assertEqual("NOT_FOUND", result["state"])
        self.assertIsNone(result["video_id"])

    def test_aerial_meta_returns_video_id_without_playback_uris(self):
        with patch("expedition.ui.serve.maps_key", return_value="not-secret"):
            with patch(
                "expedition.adapters.aerial.lookup_metadata",
                return_value={
                    "state": "ACTIVE",
                    "videoId": "KPvJfAwQnLollCjP2bks-y",
                    "uris": {"MP4_HIGH": "https://secret.example/playback"},
                    "duration": "40s",
                },
            ):
                status, result = self.get_json(
                    "/api/aerial-meta?query=5801%20S%20Ellis%20Ave,%20Chicago,%20IL"
                )
        self.assertEqual(200, status)
        self.assertEqual("ACTIVE", result["state"])
        self.assertEqual("KPvJfAwQnLollCjP2bks-y", result["video_id"])
        self.assertNotIn("uris", result)
        self.assertNotIn("secret", json.dumps(result))

    def test_aerial_meta_keeps_processing_video_id(self):
        with patch("expedition.ui.serve.maps_key", return_value="not-secret"):
            with patch(
                "expedition.adapters.aerial.lookup_metadata",
                return_value={"state": "PROCESSING", "metadata": {"videoId": "pending-id"}},
            ):
                status, result = self.get_json(
                    "/api/aerial-meta?query=3605%20Winfield%20Cove,%20Austin,%20TX"
                )
        self.assertEqual(200, status)
        self.assertEqual("PROCESSING", result["state"])
        self.assertEqual("pending-id", result["video_id"])

    def test_aerial_meta_lookup_by_video_id(self):
        with patch("expedition.ui.serve.maps_key", return_value="not-secret"):
            with patch(
                "expedition.adapters.aerial.lookup_metadata_by_id",
                return_value={"state": "ACTIVE", "videoId": "abc123"},
            ) as lookup:
                status, result = self.get_json("/api/aerial-meta?video_id=abc123")
        self.assertEqual(200, status)
        self.assertEqual("ACTIVE", result["state"])
        self.assertEqual("abc123", result["video_id"])
        lookup.assert_called_once_with("abc123", "not-secret")

    def test_aerial_render_requires_an_address(self):
        status, result = self.request("/api/aerial-render", {})
        self.assertEqual(400, status)
        self.assertIn("address", result["error"])

    def test_aerial_render_returns_state_without_playback_uris(self):
        with patch("expedition.ui.serve.maps_key", return_value="not-secret"):
            with patch(
                "expedition.adapters.aerial.render_video",
                return_value={
                    "state": "PROCESSING",
                    "metadata": {"videoId": "new-id"},
                    "uris": {"MP4_HIGH": "https://secret.example/playback"},
                },
            ):
                status, result = self.request(
                    "/api/aerial-render",
                    {"address": "3605 Winfield Cove, Austin, TX"},
                )
        self.assertEqual(200, status)
        self.assertEqual("PROCESSING", result["state"])
        self.assertEqual("new-id", result["video_id"])
        self.assertNotIn("uris", result)
        self.assertNotIn("secret", json.dumps(result))

    def test_aerial_render_maps_unsupported_address(self):
        error = urllib.error.HTTPError("url", 400, "bad", {}, None)
        with patch("expedition.ui.serve.maps_key", return_value="not-secret"):
            with patch("expedition.adapters.aerial.render_video", side_effect=error):
                status, result = self.request(
                    "/api/aerial-render",
                    {"address": "not a us postal address"},
                )
        self.assertEqual(200, status)
        self.assertEqual("UNSUPPORTED", result["state"])
        self.assertIsNone(result["video_id"])

    def test_aerial_ensure_accepts_coordinates_without_address(self):
        with patch("expedition.ui.serve.maps_key", return_value="not-secret"):
            with patch(
                "expedition.adapters.aerial.ensure_aerial",
                return_value={
                    "state": "ACTIVE",
                    "video_id": "midtown-id",
                    "query": "350 5th Avenue, New York, New York, 10118",
                    "duration": "40s",
                    "capture_date": None,
                },
            ) as ensure:
                status, result = self.request(
                    "/api/aerial-ensure",
                    {"lat": 40.748, "lng": -73.985, "render": True},
                )
        self.assertEqual(200, status)
        self.assertEqual("ACTIVE", result["state"])
        self.assertEqual("midtown-id", result["video_id"])
        self.assertIn("350 5th Avenue", result["query"])
        ensure.assert_called_once()
        kwargs = ensure.call_args.kwargs
        self.assertEqual(kwargs["lat"], 40.748)
        self.assertEqual(kwargs["lng"], -73.985)
        self.assertTrue(kwargs["render"])

    def test_aerial_ensure_requires_an_address_or_pin(self):
        status, result = self.request("/api/aerial-ensure", {})
        self.assertEqual(400, status)
        self.assertIn("address", result["error"])

    def request_with_headers(self, path, payload, *, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=2)
        body = payload if isinstance(payload, str) else json.dumps(payload)
        request_headers = {"Content-Type": "application/json"}
        request_headers.update(headers or {})
        connection.request("POST", path, body=body, headers=request_headers)
        response = connection.getresponse()
        raw = response.read()
        result_headers = dict(response.getheaders())
        connection.close()
        return response.status, json.loads(raw or b"{}"), result_headers

    def test_plan_rejects_non_object_json_without_dropping_connection(self):
        for payload in ("[]", "null"):
            with self.subTest(payload=payload):
                status, result = self.request("/api/plan", payload)
                self.assertEqual(400, status)
                self.assertEqual("invalid_request", result["error"])

    def test_run_missing_required_fields_is_a_client_error(self):
        status, result = self.request("/api/run", {})
        self.assertEqual(400, status)
        self.assertEqual("invalid_request", result["error"])
        self.assertIn("mission", result["message"])

    def test_unknown_expedition_mission_is_not_an_empty_success(self):
        status, result = self.request(
            "/api/expedition",
            {"mission": "unknown", "live": False, "controls": {}},
        )
        self.assertEqual(400, status)
        self.assertEqual("invalid_request", result["error"])

    def test_non_finite_json_number_is_rejected(self):
        status, result = self.request(
            "/api/plan",
            '{"mission":"warehouse","route_anchors":[{"id":"x","name":"x","lat":NaN,"lng":-95}]}',
        )
        self.assertEqual(400, status)
        self.assertEqual("invalid_request", result["error"])

    def test_https_proxy_same_origin_is_accepted_when_proxy_is_trusted(self):
        status, _ = self.request(
            "/api/plan",
            {"mission": "warehouse"},
            headers={
                "Host": "demo.trycloudflare.com",
                "Origin": "https://demo.trycloudflare.com",
                "X-Forwarded-Proto": "https",
            },
        )
        self.assertEqual(200, status)

    def test_run_stream_emits_workstream_events_before_the_packet(self):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=15)
        body = json.dumps({
            "mission": "warehouse",
            "candidate_id": "san_leon",
            "live": False,
            "controls": {"scan_budget": "standard"},
        })
        connection.request(
            "POST",
            "/api/run-stream",
            body=body,
            headers={
                "Authorization": "Bearer test-access-token",
                "Content-Type": "application/json",
            },
        )
        response = connection.getresponse()
        raw = response.read().decode()
        connection.close()
        self.assertEqual(200, response.status)
        self.assertIn("ndjson", (response.getheader("Content-Type") or "").lower())
        events = [json.loads(line) for line in raw.splitlines() if line.strip()]
        kinds = [row.get("event") for row in events]
        self.assertIn("packet", kinds)
        packet_index = kinds.index("packet")
        prior = events[:packet_index]
        self.assertGreaterEqual(len(prior), 2, prior)
        self.assertTrue(
            any(row.get("event") == "workstream" for row in prior),
            prior,
        )
        self.assertTrue(
            any(row.get("status") in {"running", "succeeded"} for row in prior),
            prior,
        )
        packet = events[packet_index]["packet"]
        self.assertEqual("reject", packet["verdict"]["verdict"])
        self.assertEqual("flood_rewind", packet["scene"]["past"]["kind"])

    def test_expedition_omitted_candidate_ids_is_the_full_mission_list(self):
        warehouse = serve.MISSION_SITES["warehouse"]
        self.assertEqual(["san_leon", "san_marcos_tx", "alliance_tx", "port_houston", "joliet_il"], warehouse)
        self.assertEqual(warehouse, serve.expedition_catalog_ids("warehouse"))
        self.assertEqual(
            warehouse,
            serve.expedition_catalog_ids(
                "warehouse",
                list(warehouse),
                {"search_region": "texas_triangle", "geography_band": "selected_region"},
            ),
        )

    def test_expedition_candidate_ids_cannot_inject_an_off_mission_id(self):
        controls = {
            "search_region": "texas_triangle",
            "geography_band": "selected_region",
        }
        self.assertEqual(
            ["san_leon"],
            serve.expedition_catalog_ids(
                "warehouse",
                ["san_leon", "iowa_corn", "not_a_site"],
                controls,
            ),
        )
        self.assertEqual(
            [],
            serve.expedition_catalog_ids("warehouse", [], controls),
        )
        self.assertEqual(
            ["san_leon"],
            serve.expedition_catalog_ids(
                "warehouse",
                ["san_leon", "joliet_il"],
                controls,
            ),
        )
        self.assertEqual(
            ["iowa_corn"],
            serve.expedition_catalog_ids("farm", ["iowa_corn", "san_leon"]),
        )

    def test_expedition_posts_intersected_candidate_ids_to_run_mission(self):
        packet = {"mission": "warehouse", "results": [], "comparison": []}
        with patch("expedition.engine.run_mission", return_value=packet) as mocked:
            status, result = self.request(
                "/api/expedition",
                {
                    "mission": "warehouse",
                    "live": False,
                    "candidate_ids": ["san_leon", "iowa_corn", "not_a_site"],
                    "controls": {
                        "search_region": "texas_triangle",
                        "geography_band": "selected_region",
                    },
                },
            )
        self.assertEqual(200, status)
        self.assertEqual([], result["results"])
        self.assertEqual(["san_leon"], mocked.call_args.args[1])

        with patch("expedition.engine.run_mission", return_value=packet) as mocked:
            status, _ = self.request(
                "/api/expedition",
                {
                    "mission": "warehouse",
                    "live": False,
                    "controls": {
                        "search_region": "texas_triangle",
                        "geography_band": "selected_region",
                    },
                },
            )
        self.assertEqual(200, status)
        self.assertEqual(serve.MISSION_SITES["warehouse"], mocked.call_args.args[1])

    def test_inline_candidate_cannot_forge_listed_provenance(self):
        status, result = self.request(
            "/api/run",
            {
                "mission": "warehouse",
                "candidate_id": "san_marcos_tx",
                "live": False,
                "candidate": {
                    "id": "san_marcos_tx",
                    "name": "Forged listing",
                    "lat": 29.883,
                    "lng": -97.941,
                    "label": "LISTED",
                    "site_form": "either",
                    "source": "unverified-inline-claim",
                },
            },
        )
        self.assertEqual(400, status)
        self.assertEqual("invalid_candidate", result["error"])

    def test_intent_compiles_a_warehouse_plan_from_plain_speech(self):
        status, result = self.request(
            "/api/intent",
            {
                "text": "Warehouse near Dallas with rail, no flood",
                "live_model": False,
            },
        )
        self.assertEqual(200, status)
        self.assertEqual("warehouse", result["controls"]["mission"])
        self.assertEqual(["dallas_fort_worth"], result["region_allowlist"])
        self.assertTrue(result["plan"]["flood_intolerant"])

    def test_intent_reads_corn_plantations_as_farm(self):
        status, result = self.request(
            "/api/intent",
            {"text": "corn plantations", "live_model": False},
        )
        self.assertEqual(200, status)
        self.assertEqual("farm", result["controls"]["mission"])
        self.assertFalse(result["controls"]["flood_intolerant"])
        self.assertEqual("corn", result["crop"])
        self.assertIn("chicago", result["region_allowlist"])
        self.assertFalse(result["open_inventory"])
        self.assertNotIn("not_mapped_sfha", result["plan"]["hard_constraints"])

    def test_intent_rejects_empty_text(self):
        status, result = self.request("/api/intent", {"text": "  "})
        self.assertEqual(400, status)
        self.assertEqual("invalid_request", result["error"])

    def test_intent_rejects_non_string_text(self):
        status, result = self.request("/api/intent", {"text": 123})
        self.assertEqual(400, status)
        self.assertEqual("invalid_request", result["error"])

    def test_intent_refuses_unsupported_use_with_422(self):
        status, result = self.request(
            "/api/intent",
            {"text": "looking for opening a cafe in atlanta", "live_model": False},
        )
        self.assertEqual(422, status)
        self.assertEqual("unsupported_use", result["error"])
        self.assertIn("farm", result["supported"])

    def test_discover_rejects_unknown_mission(self):
        status, result = self.request(
            "/api/discover",
            {"mission": "casino", "search_region": "phoenix", "network": False},
        )
        self.assertEqual(400, status)
        self.assertEqual("invalid_request", result["error"])

    def test_discover_rejects_unknown_region(self):
        status, result = self.request(
            "/api/discover",
            {"mission": "farm", "search_region": "mars_colony", "network": False},
        )
        self.assertEqual(400, status)
        self.assertEqual("invalid_request", result["error"])

    def test_regions_rank_texas_warehouses_without_mireye(self):
        status, result = self.request(
            "/api/regions",
            {
                "mission": "warehouse",
                "region_allowlist": ["texas_triangle"],
                "controls": {
                    "search_region": "texas_triangle",
                    "flood_intolerant": True,
                    "preferences": [{"id": "rail_access", "weight": "priority"}],
                },
            },
        )
        self.assertEqual(200, status)
        self.assertEqual("locate", result["stage"])
        self.assertEqual("dallas_fort_worth", result["top_region_ids"][0])
        self.assertEqual(0, result["credits"]["spent"])
        self.assertFalse(result["credits"]["mireye"])
        self.assertNotIn("civilian_employed", result["regions"][0]["preference_basis"])

    def test_regions_accept_default_useful_route_time_without_non_finite_json(self):
        status, result = self.request(
            "/api/regions",
            {
                "mission": "warehouse",
                "region_allowlist": ["dallas_fort_worth"],
                "controls": {
                    "search_region": "dallas_fort_worth",
                    "flood_intolerant": True,
                    "preferences": [
                        {"id": "major_road_access", "weight": "priority"},
                        {"id": "route_time", "weight": "useful"},
                        {"id": "rail_access", "weight": "priority"},
                        {"id": "grid_proximity", "weight": "useful"},
                    ],
                },
            },
        )
        self.assertEqual(200, status)
        self.assertNotIn("error", result)
        self.assertEqual("dallas_fort_worth", result["top_region_ids"][0])
        self.assertEqual(0, result["credits"]["spent"])


class SlowClientBoundaryTests(unittest.TestCase):
    def test_incomplete_headers_are_closed_by_pre_header_socket_timeout(self):
        server = serve.BoundedThreadingHTTPServer(
            ("127.0.0.1", 0),
            serve.Handler,
            max_connections=1,
            socket_timeout=0.1,
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        client = socket.create_connection(server.server_address, timeout=1)
        client.settimeout(1)
        try:
            client.sendall(b"GET /api/credits HTTP/1.1\r\nHost: local")
            self.assertEqual(b"", client.recv(1))
        finally:
            client.close()
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_connection_bound_applies_backpressure_instead_of_dropping_burst(self):
        class SlowOkHandler(BaseHTTPRequestHandler):
            def log_message(self, _format, *_args):
                return

            def do_GET(self):  # noqa: N802
                time.sleep(0.05)
                body = b"ok"
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        server = serve.BoundedThreadingHTTPServer(
            ("127.0.0.1", 0),
            SlowOkHandler,
            max_connections=2,
            socket_timeout=1,
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        def request_once(_index):
            connection = http.client.HTTPConnection(
                *server.server_address,
                timeout=2,
            )
            try:
                connection.request("GET", "/")
                response = connection.getresponse()
                response.read()
                return response.status
            finally:
                connection.close()

        try:
            with ThreadPoolExecutor(max_workers=8) as pool:
                statuses = list(pool.map(request_once, range(8)))
            self.assertEqual([200] * 8, statuses)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_full_slots_return_busy_json_instead_of_empty_close(self):
        started = threading.Event()
        release = threading.Event()

        class HangHandler(BaseHTTPRequestHandler):
            def log_message(self, _format, *_args):
                return

            def do_GET(self):  # noqa: N802
                started.set()
                release.wait(2)
                body = b"ok"
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        server = serve.BoundedThreadingHTTPServer(
            ("127.0.0.1", 0),
            HangHandler,
            max_connections=1,
            socket_timeout=0.2,
            slot_wait_timeout=0.2,
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        occupant = http.client.HTTPConnection(*server.server_address, timeout=2)
        try:
            occupant.putrequest("GET", "/")
            occupant.putheader("Host", "local")
            occupant.endheaders()
            self.assertTrue(started.wait(1))
            probe = http.client.HTTPConnection(*server.server_address, timeout=2)
            probe.request("GET", "/")
            response = probe.getresponse()
            body = json.loads(response.read())
            probe.close()
            self.assertEqual(503, response.status)
            self.assertEqual("server_busy", body["error"])
        finally:
            release.set()
            occupant.close()
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
