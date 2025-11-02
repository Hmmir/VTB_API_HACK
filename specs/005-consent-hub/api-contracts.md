# API Contracts — Consent & Interbank Suite

## 1. Consent Lifecycle

### POST `/api/v1/consents/request`
- **Auth**: partner bank JWT (RS256) + mutual TLS if ГОСТ.
- **Body**
```json
{
  "user_login": "team075-4",
  "scopes": [{
    "resource": "accounts",
    "permissions": ["balances.read", "transactions.read"]
  }],
  "callback_url": "https://partner.bank/consent/callback",
  "justification": "Аналитика расходов для персональных предложений"
}
```
- **Response** `202 Accepted`
```json
{
  "request_id": "c9b6...",
  "status": "requested",
  "expires_at": "2025-11-02T23:59:59Z"
}
```

### POST `/api/v1/consents/{request_id}/sign`
- **Auth**: FinanceHub client token (HS256) + ГОСТ signing.
- **Body**
```json
{
  "decision": "approve",
  "signature": "base64-gost-signature",
  "valid_until": "2025-12-31T21:00:00Z"
}
```
- **Response**
```json
{
  "consent_id": "CONSENT-7f83",
  "status": "active"
}
```

### DELETE `/api/v1/consents/{consent_id}`
- Revokes consent, triggers webhook.
- Response 204.

### GET `/api/v1/consents` (client)
- Query params: `type=outbound|inbound`, `status`, `scope`.
- Returns array with timeline events embedded.

## 2. Interbank Transfers

### POST `/api/v1/transfers/interbank`
- **Headers**: `X-Consent-ID`, `X-Requesting-Bank`
- **Body**
```json
{
  "from_account_id": 41,
  "to_bank": "alpha-bank",
  "counterparty_account": "40817810099910004312",
  "amount": 150000.50,
  "currency": "RUB",
  "purpose": "Перевод на накопительный вклад"
}
```
- **Response** `202 Accepted`
```json
{
  "transfer_id": "TRF-20251102-0001",
  "status": "initiated",
  "eta": "2025-11-02T14:05:00Z"
}
```

### POST `/api/v1/transfers/interbank/{transfer_id}/webhook`
- Used by partner banks to update status (signed payload).
- Body includes `status`, `settled_at`, `partner_reference`.

## 3. Payments API
- `POST /api/v1/payments` (initiate internal or partner payment)
- `GET /api/v1/payments/{id}` (status + attached documents)
- Attachments served via pre-signed URLs.

## 4. Security/Event Stream
- `POST /api/v1/security/events` (internal service-to-service) for capturing actions.
- Fields: `event`, `actor`, `context`, `severity`, `hash` (for tamper detection).

## 5. JWKS & Crypto
- `GET /.well-known/jwks.json` returns RS256 public keys.
- `GET /api/v1/crypto/gost-report` generates the compliance report for admin UI.

## 6. Swagger Grouping
- Use tags: `Consents`, `Payments`, `Interbank`, `Security`, `Crypto`, `Admin`.
- Add examples mirroring competitor capabilities + our premium narratives.


