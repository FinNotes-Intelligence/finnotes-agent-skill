# FinNotes API Documents

This document defines the commercial FinNotes API contract for authentication, request format, point charging, response headers, product endpoints, usage inspection, logs, newsletter preferences, and AI Agent push delivery.

The canonical API base URL is:

```text
https://api.finnotes.com/v1
```

All examples use API version `v1`. The developer console (mint keys, inspect usage, configure delivery) lives at `https://platform.finnotes.com` — that hostname serves the human-readable HTML console, not the API itself.

## 1. Core Principles

FinNotes API access is point based. A normal product request is charged when it successfully returns or delivers billable data. Error and invalid requests are covered by the daily invalid-request allowance in Section 6.

Points are deducted from the authenticated account's active monthly allowance. Response headers and response bodies include the charged amount and remaining balance whenever the endpoint is billable.

All requests must use HTTPS and JSON. API keys must be sent in the `Authorization` header. Do not send API keys in query strings, request bodies, logs, or client-side code.

## 2. Plans And Monthly Points

| Plan | Monthly points | Sustained request limit | Intended usage |
| --- | ---: | ---: | --- |
| Pro | 1,350 pts | 3 requests / second | Regular API access and controlled production usage. |
| Max | 5,000 pts | 10 requests / second | Higher-volume workflows, broader data pulls, and heavier automation. |

Monthly points reset on the account billing reset date. Unused points do not roll over unless a separate commercial agreement says otherwise.

## 3. Authentication

Use Bearer authentication.

```http
Authorization: Bearer fnp_xxxxxxxxxxxxxxxxxxxxx
Accept: application/json
```

All API platform keys use the `fnp_` prefix. There is no separate live / sandbox / test key class — each account uses a single key type, matching the convention used by OpenAI, Anthropic, and Gemini. Developers test against their own real account; we do not maintain a sandbox environment.

Example:

```bash
curl "https://api.finnotes.com/v1/news?range=today&type=all" \
  -H "Authorization: Bearer $FINNOTES_API_KEY" \
  -H "Accept: application/json"
```

### Required Headers

| Header | Required | Description |
| --- | --- | --- |
| `Authorization` | Yes | `Bearer <api_key>`. |
| `Accept` | Recommended | Use `application/json`. |
| `Content-Type` | Required for body requests | Use `application/json` for `POST`, `PUT`, and `PATCH`. |
| `Idempotency-Key` | Recommended for writes | Unique client-generated key for retrying write requests safely. |

### Response Headers

Billable and usage-aware endpoints return point headers.

| Header | Description |
| --- | --- |
| `X-Request-Id` | Unique request identifier for support, logs, and reconciliation. |
| `X-Points-Charged` | Points charged for this request. `0.00` for non-billable or failed requests. |
| `X-Points-Remaining` | Remaining monthly points after this request. |
| `X-Points-Allowance` | Current monthly point allowance for the account. |
| `X-RateLimit-Limit` | Account-specific request limit for the current window, when applicable. |
| `X-RateLimit-Remaining` | Remaining requests in the current rate-limit window, when applicable. |
| `Retry-After` | Seconds to wait before retrying a `429` response. |

Point values are decimal numbers. The ledger stores point charges to two decimal places.

## 4. API Key Permissions

Permissions are configured in the API Platform UI when creating or editing a key.

| Permission | Default | Grants access to |
| --- | --- | --- |
| `Basic(all news, report & data)` | On | News metadata, market-news detail, chart-news detail, full reports, and data-series endpoints. |
| `Notes Download & Upload` | On | Notes list, download, import, upload, and sync endpoints for the authenticated user. |
| `View Usage and remaining points` | Off | Own point balance and current-month daily point totals. |
| `View Log` | Off | Read enabled request logs. |
| `Manage Log` | Off | Enable, disable, and delete request logs. |
| `Manage Newsletter preferences` | Off | Create, update, and cancel report/push subscriptions. |
| `All API usage state` | Off | Account-wide current-month daily point totals across all keys. This does not expose request details. |
| `Notification management` | Off | Manage API activity email notifications. |

Every billable response still returns the calling key's point headers. The `View Usage and remaining points` permission is required only when calling dedicated account or usage endpoints.

### 4.1 View The Current Key's Permissions

```http
GET /v1/api-keys/current
```

Returns the permissions attached to the API key used for the request.

Required permission: none beyond a valid API key. A key must always be able to inspect its own permissions so developers can debug access issues without needing account-wide Usage or Log permissions.

Point charge: `0.00 pts`. Key inspection is free.

This endpoint does not list other API keys and does not return the full API key secret.

**Point balance.** The envelope's `remaining_points` field reflects the live account balance — for a brand-new key that has not yet made a billable request, it returns the full plan allowance (e.g. `1350.0` for Pro). For the authoritative full point breakdown (allowance, used, remaining, usage rate, reset timestamp), call **`/v1/account/points`**.

### Request

```bash
curl "https://api.finnotes.com/v1/api-keys/current" \
  -H "Authorization: Bearer $FINNOTES_API_KEY" \
  -H "Accept: application/json"
```

### Response

```json
{
  "data": {
    "api_key_id": "key_prod_001",
    "name": "Production server",
    "key_prefix": "fnp",
    "status": "active",
    "permissions": [
      {
        "id": "basic",
        "label": "Basic(all news, report & data)",
        "enabled": true
      },
      {
        "id": "notes",
        "label": "Notes Download & Upload",
        "enabled": true
      },
      {
        "id": "usage",
        "label": "View Usage and remaining points",
        "enabled": true
      },
      {
        "id": "view_log",
        "label": "View Log",
        "enabled": false
      }
    ]
  },
  "points_charged": 0.0,
  "remaining_points": 922.0,
  "request_id": "req_8e30d3ac"
}
```

## 5. Point Charging Rules

### 5.1 News List Metadata

`GET /v1/news` returns routing metadata and display metadata for `market-news`, `chart-news`, and `column-article`: `id`, `type`, `slug`, `url`, `title`, and `dek`.

| Date mode | Request | Point charge |
| --- | --- | ---: |
| Today | `range=today` | 1.00 pt |
| Specific date | `date=YYYY-MM-DD` | 1.50 pts |
| Last X days | `last_days=X` | `1.5 * X - 0.5` pts |

Examples:

| Example | Charge |
| --- | ---: |
| `GET /v1/news?range=today&type=all` | 1.00 pt |
| `GET /v1/news?date=2026-06-19&type=all` | 1.50 pts |
| `GET /v1/news?last_days=7&type=all` | 10.00 pts |

The `type` filter does not multiply the point charge. A request for `type=all` and a request for a single supported type use the same date-window charge. The list endpoint does not include article body content.

Use the returned `type` and `slug` to request a priced detail payload with `GET /v1/news/{type}/{slug}`. The returned website `url` remains available for display, attribution, and user-facing links, but clients should not URL-encode the full website URL into the detail endpoint.

`column-article` is included in the news list metadata product only. The current pricing contract does not define a standalone `column-article` detail endpoint. If full column content is commercialized later, it must receive an explicit point price before being exposed.

### 5.2 Product Request Pricing

