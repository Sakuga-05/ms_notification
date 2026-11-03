# Servicio de notificaciones por correo

El servidor Flask expone `POST /senemail` y envía el texto recibido usando la
cuenta Gmail autorizada para la Gmail API. El asunto se establece como
`Mensaje desde API`.

## Requisitos

- Python 3.12
- Dependencias de `requeriments.txt`
- `credentials/credentials.json` y un token OAuth autorizado en
  `credentials/token.pickle`

El token debe tener el permiso Gmail `gmail.send`. Si todavía no existe, autoriza
la cuenta con el flujo OAuth local utilizado por los scripts de prueba antes de
arrancar el servidor.

## Iniciar el servidor

```powershell
.\venv\Scripts\python.exe -m pip install -r requeriments.txt
.\venv\Scripts\python.exe app.py
```

El servidor escucha localmente en `http://127.0.0.1:5000`. Se puede configurar
la dirección con `HOST` y el puerto con `PORT`.
El endpoint no tiene autenticación; mantenlo en localhost o detrás de una red
confiable y no lo expongas directamente a Internet.

## Enviar un correo

Envía un POST con JSON:

```json
{
  "to": "destinatario@example.com",
  "text": "Hola, este es el contenido del correo."
}
```

Ejemplo con PowerShell:

```powershell
Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:5000/senemail `
  -ContentType "application/json" `
  -Body '{"to":"destinatario@example.com","text":"Hola desde Flask."}'
```
