import os
import sys
import io

# Load .env file if present (for local development)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Fix Windows Unicode encoding issue (charmap codec error for emoji etc.)
if sys.stdout and hasattr(sys.stdout, 'encoding') and sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr and hasattr(sys.stderr, 'encoding') and sys.stderr.encoding and sys.stderr.encoding.lower() != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
os.environ['PYTHONUTF8'] = '1'

import json
import time
import base64
import secrets
import requests
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from datetime import datetime
from flask import Flask, request, redirect, session, render_template, jsonify, url_for

# ─────────────────────────────────────────────
#  ██████  CONFIG – PASTE YOUR API KEYS HERE
# ─────────────────────────────────────────────
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "").strip()
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "").strip()
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", "").strip()
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "").strip()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "").strip()

print("Spotify client loaded:", bool(SPOTIFY_CLIENT_ID))
print("Spotify secret loaded:", bool(SPOTIFY_CLIENT_SECRET))
print("Spotify redirect uri:", SPOTIFY_REDIRECT_URI)
print("Weather key loaded:", bool(OPENWEATHER_API_KEY))
print("Weather key first 5 chars:", OPENWEATHER_API_KEY[:5] if OPENWEATHER_API_KEY else None)


# Flask secret key – change this to a random string in production
SECRET_KEY = secrets.token_hex(32)

# Spotify OAuth scopes needed
SPOTIFY_SCOPES = (
    "streaming "
    "user-read-email "
    "user-read-private "
    "user-read-playback-state "
    "user-modify-playback-state "
    "user-read-currently-playing"
)

scope = SPOTIFY_SCOPES
try:
    sp_oauth = SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope="streaming user-read-email user-read-private user-read-playback-state user-modify-playback-state user-read-currently-playing",
        cache_path=None
    )
except Exception as e:
    print(f"[WARNING] SpotifyOAuth init failed: {e}")
    sp_oauth = None

# ─────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev_secret").strip()
app.config["TEMPLATES_AUTO_RELOAD"] = True   # always serve fresh templates
# Only enforce HTTPS cookies in true production (not on localhost)
_is_local = "localhost" in SPOTIFY_REDIRECT_URI or "127.0.0.1" in SPOTIFY_REDIRECT_URI
app.config["SESSION_COOKIE_SECURE"] = not _is_local
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# ─────────────────────────────────────────────
#  HELPER – WEATHER LOGIC
# ─────────────────────────────────────────────

# Dynamic mood logic using time of day and temperature instead of a static map

def get_season(month: int) -> str:
    if month in (12, 1, 2):
        return "Winter"
    elif month in (3, 4, 5):
        return "Summer"
    elif month in (6, 7, 8, 9):
        return "Monsoon"
    else:
        return "Autumn"