| Product | Endpoint family | Payload | Point charge |
| --- | --- | --- | ---: |
| Market-news detail | `/v1/news/market-news/{slug}` | Single market-news article payload. | 1.00 pt |
| Chart-news detail | `/v1/news/chart-news/{slug}` | Chart article payload and chart binding metadata. | 1.25 pts |
| Full Report | `/v1/reports/{id_or_slug}` | Long-form report content, sections, citations, and references. | 5.50 pts |
| Data-series list | `/v1/data-series/categories`, `/v1/data-series` | Category directory or series directory. Category items return `name`, `slug`, and `url`; series items return `name`, `slug`, `url`, and `unit`. | First 10 list requests per day are free; then 5.00 pts/request |
| Data-series detail | `/v1/data-series/{slug}` | Detailed metadata for one series. Does not include data points or latest numeric value. | 1.00 pt |
| Data-series points | `/v1/data-series/{slug}/points` | Selected data points for one series. Supports all, between dates, or since a date. | 1.00 pt per 250 returned data points, minimum 1.00 pt |
| Own Notes list | `/v1/notes` | User-owned Notes list for the authenticated account. | First 10 list requests per day are free; then 1.00 pt/request |
| Notes download / upload | `/v1/notes/{note_id}`, `/v1/notes/import` | Move Notes payloads in or out of the account workspace. | 3.50 pts |

### 5.3 Non-Billable Platform Requests

The following requests do not deduct points:

| Area | Examples |
| --- | --- |
| Current API key inspection | `/v1/api-keys/current` |
| Account balance and usage inspection | `/v1/account/points`, `/v1/usage` |
| Log configuration and retrieval | `/v1/logs/settings`, `/v1/logs` |
| Newsletter preference configuration | `/v1/newsletter/preferences`, `/v1/push/*/preferences` |
| API activity notification settings | `/v1/notifications/preferences` |

These endpoints may require explicit key permissions.

### 5.4 Push Charging

Free report subscriptions do not consume points.

Trace Data Release push is charged when a selected release or policy decision alert is delivered:

| Delivery channel | Charge per triggered alert |
| --- | ---: |
| Email only | 2.50 pts |
| API Push only | 2.50 pts |
| Email + API Push | 4.00 pts |

Real-time News Push follows the same point price as actively retrieving the delivered article through the API. For example, a delivered `market-news` item costs 1.00 pt and a delivered `chart-news` item costs 1.25 pts.

Push charges are deducted at delivery time, not at preference-save time.

## 6. Abuse Protection And Rate Limits

FinNotes applies invalid-request charging and per-second request limits to reduce abuse, scraping probes, and unfair competitive traffic.

### Daily Invalid-Request Allowance

Each membership account receives 40 free error or invalid requests per calendar day. The allowance resets daily at 00:00 UTC.

After the first 40 error or invalid requests in the same day, each additional error or invalid request costs `1.00 pt`.

Examples of error or invalid requests:

| Request type | Example |
| --- | --- |
| Malformed query | Invalid date format, unsupported enum value, missing required range parameter. |
| Invalid resource identifier | Wrong article slug, wrong data-series slug, nonexistent note ID. |
| Permission error | API key calls an endpoint without the required permission. |
| Authentication error | Missing, malformed, revoked, or invalid API key. |
| Validation error | JSON body is valid JSON but fails semantic validation. |

The invalid-request allowance is account-level, not per API key. Requests across all API keys on the same account count toward the same daily 40-request allowance.

### Invalid-Request Charging Rules

| Daily invalid request count | Point charge |
| ---: | ---: |
| 1-40 | 0.00 pts |
| 41+ | 1.00 pt per invalid request |

Server-side `500` and `503` errors are not counted as user invalid requests and do not deduct points.

Rate-limit responses (`429`) do not deduct points. Clients should respect `Retry-After`.

**No-overdraw policy.** Past the 40 free invalid requests, if the account's `remaining_points` is less than the 1.00 pt overage charge, FinNotes **does not deduct anything**. The 4xx error response still goes back to the caller and the daily invalid counter still increments (so abuse signals are preserved), but no points are debited and no `X-Points-Charged` header is emitted on that response. This is forgiving by design — the most common cause of an excess-of-40 invalid burst is an AI agent that hasn't realised the account is out of quota and is retrying.

### Per-Second Request Limits

| Plan | Limit |
| --- | ---: |
| Pro | 3 requests / second |
| Max | 10 requests / second |

The rate limit is account-level and applies across all API keys. If a client exceeds the plan limit, FinNotes returns `429 rate_limit_exceeded` with `Retry-After`.

The rate-limit algorithm is a **1-second sliding window of completed requests**: each successful request lands a row in the internal request ledger with its completion timestamp; a new request is rejected when the count of ledger rows in the trailing 1.0 second already meets the plan limit. `Retry-After` returns the integer seconds until the oldest in-window row expires (typically `1`).

Practical note for clients: because the window counts *completed* requests rather than arrival timestamps, a tight burst of concurrent requests can briefly let more than the nominal plan limit start processing — the limit re-asserts as soon as the first wave of ledger rows is written. Throttling on the client side (one request at a time, or a small concurrency cap) gives the cleanest behaviour. There is no token-bucket reserve.

### Error Response With Invalid-Request Charge

When an invalid request is charged after the daily free allowance is exhausted, the error response includes point fields:

```json
{
  "error": {
    "code": "not_found",
    "message": "The requested data series does not exist.",
    "request_id": "req_invalid_41",
    "details": {
      "invalid_requests_today": 41,
      "free_invalid_requests_remaining": 0
    }
  },
  "points_charged": 1.0,
  "remaining_points": 916.0
}
```

## 7. Common Request Parameters

### Article Type Enum (Case Convention)

The API uses kebab-case for article type values in both request and response:

| API value | Internal storage |
| --- | --- |
| `market-news` | `market_news` |
| `chart-news` | `chart_news` (resolved via the `ChartArticle` model) |
| `column-article` | `column_article` |

The internal snake_case form is never exposed in v1 API payloads. Clients must use the kebab-case form for filtering, path parameters, and event payloads.

### Date And Time

All API timestamps are ISO 8601 strings in UTC, for example:

```text
2026-06-19T10:30:00Z
```

Date-only parameters use `YYYY-MM-DD` and are interpreted as the FinNotes publishing date in UTC.

### Pagination

List endpoints use cursor pagination.

| Parameter | Type | Default | Description |
| --- | --- | ---: | --- |
| `limit` | integer | 50 | Number of records to return. Maximum `100`. |
| `cursor` | string | None | Cursor returned by the previous page. |

Paginated responses include:

```json
{
  "data": [],
  "pagination": {
    "next_cursor": "cur_abc123",
    "has_more": true
  }
}
```

### Sorting

Where sorting is supported:

| Parameter | Values | Description |
| --- | --- | --- |
| `sort` | `published_at`, `score`, `title` | Sort field. |
| `order` | `asc`, `desc` | Sort direction. Defaults to `desc`. |

## 8. Standard Response Envelope

Successful billable endpoints use this shape:

```json
{
  "data": {},
  "points_charged": 1.0,
  "remaining_points": 921.0,
  "request_id": "req_9f8a21c7"
}
```

Successful list endpoints use:

```json
{
  "data": [],
  "pagination": {
    "next_cursor": null,
    "has_more": false
  },
  "points_charged": 1.0,
  "remaining_points": 921.0,
  "request_id": "req_9f8a21c7"
}
```

Non-billable platform endpoints use the same envelope but return `points_charged: 0.0`.

## 9. Error Response

Errors use a consistent JSON shape:

After the daily 40-request invalid-request allowance is exhausted, user-side error responses may include `points_charged: 1.0` and `remaining_points` at the top level.

