from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routes import auth, clients, projects, time_entries, billing_rules, invoices, payments, users, integrations, notifications

app = FastAPI(
    title="BillOps API",
    version="0.1.0",
    description="Automated billing and time capture platform",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}

# Include v1 routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(clients.router, prefix="/api/v1")
app.include_router(projects.router, prefix="/api/v1")
app.include_router(time_entries.router, prefix="/api/v1")
app.include_router(billing_rules.router, prefix="/api/v1")
app.include_router(invoices.router, prefix="/api/v1")
app.include_router(payments.router, prefix="/api/v1")
app.include_router(integrations.router, prefix="/api/v1")
app.include_router(notifications.router)
