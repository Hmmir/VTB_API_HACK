# Consent & Payments Data Model

## 1. Diagram (textual)
```
users ─┬─< bank_connections ─┬─< accounts ─┬─< transactions
       │                     │
       │                     └─< interbank_transfers >─┬─ partner_banks
       │                                              └─ consent_grants >─ consents
       │
       └─< consent_requests ─┬─< consent_events (audit)
                             └─ consent_grants ─┬─< consent_scope_items
                                                └─ consent_revocations

payments ─┬─ payment_events
          └─ payment_documents (generated artefacts)

security_events log everything (streamed from backend services)
```

## 2. Table Definitions

### `consent_requests`
- `id` UUID PK
- `requesting_bank_id` FK → `partner_banks`
- `user_id` FK → `users`
- `requested_scopes` JSONB (Open Banking style)
- `expires_at`, `status` enum (`requested`, `approved`, `rejected`, `expired`)
- `justification` text (displayed in UI)

### `consents`
- `id` UUID PK (Consent-ID)
- `consent_request_id` FK → `consent_requests`
- `signed_at`, `effective_until`
- `signature_hash` (ГОСТ, stored as base64)
- `status` enum (`active`, `revoked`, `expired`)

### `consent_events`
- `id` bigserial PK
- `consent_id`
- `event_type` (`requested`, `signed`, `revoked`, `usage`, `expiry`)
- `payload` JSONB
- `created_at`
- `actor` (user/banker/system)

### `partner_banks`
- `id` UUID PK
- `name`
- `bic`
- `jwks_uri`
- `status`

### `interbank_transfers`
- `id` UUID PK
- `from_bank_connection_id`, `to_partner_bank_id`
- `amount`, `currency`
- `status` (`initiated`, `pending_settlement`, `settled`, `failed`)
- `consent_id` FK → `consents`
- `metadata` JSONB (FX rate, fees)
- `initiated_at`, `settled_at`

### `payments`
- `id` UUID PK
- `user_id`
- `account_id`
- `counterparty`
- `amount`, `currency`
- `payment_type` (internal, interbank, partner)
- `status`
- `consent_id`

### `security_events`
- `id` bigserial
- `entity_type`, `entity_id`
- `event`
- `severity`
- `details` JSONB
- `recorded_at`

## 3. Relationships & Cardinality Highlights
- 1 consent_request → 0..1 consent → n consent_events.
- 1 consent → many interbank_transfers & payments (enforced by FK).
- `security_events` is polymorphic referencing any entity through `(entity_type, entity_id)`.

## 4. Migration Strategy
- Create new schema migrations in `backend/app/migrations/versions/`.
- Backfill: existing transfers (internal) will get null consent_id, but future ones must reference consents (nullable false for interbank).
- Add indexes for `consent_id`, `status`, `created_at` to support audit queries.

## 5. Sample Consent Scope Payload
```json
{
  "resource": "accounts",
  "permissions": [
    "balances.read",
    "transactions.read",
    "payments.initiate"
  ],
  "constraints": {
    "accounts": ["*"],
    "valid_until": "2025-12-31T23:59:59Z",
    "usage_limit": 120
  }
}
```


