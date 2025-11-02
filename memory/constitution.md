# Project Constitution: FinanceHub

**Version**: 1.0.0  
**Ratification Date**: 2025-10-28  
**Last Amended**: 2025-10-28

---

## Project Overview

**FinanceHub** is a multi-bank financial aggregation platform for the VTB API Hackathon 2025. It solves the problem of financial data fragmentation by providing a unified interface for managing accounts across multiple banks (VBank, ABank, SBank).

---

## Core Principles

### 1. Simplicity First

**Rule**: Focus on core features that solve the main problem.

**Rationale**: In a hackathon environment with limited time (7 days), we must prioritize working functionality over feature completeness. Every feature must directly address the core user problem: financial data fragmentation.

**Application**:
- Choose proven, well-documented technologies
- Avoid premature optimization
- Implement only features listed in MVP scope
- Defer "nice-to-have" features to post-hackathon

### 2. User Value

**Rule**: Every feature MUST provide measurable value to end users.

**Rationale**: The hackathon evaluation criteria emphasize user value and real-world applicability. Features that don't solve real user problems dilute the product vision and waste development time.

**Application**:
- Each feature must map to a specific user pain point
- Success metrics must be defined before implementation
- User scenarios must be validated against real use cases
- Features must be demonstrable in the live demo

### 3. Scalability

**Rule**: Architecture MUST support adding new banks easily.

**Rationale**: The judges will evaluate scalability and extensibility. Our multi-bank aggregation approach is only valuable if it can scale beyond the initial 3 banks.

**Application**:
- Plugin architecture for bank integrations
- Standardized interfaces for bank API adapters
- Configuration-driven bank setup (no hardcoded bank logic)
- Clear separation of concerns between core logic and bank-specific code

### 4. Security

**Rule**: Follow Open Banking security standards strictly.

**Rationale**: Financial data handling requires the highest security standards. Any security vulnerability would be a critical failure in evaluation and real-world deployment.

**Application**:
- OAuth 2.0 for all bank integrations
- JWT tokens with proper expiration and refresh
- Encrypted storage for sensitive tokens
- No secrets in code (environment variables only)
- Input validation and sanitization
- Rate limiting and DDoS protection
- HTTPS only in production

### 5. Performance

**Rule**: Real-time data updates, fast response times.

**Rationale**: User experience depends on responsive interfaces and timely data synchronization. Financial data must feel current and reliable.

**Application**:
- Redis caching for frequently accessed data
- Lazy loading for UI components
- Optimized database queries (indexes, select only needed fields)
- Asynchronous operations for external API calls
- Target: < 200ms API response time, < 1s page load

---

## Technical Constraints

### Backend
- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Reason**: Modern async support, automatic API documentation, type safety with Pydantic

### Database
- **Primary Store**: PostgreSQL 15
- **Reason**: Robust relational database with excellent JSON support, ACID compliance for financial data

### Cache & Sessions
- **Cache Layer**: Redis 7
- **Reason**: High-performance caching, session storage, real-time pub/sub for notifications

### Frontend
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **Styling**: TailwindCSS
- **Charts**: Recharts
- **Reason**: Modern stack with excellent developer experience, fast builds, type safety

### API Integration
- **Standard**: Open Banking Russia v2.1
- **Reason**: Official hackathon requirement, industry standard

### Authentication
- **Bank Integration**: OAuth 2.0
- **User Sessions**: JWT tokens
- **Reason**: Industry standard, secure, widely supported

### Deployment
- **Containerization**: Docker
- **Orchestration**: Docker Compose
- **Reason**: Consistent environments, easy local development and cloud deployment

---

## Must-Have Features (MVP)

1. ✅ User authentication (JWT)
2. ✅ Multi-bank OAuth integration (3 banks: VBank, ABank, SBank)
3. ✅ Account aggregation (balances, transactions)
4. ✅ Automatic categorization of expenses
5. ✅ **Budget management system** (auto-create budgets based on spending patterns)
6. ✅ Analytics dashboard with charts (spending by category, trends)
7. ✅ Responsive PWA design (mobile-first)

---

## Should-Have Features (Post-MVP)

These features are valuable but not critical for the initial hackathon demo:

- Advanced ML-based spending predictions
- Multi-currency support
- Export to PDF/Excel
- Push notifications (web and mobile)
- Native mobile apps (iOS, Android)
- Advanced financial health scoring
- Automatic savings recommendations

---

## Won't-Have (Out of Scope)

Explicitly excluded from this project:

- Payment initiation (только просмотр данных - read-only access)
- Cryptocurrency integration
- Investment portfolio management
- Tax filing automation
- Loan applications
- Credit score monitoring

---

## Code Quality Standards

### Test Coverage
- **Requirement**: Minimum 70% coverage for business logic
- **Focus Areas**: Service layer, data transformations, API integrations
- **Tools**: pytest (backend), Jest (frontend)

### Type Safety
- **Backend**: Strict Pydantic models for all data structures
- **Frontend**: TypeScript strict mode enabled
- **Rationale**: Catch errors at compile time, improve IDE support

### Documentation
- **Code Comments**: For complex logic only (self-documenting code preferred)
- **API Documentation**: Automatically generated from FastAPI (OpenAPI/Swagger)
- **README**: Setup instructions, architecture overview, deployment guide

### Error Handling
- **Strategy**: Graceful degradation
- **Retry Logic**: Exponential backoff for external API calls
- **User Feedback**: Clear, actionable error messages
- **Logging**: Structured logging with correlation IDs

