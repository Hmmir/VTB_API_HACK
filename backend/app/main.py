"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.utils.error_handlers import setup_error_handlers

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Мультибанковское приложение для агрегации финансовых данных",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup global error handlers
setup_error_handlers(app)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION
    }


# Import API routers
from app.api import auth, banks, accounts, transactions, analytics, budgets, recommendations, goals, products, system, gost, well_known, consents, payments, product_agreements, notifications, multibank, key_rate, bank_capital, unified_banking, banker
from app.api import export as export_router

# Register API routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(banks.router, prefix="/api/v1/banks", tags=["Banks"])
app.include_router(accounts.router, prefix="/api/v1/accounts", tags=["Accounts"])
app.include_router(transactions.router, prefix="/api/v1/transactions", tags=["Transactions"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])
app.include_router(budgets.router, prefix="/api/v1/budgets", tags=["Budgets"])
app.include_router(goals.router, prefix="/api/v1/goals", tags=["Goals"])
app.include_router(product_agreements.router, prefix="/api/v1/products", tags=["Product Agreements"])  # Должен быть ПЕРЕД products.router
app.include_router(products.router, prefix="/api/v1/products", tags=["Products"])
app.include_router(recommendations.router, prefix="/api/v1/recommendations", tags=["Recommendations"])
app.include_router(export_router.router, prefix="/api/v1/export", tags=["Export"])
app.include_router(consents.router, prefix="/api/v1/consents", tags=["Consents"])
app.include_router(payments.router, prefix="/api/v1/payments", tags=["Payments"])
app.include_router(notifications.router, prefix="/api/v1", tags=["Notifications"])
app.include_router(system.router, prefix="/api/v1", tags=["System"])
app.include_router(gost.router, prefix="/api/v1", tags=["GOST"])
app.include_router(multibank.router, tags=["Multibank"])
app.include_router(key_rate.router, tags=["Key Rate"])
app.include_router(bank_capital.router, tags=["Bank Capital"])
app.include_router(well_known.router, tags=["Well-Known"])
app.include_router(unified_banking.router, prefix="/api/v1", tags=["Unified Banking"])
app.include_router(banker.router, tags=["Banker"])

# TODO: Add more routers as they are implemented
# from app.api import goals, products, recommendations
# app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])
# app.include_router(budgets.router, prefix="/api/v1/budgets", tags=["Budgets"])
# app.include_router(goals.router, prefix="/api/v1/goals", tags=["Goals"])
# app.include_router(products.router, prefix="/api/v1/products", tags=["Products"])
# app.include_router(recommendations.router, prefix="/api/v1/recommendations", tags=["Recommendations"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