```json
{
  "error": {
    "code": "insufficient_points",
    "message": "The account does not have enough points for this request.",
    "request_id": "req_9f8a21c7",
    "details": {
      "required_points": 5.5,
      "remaining_points": 2.0
    }
  }
}
```

Every error response carries the same `X-Request-Id` HTTP header documented in section 3, regardless of status code. The `request_id` field inside the error body mirrors that header so support tooling can grep either surface.

| HTTP status | Code examples | Meaning |
| ---: | --- | --- |
| `400` | `bad_request`, `invalid_query` | Malformed request or incompatible parameters. |
| `401` | `unauthorized`, `invalid_api_key` | Missing, invalid, or revoked API key. |
| `402` | `insufficient_points` | Request is valid but the account does not have enough points. |
| `403` | `permission_denied` | API key does not have the required permission. |
| `404` | `not_found` | Requested resource does not exist or is not visible to the account. |
| `409` | `idempotency_conflict` | Same idempotency key was reused with a different request body. |
| `422` | `validation_error` | Request body is syntactically valid but semantically invalid. |
| `429` | `rate_limit_exceeded` | Too many requests. Respect `Retry-After`. |
| `500` | `internal_error` | Internal server error. |
| `503` | `service_unavailable` | Temporary outage or maintenance. |

## 10. Endpoints

## 10.1 News List Metadata

```http
GET /v1/news
```

Returns metadata for `market-news`, `chart-news`, and `column-article`.

Required permission: `Basic(all news, report & data)`.

Point charge: by date mode.

### Query Parameters

Exactly one date mode must be supplied.

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `range` | string | Conditional | Use `today` for the current FinNotes publishing date. |
| `date` | string | Conditional | Specific publishing date, `YYYY-MM-DD`. |
| `last_days` | integer | Conditional | Rolling lookback window in days. Minimum `1`. |
| `type` | string | Optional | `all`, `market-news`, `chart-news`, or `column-article`. Defaults to `all`. |
| `limit` | integer | Optional | Page size. Maximum `100`. |
| `cursor` | string | Optional | Cursor for the next page. |
| `sort` | string | Optional | `published_at` or `score`. Defaults to `published_at`. |
| `order` | string | Optional | `asc` or `desc`. Defaults to `desc`. |

Invalid combinations:

| Invalid request | Reason |
| --- | --- |
| `range=today&date=2026-06-19` | Multiple date modes. |
| `last_days=0` | Lookback window must be at least one day. |
| `type=report` | Unsupported news list type. |

### Request

```bash
curl "https://api.finnotes.com/v1/news?range=today&type=all&limit=50" \
  -H "Authorization: Bearer $FINNOTES_API_KEY" \
  -H "Accept: application/json"
```

### Response

```json
{
  "data": [
    {
      "id": "mn_01jz9x2h0n",
      "type": "market-news",
      "slug": "oil-risk-premium-cools",
      "title": "Oil trims weekly gain as shipping risk premium cools",
      "url": "https://finnotes.com/market-news/oil-risk-premium-cools",
      "dek": "Crude eased after traders reassessed near-term supply disruption risk.",
      "published_at": "2026-06-19T08:15:00Z",
      "importance_score": 7.4,
      "anomaly_score": 5.8
    }
  ],
  "pagination": {
    "next_cursor": null,
    "has_more": false
  },
  "points_charged": 1.0,
  "remaining_points": 921.0,
  "request_id": "req_9f8a21c7"
}
```

## 10.2 News Detail By Type And Slug

```http
GET /v1/news/{type}/{slug}
```

Returns the full payload for one priced news-detail product.

This is the primary detail endpoint because it follows the same routing information returned by `GET /v1/news`. A list item with:

```json
{
  "type": "market-news",
  "slug": "oil-risk-premium-cools",
  "url": "https://finnotes.com/market-news/oil-risk-premium-cools"
}
```

maps directly to:

```http
GET /v1/news/market-news/oil-risk-premium-cools
```

Required permission: `Basic(all news, report & data)`.

Point charge:

| Type | Point charge | Detail support |
| --- | ---: | --- |
| `market-news` | 1.00 pt | Supported |
| `chart-news` | 1.25 pts | Supported |
| `column-article` | Not priced | Metadata only until a standalone detail price is defined |

### Path Parameters

| Parameter | Description |
| --- | --- |
| `type` | `market-news` or `chart-news`. |
| `slug` | Article slug returned by `/v1/news`. This is the final path segment of the website URL. |

### Query Parameters

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `include_chart` | boolean | `true` | Chart-news only. Include chart binding metadata. Ignored for market-news. |
| `include_references` | boolean | `true` | Include references and source links where available. |

### Market-News Request

```bash
curl "https://api.finnotes.com/v1/news/market-news/oil-risk-premium-cools?include_references=true" \
  -H "Authorization: Bearer $FINNOTES_API_KEY" \
  -H "Accept: application/json"
```

### Market-News Response

```json
{
  "data": {
    "id": "mn_01jz9x2h0n",
    "type": "market-news",
    "slug": "oil-risk-premium-cools",
    "title": "Oil trims weekly gain as shipping risk premium cools",
    "url": "https://finnotes.com/market-news/oil-risk-premium-cools",
    "dek": "Crude eased after traders reassessed near-term supply disruption risk.",
    "body": "Full article body...",
    "published_at": "2026-06-19T08:15:00Z",
    "importance_score": 7.4,
    "anomaly_score": 5.8,
    "references": [
      {
        "title": "Source title",
        "url": "https://example.com/source"
      }
    ]
  },
  "points_charged": 1.0,
  "remaining_points": 920.0,
  "request_id": "req_6b18e827"
}
```

### Chart-News Request

```bash
curl "https://api.finnotes.com/v1/news/chart-news/us-yields-reprice-policy-path?include_chart=true" \
  -H "Authorization: Bearer $FINNOTES_API_KEY" \
  -H "Accept: application/json"
```

### Chart-News Response

```json
{
  "data": {
    "id": "cn_01jz9xd7nm",
    "type": "chart-news",
    "slug": "us-yields-reprice-policy-path",
    "title": "US yields reprice the policy path after payrolls",
    "url": "https://finnotes.com/charts/us-yields-reprice-policy-path",
    "dek": "A chart-backed read on the front-end rate reaction.",
    "body": "Full article body...",
    "published_at": "2026-06-19T09:05:00Z",
    "importance_score": 8.1,
    "anomaly_score": 7.2,
    "chart": {
      "id": "chart_10y_2y_policy_path",
      "title": "Treasury curve and policy expectations",
      "is_featured": true,
      "window_type": "dynamic",
      "dynamic_window_months": 36,
      "window_start_date": null,
      "window_end_date": null,
      "series": [
        {
          "series_id": "us_10y_yield",
          "label": "US 10Y yield"
        },
        {
          "series_id": "us_2y_yield",
          "label": "US 2Y yield"
        }
      ]
    },
    "references": []
  },
  "points_charged": 1.25,
  "remaining_points": 918.75,
  "request_id": "req_52a87c8e"
}
```

## 10.3 News Detail By ID

```http
GET /v1/news/{id}
```

Returns the same detail payload as `GET /v1/news/{type}/{slug}` by resolving the article ID returned from `GET /v1/news`.

This endpoint is a convenience path for clients that store FinNotes IDs. The primary human-readable path remains `GET /v1/news/{type}/{slug}`.

Required permission: `Basic(all news, report & data)`.

