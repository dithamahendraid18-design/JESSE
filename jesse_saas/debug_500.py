from app import create_app, db
from app.services.analytics import AnalyticsService
from app.models import Client
from datetime import datetime

app = create_app()

with app.app_context():
    try:
        print("Testing AnalyticsService.get_client_stats...")
        stats = AnalyticsService.get_client_stats()
        print(f"Stats: {stats}")
        
        print("Testing Client Query...")
        clients = Client.query.all()
        print(f"Clients found: {len(clients)}")

        print("Testing Render Template Logic simulation...")
        # Simulate what's passed to template
        context = {
            'clients': clients,
            'active_page': 'clients',
            'stats': stats,
            'today': datetime.now().date()
        }
        print("Context created successfully.")
        
        # Check endpoints
        print(f"Endpoints: {list(app.view_functions.keys())}")
        if 'uploaded_file' not in app.view_functions:
            print("CRITICAL: 'uploaded_file' endpoint NOT FOUND!")

        # Test request context for url_for
        with app.test_request_context():
            print("Testing UploadService (Local)...")
            from app.services.upload_service import UploadService
            
            # Test with dummy file
            url_local = UploadService.resolve_url("avatars/test.jpg")
            print(f"Resolved Local URL: {url_local}")
            
            # Test with None
            url_none = UploadService.resolve_url(None)
            print(f"Resolved None: {url_none}")

    except Exception as e:
        print("CRASH DETECTED!")
        print(e)
        import traceback
        traceback.print_exc()
