# DNR → API Contract JSON — Extraction Prompt

You are extracting a **skeleton API contract** from a "Detailný návrh riešenia"
(DNR). This runs **only in backend mode** and produces the `contracts[]` block
that is merged into the Teamwork plan JSON. Python then renders it
deterministically into `openapi.yaml` + `data-model.md`, so you output
**structured JSON, never raw YAML**.

## Golden rule

**Never invent an endpoint, field or type that the DNR does not support.**
Where the DNR is silent, emit the structure but mark it: set
`"status": "draft"` on the endpoint and put `[DOPLNIŤ]` in its `description`.
The same convention as `dnr-business`. A skeleton with honest `[DOPLNIŤ]`
placeholders is correct; a confident hallucination is not.

## Inputs you are given

- The DNR plain text.
- `error_http_convention` — `"http_status"` or `"ok"` (from the user). You do
  **not** encode this in the JSON; the renderer applies it. When it is
  `"http_status"` you may set per-endpoint `error_statuses` (default `[401, 422]`
  is applied if you omit it).
- `contract_desc_language` — `"sk"` / `"en"` / `"cs"`. Write endpoint
  `description` (and schema/field descriptions) in this language. Write
  `summary` in the DNR language. `operation_id` is **always English**.
- `contract_granularity` — `"per_project"` (one contract) or `"per_phase"`
  (one contract per module/phase). Only asked when the DNR modules are
  ambiguous; otherwise derive one contract per clearly-separable feature.

## Output

A JSON object `{ "contracts": [ … ] }`. Each contract:

```json
{
  "feature_slug": "objednavky-editel-sync",
  "title": "Objednávky — synchronizácia s Editelom",
  "version": "0.1.0",
  "linked_sections": ["4.1"],
  "openapi": {
    "servers": [{"url": "/api/v1", "description": "…"}],
    "endpoints": [ … ],
    "schemas": [ … ]
  },
  "data_model": { "entities": [ … ] }
}
```

### `feature_slug`

- **kebab-case**, derived from the **module / feature heading** in the DNR
  (e.g. "Rozšírenie č. 1 — Synchronizácia objednávok" → `objednavky-editel-sync`),
  **not** from the project name.
- ASCII, lowercase, words joined by `-`. Strip diacritics
  (`Objednávky` → `objednavky`).
- Must match `^[a-z0-9]+(-[a-z0-9]+)*$` — the validator enforces this.

### `version`

Always start at `"0.1.0"` for a new contract.

### `linked_sections`

The DNR `section_ref`(s) whose tasklists this contract serves (e.g. `["4.1"]`).
Used to place the "Definovať API kontrakt" task into the earliest such section.

### `openapi.endpoints[]`

```json
{
  "method": "post",
  "path": "/orders/{id}/sync",
  "operation_id": "syncOrder",
  "summary": "Synchronizácia objednávky do Editelu",
  "description": "Odošle objednávku do Editelu a vráti stav párovania.",
  "tags": ["Orders"],
  "status": "draft",
  "request_schema": "SyncOrderRequest",
  "success_data_schema": "OrderSyncResult",
  "error_statuses": [401, 422]
}
```

- `method` — lowercase HTTP verb.
- `path` — REST path under `/api/v1` (do not repeat the server prefix). Use
  `{id}`-style templates.
- `operation_id` — **English**, camelCase, unique within the contract. Goes
  into generated TypeScript types later, so it must read well in English.
- `summary` — short, DNR language.
- `description` — `contract_desc_language`. If the DNR does not pin the
  behaviour down, set `status: "draft"` and put `[DOPLNIŤ]` (optionally with a
  hint: `"[DOPLNIŤ] presné pravidlá párovania"`).
- `status` — `"stable"` only when the DNR describes the endpoint
  unambiguously; otherwise `"draft"`.
- `request_schema` / `success_data_schema` — names of entries in
  `openapi.schemas` (the request body and the `data` payload of the success
  envelope). Omit when there is none (e.g. a GET with no body).

Do **not** hand-write `responses` or the WAME envelope — the renderer wraps
every success in `WameSuccess` (with `data` concretised via `allOf`) and every
error in `WameError`, referenced from `../_shared/wame-envelope.yaml`.

### `openapi.schemas[]`

Component schemas for request bodies and success `data` payloads:

```json
{
  "name": "OrderSyncResult",
  "description": "Výsledok párovania objednávky.",
  "fields": [
    {"name": "id", "type": "integer", "nullable": false, "description": "ID objednávky"},
    {"name": "editel_ref", "type": "string", "nullable": true, "description": "Referencia z Editelu"}
  ]
}
```

- `type` — OpenAPI scalar (`string`, `integer`, `number`, `boolean`, `array`,
  `object`). `nullable: true` renders as `type: [<type>, "null"]`.
- `required` per field defaults to `not nullable`; set it explicitly to
  override.

### `data_model.entities[]`

The persistence view (basis for migrations + ERD). **No PHP.**

```json
{
  "name": "Order",
  "description": "Objednávka klienta.",
  "fields": [
    {"name": "id", "type": "bigint", "nullable": false, "description": "PK"},
    {"name": "editel_ref", "type": "string", "nullable": true, "default": null, "description": "Referencia z Editelu"}
  ],
  "relations": [{"kind": "belongsTo", "target": "Customer", "description": "vlastník"}],
  "indexes": [{"columns": ["editel_ref"], "unique": true, "description": "rýchle vyhľadávanie"}],
  "notes": ["Migrácia potrebuje backfill existujúcich objednávok."]
}
```

Use DB-level types (`bigint`, `varchar`, `decimal(10,2)`, `timestamp`, …) here —
these describe the schema, not the API surface. Where a field is implied but its
exact type is unknown, use `[DOPLNIŤ]` in the type/description.

## Final check

- [ ] JSON parses.
- [ ] Every `feature_slug` is kebab-case ASCII.
- [ ] Every `operation_id` is English and unique within its contract.
- [ ] Every endpoint that is not fully specified has `status: "draft"` and
      `[DOPLNIŤ]` in its `description`.
- [ ] No invented endpoints, fields or types — silence in the DNR → `[DOPLNIŤ]`.
- [ ] `summary` in DNR language, `description` in `contract_desc_language`.
