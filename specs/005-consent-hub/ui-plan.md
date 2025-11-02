# UI Expansion Plan — Consent, Banker & Compliance

## 1. Consent Center (Client)
- **Navigation**: new primary tab `Согласия` between `Аналитика` и `Рекомендации`.
- **Layout**:
  - Hero card: «Ваш цифровой нотариус» with stats (`активные`, `истекают`, `запросы`).
  - Tabs: `Запросы`, `Активные`, `История`.
  - Request card: shows requesting bank, scopes, expiry, CTA buttons `Одобрить` / `Отклонить` with consent modal.
  - Timeline modal: micro-animations, ГОСТ signature details, share/export button (PDF).
- **Styling cues**: reuse aurora backgrounds, add holographic passport overlay when viewing signature (subtle animation).

## 2. Accounts → Interbank View
- Extend existing page with `Маршруты` section: sankey chart showing bank-to-bank flows (use gradient lines, accent glows).
- Transfer modal gets new tab `Межбанковский` requiring consent selection and counterparty details.
- Security journal upgraded with icons per event type (consent, transfer, admin).

## 3. Banker Studio
- **Route**: `/banker` (protected by role, separate login or role switch in header).
- **Pages**:
  1. Dashboard — KPI tiles (capital, net inflow, consent approvals), compliance heatmap.
  2. Products — table with inline editing of rates, create new offers (cards use bevel shadow varients).
  3. Consents — list with filters by status, ability to revoke/extend, timeline viewer.
  4. Payments — queue of pending interbank transfers with approve/flag actions.
- **Components**: reuse `Card` / `Button`, introduce `Badge` variations (ink/sand/glow) for statuses.

## 4. Admin Studio (Compliance Ops)
- **Route**: `/admin`.
- **Sections**:
  - ГОСТ монитор: component grid showing OpenSSL, CryptoPRO, JWKS validity; CTA to “Прогнать тест” → opens modal with live log streaming.
  - Security analytics: charts for event severity over time, quick filters (`Consent`, `Payment`, `Auth`).
  - Export center: buttons to download PDF/CSV packages for jury.
- **Visual**: dusk gradient background, animated wireframe globe to convey network trust.

## 5. Shared Enhancements
- Header adds role-switcher dropdown (Client / Banker / Admin), with relevant avatar states.
- Toast UX: new status icons for consent + interbank success.
- Dark theme ensures neon accents remain legible (audit sections in `nocturne` theme get cyan highlights instead of green).

## 6. Responsive & Mobile
- Consent cards stack with swipe gestures to approve/decline (use `framer-motion` like interactions but respect reduced motion settings).
- Banker/Admin dashboards collapse into accordions with sticky metrics.

## 7. Asset Requirements
- Illustrations: create abstract line art for consent handshake, compliance shield.
- Iconography: new set for `scope`, `signature`, `bank`, `transfer`, `compliance` (outline style consistent with heroicons).