Point charge: based on the resolved article type.

| ID prefix | Resolved type | Point charge |
| --- | --- | ---: |
| `mn_` | `market-news` | 1.00 pt |
| `cn_` | `chart-news` | 1.25 pts |

If the ID resolves to a product without standalone detail pricing, the API returns `422 unsupported_detail_product` and deducts no points.

### Request

```bash
curl "https://api.finnotes.com/v1/news/cn_01jz9xd7nm?include_chart=true" \
  -H "Authorization: Bearer $FINNOTES_API_KEY" \
  -H "Accept: application/json"
```

### Response

The response envelope and payload fields are the same as the corresponding `GET /v1/news/{type}/{slug}` response.

## 10.4 Full Report

```http
GET /v1/reports/{id_or_slug}
```

Returns a long-form report payload, including sections, citations, and references.

A FinNotes Full Report is stored as the long-form `full_report` field of a research article (internally `column_article`). The same article may have a separate short body that the news list metadata surfaces as `column-article`; only the long-form `full_report` is priced and returned here. Use the article's slug or id as `id_or_slug`.

Required permission: `Basic(all news, report & data)`.

Point charge: `5.50 pts`.

### Query Parameters

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `include_references` | boolean | `true` | Include references and source links. |

The report body is returned as raw HTML in `sections[0].body`. Server-side markdown conversion is not implemented in v1; clients that need markdown should convert on the consumer side.

### Request

```bash
curl "https://api.finnotes.com/v1/reports/macro-strategy-fed-path" \
  -H "Authorization: Bearer $FINNOTES_API_KEY" \
  -H "Accept: application/json"
```

The `id_or_slug` path parameter accepts either a `ca_<n>` typed id (matching the column-article entries surfaced in the news list metadata) or the column-article's slug.

### Response

```json
{
  "data": {
    "id": "ca_42",
    "title": "Fed path: what changed after payrolls",
    "url": "https://finnotes.com/market-news/macro-strategy-fed-path",
    "dek": "A long-form report on policy expectations, rates, and macro risk.",
    "published_at": "2026-06-19T11:00:00Z",
    "sections": [
      {
        "heading": "",
        "body": "<p>Section body...</p>"
      }
    ],
    "citations": [],
    "references": []
  },
  "points_charged": 5.5,
  "remaining_points": 913.25,
  "request_id": "req_e510d55e"
}
```

## 10.5 Data-Series Lists

### Data Categories

```http
GET /v1/data-series/categories
```

Returns the available data categories. Clients can use the returned category `url` to request all data series in that category.

Required permission: `Basic(all news, report & data)`.

Point charge: first 10 data-series list requests per account per day are free; additional requests cost `5.00 pts` each.

Category directory items return only:

| Field | Description |
| --- | --- |
| `name` | Human-readable category name. |
| `slug` | Category slug used for filtering. |
| `url` | API URL for retrieving the data-series directory in this category. |

### Categories Request

```bash
curl "https://api.finnotes.com/v1/data-series/categories" \
  -H "Authorization: Bearer $FINNOTES_API_KEY" \
  -H "Accept: application/json"
```

### Categories Response

```json
{
  "data": [
    {
      "name": "Commodities",
      "slug": "commodities",
      "url": "https://api.finnotes.com/v1/data-series?category=commodities"
    },
    {
      "name": "Macro",
      "slug": "macro",
      "url": "https://api.finnotes.com/v1/data-series?category=macro"
    },
    {
      "name": "Rates",
      "slug": "rates",
      "url": "https://api.finnotes.com/v1/data-series?category=rates"
    }
  ],
  "daily_free_list_requests_remaining": 9,
  "points_charged": 0.0,
  "remaining_points": 922.0,
  "request_id": "req_categories_6f9c02"
}
```

### Data-Series Directory

```http
GET /v1/data-series
```

Returns a paginated directory of available data series. Clients can request the full directory or filter it by one category.

Required permission: `Basic(all news, report & data)`.

Point charge: first 10 data-series list requests per account per day are free; additional requests cost `5.00 pts` each.

This endpoint returns lightweight directory records only. It does not return frequency, source, date availability, latest values, or historical point values. Use `GET /v1/data-series/{slug}` when the client needs detailed metadata, and use `GET /v1/data-series/{slug}/points` when the client needs actual point values.

Data-series directory items return only:

| Field | Description |
| --- | --- |
| `name` | Human-readable series name. |
| `slug` | Series slug used in the detail endpoint. |
| `url` | API URL for retrieving the series detail payload. |
| `unit` | Unit for the series values, such as `USD/oz`, `%`, `index`, or `USD`. |

### Query Parameters

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `category` | string | None | Optional category slug returned by `GET /v1/data-series/categories`. If omitted, returns the full data-series directory. |
| `limit` | integer | `100` | Page size. Maximum `500`. |
| `cursor` | string | None | Cursor for the next page. |

The full directory may contain thousands of records. `GET /v1/data-series` is always paginated; clients must follow `pagination.next_cursor` to retrieve additional pages. Each cursor page is a separate data-series list request and counts toward the daily 10 free list requests. After the free allowance is exhausted, each cursor page costs 5.00 pts.

### All Series Request

```bash
curl "https://api.finnotes.com/v1/data-series?limit=100" \
  -H "Authorization: Bearer $FINNOTES_API_KEY" \
  -H "Accept: application/json"
```

### Category Series Request

```bash
curl "https://api.finnotes.com/v1/data-series?category=commodities&limit=100" \
  -H "Authorization: Bearer $FINNOTES_API_KEY" \
  -H "Accept: application/json"
```

### Series Directory Response

```json
{
  "data": [
    {
      "name": "Gold spot price",
      "slug": "gold",
      "url": "https://api.finnotes.com/v1/data-series/gold",
      "unit": "USD/oz"
    },
    {
      "name": "Annual GDP",
      "slug": "annual-gdp",
      "url": "https://api.finnotes.com/v1/data-series/annual-gdp",
      "unit": "USD"
    }
  ],
  "pagination": {
    "next_cursor": null,
    "has_more": false
  },
  "daily_free_list_requests_remaining": 8,
  "points_charged": 0.0,
  "remaining_points": 922.0,
  "request_id": "req_catalog_13d904"
}
```

After the daily free data-series list allowance is exhausted, the same endpoint returns `points_charged: 5.0`:

```json
{
  "data": [
    {
      "name": "Gold spot price",
      "slug": "gold",
      "url": "https://api.finnotes.com/v1/data-series/gold",
      "unit": "USD/oz"
    }
  ],
  "pagination": {
    "next_cursor": "cur_next_page",
    "has_more": true
  },
  "daily_free_list_requests_remaining": 0,
  "points_charged": 5.0,
  "remaining_points": 917.0,
  "request_id": "req_catalog_paid_7aa2b1"
}
```

## 10.6 Data-Series Detail

```http
GET /v1/data-series/{slug}
```

Returns detailed metadata for one data series. This endpoint does not return historical data points, latest numeric value, or selected point values.

Required permission: `Basic(all news, report & data)`.

Point charge: `1.00 pt`.

### Path Parameters

| Parameter | Description |
| --- | --- |
| `slug` | Series slug returned by the data-series directory. |

### Request

```bash
curl "https://api.finnotes.com/v1/data-series/gold" \
  -H "Authorization: Bearer $FINNOTES_API_KEY" \
  -H "Accept: application/json"
```

### Response

