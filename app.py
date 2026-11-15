import os
import secrets
import html
from urllib.parse import urlencode

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from starlette.middleware.sessions import SessionMiddleware

load_dotenv()

CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
HOSTNAME = os.getenv("RENDER_EXTERNAL_HOSTNAME")
REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI") or (
    f"https://{HOSTNAME}/auth/discord/callback" if HOSTNAME
    else "http://localhost:8000/auth/discord/callback"
)
SESSION_SECRET = os.getenv("SESSION_SECRET")
IS_PRODUCTION = bool(HOSTNAME)

if not all([CLIENT_ID, CLIENT_SECRET, SESSION_SECRET]):
    raise RuntimeError(
        "DISCORD_CLIENT_ID, DISCORD_CLIENT_SECRET ve SESSION_SECRET ortam değişkenleri ayarlanmalı."
    )

app = FastAPI(title="FIVEGUARD SCANNER PRO")
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    same_site="lax",
    https_only=IS_PRODUCTION,
)

@app.get("/", response_class=HTMLResponse)
async def home():
    with open("index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

@app.get("/auth/discord")
async def discord_login(request: Request):
    state = secrets.token_urlsafe(32)
    request.session["oauth_state"] = state
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "identify",
        "state": state,
    }
    return RedirectResponse("https://discord.com/oauth2/authorize?" + urlencode(params))

@app.get("/auth/discord/callback")
async def discord_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
):
    if error:
        raise HTTPException(status_code=400, detail="Discord girişi iptal edildi veya reddedildi.")
    expected_state = request.session.pop("oauth_state", None)
    if (
        not code or not state or not expected_state
        or not secrets.compare_digest(state, expected_state)
    ):
        raise HTTPException(status_code=400, detail="Güvenlik doğrulaması başarısız. Tekrar giriş yapın.")

    async with httpx.AsyncClient(timeout=15) as client:
        token_response = await client.post(
            "https://discord.com/api/oauth2/token",
            data={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": REDIRECT_URI,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if token_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Discord token doğrulaması başarısız.")
        access_token = token_response.json().get("access_token")
        user_response = await client.get(
            "https://discord.com/api/users/@me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if user_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Discord kullanıcı bilgisi alınamadı.")
        user = user_response.json()

    request.session["discord_user"] = {
        "id": user.get("id"),
        "username": user.get("username"),
        "global_name": user.get("global_name"),
    }
    display_name = html.escape(user.get("global_name") or user.get("username") or "Kullanıcı")
    return HTMLResponse(
        f"""<!doctype html><html lang="tr"><meta charset="utf-8">
        <body style="background:#090a0e;color:#f4f4f4;font:18px Arial;padding:48px">
        <h1>Giriş başarılı, {display_name}!</h1>
        <p>Discord hesabın doğrulandı.</p>
        <p>Bu sürümde tarama motoru, ödeme ve üyelik/rol veritabanı henüz etkin değildir.</p>
        <a style="color:#ff6976" href="/">Ana sayfa</a> ·
        <a style="color:#ff6976" href="/me">Hesabım</a> ·
        <a style="color:#ff6976" href="/logout">Çıkış yap</a>
        </body></html>"""
    )

@app.get("/me")
async def me(request: Request):
    user = request.session.get("discord_user")
    if not user:
        return JSONResponse({"logged_in": False}, status_code=401)
    return {"logged_in": True, "discord_user": user}

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/")