def parse_weather(data: dict) -> dict:
    weather_main = data["weather"][0]["main"]
    weather_desc = data["weather"][0]["description"].title()
    icon_code    = data["weather"][0]["icon"]
    temp_c       = round(data["main"]["temp"] - 273.15, 1)
    humidity     = data["main"]["humidity"]
    city         = data.get("name", "Unknown")
    country      = data.get("sys", {}).get("country", "")

    now    = datetime.now()
    month  = now.month
    month_name = now.strftime("%B")
    season = get_season(month)

    is_day = 'd' in icon_code
    mood, vibe = "Chill", "Every day is a music day 🎵"

    if weather_main == "Clear":
        if is_day:
            if temp_c > 35:
                mood, vibe = "Chill", "Too hot outside, chill inside 🥵"
            else:
                mood, vibe = "Party", "Sunny vibes, let's celebrate! ☀️"
        else:
            mood, vibe = "Romantic", "Clear starry night ✨"
    elif weather_main == "Clouds":
        if is_day:
            mood, vibe = "Chill", "Cloudy skies, cozy feels 🌥️"
        else:
            mood, vibe = "Sad", "Cloudy night, introspective vibes ☁️"
    elif weather_main in ("Rain", "Drizzle"):
        mood, vibe = "Romantic", "Rainy weather, perfect for love songs 🌧️"
    elif weather_main == "Thunderstorm":
        mood, vibe = "Workout", "Thunder energy! Go beast mode! ⚡"
    elif weather_main == "Snow":
        mood, vibe = "Classic", "Snowfall classics for a white winter 🌨️"
    elif weather_main in ("Mist", "Fog", "Haze"):
        if is_day:
            mood, vibe = "Chill", "Misty/Hazy day, relax and calm 🌫️"
        else:
            mood, vibe = "Sad", "Foggy night, lay back and think 🌁"
    elif weather_main in ("Smoke", "Dust", "Sand", "Ash"):
        mood, vibe = "Sad", "Dusty/Smoky atmosphere 🌪️"
    elif weather_main in ("Squall", "Tornado"):
        mood, vibe = "Workout", "Extreme weather, pump up the volume! 🌪️"

    return {
        "city"         : city,
        "country"      : country,
        "temperature"  : temp_c,
        "humidity"     : humidity,
        "condition"    : weather_main,
        "description"  : weather_desc,
        "icon_code"    : icon_code,
        "weather_icon" : f"https://openweathermap.org/img/wn/{icon_code}@2x.png",
        "month"        : month_name,
        "season"       : season,
        "mood"         : mood,
        "vibe"         : vibe,
    }

# ─────────────────────────────────────────────
#  HELPER – SPOTIFY AUTH
# ─────────────────────────────────────────────

def get_client_credentials_token():
    """Fallback token using Client Credentials (no user login needed for search)."""
    cached = session.get("cc_token")
    cached_exp = session.get("cc_token_exp", 0)
    if cached and time.time() < cached_exp:
        return cached

    creds = base64.b64encode(
        f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}".encode()
    ).decode()
    
    try:
        resp = requests.post(
            "https://accounts.spotify.com/api/token",
            headers={"Authorization": f"Basic {creds}",
                     "Content-Type": "application/x-www-form-urlencoded"},
            data={"grant_type": "client_credentials"},
            timeout=10,
        )
        if resp.status_code != 200:
            return None
        token_data = resp.json()
        session["cc_token"]     = token_data["access_token"]
        session["cc_token_exp"] = time.time() + token_data.get("expires_in", 3600) - 60
        return token_data["access_token"]
    except Exception as e:
        print(f"[Spotify] Client token fetch error: {e}")
        return None

def get_user_token():
    """Return user OAuth access token, refreshing if expired."""
    access_token = session.get("access_token")
    expires_at   = session.get("token_expires_at", 0)

    if access_token and time.time() < expires_at:
        return access_token

    # Try refresh
    refresh_token = session.get("refresh_token")
    if not refresh_token:
        return None

    creds = base64.b64encode(
        f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}".encode()
    ).decode()
    
    try:
        resp = requests.post(
            "https://accounts.spotify.com/api/token",
            headers={"Authorization": f"Basic {creds}",
                     "Content-Type": "application/x-www-form-urlencoded"},
            data={"grant_type": "refresh_token", "refresh_token": refresh_token},
            timeout=10,
        )
        if resp.status_code != 200:
            session.pop("access_token", None)
            return None

        token_data = resp.json()
        session["access_token"]     = token_data["access_token"]
        session["token_expires_at"] = time.time() + token_data.get("expires_in", 3600) - 60
        if "refresh_token" in token_data:
            session["refresh_token"] = token_data["refresh_token"]
        return token_data["access_token"]
    except Exception as e:
        print(f"[Spotify] User token refresh error: {e}")
        session.pop("access_token", None)
        return None

def best_token():
    """Return user token if available, fall back to client credentials."""
    return get_user_token() or get_client_credentials_token()

# ─────────────────────────────────────────────
#  HELPER – BUILD SPOTIFY SEARCH QUERY
# ─────────────────────────────────────────────

