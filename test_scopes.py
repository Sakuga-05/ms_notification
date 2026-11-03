import app, pickle
with open(app.TOKEN_FILE, "rb") as f:
    creds = pickle.load(f)
print("Scopes:", getattr(creds, 'scopes', None))

