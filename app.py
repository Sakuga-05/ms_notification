import base64
import logging
import os
import pickle
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, request
from google.auth.transport.requests import Request
from googleapiclient.discovery import build


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
TOKEN_FILE = BASE_DIR / "credentials" / "token.pickle"
SUBJECT = "Mensaje desde API"

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024


class GmailAuthorizationError(Exception):
    pass


def send_email(to: str, text: str, subject: str = SUBJECT) -> str:
    if not TOKEN_FILE.is_file():
        raise GmailAuthorizationError(
            "No se encontró el token de Gmail. Autoriza la cuenta antes de iniciar el servidor."
        )

    with TOKEN_FILE.open("rb") as token_file:
        credentials = pickle.load(token_file)

    if not credentials.valid:
        if not credentials.expired or not credentials.refresh_token:
            raise GmailAuthorizationError(
                "El token de Gmail no es válido. Vuelve a autorizar la cuenta."
            )
        credentials.refresh(Request())
        with TOKEN_FILE.open("wb") as token_file:
            pickle.dump(credentials, token_file)

    service = build("gmail", "v1", credentials=credentials)
    message = MIMEText(text, "plain", "utf-8")
    message["to"] = to
    message["subject"] = subject
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")
    result: dict[str, Any] = (
        service.users()
        .messages()
        .send(userId="me", body={"raw": raw_message})
        .execute()
    )
    return str(result["id"])


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return response


@app.get("/")
@app.get("/health")
def health_check():
    return jsonify(status="ok", service="ms_notification"), 200


@app.post("/notifications/2fa")
def notifications_2fa():
    if not request.is_json:
        return jsonify(error="El cuerpo debe ser JSON."), 415

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error="El cuerpo debe ser un objeto JSON."), 400

    to = data.get("to") or data.get("email")
    code = data.get("code")
    if not isinstance(to, str) or not to.strip():
        return jsonify(error="El campo 'to' es obligatorio y debe ser texto."), 400
    if not code or not str(code).strip():
        return jsonify(error="El campo 'code' es obligatorio."), 400

    code_str = str(code).strip()
    subject = "Código de verificación 2FA - OneSports"
    text = (
        f"Tu código de verificación de inicio de sesión (2FA) en OneSports es:\n\n"
        f"    {code_str}\n\n"
        f"Este código es válido por 5 minutos.\n"
        f"Si no solicitaste este código, puedes ignorar este mensaje de forma segura.\n"
    )

    try:
        message_id = send_email(to.strip(), text, subject=subject)
    except GmailAuthorizationError as error:
        return jsonify(error=str(error)), 503
    except Exception:
        logger.exception("No se pudo enviar el correo de verificación 2FA")
        return jsonify(error="No se pudo enviar el correo."), 502

    return jsonify(message="Código de verificación 2FA enviado.", id=message_id), 200


@app.post("/senemail")
@app.post("/sendemail")
def senemail():
    if not request.is_json:
        return jsonify(error="El cuerpo debe ser JSON."), 415

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error="El cuerpo debe ser un objeto JSON."), 400

    to = data.get("to")
    text = data.get("text")
    if not isinstance(to, str) or not to.strip():
        return jsonify(error="El campo 'to' es obligatorio y debe ser texto."), 400
    if not isinstance(text, str) or not text.strip():
        return jsonify(error="El campo 'text' es obligatorio y debe ser texto."), 400

    try:
        message_id = send_email(to.strip(), text)
    except GmailAuthorizationError as error:
        return jsonify(error=str(error)), 503
    except Exception:
        logger.exception("No se pudo enviar el correo")
        return jsonify(error="No se pudo enviar el correo."), 502

    return jsonify(message="Correo enviado.", id=message_id), 200


@app.errorhandler(413)
def request_too_large(_error):
    return jsonify(error="El cuerpo de la solicitud supera el límite de 1 MB."), 413


if __name__ == "__main__":
    app.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", "5000")))