MOOD_GENRE_MAP = {
    "Romantic" : ["romance", "love songs", "bollywood romantic"],
    "Party"    : ["party", "dance", "upbeat hits"],
    "Chill"    : ["chill", "lo-fi", "acoustic chill"],
    "Sad"      : ["sad songs", "heartbreak", "melancholic"],
    "Workout"  : ["workout", "pump up", "gym beats"],
    "Classic"  : ["classic hits", "timeless classics", "oldies"],
    "All"      : ["top hits", "popular"],
}

LANGUAGE_MAP = {
    "Hindi"    : "hindi",
    "English"  : "english",
    "Tamil"    : "tamil",
    "Telugu"   : "telugu",
    "Marathi"  : "marathi",
    "Punjabi"  : "punjabi",
    "Bengali"  : "bengali",
    "Bhojpuri" : "bhojpuri",
    "Odia"     : "odia",
}

GENERATION_MAP = {
    "90s"         : "90s",
    "2000s"       : "2000s",
    "GenZ"        : "genz",
    "Trending"    : "trending",
    "New Release" : "new release 2024",
}

def build_search_query(mood, singer, language, generation, variant=0):
    genre_terms = MOOD_GENRE_MAP.get(mood, MOOD_GENRE_MAP["All"])
    # variant cycles through available genre terms to give different results on Refresh
    genre = genre_terms[variant % len(genre_terms)]

    parts = [genre]
    if language and language != "All":
        parts.append(LANGUAGE_MAP.get(language, language))
    
    # Ignore placeholders like 'any', 'all', 'any artist'
    if singer:
        s_lower = singer.lower().strip()
        if s_lower not in ("all", "any", "", "any artist"):
            parts.append(singer)
            
    if generation and generation != "All":
        parts.append(GENERATION_MAP.get(generation, generation))

    return " ".join(parts)

# ─────────────────────────────────────────────
#  ROUTES
# ─────────────────────────────────────────────

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/test")
def test():
    return "Server working"


# ── Weather ──────────────────────────────────

@app.route("/api/weather")
def api_weather():
    city = request.args.get("city", "").strip()
    lat  = request.args.get("lat")
    lon  = request.args.get("lon")

    if OPENWEATHER_API_KEY == "YOUR_OPENWEATHERMAP_API_KEY":
        return jsonify({"error": "OpenWeatherMap API key not configured. Please edit app.py and add your key."}), 503

    try:
        if city:
            url    = "https://api.openweathermap.org/data/2.5/weather"
            params = {"q": city, "appid": OPENWEATHER_API_KEY}
        elif lat and lon:
            url    = "https://api.openweathermap.org/data/2.5/weather"
            params = {"lat": lat, "lon": lon, "appid": OPENWEATHER_API_KEY}
        else:
            return jsonify({"error": "Provide 'city' or 'lat' and 'lon' query parameters."}), 400

        resp = requests.get(url, params=params, timeout=10)
        print("Weather key loaded:", bool(OPENWEATHER_API_KEY))
        print("Weather API URL:", url)
        print("Weather API status:", resp.status_code)
        print("Weather API response:", resp.text)

        if resp.status_code == 404:
            return jsonify({"error": f"City '{city}' not found. Please check the spelling."}), 404
        if resp.status_code == 401:
            return jsonify({"error": "Invalid OpenWeatherMap API key."}), 401
        if resp.status_code == 429:
            return jsonify({"error": "Weather API rate limit reached. Please try again later."}), 429
        if resp.status_code != 200:
            return jsonify({"error": "Weather service unavailable."}), 502

        return jsonify(parse_weather(resp.json()))

    except requests.exceptions.ConnectionError:
        return jsonify({"error": "No internet connection."}), 503
    except requests.exceptions.Timeout:
        return jsonify({"error": "Weather request timed out."}), 504
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ── Music Recommendations ──────────────────

