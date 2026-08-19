# DoorDash + Uber MCP exploration

Cloned under `mcp-explore/`. Official vendor docs: [Drive API](https://developer.doordash.com/en-US/api/drive/), [About Drive](https://developer.doordash.com/en-US/docs/drive/overview/about_drive/), [Uber Rides v1.2](https://developer.uber.com/docs/riders/references/api), [Uber sandbox](https://developer.uber.com/docs/riders/guides/sandbox). There is **no official DoorDash or Uber MCP**. Community copies live on GitHub / Glama / LobeHub / npm.

## What is actually installed

| Server | In Cursor? | Needs keys? | Status |
|---|---|---|---|
| `chaituredd/doordash-mcp-server` mock | **Yes** — `.cursor/mcp.json` `doordash` | No | Built, 12 tools listed over stdio |
| `amannm/doordash-mcp` | No | Yes (JWT) | Cloned only |
| `199-mcp/mcp-uber` | No | Yes (OAuth) | `npm install` + `tsc` OK; will not talk to Uber without an app |
| `MoulikShah/uber-mcp` | No | No in mock | Cloned; best Uber **mock** (surge 409) |
| `AriOliv/uber-mcp` | **Do not add** | Uber cookies + Chromium | Rider-web scrape, PerimeterX, ToS |

DoorDash mock was broken on `npm run build` (MCP SDK now wants Zod on `server.prompt`). Local patch: `src/server.ts` prompt args → `z.string()`. Then `npm run build` succeeded.

Reload MCP in Cursor to pick up `doordash`.

## DoorDash Drive — real HTTP

Base: `https://openapi.doordash.com`. Auth: JWT from `developer_id` + `key_id` + `signing_secret`. Sandbox keys are free at [developer.doordash.com](https://developer.doordash.com). **Production access is currently restricted** (docs: pause if you have not already submitted for review).

| Method | Path | MCP tool (chaituredd) |
|---|---|---|
| POST | `/drive/v2/quotes` | `create_delivery_quote` |
| POST | `/drive/v2/quotes/{id}/accept` | `accept_delivery_quote` |
| POST | `/drive/v2/deliveries` | `create_delivery` |
| GET | `/drive/v2/deliveries/{id}` | `get_delivery_status` |
| PATCH | `/drive/v2/deliveries/{id}` | (amannm only: `update_delivery`) |
| PUT | `/drive/v2/deliveries/{id}/cancel` | `cancel_delivery` |
| GET/POST | `/developer/v1/businesses…` | `get_business_info` / `list_stores` / `create_store` |

Drive is **logistics**, not restaurant search. There is no official “search nearby tacos” endpoint.

### Bugs / lies in the wrappers

- chaituredd README marks `search_restaurants` / `get_menu` as live ✓. Live client returns `[]` / `null`. Mock restaurants are a hard-coded **Austin, TX** list (Torchy’s, Thai Kun, Franklin BBQ, …).
- chaituredd live business calls hit `/drive/v2/businesses/…`. Official catalog is `/developer/v1/businesses/…`. Those three tools will 404 against a real key.
- amannm is a thin `@doordash/sdk` pass-through (6 tools). No mock. Needs a live JWT or it prints missing-env and dies.

### Proven mock loop (ran 12 Aug 2026)

```
create_delivery_quote  pickup=2801 Guadalupe St, Austin  dropoff=San Leon, TX
  → Quote D-x2cxxljj  fee $3.99  pickup ~18 min  dropoff ~38 min  expires 5 min
create_delivery        external_delivery_id=DEMO-FLOOD-1
  → status created
cancel_delivery        reason=dropoff inundated
  → status cancelled
```

That is the contest-shaped Drive act: quote → cited planet check → cancel.

## Uber Rides — real HTTP

| Env | Base |
|---|---|
| production | `https://api.uber.com/v1.2` |
| sandbox | `https://sandbox-api.uber.com/v1.2` |

OAuth scopes: `profile`, `request`, `ride_request`. `request` is privileged. **MoulikShah’s README (and LEARNING.md): even sandbox apps get `invalid_scope` until Uber BD whitelist.** That matches Uber’s own “privileged scope” docs. Do not plan a live Uber clip this week.

Core rider endpoints: `GET /estimates/price`, `POST /requests/estimate`, `POST /requests`, `GET/DELETE /requests/{id}`.

Sandbox-only (the fashionable demo hook):

```
PUT https://sandbox-api.uber.com/v1.2/sandbox/products/{product_id}
{ "surge_multiplier": 2.2, "drivers_available": true }
```

Multiplier ≥ 2.0 triggers Uber’s two-stage surge confirm. Changes also show up on `GET /estimates/price`.

### Wrapper gaps

- **199-mcp/mcp-uber** tools: `uber_get_auth_url`, `uber_set_access_token`, `uber_get_price_estimates`, `uber_request_ride`, `uber_get_ride_status`, `uber_cancel_ride`. Default `apiBaseUrl` is `https://api.uber.com` even when `UBER_ENVIRONMENT=sandbox`. **No tool** for `PUT /sandbox/products/{id}`. Surge cannot be driven from this MCP as shipped.
- **MoulikShah/uber-mcp** is the one that actually models surge: mock FastAPI on `:8100`, `FORCE_SURGE=true`, `book_ride` returns 409 + `surge_confirmation_id`, tool-level `confirmed: bool` gate. Client already has `sandbox_set_product`. Needs a second process (`uvicorn src.mock_uber_api:app --port 8100`) plus the MCP. Not wired into Cursor yet.
- **AriOliv/uber-mcp**: 35 tools against the rider website via Playwright + cookie capture. ~170 MB Chromium. Cookies last ~24h. ToS / PerimeterX. Skip.

## What we can do from here

**This week, no vendor keys**

1. Cursor already has DoorDash mock. Agent: `create_delivery_quote` → Mireye/EE on the dropoff pin → `cancel_delivery`.
2. Optional Uber-shaped clip: run Moulik mock with `FORCE_SURGE=true`, refuse the ride when the pin is wet. Same loop, fake Uber HTTP.

**If you sign up at developer.doordash.com (sandbox JWT, free)**

Same quote/cancel against `openapi.doordash.com`. Still no restaurant search. Production Drive is gated.

**If you want live Uber**

Create an app at [developer.uber.com](https://developer.uber.com), expect `invalid_scope` until BD approval, then you still have to patch mcp-uber’s sandbox base URL and add the surge PUT. Moulik’s client is closer.

**Do not**

- Add AriOliv to Cursor.
- Film `create_store` / ghost kitchens (wrong Drive path + not the buyer).
- Treat chaituredd restaurant search as a real DoorDash Marketplace API.
