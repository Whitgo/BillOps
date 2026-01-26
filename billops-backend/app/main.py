from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
import time
import logging

from app.api.v1.routes import auth, clients, projects, time_entries, billing_rules, invoices, payments, users, integrations, notifications
from app.services.analytics import get_analytics, EventType

logger = logging.getLogger(__name__)

app = FastAPI(
    title="BillOps API",
    version="0.1.0",
    description="Automated billing and time capture platform",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Custom OpenAPI schema
def custom_openapi():
    """Generate custom OpenAPI schema with enhanced documentation."""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="BillOps API",
        version="0.1.0",
        description="""
        # BillOps - Automated Billing & Time Capture

        A comprehensive platform for tracking time, managing clients, and automating invoice generation.

        ## Features

        ### Time Tracking
        - Capture billable and non-billable time entries
        - Multi-project time allocation
        - Daily/weekly/monthly summaries

        ### Invoice Management
        - Automated invoice generation from time entries
        - Invoice status workflow (draft → sent → paid)
        - Payment tracking and reconciliation

        ### Client Management
        - Client profiles and settings
        - Billing rules and rate configurations
        - Project-based organization

        ### Integrations
        - Google Calendar sync
        - Microsoft Outlook integration
        - Slack status updates
        - Email notifications

        ### Analytics
        - Event tracking and analytics
        - API performance monitoring
        - Business metrics and reporting

        ## Authentication

        All protected endpoints require a JWT token in the `Authorization` header:

        ```
        Authorization: Bearer <your_jwt_token>
        ```

        ## API Structure

        - `/api/v1/auth` - Authentication (login, register)
        - `/api/v1/users` - User management
        - `/api/v1/clients` - Client management
        - `/api/v1/projects` - Project management
        - `/api/v1/time-entries` - Time tracking
        - `/api/v1/invoices` - Invoice management
        - `/api/v1/payments` - Payment tracking
        - `/api/v1/billing-rules` - Billing configuration
        - `/api/v1/integrations` - External integrations
        """,
        routes=app.routes,
    )
    
    # Add server information
    openapi_schema["servers"] = [
        {"url": "http://localhost:8000", "description": "Development"},
        {"url": "https://api.billops.com", "description": "Production"},
    ]
    
    # Add authentication scheme
    openapi_schema["components"]["securitySchemes"] = {
        "Bearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT token for authentication",
        }
    }
    
    # Add tags descriptions
    openapi_schema["tags"] = [
        {"name": "auth", "description": "Authentication endpoints"},
        {"name": "users", "description": "User management"},
        {"name": "clients", "description": "Client management"},
        {"name": "projects", "description": "Project management"},
        {"name": "time-entries", "description": "Time entry tracking"},
        {"name": "invoices", "description": "Invoice management"},
        {"name": "payments", "description": "Payment tracking"},
        {"name": "billing-rules", "description": "Billing rules"},
        {"name": "integrations", "description": "External integrations"},
        {"name": "health", "description": "Health check"},
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Analytics middleware
@app.middleware("http")
async def analytics_middleware(request: Request, call_next):
    """Track API calls for analytics."""
    start_time = time.time()
    
    # Call the next middleware/route
    response = await call_next(request)
    
    # Calculate response time
    elapsed_time = time.time() - start_time
    elapsed_ms = elapsed_time * 1000
    
    # Track API call
    analytics = get_analytics()
    analytics.track_api_call(
        endpoint=request.url.path,
        method=request.method,
        status_code=response.status_code,
        response_time_ms=elapsed_ms,
    )
    
    # Add response time header
    response.headers["X-Process-Time"] = str(elapsed_time)
    
    return response

# Health check endpoint
@app.get("/health", tags=["health"], summary="Health Check")
def health() -> dict[str, str]:
    """Check if API is healthy and running."""
    return {"status": "healthy", "version": "0.1.0"}

# OpenAPI documentation endpoints
@app.get("/api/docs", tags=["docs"], summary="Interactive API Documentation")
def docs():
    """Swagger UI interactive documentation."""
    return {"docs_url": "/api/docs", "message": "Use /api/docs for Swagger UI"}

@app.get("/api/redoc", tags=["docs"], summary="ReDoc Documentation")
def redoc():
    """ReDoc API documentation."""
    return {"redoc_url": "/api/redoc", "message": "Use /api/redoc for ReDoc"}

# Include v1 routers
app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
app.include_router(users.router, prefix="/api/v1", tags=["users"])
app.include_router(clients.router, prefix="/api/v1", tags=["clients"])
app.include_router(projects.router, prefix="/api/v1", tags=["projects"])
app.include_router(time_entries.router, prefix="/api/v1", tags=["time-entries"])
app.include_router(billing_rules.router, prefix="/api/v1", tags=["billing-rules"])
app.include_router(invoices.router, prefix="/api/v1", tags=["invoices"])
app.include_router(payments.router, prefix="/api/v1", tags=["payments"])
app.include_router(integrations.router, prefix="/api/v1", tags=["integrations"])
app.include_router(notifications.router, tags=["notifications"])
