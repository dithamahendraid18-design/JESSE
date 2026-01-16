def test_index(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b"JESSE SaaS Backend Active" in response.data

def test_admin_login_page(client):
    response = client.get('/admin/login')
    assert response.status_code == 200
    # Check for some login page content
    assert b"Login" in response.data or b"Sign In" in response.data
