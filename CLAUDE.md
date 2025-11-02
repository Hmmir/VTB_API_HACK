# Claude Instructions for FinanceHub Project

## Project Overview
**FinanceHub** is a multi-bank financial aggregation platform for the VTB API Hackathon 2025. It solves the problem of financial data fragmentation by providing a unified interface for managing accounts across multiple banks (VBank, ABank, SBank).

## Constitution
This document defines the core principles and constraints for developing FinanceHub.

### Core Principles
1. **Simplicity First** - Focus on core features that solve the main problem
2. **User Value** - Every feature must provide measurable value to end users
3. **Scalability** - Architecture must support adding new banks easily
4. **Security** - Follow Open Banking security standards strictly
5. **Performance** - Real-time data updates, fast response times

### Technical Constraints
- **Backend**: Python 3.11+ with FastAPI framework
- **Database**: PostgreSQL 15 for relational data
- **Cache**: Redis 7 for session storage and real-time data
- **Frontend**: React 18 with TypeScript, Vite, TailwindCSS
- **API Standard**: Open Banking Russia v2.1 specification
- **Authentication**: OAuth 2.0 + JWT tokens
- **Deployment**: Docker containers, Docker Compose for orchestration

### Must-Have Features (MVP)
1. ✅ User authentication (JWT)
2. ✅ Multi-bank OAuth integration (3 banks)
3. ✅ Account aggregation (balances, transactions)
4. ✅ Automatic categorization of expenses
5. ✅ **Budget management system** (auto-create budgets)
6. ✅ Analytics dashboard with charts
7. ✅ Responsive PWA design

### Should-Have Features (Post-MVP)
- Advanced ML-based predictions
- Multi-currency support
- Export to PDF/Excel
- Push notifications
- Mobile native apps

### Won't-Have (Out of Scope)
- Payment initiation (только просмотр данных)
- Cryptocurrency integration
- Investment portfolio management
- Tax filing automation

### Code Quality Standards
- **Test Coverage**: Minimum 70% for business logic
- **Type Safety**: Strict TypeScript, Pydantic models
- **Documentation**: Inline comments for complex logic, API documentation
- **Error Handling**: Graceful degradation, retry logic with exponential backoff
- **Security**: No secrets in code, encrypted storage, input validation

### API Integration Requirements
Must use ALL available Open Banking API types:
1. **Auth API** - Bank token acquisition
2. **Consents API** - User consent management
3. **Accounts API** - Account data retrieval
4. **Products API** - Bank product catalog (for comparison)
5. **Customer Leads API** - Optional for partnerships
6. **Agreements API** - Optional for product enrollment

### Development Process
1. **Specification First** - Write detailed spec before coding
2. **Test-Driven** - Write tests before implementation where critical
3. **Incremental** - Deliver working features one at a time
4. **Review** - Validate against constitution after each major milestone

### Success Criteria (Hackathon Evaluation)
Based on VTB API Hackathon criteria:

**Business (33%)**
- [ ] Clear user value proposition
- [ ] Concrete monetization model (Freemium + partnerships)
- [ ] Scalable architecture (can add 10+ banks)

**Technical (33%)**
- [ ] Deep API usage (all 6 types)
- [ ] Solid architecture (microservices pattern)
- [ ] Working implementation (demo-ready)
- [ ] Error handling and resilience

**Presentation (34%)**
- [ ] Clear problem-solution narrative
- [ ] Live demo showing key features
- [ ] Professional slides and video
- [ ] Innovation and creativity

### Timebox
- **Total Development Time**: 7 days
- **Backend**: 4 days
- **Frontend**: 2 days
- **Polish + Documentation**: 1 day
- **Deadline**: November 9, 2025, 22:00 MSK

### Commands You Can Use
- `/speckit.plan` - Generate implementation plan
- `/speckit.tasks` - Break down into actionable tasks
- `/speckit.implement` - Execute implementation

### Memory Management
Important decisions and context are stored in:
- `memory/constitution.md` - This constitution
- `memory/architecture-decisions.md` - ADRs (Architecture Decision Records)
- `memory/api-integration-notes.md` - API-specific learnings

### When You Get Stuck
1. Review the constitution for guidance
2. Check existing specs for similar problems
3. Ask clarifying questions before making assumptions
4. Validate decisions against success criteria

---

**Remember**: We're building for a hackathon. Prioritize working demo over perfection. Every feature must map to evaluation criteria. Keep it simple, make it work, make it impressive.