```json
{
  "data": {
    "name": "Gold spot price",
    "slug": "gold",
    "url": "https://api.finnotes.com/v1/data-series/gold",
    "description": "Daily gold spot price in US dollars per troy ounce.",
    "category": {
      "name": "Commodities",
      "slug": "commodities",
      "url": "https://api.finnotes.com/v1/data-series?category=commodities"
    },
    "frequency": "daily",
    "unit": "USD/oz",
    "region": "GLOBAL",
    "source": "finnotes",
    "first_period_date": "1979-01-01",
    "latest_period_date": "2026-06-19",
    "default_order": "asc",
    "points_url": "https://api.finnotes.com/v1/data-series/gold/points"
  },
  "points_charged": 1.0,
  "remaining_points": 916.0,
  "request_id": "req_series_detail_4dc9f8"
}
```

## 10.7 Data-Series Points

```http
GET /v1/data-series/{slug}/points
```

Returns selected data points for one data series. This is the only data-series endpoint that returns point values.

Required permission: `Basic(all news, report & data)`.

Point charge:

| Result | Point charge |
| --- | ---: |
| Valid request returns `N` data points | `max(1, ceil(N / 250))` pts |
| Valid request, series exists, but the selected date window contains no data points | 1.00 pt |
| Validation error, unsupported range mode, missing required date, malformed date, `start_date > end_date`, permission error, or series not found | 0.00 pts |

Pricing is calculated per response page. If a selected range has more data than one page, each cursor request is charged by the number of data points returned in that response.

Examples:

| Returned data points in one response | Point charge |
| ---: | ---: |
| 0 valid empty window | 1.00 pt |
| 1-250 | 1.00 pt |
| 251-500 | 2.00 pts |
| 501-750 | 3.00 pts |

### Data Selection Modes

Exactly one data selection mode must be supplied.

| Mode | Required parameters | Meaning |
| --- | --- | --- |
| `range=all` | None | Select the full available history for the series. Use `limit` and `cursor` to page through large point sets. |
| `range=between` | `start_date`, `end_date` | Return points with `period_date >= start_date` and `period_date <= end_date`. |
| `range=since` | `start_date` | Return points from `start_date` through the latest available point. |

Invalid combinations:

| Invalid request | Reason | Point charge |
| --- | --- | ---: |
| `range=between&start_date=2024-01-01` | Missing `end_date`. | 0.00 pts |
| `range=since&end_date=2026-06-19` | `since` only accepts `start_date`. | 0.00 pts |
| `range=between&start_date=2026-01-01&end_date=2025-01-01` | `start_date` is after `end_date`. | 0.00 pts |
| `range=all&start_date=2024-01-01` | `all` does not accept date boundaries. | 0.00 pts |

Valid empty-window request:

```http
GET /v1/data-series/annual-gdp/points?range=between&start_date=2025-04-01&end_date=2025-05-01
```

If the series exists but has no points inside that valid window, the API returns `data.points: []`, `empty_window: true`, and `points_charged: 1.0`.

### Query Parameters

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `range` | string | Required | `all`, `between`, or `since`. |
| `start_date` | string | Conditional | Required for `between` and `since`. Date format: `YYYY-MM-DD`. |
| `end_date` | string | Conditional | Required for `between`; not accepted for `all` or `since`. Date format: `YYYY-MM-DD`. |
| `limit` | integer | `500` | Maximum point count. Maximum `5000`. |
| `cursor` | string | None | Cursor for the next page when the selected point set exceeds `limit`. |
| `order` | string | `asc` | `asc` or `desc`. |

### Since Request

```bash
curl "https://api.finnotes.com/v1/data-series/gold/points?range=since&start_date=2024-01-01&limit=500" \
  -H "Authorization: Bearer $FINNOTES_API_KEY" \
  -H "Accept: application/json"
```

### Since Response

```json
{
  "data": {
    "name": "Gold spot price",
    "slug": "gold",
    "range": {
      "mode": "since",
      "start_date": "2024-01-01",
      "end_date": "2026-06-19"
    },
    "empty_window": false,
    "returned_points": 2,
    "points": [
      {
        "period_date": "2026-06-18",
        "value": 2438.1
      },
      {
        "period_date": "2026-06-19",
        "value": 2450.25
      }
    ]
  },
  "pagination": {
    "next_cursor": null,
    "has_more": false
  },
  "points_charged": 1.0,
  "remaining_points": 915.0,
  "request_id": "req_843ea97d"
}
```

### All Points Request

```bash
curl "https://api.finnotes.com/v1/data-series/gold/points?range=all&limit=5000&order=asc" \
  -H "Authorization: Bearer $FINNOTES_API_KEY" \
  -H "Accept: application/json"
```

### Between Dates Request

```bash
curl "https://api.finnotes.com/v1/data-series/gold/points?range=between&start_date=2026-01-01&end_date=2026-06-19" \
  -H "Authorization: Bearer $FINNOTES_API_KEY" \
  -H "Accept: application/json"
```

### Empty Window Response

```json
{
  "data": {
    "name": "Annual GDP",
    "slug": "annual-gdp",
    "range": {
      "mode": "between",
      "start_date": "2025-04-01",
      "end_date": "2025-05-01"
    },
    "empty_window": true,
    "returned_points": 0,
    "points": []
  },
  "pagination": {
    "next_cursor": null,
    "has_more": false
  },
  "points_charged": 1.0,
  "remaining_points": 914.0,
  "request_id": "req_empty_5c137a"
}
```

## 10.8 Own Notes List

```http
GET /v1/notes
```

Returns user-owned Notes metadata for the authenticated account.

Required permission: `Notes Download & Upload`.

Point charge: first 10 Own Notes list requests per account per day are free; additional requests cost `1.00 pt` each. Each cursor page is a separate Own Notes list request and counts toward the daily 10 free Own Notes list requests.

### Query Parameters

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `limit` | integer | `50` | Page size. Maximum `100`. |
| `cursor` | string | None | Cursor for the next page. |
| `updated_after` | string | None | Return Notes updated after this UTC timestamp. |

### Request

```bash
curl "https://api.finnotes.com/v1/notes?limit=50" \
  -H "Authorization: Bearer $FINNOTES_API_KEY" \
  -H "Accept: application/json"
```

### Response

```json
{
  "data": [
    {
      "note_id": "note_01jz9z9x6m",
      "title": "Rates watchlist",
      "updated_at": "2026-06-19T07:10:00Z",
      "size_bytes": 18422
    }
  ],
  "pagination": {
    "next_cursor": null,
    "has_more": false
  },
  "daily_free_notes_list_requests_remaining": 9,
  "points_charged": 0.0,
  "remaining_points": 922.0,
  "request_id": "req_436e9f31"
}
```

After the daily free Own Notes list allowance is exhausted, the same endpoint returns `points_charged: 1.0`.

## 10.9 Notes Download

```http
GET /v1/notes/{note_id}
```

Downloads one user-owned Note payload.

Required permission: `Notes Download & Upload`.

Point charge: `3.50 pts`.

### Request

```bash
curl "https://api.finnotes.com/v1/notes/note_01jz9z9x6m" \
  -H "Authorization: Bearer $FINNOTES_API_KEY" \
  -H "Accept: application/json"
```

### Response

```json
{
  "data": {
    "note_id": "note_01jz9z9x6m",
    "title": "Rates watchlist",
    "content_type": "text/markdown",
    "content": "# Rates watchlist\n\nNote content...",
    "updated_at": "2026-06-19T07:10:00Z"
  },
  "points_charged": 3.5,
  "remaining_points": 906.5,
  "request_id": "req_57ee9e2d"
}
```

