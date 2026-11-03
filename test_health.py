import app

client = app.app.test_client()
res = client.get("/health")
print("Health status:", res.status_code, res.get_json())