### Security
- **No Secrets in Code**: All credentials via environment variables
- **Encrypted Storage**: Database encryption for OAuth tokens
- **Input Validation**: Strict validation on all user inputs and API responses
- **Rate Limiting**: Protect against abuse and DDoS

---

## API Integration Requirements

**Must use ALL available Open Banking API types** to demonstrate depth of integration:

1. **Auth API** - Bank token acquisition
2. **Consents API** - User consent management (GDPR compliance)
3. **Accounts API** - Account data retrieval (balances, details)
4. **Transactions API** - Transaction history
5. **Products API** - Bank product catalog (for comparison and recommendations)
6. **Customer Leads API** - Optional for partnership revenue model
7. **Agreements API** - Optional for product enrollment

**Why all types?**: Hackathon evaluation criteria explicitly reward "depth of API usage." Implementing all API types demonstrates:
- Technical competence
- Understanding of Open Banking ecosystem
- Comprehensive solution design

---

## Development Process

### 1. Specification First
- Write detailed functional specs before coding
- Validate specs against constitution principles
- Get stakeholder approval (in real project) or self-review (hackathon)

### 2. Test-Driven (Where Critical)
- Write tests before implementation for:
  - Business logic (budget calculations, categorization)
  - External API integrations (bank APIs)
  - Data transformations
- Tests optional for:
  - UI components (manual testing acceptable for hackathon)
  - Configuration code

### 3. Incremental Delivery
- Deliver working features one at a time
- Each feature should be independently deployable and testable
- Continuous integration (run tests on every commit)

### 4. Review & Validation
- Validate against constitution after each major milestone
- Check that features align with success criteria
- Ensure no scope creep (out-of-scope features)

---

## Success Criteria (Hackathon Evaluation)

Based on VTB API Hackathon evaluation criteria:

### Business Value (33%)
- [ ] Clear user value proposition (unified financial view)
- [ ] Concrete monetization model (Freemium + partnership revenue)
- [ ] Scalable architecture (can add 10+ banks easily)
- [ ] Real-world applicability (addresses genuine user problem)

### Technical Excellence (33%)
- [ ] Deep API usage (all 6-7 Open Banking API types)
- [ ] Solid architecture (microservices pattern, separation of concerns)
- [ ] Working implementation (demo-ready, no critical bugs)
- [ ] Error handling and resilience (retry logic, graceful degradation)
- [ ] Code quality (type safety, tests, documentation)

### Presentation Quality (34%)
- [ ] Clear problem-solution narrative (fragmentation → unified view)
- [ ] Live demo showing key features (account aggregation, budgets, analytics)
- [ ] Professional slides and video (problem, solution, demo, business model)
- [ ] Innovation and creativity (automatic budgeting, ML insights)

---

## Timebox & Milestones

**Total Development Time**: 7 days  
**Deadline**: November 9, 2025, 22:00 MSK

### Day 1-4: Backend (4 days)
- [ ] FastAPI project setup
- [ ] JWT authentication
- [ ] OAuth 2.0 integration with 3 banks
- [ ] Consent management
- [ ] Accounts aggregation
- [ ] Transactions sync
- [ ] Auto-categorization
- [ ] Budget management system
- [ ] Analytics API

### Day 5-6: Frontend (2 days)
- [ ] React + Vite + TailwindCSS setup
- [ ] Authentication UI
- [ ] Dashboard with charts
- [ ] Budgets page
- [ ] Accounts & Transactions view
- [ ] Analytics page
- [ ] Responsive design

### Day 7: Polish & Presentation (1 day)
- [ ] Docker setup and deployment
- [ ] Documentation (README, API docs)
- [ ] Presentation slides (PDF)
- [ ] Video demo (2 min)
- [ ] Final testing and bug fixes

---

## Commands Available

Spec-Driven Development commands:

- `/speckit.constitution` - Update this constitution
- `/speckit.specify` - Create feature specification
- `/speckit.plan` - Generate implementation plan
- `/speckit.tasks` - Break down into actionable tasks
- `/speckit.implement` - Execute implementation

---

## Memory Management

Important decisions and context stored in:

- `memory/constitution.md` - This constitution (project principles)
- `memory/architecture-decisions.md` - ADRs (Architecture Decision Records)
- `memory/api-integration-notes.md` - API-specific learnings and gotchas

---

## When You Get Stuck

1. **Review the constitution** for guidance and decision-making principles
2. **Check existing specs** for similar problems or patterns
3. **Ask clarifying questions** before making assumptions
4. **Validate decisions** against success criteria (does this help win the hackathon?)
5. **Prioritize ruthlessly** - if it doesn't map to evaluation criteria, defer it

---

## Amendment Process

This constitution can be updated via `/speckit.constitution` command.

**When to amend**:
- New constraints discovered (e.g., API limitations)
- Scope adjustments (add/remove features)
- Technical decisions changed (e.g., switch from PostgreSQL to MongoDB)
- Process improvements (e.g., add new quality gate)

**Version bumping**:
- **MAJOR** (X.0.0): Principle changes, scope redefinition
- **MINOR** (0.X.0): New principle added, feature scope change
- **PATCH** (0.0.X): Clarifications, typo fixes, wording improvements

---

**Remember**: We're building for a hackathon. Prioritize **working demo** over perfection. Every feature must map to **evaluation criteria**. Keep it simple, make it work, make it impressive. 🚀

