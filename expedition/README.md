# Site Expedition

Secure, US-only site screening and comparison for the Mireye challenge. Warehouse
is the visual hero; Home, Farm, Data Center, and reviewed Custom Missions share
the same deterministic engine.

Current release gate: **115/115 tests**, **11/11 held-out cases**, **8/8 live
E2E**, and **7/7 real-browser flows** on loopback and the HTTPS tunnel.

## Run locally

From the repository root:

```bash
PYTHONPATH=. python3 -m expedition serve
```

The server binds to `127.0.0.1:8030` by default. Authentication is mandatory:
on first start it creates a private token at `expedition/var/access-token`; the
browser exchanges that token for an expiring HttpOnly session cookie. Never put
the token in a URL, JavaScript, screenshot, or checked-in file.

For an HTTPS reverse proxy or Cloudflare quick tunnel, trust forwarded scheme
headers explicitly:

```bash
EXPEDITION_TRUST_PROXY=1 PYTHONPATH=. python3 -m expedition serve
cloudflared tunnel --url http://127.0.0.1:8030 --no-autoupdate
```

Quick-tunnel URLs expire and are demo transport, not durable hosting.

For a temporary public testing session without the access-token prompt:

```bash
EXPEDITION_DISABLE_AUTH=1 EXPEDITION_TRUST_PROXY=1 PYTHONPATH=. python3 -m expedition serve
```

This exposes APIs and paid live actions to anyone with the link. Never use this
mode for production or leave the tunnel running unattended.

## Verify

```bash
node --check expedition/ui/app.js
PYTHONPATH=. python3 -m unittest discover -s expedition/tests
PYTHONPATH=. python3 -m expedition verify
python3 -m expedition.verify.browser_smoke
python3 -m expedition.verify.scene_startup
python3 -m expedition.verify.stress_http
```

The browser runner launches an isolated Chromium profile, unlocks through the
real UI, tests Warehouse/FUTURE/Farm/Data Center/Custom/replay-miss states, and
writes inspected PNGs plus `expedition/var/browser-smoke/report.json`. Pass
`--base-url` and `--output-dir` to run the same gate through HTTPS.

The startup gate verifies a real Google aerial tile is visibly rendered within
four seconds of confirming a plan. The fast first map uses direct image tiles;
Cesium/WebGL is loaded only for explicit TODAY 3D and FUTURE views.

The stress runner checks the five-second slow-header cutoff, immediate recovery,
and 80 replay Expeditions with 16 requests in flight. It spends no Mireye
credits, never prints the deployment token, and writes
`expedition/var/stress-http.json`.

The live E2E gate is explicit because it spends 43 Mireye credits:

```bash
PYTHONPATH=. python3 -m expedition.verify.e2e_live
```

## Product boundary

The board at `/` compiles a structured Mission Plan, screens reviewed or
user-supplied Candidate Sites, isolates Workstream/provider failures, and emits
cited Evidence Atoms, deterministic verdicts, comparison, Skeptic Review, and a
verification brief. Google 3D/Aerial and the rights-cleared FUTURE GLTF are
presentation-only and never score.

An EPA ECHO/FRS lookup runs only after a Mireye RMP proximity hit. It links the
official facility record and adds a blocking Phase I ESA action, but shares the
`EPA` independence group and never becomes duplicate corroboration or a clean-site
certification.

`--live` spends Mireye credits. Quote-before-fetch and the 20,000 soft / 25,000
hard build ceilings remain enforced; parcel-group fields are opt-in.

This is a hardened, locally demoable prototype—not durable production hosting.
The stdlib server is not a production TLS reverse proxy. Licensed national
inventory, authoritative capacity, zoning approval, water rights, FIT parcel
geometry, cloud monetary instrumentation, and progressive result streaming
remain intentionally deferred.

For the demo path and exact residual risks, read [`var/DEMO.md`](var/DEMO.md)
and [`HANDOFF.md`](HANDOFF.md).
