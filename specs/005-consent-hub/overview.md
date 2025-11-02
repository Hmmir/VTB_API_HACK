# Consent & Interbank Orchestrator — Solution Blueprint

## 1. Purpose
- Elevate FinanceHub from personal-finance aggregator to a regulated-ready open banking platform.
- Deliver feature parity and differentiation vs. competitor [bank-in-a-box](https://github.com/GalkinTech/bank-in-a-box.git) by adding consent governance, interbank rails, and banker tooling.
- Maintain the established `frontend_aesthetics` language while extending backend architecture for audit-grade flows.

## 2. Scope Snapshot
- Consent ledger covering request → signature → lifecycle management.
- Interbank and payment services wired to consent enforcement & audit.
- Banker/Admin studios (web apps) that operate in the same repository (share auth + design tokens).
- JWKS/crypto hardening with RS256 + ГОСТ reporting panel.

## 3. Target Personas & Journeys
| Persona | Key Scenario | Journey | Monetization Lever |
| --- | --- | --- | --- |
| Everyday client | Connect external bank, approve consent, monitor spend | Login → Consent Center → Approve → Accounts/Audit | Premium automation, paid advisory |
| Partner bank | Request consent for data/payout | API `/consents/request` → callback | B2B fees per consent / per payment |
| Banker ops | Configure products, watch capital, revoke risk consents | Banker Studio dashboards | SaaS / management fee |
| Compliance officer | Validate ГОСТ readiness, export reports | Admin Studio → Compliance Ops | Enterprise upsell |

## 4. Competitive Differentiators
- **Holistic UX**: competitor splits UI (client/banker) but lacks storytelling. Our design merges artistry with regulator-grade flows.
- **Embedded Monetization**: consent + payment events feed premium insights (cashflow autopilot, partner success metrics).
- **Audit-first**: every operation (consent, interbank transfer, admin action) streams to a security log with export-ready artefacts.

## 5. Deliverables per Track
| Track | Deliverables |
| --- | --- |
| Backend | DB migrations, `consent_service.py`, `payment_service.py`, RSA/JWKS, webhook scaffolds, test suites |
| Frontend | Consent Center, Security Journal v2, Interbank map, Banker/Admin Studios, compliance dashboards |
| DevOps | JWKS endpoints, secrets management, demo scripts, infra configs |
| Docs | Swagger split, quickstart, architecture diagrams, jury demo scenarios |

## 6. High-level Timeline (can compress for hackathon)
1. **Architecture Sprint (Day 0-0.5)** – data models, contract drafts, UI maps.
2. **Consent Core (Day 0.5-1.5)** – migrations, service, API + client flows.
3. **Interbank Rails (Day 1.5-2.5)** – payment endpoints, settlement logic, analytics surfaces.
4. **Banker/Admin Studios (Day 2.5-3.5)** – UI, role-based auth, product configurator, compliance ops.
5. **Polish + Demo (Day 3.5+)** – docs, scripts, stress test, video capture.


