"""
Quick validation script to verify all routes are properly wired
"""
from app.main import app

def test_routes_exist():
    """Verify all routes are registered"""
    routes = app.routes
    route_paths = set()
    
    for route in routes:
        if hasattr(route, 'path'):
            route_paths.add(route.path)
    
    expected_routes = [
        "/health",
        "/api/v1/auth/signup",
        "/api/v1/auth/login",
        "/api/v1/auth/refresh",
        "/api/v1/auth/me",
        "/api/v1/clients/",
        "/api/v1/clients/{client_id}",
        "/api/v1/projects/",
        "/api/v1/projects/{project_id}",
        "/api/v1/time-entries/",
        "/api/v1/time-entries/{entry_id}",
        "/api/v1/billing-rules/",
        "/api/v1/billing-rules/{rule_id}",
        "/api/v1/invoices/",
        "/api/v1/invoices/{invoice_id}",
        "/api/v1/invoices/number/{invoice_number}",
        "/api/v1/payments/",
        "/api/v1/payments/{payment_id}",
    ]
    
    for route in expected_routes:
        assert route in route_paths, f"Missing route: {route}"
    
    print(f"✓ All {len(expected_routes)} core routes registered")
    print(f"  Total routes including openapi: {len(route_paths)}")
    
    return True

def test_route_methods():
    """Verify HTTP methods are properly configured"""
    routes_by_path = {}
    
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            path = route.path
            if path not in routes_by_path:
                routes_by_path[path] = []
            routes_by_path[path].extend(route.methods)
    
    # Check some key routes have expected methods
    assert "GET" in routes_by_path.get("/api/v1/clients/", []), "GET /clients not found"
    assert "POST" in routes_by_path.get("/api/v1/clients/", []), "POST /clients not found"
    assert "GET" in routes_by_path.get("/api/v1/clients/{client_id}", []), "GET /clients/{id} not found"
    assert "PATCH" in routes_by_path.get("/api/v1/clients/{client_id}", []), "PATCH /clients/{id} not found"
    assert "DELETE" in routes_by_path.get("/api/v1/clients/{client_id}", []), "DELETE /clients/{id} not found"
    
    print(f"✓ All route methods properly configured")
    return True

def test_openapi_schema():
    """Verify OpenAPI schema generation"""
    schema = app.openapi()
    assert schema is not None, "OpenAPI schema not generated"
    assert "paths" in schema, "No paths in OpenAPI schema"
    assert "components" in schema, "No components in OpenAPI schema"
    print(f"✓ OpenAPI schema generated with {len(schema['paths'])} paths")
    return True

if __name__ == "__main__":
    try:
        test_routes_exist()
        test_route_methods()
        test_openapi_schema()
        print("\n✓ All validation tests passed!")
    except AssertionError as e:
        print(f"\n✗ Validation failed: {e}")
        exit(1)
    except Exception as e:
        print(f"\n✗ Error during validation: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
