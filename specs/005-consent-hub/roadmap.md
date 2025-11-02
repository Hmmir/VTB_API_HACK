# Implementation Roadmap

## Milestone A — Consent Core (Backend-first)
1. **Migrations**: `consent_requests`, `consents`, `consent_events`, `partner_banks`.
2. **Service Layer**: `app/services/consent_service.py` with validation, signature verification, webhook dispatch.
3. **API**: `app/api/consents.py` exposing request/sign/revoke/list.
4. **Security Event Hook**: log every state change.
5. **Tests**: unit + integration (simulate partner request, client approval, revoke).

## Milestone B — Interbank Rail & Payments
1. Extend `accounts.transfer_funds` to route to `payment_service`.
2. Add `interbank_transfers` model, queue processor.
3. Webhook endpoint for partner settlement.
4. Update analytics service to surface interbank stats.

## Milestone C — Frontend Client Experience
1. Build Consent Center pages & modals.
2. Update Accounts page with new transfer modes + sankey component.
3. Enhance security journal with consent/payout events + export.

## Milestone D — Banker/Admin Studios
1. Role-aware routing (extend `AuthContext` with roles).
2. Banker dashboards, product configurator, consent table.
3. Admin compliance panel, JWKS tester, export workflows.

## Milestone E — Crypto & Docs
1. Generate RSA keys, publish JWKS route.
2. Update auth to sign partner tokens with RS256.
3. Swagger re-organization, quickstart & demo script updates.

## Deliverable Definition of Done
- All new endpoints documented & covered with tests.
- UI flows accessible, keyboard-friendly, reduced-motion compliant.
- Demo script: consent request → approval → interbank transfer → admin audit export.