@app.route("/api/recommend")
def api_recommend():
    mood       = request.args.get("mood",       "Chill")
    singer     = request.args.get("singer",     "")
    language   = request.args.get("language",   "Hindi")
    generation = request.args.get("generation", "Trending")

    if SPOTIFY_CLIENT_ID == "YOUR_SPOTIFY_CLIENT_ID":
        return jsonify({"error": "Spotify API credentials not configured. Please edit app.py and add your keys."}), 503

    token = best_token()
    if not token:
        return jsonify({"error": "Could not obtain Spotify token. Check your Client ID and Secret."}), 503

    variant = int(request.args.get("variant", 0))
    query = build_search_query(mood, singer, language, generation, variant)

    try:
        def do_search(tok):
            return requests.get(
                "https://api.spotify.com/v1/search",
                headers={"Authorization": f"Bearer {tok}"},
                params={"q": query, "type": "track", "limit": 10, "market": "IN"},
                timeout=10,
            )

        resp = do_search(token)

        if resp.status_code == 401:
            # Token expired – clear and retry once
            session.pop("access_token", None)
            session.pop("cc_token",     None)
            token = best_token()
            if token:
                resp = do_search(token)
            else:
                return jsonify({"error": "Spotify authentication failed."}), 401

        if resp.status_code == 429:
            return jsonify({"error": "Spotify rate limit reached."}), 429

        if resp.status_code == 403 and "registered" in resp.text.lower():
            session.clear()
            return jsonify({"error": "Dashboard Email Error: The Spotify account you logged in with doesn't match the one in your Dashboard. Please open an Incognito window and login again."}), 403

        if resp.status_code != 200:
            return jsonify({"error": f"Search failed: {resp.text}"}), 502

        items = resp.json().get("tracks", {}).get("items", [])

        # ── Deduplicate by normalized (name + primary artist) ──
        seen   = set()
        tracks = []
        for item in items:
            primary_artist = (item.get("artists") or [{}])[0].get("name", "").lower().strip()
            norm_key       = (item["name"].lower().strip(), primary_artist)
            if norm_key in seen:
                continue
            seen.add(norm_key)

            album_images = item.get("album", {}).get("images", [])
            album_art    = album_images[0]["url"] if album_images else ""
            artists      = ", ".join(a["name"] for a in item.get("artists", []))
            duration_ms  = item.get("duration_ms", 0)
            duration_s   = duration_ms // 1000
            duration_fmt = f"{duration_s // 60}:{duration_s % 60:02d}"

            tracks.append({
                "id"          : item["id"],
                "name"        : item["name"],
                "artists"     : artists,
                "album"       : item.get("album", {}).get("name", ""),
                "album_art"   : album_art,
                "duration"    : duration_fmt,
                "duration_ms" : duration_ms,
                "preview_url" : item.get("preview_url"),
                "uri"         : item.get("uri"),
                "external_url": item.get("external_urls", {}).get("spotify", ""),
            })

            if len(tracks) >= 10:
                break

        return jsonify({"tracks": tracks, "query": query})

    except requests.exceptions.Timeout:
        return jsonify({"error": "Spotify request timed out."}), 504
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ── YouTube Search ─────────────────────────────