## 10.10 Notes Import / Upload

```http
POST /v1/notes/import
```

Creates a new Note in the authenticated account workspace.

Required permission: `Notes Download & Upload`.

Point charge: `3.50 pts`.

**Quota policy.** API-imported Notes are governed by **point allowance only**, not by the workspace UI's note-count quota (Free 2 / Pro 25 / Max 100 — those caps apply only to in-browser Note creation). An API client can store many more Notes than the UI cap, paying 3.50 pts each. Maximum note body size is 500,000 characters; `title` and `external_id` are also bounded.

### Request Body

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `title` | string | Yes | Note title. Max 200 chars. |
| `content_type` | string | Yes | Must be `text/markdown` in v1. Max 64 chars. |
| `content` | string | Yes | Markdown note body. Max 500,000 chars (~500 KB UTF-8). |
| `external_id` | string | Optional | Accepted for future-proofing. **Ignored in v1** — every call creates a fresh note. Max 200 chars. |

v1 limitations vs future versions:
- Only `text/markdown` is accepted. `application/json` is reserved for a later phase.
- `external_id` is parsed but does not trigger upsert in v1; the response `status` is always `created`. Clients that need upsert today should track the returned `note_id` themselves.

### Request

```bash
curl "https://api.finnotes.com/v1/notes/import" \
  -X POST \
  -H "Authorization: Bearer $FINNOTES_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Rates watchlist",
    "content_type": "text/markdown",
    "content": "# Rates watchlist\n\nNote content..."
  }'
```

### Response

```json
{
  "data": {
    "note_id": "note_42",
    "status": "created",
    "updated_at": "2026-06-19T12:00:00Z"
  },
  "points_charged": 3.5,
  "remaining_points": 903.0,
  "request_id": "req_4ee91d84"
}
```

## 10.11 Account Points

```http
GET /v1/account/points
```

Returns the authenticated account's current point state.

Required permission: `View Usage and remaining points`.

Point charge: `0.00 pts`.

### Request

```bash
curl "https://api.finnotes.com/v1/account/points" \
  -H "Authorization: Bearer $FINNOTES_API_KEY" \
  -H "Accept: application/json"
```

### Response

```json
{
  "data": {
    "plan": "pro",
    "monthly_allowance": 1350.0,
    "used_points": 428.0,
    "remaining_points": 922.0,
    "usage_rate": 0.317,
    "reset_at": "2026-06-30T00:00:00Z"
  },
  "points_charged": 0.0,
  "remaining_points": 922.0,
  "request_id": "req_71a7bf80"
}
```

## 10.12 Monthly Usage

```http
GET /v1/usage
```

Returns the authenticated user's current-month usage as daily point totals.

This endpoint is intentionally privacy-limited. It does not return visited endpoints, URLs, slugs, article titles, data-series names, request IDs, API-key names, categories, user agents, IP addresses, or any request-level history. Request-level history is available only through the opt-in Log endpoints after logging has been enabled.

Required permission:

- `View Usage and remaining points` for the calling key's own daily point totals.
- `All API usage state` for account-wide daily point totals across all keys.

Point charge: `0.00 pts`.

### Query Parameters

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `range` | string | `this_month` | Must be `this_month` in `v1`. Other ranges are not exposed by this endpoint. |
| `scope` | string | `current_key` | `current_key` returns the calling key's usage. `account` returns account-wide totals and requires `All API usage state`. |

The response covers every calendar date in the current month. Past and current dates return decimal point totals, including `0.0` when no points were consumed. Future dates return `points: null` so clients can draw the full month while leaving future usage blank.

### Request

```bash
curl "https://api.finnotes.com/v1/usage?range=this_month&scope=account" \
  -H "Authorization: Bearer $FINNOTES_API_KEY" \
  -H "Accept: application/json"
```

### Response

```json
{
  "data": {
    "range": "this_month",
    "scope": "account",
    "month": "2026-06",
    "timezone": "UTC",
    "summary": {
      "used_points": 428.0,
      "remaining_points": 922.0,
      "monthly_allowance": 1350.0,
      "usage_rate": 0.317
    },
    "daily_points": [
      {
        "date": "2026-06-01",
        "points": 8.0
      },
      {
        "date": "2026-06-19",
        "points": 39.5
      },
      {
        "date": "2026-06-20",
        "points": null
      }
    ]
  },
  "points_charged": 0.0,
  "remaining_points": 922.0,
  "request_id": "req_2b2df772"
}
```

## 10.13 Log Settings

```http
GET /v1/logs/settings
PATCH /v1/logs/settings
```

Request logs are opt-in. FinNotes does not collect user information for this log by default. When enabled, logs are visible only to the user who enabled them and to API keys with the required log permissions.

Required permissions:

- `View Log` for `GET /v1/logs/settings`.
- `Manage Log` for `PATCH /v1/logs/settings`.

Point charge: `0.00 pts`.

### Enable Logs

```bash
curl "https://api.finnotes.com/v1/logs/settings" \
  -X PATCH \
  -H "Authorization: Bearer $FINNOTES_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": true,
    "retention_days": 30
  }'
```

### Response

```json
{
  "data": {
    "enabled": true,
    "retention_days": 30,
    "updated_at": "2026-06-19T12:00:00Z"
  },
  "points_charged": 0.0,
  "remaining_points": 922.0,
  "request_id": "req_c14888df"
}
```

## 10.14 Request Logs

```http
GET /v1/logs
DELETE /v1/logs
```

Returns or deletes request logs after logging has been enabled.

Required permissions:

- `View Log` for `GET /v1/logs`.
- `Manage Log` for `DELETE /v1/logs`.

Point charge: `0.00 pts`.

> **Delete behavior:** `DELETE /v1/logs` hides previously stored request rows, but the delete action itself is recorded as a new visible row in subsequent `GET /v1/logs` responses. This is intentional — it gives the account-holder an audit trail that "logs were cleared at time X" so a deleted history can't be silently denied later.

### Query Parameters

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `range` | string | `last_24_hours` | `last_24_hours`, `last_7_days`, or `this_month`. |
| `status` | string | `all` | `all`, `2xx`, `4xx`, or `5xx`. |
| `api_key_id` | string | Optional | Filter to one API key. |
| `query` | string | Optional | Substring match against path and request_id. |
| `limit` | integer | `50` | Page size. Maximum `100`. |
| `cursor` | string | Optional | Cursor for next page. |

Query strings on the original request are not retained by the audit ledger and therefore the `query` field on each log entry is always `{}` in v1. Clients should rely on `path` for endpoint grouping.

### Request

```bash
curl "https://api.finnotes.com/v1/logs?range=last_24_hours&status=all" \
  -H "Authorization: Bearer $FINNOTES_API_KEY" \
  -H "Accept: application/json"
```

### Response

```json
{
  "data": [
    {
      "time": "2026-06-19T10:04:21Z",
      "request_id": "req_9f8a21c7",
      "api_key_name": "Production server",
      "method": "GET",
      "path": "/v1/news",
      "query": {},
      "status": 200,
      "points_charged": 1.0,
      "latency_ms": 184
    }
  ],
  "pagination": {
    "next_cursor": null,
    "has_more": false
  },
  "points_charged": 0.0,
  "remaining_points": 922.0,
  "request_id": "req_aac59d4e"
}
```

