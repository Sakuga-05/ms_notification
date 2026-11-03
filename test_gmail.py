import app
import pickle
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

with open(app.TOKEN_FILE, "rb") as f:
    creds = pickle.load(f)

if not creds.valid and creds.refresh_token:
    creds.refresh(Request())

service = build("gmail", "v1", credentials=creds)
profile = service.users().getProfile(userId="me").execute()
print("Gmail connection SUCCESS! Email address:", profile.get("emailAddress"))