@app.route("/api/youtube_search")
def api_youtube_search():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"error": "Query parameter 'q' is required."}), 400

    try:
        from yt_app import _fetch_single_query, YOUTUBE_API_KEY
        results = _fetch_single_query(q, 1, YOUTUBE_API_KEY, "", "All", "All")
        if results and isinstance(results, list) and len(results) > 0:
            return jsonify({"video_id": results[0].get("video_id")})
        return jsonify({"error": "No video found."}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Single Song Search ────────────────────────

@app.route("/api/search_single")
def api_search_single():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"error": "Query parameter 'q' is required."}), 400

    token = best_token()
    if not token:
        return jsonify({"error": "Could not obtain Spotify token."}), 503

    def do_search(tok, query, limit=10):
        return requests.get(
            "https://api.spotify.com/v1/search",
            headers={"Authorization": f"Bearer {tok}"},
            params={"q": query, "type": "track", "limit": limit, "market": "IN"},
            timeout=10,
        )

    try:
        resp = do_search(token, q)

        if resp.status_code == 401:
            session.pop("access_token", None)
            session.pop("cc_token", None)
            token = best_token()
            if token:
                resp = do_search(token, q)
            else:
                return jsonify({"error": "Spotify authentication failed."}), 401

        if resp.status_code == 429:
            return jsonify({"error": "Spotify rate limit reached."}), 429

        if resp.status_code != 200:
            return jsonify({"error": f"Search failed: {resp.text}"}), 502

        items = resp.json().get("tracks", {}).get("items", [])
        if not items:
            return jsonify({"error": f"No track found for '{q}'"}), 404

        # ── Smart matching: exact → starts-with → partial → fallback ──
        q_lower = q.lower().strip()

        # Priority 1: Exact title match
        best = next((i for i in items if i["name"].lower().strip() == q_lower), None)
        # Priority 2: Title starts with query
        if not best:
            best = next((i for i in items if i["name"].lower().strip().startswith(q_lower)), None)
        # Priority 3: Query starts with title (e.g. "khat" matches "Khat (feat. ...)")
        if not best:
            best = next((i for i in items if q_lower.startswith(i["name"].lower().strip())), None)
        # Priority 4: Title contains the query word
        if not best:
            best = next((i for i in items if q_lower in i["name"].lower()), None)
        # Priority 5: Fall back to first Spotify result
        if not best:
            best = items[0]

        item = best
        album_images = item.get("album", {}).get("images", [])
        album_art    = album_images[0]["url"] if album_images else ""
        artists      = ", ".join(a["name"] for a in item.get("artists", []))
        duration_ms  = item.get("duration_ms", 0)
        duration_s   = duration_ms // 1000
        duration_fmt = f"{duration_s // 60}:{duration_s % 60:02d}"

        track = {
            "id"          : item["id"],
            "name"        : item["name"],
            "artists"     : artists,
            "album"       : item.get("album", {}).get("name", ""),
            "album_art"   : album_art,
            "duration"    : duration_fmt,
            "duration_ms" : duration_ms,
            "preview_url" : item.get("preview_url"),
            "uri"         : item.get("uri"),
            "external_url": item.get("external_urls", {}).get("spotify", ""),
        }
        return jsonify({"track": track})

    except requests.exceptions.Timeout:
        return jsonify({"error": "Spotify request timed out."}), 504
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ── Spotify OAuth ────────────────────────────

@app.route("/login")
def login():
    if not sp_oauth:
        return redirect("/?auth=error&msg=Spotify+credentials+not+configured")
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route("/callback")
def callback():
    try:
        error = request.args.get("error")
        code = request.args.get("code")

        if error:
            return redirect("/?auth=error&msg=" + error)

        if not code:
            return redirect("/?auth=error&msg=No+code+received")

        if not sp_oauth:
            return redirect("/?auth=error&msg=Spotify+credentials+not+configured")

        token_info = sp_oauth.get_access_token(code)

        # Save tokens using the keys that get_user_token() expects
        session["token_info"]       = token_info
        session["access_token"]     = token_info["access_token"]
        session["refresh_token"]    = token_info.get("refresh_token", "")
        session["token_expires_at"] = time.time() + token_info.get("expires_in", 3600) - 60

        # Fetch user profile so we can display name/avatar in the header
        try:
            me_resp = requests.get(
                "https://api.spotify.com/v1/me",
                headers={"Authorization": f"Bearer {token_info['access_token']}"},
                timeout=10,
            )
            if me_resp.status_code == 200:
                me = me_resp.json()
                session["user_name"]    = me.get("display_name") or me.get("id", "Listener")
                session["user_product"] = me.get("product", "free")
                images = me.get("images", [])
                session["user_image"]   = images[0]["url"] if images else ""
        except Exception:
            pass  # Non-critical – profile display is optional

        return redirect("/?auth=success")

    except Exception as e:
        return f"Callback error: {repr(e)}", 500

# ── Token Endpoint (for Spotify SDK) ────────

@app.route("/api/token")
def api_token():
    token = get_user_token()
    if not token:
        return jsonify({"error": "Not authenticated"}), 401
    return jsonify({
        "access_token" : token,
        "product"      : session.get("user_product", "free"),
    })