## 10.15 Newsletter Preferences

> **Status: Phase 2 — not yet mounted in the API router.** Reading or writing this endpoint currently returns `404`. The contract is final; mounting is tracked separately. Do not integrate against this endpoint until announced. Newsletter preferences can still be managed via the developer console at `https://platform.finnotes.com/newsletter`.

```http
GET /v1/newsletter/preferences
PATCH /v1/newsletter/preferences
```

Manages free report subscriptions.

Required permission: `Manage Newsletter preferences`.

Point charge: `0.00 pts` for reading or saving preferences.

Free subscriptions:

| Subscription | Charge |
| --- | ---: |
| Daily Report | 0.00 pts |
| Weekly Report | 0.00 pts |
| Weekly Calendar | 0.00 pts |

### Read All Newsletter Subscription Status

`GET /v1/newsletter/preferences` returns the complete free Newsletter subscription state in one response. It does not query a single subscription.

```bash
curl "https://api.finnotes.com/v1/newsletter/preferences" \
  -H "Authorization: Bearer $FINNOTES_API_KEY" \
  -H "Accept: application/json"
```

### Read Response

```json
{
  "data": {
    "subscriptions": {
      "daily_report": true,
      "weekly_report": false,
      "weekly_calendar": true
    },
    "updated_at": "2026-06-19T12:00:00Z"
  },
  "points_charged": 0.0,
  "remaining_points": 922.0,
  "request_id": "req_newsletter_read_6c0d2c"
}
```

### Update One Or More Newsletter Subscriptions

`PATCH /v1/newsletter/preferences` accepts one or more subscription keys. Only submitted keys are changed; omitted subscriptions keep their existing state.

Valid subscription keys:

| Key | Subscription |
| --- | --- |
| `daily_report` | Daily Report |
| `weekly_report` | Weekly Report |
| `weekly_calendar` | Weekly Calendar |

### Update Request

```bash
curl "https://api.finnotes.com/v1/newsletter/preferences" \
  -X PATCH \
  -H "Authorization: Bearer $FINNOTES_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "subscriptions": {
      "weekly_report": true,
      "weekly_calendar": false
    }
  }'
```

### Update Response

```json
{
  "data": {
    "subscriptions": {
      "daily_report": true,
      "weekly_report": true,
      "weekly_calendar": false
    },
    "updated_at": "2026-06-19T12:00:00Z"
  },
  "points_charged": 0.0,
  "remaining_points": 922.0,
  "request_id": "req_a44e0500"
}
```

> ⏸️ **Sections 10.16, 10.17, and 11 are Phase 2 / Agent Skill scope and are not part of v1 launch.** The preference-save endpoints may be implemented earlier to let users configure intent, but the delivery side (webhook URL registration, HMAC signature spec, server-initiated retry, dead-letter handling) must be finalized before any API Push or Email push is actually delivered. Until then, setting `channels.api_push.enabled=true` returns `422 validation_error` with `code: "feature_unavailable"`.

## 10.16 Trace Data Release Push Preferences

```http
GET /v1/push/trace-data-release/preferences
PATCH /v1/push/trace-data-release/preferences
```

Configures immediate alerts for selected data releases and policy decisions.

Required permission: `Manage Newsletter preferences`.

Preference-save charge: `0.00 pts`.

Delivery charge: charged per triggered alert.

### Supported Release IDs

Initial supported release IDs:

| ID | Label |
| --- | --- |
| `us_cpi` | US CPI |
| `nonfarm_payrolls` | Nonfarm Payrolls |
| `fomc_rate_decision` | FOMC Rate Decision |
| `fed_chair_press_conference` | Fed Chair Press Conference |
| `ecb_rate_decision` | ECB Rate Decision |
| `eia_petroleum_status` | EIA Petroleum Status |
| `initial_jobless_claims` | Initial Jobless Claims |
| `us_gdp_advance` | US GDP Advance |

### Request Body

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `enabled` | boolean | Yes | Turn this subscription on or off. |
| `release_ids` | array | Yes when enabled | Selected release and decision IDs. |
| `channels.email.enabled` | boolean | Yes | Enable email delivery. |
| `channels.email.use_default_email` | boolean | Required when email enabled | Use the account default email. |
| `channels.email.email` | string | Conditional | Required when email is enabled and default email is not used. |
| `channels.api_push.enabled` | boolean | Yes | Enable AI Agent API Push when available. |
| `channels.api_push.api_key_id` | string | Conditional | Active API key name or ID used by the mounted Agent Skill. |

API Push for Trace Data Release is reserved until the Agent Skill channel is enabled in production. If unavailable, setting `channels.api_push.enabled=true` returns `422 validation_error`.

### Request

```bash
curl "https://api.finnotes.com/v1/push/trace-data-release/preferences" \
  -X PATCH \
  -H "Authorization: Bearer $FINNOTES_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": true,
    "release_ids": ["us_cpi", "nonfarm_payrolls", "fomc_rate_decision"],
    "channels": {
      "email": {
        "enabled": true,
        "use_default_email": true
      },
      "api_push": {
        "enabled": false,
        "api_key_id": null
      }
    }
  }'
```

### Response

```json
{
  "data": {
    "enabled": true,
    "release_ids": ["us_cpi", "nonfarm_payrolls", "fomc_rate_decision"],
    "channels": {
      "email": {
        "enabled": true,
        "use_default_email": true,
        "email": null
      },
      "api_push": {
        "enabled": false,
        "api_key_id": null
      }
    },
    "updated_at": "2026-06-19T12:00:00Z"
  },
  "points_charged": 0.0,
  "remaining_points": 922.0,
  "request_id": "req_72f6cc3c"
}
```

## 10.17 Real-Time News Push Preferences

```http
GET /v1/push/news/preferences
PATCH /v1/push/news/preferences
```

Configures article push rules for newly published FinNotes articles.

Required permission: `Manage Newsletter preferences`.

Preference-save charge: `0.00 pts`.

Delivery charge: same as the active API retrieval price for each delivered article.

### Request Body

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `enabled` | boolean | Yes | Turn this subscription on or off. |
| `types` | array | Yes when enabled | Any of `market-news`, `chart-news`, `column-article`. |
| `importance_score_min` | number | Yes | Minimum importance score, `0.0` to `10.0`. |
| `anomaly_score_min` | number | Yes | Minimum anomaly score, `0.0` to `10.0`. |
| `channels.email.enabled` | boolean | Yes | Enable email delivery. |
| `channels.email.use_default_email` | boolean | Required when email enabled | Use the account default email. |
| `channels.email.email` | string | Conditional | Required when email is enabled and default email is not used. |
| `channels.email.acknowledge_high_frequency_email` | boolean | Conditional | Must be `true` when enabling email for real-time news push. |
| `channels.api_push.enabled` | boolean | Yes | Send matching articles to a mounted AI Agent. |
| `channels.api_push.api_key_id` | string | Conditional | Active API key used by the mounted Agent Skill. |

Both `importance_score_min` and `anomaly_score_min` are applied. A delivered article must meet or exceed both floors.

### Request

```bash
curl "https://api.finnotes.com/v1/push/news/preferences" \
  -X PATCH \
  -H "Authorization: Bearer $FINNOTES_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": true,
    "types": ["market-news", "chart-news"],
    "importance_score_min": 7.0,
    "anomaly_score_min": 7.0,
    "channels": {
      "email": {
        "enabled": true,
        "use_default_email": false,
        "email": "agent-managed-inbox@example.com",
        "acknowledge_high_frequency_email": true
      },
      "api_push": {
        "enabled": true,
        "api_key_id": "key_prod_001"
      }
    }
  }'
```