# ── User Info ────────────────────────────────

@app.route("/api/me")
def api_me():
    if not session.get("access_token"):
        return jsonify({"logged_in": False})
    return jsonify({
        "logged_in"   : True,
        "name"        : session.get("user_name", "Listener"),
        "image"       : session.get("user_image", ""),
        "product"     : session.get("user_product", "free"),
    })

# ── Logout ──────────────────────────────────

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ── Player Proxy (optional for Spotify Web API control) ─────

@app.route("/api/player", methods=["POST"])
def api_player():
    token = get_user_token()
    if not token:
        return jsonify({"error": "Not authenticated"}), 401

    action  = request.json.get("action")   # play, pause, next, previous, volume
    payload = request.json.get("payload", {})

    endpoints = {
        "play"    : ("PUT",  "https://api.spotify.com/v1/me/player/play"),
        "pause"   : ("PUT",  "https://api.spotify.com/v1/me/player/pause"),
        "next"    : ("POST", "https://api.spotify.com/v1/me/player/next"),
        "previous": ("POST", "https://api.spotify.com/v1/me/player/previous"),
        "volume"  : ("PUT",  "https://api.spotify.com/v1/me/player/volume"),
    }

    if action not in endpoints:
        return jsonify({"error": "Unknown action"}), 400

    method, url = endpoints[action]
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    try:
        params = {}
        body   = None
        if action == "volume":
            params = {"volume_percent": payload.get("volume_percent", 50)}
        elif action == "play" and payload:
            device_id = payload.pop("device_id", None)
            if device_id:
                params["device_id"] = device_id
            if payload:
                body = json.dumps(payload)

        resp = requests.request(method, url, headers=headers, params=params, data=body, timeout=10)

        if resp.status_code in (200, 204):
            return jsonify({"status": "ok"})
        return jsonify({"error": resp.text}), resp.status_code

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─────────────────────────────────────────────
#  EMOTION → SONGS  (browser sends detected emotion)
# ─────────────────────────────────────────────

EMOTION_TO_MOOD = {
    "happy"  : "Party",
    "sad"    : "Sad",
    "angry"  : "Workout",
    "fearful": "Chill",
    "fear"   : "Chill",
    "disgusted": "Sad",
    "surprised": "Party",
    "surprise" : "Party",
    "neutral"  : "Chill",
}

EMOTION_EMOJI = {
    "happy": "😄", "sad": "😢", "angry": "😠",
    "fearful": "😨", "fear": "😨", "disgusted": "🤢",
    "surprised": "😲", "surprise": "😲", "neutral": "😐",
}

@app.route("/api/emotion_songs", methods=["POST"])
def api_emotion_songs():
    data     = request.get_json(force=True)
    emotion  = (data.get("emotion") or "neutral").lower()
    language = data.get("language", "Hindi")
    singer   = data.get("singer", "")
    generation = data.get("generation", "All")
    mood     = EMOTION_TO_MOOD.get(emotion, "Chill")
    emoji    = EMOTION_EMOJI.get(emotion, "😐")
    return jsonify({"mood": mood, "emoji": emoji, "emotion": emotion,
                    "language": language, "singer": singer, "generation": generation})


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────

# Register yt app blueprint
try:
    from yt_app import yt_bp
    app.register_blueprint(yt_bp, url_prefix="/yt")
except Exception as e:
    import traceback
    err_trace = traceback.format_exc()
    print(f"[ERROR] Failed to register yt_bp from yt_app.py:\n{err_trace}")
    
    @app.route("/yt")
    @app.route("/yt/")
    def yt_error():
        return f"<h2>Failed to load YouTube App</h2><p>Please share this error with your developer:</p><pre>{err_trace}</pre>", 500

try:
    from offline_app import offline_bp
    app.register_blueprint(offline_bp)
except Exception as e:
    import traceback
    err_trace = traceback.format_exc()
    print(f"[ERROR] Failed to register offline_bp from offline_app.py:\n{err_trace}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