### Response

```json
{
  "data": {
    "enabled": true,
    "types": ["market-news", "chart-news"],
    "importance_score_min": 7.0,
    "anomaly_score_min": 7.0,
    "channels": {
      "email": {
        "enabled": true,
        "use_default_email": false,
        "email": "agent-managed-inbox@example.com"
      },
      "api_push": {
        "enabled": true,
        "api_key_id": "key_prod_001"
      }
    },
    "updated_at": "2026-06-19T12:00:00Z"
  },
  "points_charged": 0.0,
  "remaining_points": 922.0,
  "request_id": "req_0d2ac970"
}
```

## 10.18 Notifications Preferences

> **Status: Phase 2 — not yet mounted in the API router.** Reading or writing this endpoint currently returns `404`. Notifications can still be configured via the developer console.

```http
GET /v1/notifications/preferences
PATCH /v1/notifications/preferences
```

Manages account email notification preferences for API platform events.

Required permission: `Notification management`.

Point charge: `0.00 pts`.

### Request

```bash
curl "https://api.finnotes.com/v1/notifications/preferences" \
  -X PATCH \
  -H "Authorization: Bearer $FINNOTES_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "low_points_warning": true,
    "monthly_reset_notice": true,
    "key_status_change": true
  }'
```

### Response

```json
{
  "data": {
    "low_points_warning": true,
    "monthly_reset_notice": true,
    "key_status_change": true,
    "updated_at": "2026-06-19T12:00:00Z"
  },
  "points_charged": 0.0,
  "remaining_points": 922.0,
  "request_id": "req_3d2f3ad7"
}
```

## 11. AI Agent Push Delivery Payload

When API Push is enabled, FinNotes sends a signed JSON payload to the mounted Agent Skill channel.

### Common Event Envelope

```json
{
  "event_id": "evt_01jza0v9be",
  "event_type": "news.published",
  "created_at": "2026-06-19T12:00:00Z",
  "account_id": "acct_123",
  "api_key_id": "key_prod_001",
  "points_charged": 1.25,
  "remaining_points": 920.75,
  "data": {}
}
```

### News Push Event

```json
{
  "event_id": "evt_01jza0v9be",
  "event_type": "news.published",
  "created_at": "2026-06-19T12:00:00Z",
  "points_charged": 1.25,
  "remaining_points": 920.75,
  "data": {
    "id": "cn_01jz9xd7nm",
    "type": "chart-news",
    "title": "US yields reprice the policy path after payrolls",
    "url": "https://finnotes.com/charts/us-yields-reprice-policy-path",
    "dek": "A chart-backed read on the front-end rate reaction.",
    "importance_score": 8.1,
    "anomaly_score": 7.2
  }
}
```

### Trace Data Release Event

```json
{
  "event_id": "evt_01jza10h4n",
  "event_type": "trace.release_published",
  "created_at": "2026-06-19T12:30:00Z",
  "points_charged": 2.5,
  "remaining_points": 918.25,
  "data": {
    "release_id": "us_cpi",
    "release_name": "US CPI",
    "published_at": "2026-06-19T12:30:00Z",
    "headline": "US CPI prints below consensus",
    "url": "https://finnotes.com/market-news/us-cpi-below-consensus"
  }
}
```

## 12. Insufficient Points Behavior

If the account does not have enough points, the API returns `402 insufficient_points`.

No partial response is returned and no points are deducted.

```json
{
  "error": {
    "code": "insufficient_points",
    "message": "The account does not have enough points for this request.",
    "request_id": "req_730f988d",
    "details": {
      "required_points": 5.5,
      "remaining_points": 2.0
    }
  }
}
```

Recommended client behavior:

1. Stop retrying the same billable request.
2. Call `GET /v1/account/points` if the API key has permission.
3. Ask the user to upgrade, wait for monthly reset, or reduce the requested product scope.

## 13. Idempotency For Write Requests

Write endpoints should include `Idempotency-Key`.

Supported write endpoints include:

| Endpoint | Should use idempotency |
| --- | --- |
| `POST /v1/notes/import` | Yes |
| `PATCH /v1/newsletter/preferences` | Recommended |
| `PATCH /v1/push/trace-data-release/preferences` | Recommended |
| `PATCH /v1/push/news/preferences` | Recommended |
| `PATCH /v1/logs/settings` | Recommended |
| `DELETE /v1/logs` | Recommended |

If the same idempotency key is reused with the same request body, FinNotes returns the original result. If the same key is reused with a different body, FinNotes returns `409 idempotency_conflict`.

Idempotency keys are retained for **24 hours** from the first successful processing of the key. After 24 hours the key is forgotten and the same key + body combination will execute as a fresh request. Clients that need longer replay safety should rotate idempotency keys per logical operation.

## 14. Retry Guidance

Retry only transient errors:

| Status | Retry? | Guidance |
| ---: | --- | --- |
| `400`, `401`, `402`, `403`, `404`, `422` | No | Fix the request, key, permission, or account state. |
| `409` | No | Use a new idempotency key or resend the original body. |
| `429` | Yes | Wait for `Retry-After`. Rate-limit responses do not deduct points. |
| `500`, `503` | Yes | Retry with exponential backoff and jitter. |

Recommended backoff:

```text
1s, 2s, 4s, 8s, then stop or escalate
```

## 15. Python Example

```python
import os
import requests

api_key = os.environ["FINNOTES_API_KEY"]

response = requests.get(
    "https://api.finnotes.com/v1/news",
    params={"range": "today", "type": "all"},
    headers={
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    },
    timeout=20,
)

if response.status_code == 402:
    raise RuntimeError("Insufficient FinNotes points")

response.raise_for_status()

payload = response.json()
print(payload["points_charged"], payload["remaining_points"])
print(payload["data"])
```

## 16. JavaScript Example

```js
const response = await fetch("https://api.finnotes.com/v1/news?range=today&type=all", {
  headers: {
    Authorization: `Bearer ${process.env.FINNOTES_API_KEY}`,
    Accept: "application/json",
  },
});

const payload = await response.json();

if (!response.ok) {
  throw new Error(payload.error?.message ?? "FinNotes API request failed");
}

console.log(payload.points_charged, payload.remaining_points);
console.log(payload.data);
```

## 17. Security Requirements

Production integrations must follow these rules:

1. Store API keys in a secret manager or server-side environment variable.
2. Never expose API keys in frontend browser code.
3. Use the minimum required key permissions.
4. Rotate keys after personnel changes, suspected leakage, or environment migration.
5. Use separate keys for production servers, automation workers, and AI Agent integrations.
6. Enable request logs only when needed and delete logs when they are no longer necessary.
7. Use dedicated agent-managed email inboxes for high-frequency real-time news push.

## 18. Versioning

The current version is `v1`.

Backward-compatible changes may be added to `v1`, including optional fields, new enum values, and new endpoints. Breaking changes require a new API version.

Clients should ignore unknown response fields.

## 19. Pricing Change Policy

Point pricing may change by product category. When point pricing changes, FinNotes should publish the effective date and preserve enough notice for production users to update usage budgets and automation rules.

Clients should not hard-code point prices as permanent constants. Use response headers and `GET /v1/account/points` for reconciliation.
