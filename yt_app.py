import sys
import io
import os

# Load .env file for local development
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Fix Windows Unicode/charmap encoding error (emoji etc.)
if sys.stdout and hasattr(sys.stdout, 'encoding') and sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr and hasattr(sys.stderr, 'encoding') and sys.stderr.encoding and sys.stderr.encoding.lower() != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
os.environ['PYTHONUTF8'] = '1'

from flask import Flask, render_template, request, jsonify
import requests
from datetime import datetime
import calendar
import re
import concurrent.futures

from flask import Blueprint
yt_bp = Blueprint("yt_bp", __name__)

# ===== API KEYS (set these in Render dashboard / .env file) =====
WEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "use your own weather api key").strip()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "use your own yt api key").strip()
# ================================================================

SINGERS = [
    "Arijit Singh", "Shreya Ghoshal", "Atif Aslam", "KK", "Sonu Nigam",
    "Armaan Malik", "Neha Kakkar", "Jubin Nautiyal", "Badshah", "Kishore Kumar"
]

LANGUAGES = ["Hindi", "English", "Tamil", "Telugu", "Marathi", "Punjabi", "Bengali", "Bhojpuri", "Odia"]

CATEGORIES = {
    "All": "song",
    "Romantic": "romantic love song",
    "Sad": "sad emotional song",
    "Chill": "lofi chill relax song",
    "Party": "party dance song",
    "Workout": "workout gym motivation song",
    "Classic": "old classic song",
    "Mix": "songs",
    "Happy": "happy upbeat feel good song",
    "Angry": "intense powerful aggressive song",
    "Calm": "calm peaceful meditation song",
    "Devotional": "devotional bhajan spiritual song",
    "Energetic": "energetic upbeat high energy song",
    "Nostalgic": "nostalgic retro throwback song",
    "Motivational": "motivational inspiring pump up song",
}

GENERATIONS = {
    "All": "",
    "90s": "90s hits",
    "2000s": "2000s hits",
    "GenZ": "genz viral song",
    "New Release": "new released song 2025",
    "Trendy": "trending viral song india"
}

def weather_to_category(weather_data: dict) -> str:
    """
    Same mood logic as the Spotify/Moodwave music project.
    Uses weather condition, time of day (day/night via icon), and temperature.
    """
    try:
        weather_main = weather_data["weather"][0]["main"]
        icon_code    = weather_data["weather"][0]["icon"]
        temp_c       = weather_data["main"]["temp"]   # already in Celsius (units=metric)
    except (KeyError, IndexError):
        return "Chill"

    is_day = 'd' in icon_code

    if weather_main == "Clear":
        if is_day:
            return "Chill" if temp_c > 35 else "Party"
        else:
            return "Romantic"
    elif weather_main == "Clouds":
        return "Chill" if is_day else "Sad"
    elif weather_main in ("Rain", "Drizzle"):
        return "Romantic"
    elif weather_main == "Thunderstorm":
        return "Workout"
    elif weather_main == "Snow":
        return "Classic"
    elif weather_main in ("Mist", "Fog", "Haze"):
        return "Chill" if is_day else "Sad"
    elif weather_main in ("Smoke", "Dust", "Sand", "Ash"):
        return "Sad"
    elif weather_main in ("Squall", "Tornado"):
        return "Workout"
    return "Chill"



# ================= WEATHER HELPERS =================

def season_from_month(month: int) -> str:
    if month in (12, 1, 2):
        return "Winter"
    if month in (3, 4, 5):
        return "Summer"
    if month in (6, 7, 8, 9):
        return "Monsoon"
    return "Autumn"


def season_month_from_weather(w: dict):
    try:
        dt_utc = int(w.get("dt", 0))
        tz = int(w.get("timezone", 0))
        local_dt = datetime.utcfromtimestamp(dt_utc + tz)
        month_num = local_dt.month
    except Exception:
        month_num = datetime.now().month

    month_name = calendar.month_name[month_num]
    return season_from_month(month_num), month_name


def reverse_geocode(lat: float, lon: float) -> str:
    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            "format": "jsonv2",
            "lat": lat,
            "lon": lon,
            "zoom": 18,
            "addressdetails": 1
        }
        r = requests.get(
            url,
            params=params,
            headers={"User-Agent": "weather-music-app/1.0"},
            timeout=15
        )
        data = r.json()
        addr = data.get("address", {}) or {}

        for key in ["neighbourhood", "suburb", "quarter", "hamlet", "village", "town", "city", "county", "state"]:
            if addr.get(key):
                return addr.get(key)

        dn = data.get("display_name")
        if dn:
            return dn.split(",")[0].strip()
    except Exception:
        pass

    return ""


def get_weather(city: str):
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": city, "appid": WEATHER_API_KEY, "units": "metric"}
    return requests.get(url, params=params, timeout=15).json()


def get_weather_by_coords(lat: float, lon: float):
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"lat": lat, "lon": lon, "appid": WEATHER_API_KEY, "units": "metric"}
    return requests.get(url, params=params, timeout=15).json()


def yt_get(url, params):
    try:
        r = requests.get(url, params=params, timeout=12)
        print(f"[YT] HTTP {r.status_code} => {url.split('/')[-1]}")
        data = r.json()
        if "error" in data:
            err = data["error"]
            code = err.get("code", "?")
            msg  = err.get("message", str(err))
            print(f"[ERROR] YouTube API {code}: {msg}")
        return data
    except Exception as e:
        # SSL / network error → treat as quota exceeded so fallback triggers
        print(f"[YT] Network/SSL error: {e} → triggering fallback")
        return {"error": {"code": 403, "message": "quotaExceeded (network error fallback)", "errors": [{"reason": "quotaExceeded"}]}}


def parse_duration_seconds(iso: str) -> int:
    """Parse ISO 8601 duration PT#H#M#S → total seconds."""
    m = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', iso or "")
    if not m:
        return 0
    h = int(m.group(1) or 0)
    mi = int(m.group(2) or 0)
    s = int(m.group(3) or 0)
    return h * 3600 + mi * 60 + s


# ================= UPDATED fetch_songs WITH GENERATION =================

# Sentinel to signal a hard YouTube API error (quota/key)
class _YTError(Exception):
    pass

# ── YouTube InnerTube API (primary fallback — no key, no quota, very reliable) ──
_INNERTUBE_KEY = "AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8"
_INNERTUBE_URL = "https://www.youtube.com/youtubei/v1/search"
_INNERTUBE_HDR = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "X-YouTube-Client-Name": "1",
    "X-YouTube-Client-Version": "2.20240101.00.00",
}

# ── Invidious instances (last resort backup) ──
INVIDIOUS_INSTANCES = [
    "https://invidious.privacyredirect.com",
    "https://inv.nadeko.net",
    "https://yt.artemislena.eu",
]

def _no_api_search(q, target=8):
    """
    Primary fallback: YouTube InnerTube API (no API key, no quota).
    Used internally by YouTube itself — extremely reliable.
    """
    skip_kw = ["interview", "news", "episode", "podcast", "reaction",
               "review", "tutorial", "cricket", "match", "trailer"]

    # ── 1. InnerTube API ──
    try:
        payload = {
            "context": {
                "client": {
                    "clientName": "WEB",
                    "clientVersion": "2.20240101.00.00",
                    "hl": "en",
                    "gl": "IN",
                }
            },
            "query": q,
            "params": "EgIQAQ==",  # filter: videos only
        }
        resp = requests.post(
            _INNERTUBE_URL,
            params={"key": _INNERTUBE_KEY, "prettyPrint": "false"},
            headers=_INNERTUBE_HDR,
            json=payload,
            timeout=12,
        )
        data = resp.json()
        sections = (data.get("contents", {})
                        .get("twoColumnSearchResultsRenderer", {})
                        .get("primaryContents", {})
                        .get("sectionListRenderer", {})
                        .get("contents", []))
        results = []
        for section in sections:
            items = section.get("itemSectionRenderer", {}).get("contents", [])
            for item in items:
                vr = item.get("videoRenderer")
                if not vr:
                    continue
                vid     = vr.get("videoId", "")
                title   = "".join(r.get("text", "") for r in vr.get("title", {}).get("runs", []))
                channel = "".join(r.get("text", "") for r in vr.get("ownerText", {}).get("runs", []))
                if not vid or not title:
                    continue
                if any(kw in title.lower() for kw in skip_kw):
                    continue
                results.append({"video_id": vid, "title": title,
                                "channel": channel, "embeddable": True})
                if len(results) >= target:
                    break
            if len(results) >= target:
                break
        if results:
            print(f"[InnerTube] Found {len(results)} results for: {q}")
            return results
    except Exception as e:
        print(f"[InnerTube] Failed: {e}")

    # ── 2. Invidious (last resort) ──
    for base in INVIDIOUS_INSTANCES:
        try:
            r = requests.get(f"{base}/api/v1/search",
                             params={"q": q, "type": "video", "page": 1},
                             timeout=7)
            if r.status_code == 200:
                results = []
                for it in r.json()[:target]:
                    vid   = it.get("videoId")
                    title = it.get("title", "")
                    if not vid: continue
                    if any(kw in title.lower() for kw in skip_kw): continue
                    results.append({"video_id": vid, "title": title,
                                    "channel": it.get("author", ""), "embeddable": True})
                if results:
                    print(f"[Invidious] Got {len(results)} from {base}")
                    return results
        except Exception as e:
            print(f"[Invidious] {base} failed: {e}")
    return []



def _fetch_single_query(q, target, YOUTUBE_API_KEY, singer, category, generation):
    search_url = "https://www.googleapis.com/youtube/v3/search"
    search_params = {
        "part": "snippet",
        "q": q,
        "key": YOUTUBE_API_KEY,
        "maxResults": 8,
        "type": "video",
        "videoEmbeddable": "true",
        "videoSyndicated": "true",
        "safeSearch": "moderate",
        "regionCode": "IN",
        "order": "viewCount" if generation == "Trendy" else "relevance"
    }

    sdata = yt_get(search_url, search_params)
    if "error" in sdata:
        err  = sdata["error"]
        code = err.get("code", "?")
        msg  = err.get("message", str(err))
        print(f"[YT ERROR] {code}: {msg}")

        # ── Quota exceeded → fallback to no-API search ──
        if code in (403, 429) or "quota" in msg.lower() or "quotaExceeded" in str(err):
            print(f"[Fallback] YouTube quota exceeded — using no-API search for: {q}")
            fallback = _no_api_search(q, target)
            # Attach singer/category/generation metadata
            for s in fallback:
                s["singer"] = singer
                s["category"] = category
                s["generation"] = generation
            return fallback

        raise _YTError(f"YouTube API error {code}: {msg}")

    items = sdata.get("items", [])

    results = []
    for it in items:
        vid = it.get("id", {}).get("videoId")
        if not vid:
            continue

        snippet = it.get("snippet", {})

        # Skip live broadcasts
        if snippet.get("liveBroadcastContent") in ("live", "upcoming"):
            continue

        # Skip obvious non-music content
        title_lower = snippet.get("title", "").lower()
        skip_keywords = ["interview", "news", "episode", "podcast", "reaction", "review", "tutorial", "cricket", "match"]
        if any(kw in title_lower for kw in skip_keywords):
            continue

        results.append({
            "video_id": vid,
            "title": snippet.get("title", ""),
            "channel": snippet.get("channelTitle", ""),
            "singer": singer,
            "category": category,
            "generation": generation,
            "embeddable": True
        })
    return results

def fetch_songs(singer: str, language: str, category: str, generation: str = "All", target: int = 40, exclude_ids: list = None):
    """Returns (list_of_songs, error_string_or_None)."""
    query_tag = CATEGORIES.get(category, "song")
    gen_tag = GENERATIONS.get(generation, "")

    import random

    # Clean inputs
    singer = (singer or "").strip()
    language = (language or "Hindi").strip()

    # Build parts - filter empty tokens to avoid junk queries
    def q(*parts):
        return " ".join(p for p in parts if p and p.strip())

    # Extra suffixes that help get embeddable videos
    suffixes = ["audio", "lyrical video", "full song", "jukebox", "song lyrics", "slowed reverb"]
    random.shuffle(suffixes)

    if singer:
        # Singer-specific queries first, then general
        queries = [
            q(singer, language, query_tag, gen_tag, suffixes[0]),
            q(singer, language, query_tag, gen_tag, "audio"),
            q(singer, query_tag, language, gen_tag, "lyrical video"),
            q(singer, query_tag, gen_tag, suffixes[1]),
            q(query_tag, language, gen_tag, suffixes[2]),
        ]
    else:
        # No singer — use genre/mood + language queries
        queries = [
            q(language, query_tag, gen_tag, suffixes[0]),
            q(query_tag, language, gen_tag, "audio"),
            q(language, query_tag, gen_tag, "lyrical video"),
            q(query_tag, language, gen_tag, suffixes[1]),
            q(language, query_tag, gen_tag, suffixes[2]),
        ]

    # Remove duplicate or empty queries
    queries = list(dict.fromkeys(q for q in queries if len(q) > 5))

    print(f"[fetch_songs] category={category}, language={language}, singer={singer!r}, generation={generation}")
    print(f"[fetch_songs] queries={queries}")

    songs = []
    seen = set(exclude_ids or [])
    yt_error = None  # capture first YouTube API hard error

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_query = {executor.submit(_fetch_single_query, qr, target, YOUTUBE_API_KEY, singer, category, generation): qr for qr in queries}
        for future in concurrent.futures.as_completed(future_to_query):
            try:
                results = future.result()
                for song in results:
                    vid = song["video_id"]
                    if vid not in seen:
                        seen.add(vid)
                        songs.append(song)
                        if len(songs) >= target:
                            return songs, None
            except _YTError as e:
                yt_error = str(e)
                print(f"[ERROR] YouTube API hard error: {e}")
            except Exception as e:
                print(f"[ERROR] Thread execution failed: {e}")

    # If we got a YouTube error and no songs, surface the real error
    if not songs and yt_error:
        return [], yt_error

    return songs, None


# ================= ROUTES =================

@yt_bp.route("", methods=["GET", "POST"])
@yt_bp.route("/", methods=["GET", "POST"])
def home():
    error = None
    playlist = []
    weather_info = None

    selected_language = "Hindi"
    selected_singer = SINGERS[0]
    selected_category = "All"
    selected_generation = "All"

    if request.method == "POST":
        city = request.form.get("city", "").strip()
        lat_str = request.form.get("lat", "").strip()
        lon_str = request.form.get("lon", "").strip()
        selected_language = request.form.get("language", "Hindi").strip()
        selected_singer = request.form.get("singer", SINGERS[0]).strip()
        selected_category = request.form.get("category", "All").strip()
        selected_generation = request.form.get("generation", "All").strip()

        if not city and not (lat_str and lon_str):
            city = "Mumbai"

        w = {}
        if city:
            w = get_weather(city)
        elif lat_str and lon_str:
            try:
                lat = float(lat_str)
                lon = float(lon_str)
                w = get_weather_by_coords(lat, lon)
                city = reverse_geocode(lat, lon) # set city based on GPS
            except ValueError:
                pass

        if "weather" in w:
            weather_main = w["weather"][0]["main"]
            season, month = season_month_from_weather(w)

            weather_info = {
                "city": w.get("name", city) or "Your Location",
                "weather": weather_main,
                "temp": w["main"]["temp"],
                "suggested": weather_to_category(w),
                "season": season,
                "month": month,
            }

            effective_category = selected_category
            if selected_category == "All" and weather_info.get("suggested"):
                effective_category = weather_info["suggested"]

            playlist, yt_err = fetch_songs(
                selected_singer,
                selected_language,
                effective_category,
                selected_generation,
                target=40
            )

            if not playlist:
                if yt_err:
                    # Surface the real YouTube error (quota exceeded, invalid key, etc.)
                    if "quota" in yt_err.lower() or "403" in yt_err:
                        error = "YouTube API quota exceeded. Please try again after midnight (IST) or use a different API key."
                    elif "400" in yt_err or "API key" in yt_err.lower() or "keyInvalid" in yt_err.lower():
                        error = "Invalid YouTube API key. Please check your API key in the .env file."
                    else:
                        error = f"YouTube API error: {yt_err}"
                else:
                    error = "No songs found. Try different filters."
        else:
            error = "City not found / Weather API error."

    return render_template(
        "yt_index.html",
        singers=SINGERS,
        languages=LANGUAGES,
        categories=list(CATEGORIES.keys()),
        generations=list(GENERATIONS.keys()),
        selected_language=selected_language,
        selected_singer=selected_singer,
        selected_category=selected_category,
        selected_generation=selected_generation,
        playlist=playlist,
        weather_info=weather_info,
        error=error,
        year=datetime.now().year
    )


@yt_bp.route("/api/refresh", methods=["POST"])
def api_refresh():
    data = request.get_json(force=True)

    city = (data.get("city") or "").strip()
    singer = data.get("singer", SINGERS[0])
    language = data.get("language", "Hindi")
    category = data.get("category", "All")
    generation = data.get("generation", "All")
    target = int(data.get("target", 40))
    exclude_ids = data.get("exclude_ids", [])

    weather_info = None
    if city:
        w = get_weather(city)
        if "weather" in w:
            weather_main = w["weather"][0]["main"]
            season, month = season_month_from_weather(w)

            weather_info = {
                "city": w.get("name", city),
                "weather": weather_main,
                "temp": w["main"]["temp"],
                "suggested": weather_to_category(w),
                "season": season,
                "month": month,
            }

    effective_category = category
    if category == "All" and weather_info and weather_info.get("suggested"):
        effective_category = weather_info["suggested"]

    songs, yt_err = fetch_songs(singer, language, effective_category, generation, target=target, exclude_ids=exclude_ids)

    result = {"songs": songs, "weather_info": weather_info, "used_category": effective_category}
    if yt_err:
        result["error"] = yt_err
    return jsonify(result)


@yt_bp.route("/api/refresh_coords", methods=["POST"])
def api_refresh_coords():
    data = request.get_json(force=True)

    try:
        lat = float(data.get("lat"))
        lon = float(data.get("lon"))
    except (TypeError, ValueError):
        return jsonify({"songs": [], "weather_info": None, "error": "Invalid coordinates"}), 400

    singer = data.get("singer", SINGERS[0])
    language = data.get("language", "Hindi")
    category = data.get("category", "All")
    generation = data.get("generation", "All")
    target = int(data.get("target", 40))
    exclude_ids = data.get("exclude_ids", [])

    weather_info = None
    w = get_weather_by_coords(lat, lon)

    if "weather" in w:
        weather_main = w["weather"][0]["main"]
        exact_loc = reverse_geocode(lat, lon)
        season, month = season_month_from_weather(w)

        weather_info = {
            "city": w.get("name", "Your Location"),
            "location": exact_loc if exact_loc else w.get("name", "Your Location"),
            "weather": weather_main,
            "temp": w["main"]["temp"],
            "suggested": weather_to_category(w),
            "season": season,
            "month": month,
            "lat": lat,
            "lon": lon
        }

    effective_category = category
    if category == "All" and weather_info and weather_info.get("suggested"):
        effective_category = weather_info["suggested"]

    songs, yt_err = fetch_songs(singer, language, effective_category, generation, target=target, exclude_ids=exclude_ids)

    result = {"songs": songs, "weather_info": weather_info, "used_category": effective_category}
    if yt_err:
        result["error"] = yt_err
    return jsonify(result)


@yt_bp.route("/api/search_yt")
def api_search_yt():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"error": "Query required"}), 400
    search_url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": q,
        "key": YOUTUBE_API_KEY,
        "maxResults": 5,
        "type": "video",
        "videoEmbeddable": "true",
        "videoSyndicated": "true",
        "safeSearch": "moderate",
        "regionCode": "IN",
        "videoDuration": "medium",
    }
    try:
        data = yt_get(search_url, params)
        items = data.get("items", [])
        for it in items:
            vid = it.get("id", {}).get("videoId")
            if vid:
                title = it.get("snippet", {}).get("title", q)
                return jsonify({"video_id": vid, "title": title})
        return jsonify({"error": "No video found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@yt_bp.route("/api/ip_location")
def api_ip_location():
    """Get approximate location from IP address — no browser permission needed."""
    try:
        # Get the real client IP (works behind proxies too)
        client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        if client_ip:
            client_ip = client_ip.split(",")[0].strip()

        # 127.0.0.1 / localhost — use ipapi.co without specifying IP (auto-detects)
        if not client_ip or client_ip in ("127.0.0.1", "localhost", "::1"):
            r = requests.get("https://ipapi.co/json/", timeout=8,
                             headers={"User-Agent": "moodwave-app/1.0"})
        else:
            r = requests.get(f"https://ipapi.co/{client_ip}/json/", timeout=8,
                             headers={"User-Agent": "moodwave-app/1.0"})

        data = r.json()
        lat = data.get("latitude")
        lon = data.get("longitude")
        city = data.get("city", "")

        if lat and lon:
            return jsonify({"lat": lat, "lon": lon, "city": city, "ok": True})
        return jsonify({"ok": False, "error": "Could not determine location"}), 404
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ─────────────────────────────────────────────
#  EMOTION → SONGS  (browser face-api.js sends detected emotion)
# ─────────────────────────────────────────────

EMOTION_TO_MOOD_YT = {
    # face-api.js standard emotions
    "happy"     : "Happy",
    "sad"       : "Sad",
    "angry"     : "Angry",
    "fearful"   : "Calm",
    "fear"      : "Calm",
    "disgusted" : "Sad",
    "surprised" : "Energetic",
    "surprise"  : "Energetic",
    "neutral"   : "Chill",
    # extended moods (manual/extra)
    "excited"   : "Party",
    "calm"      : "Calm",
    "romantic"  : "Romantic",
    "energetic" : "Energetic",
    "tired"     : "Chill",
    "bored"     : "Nostalgic",
    "lonely"    : "Sad",
    "stressed"  : "Calm",
    "motivated" : "Motivational",
    "nostalgic" : "Nostalgic",
    "devotional": "Devotional",
}

EMOTION_EMOJI_YT = {
    "happy"     : "😄",
    "sad"       : "😢",
    "angry"     : "😠",
    "fearful"   : "😨",
    "fear"      : "😨",
    "disgusted" : "🤢",
    "surprised" : "😲",
    "surprise"  : "😲",
    "neutral"   : "😐",
    "excited"   : "🤩",
    "calm"      : "😌",
    "romantic"  : "🥰",
    "energetic" : "⚡",
    "tired"     : "😴",
    "bored"     : "😑",
    "lonely"    : "🥺",
    "stressed"  : "😰",
    "motivated" : "💪",
    "nostalgic" : "🌅",
    "devotional": "🙏",
}

EMOTION_VIBE_YT = {
    "happy"     : "Feeling great! Time to party 🎉",
    "sad"       : "Let the music heal your soul 💙",
    "angry"     : "Channel that energy into the beat! 🔥",
    "fearful"   : "Find your calm with soothing tunes 🌊",
    "fear"      : "Find your calm with soothing tunes 🌊",
    "disgusted" : "Music to lift your spirits 🌈",
    "surprised" : "Full of energy — let's go! ⚡",
    "surprise"  : "Full of energy — let's go! ⚡",
    "neutral"   : "Chill vibes, perfect lo-fi moment 🎵",
    "excited"   : "The crowd is vibing! 🎊",
    "calm"      : "Peace and tranquility for your mind 🧘",
    "romantic"  : "Love is in the air 🌹",
    "energetic" : "Maximum energy mode activated! 💥",
    "tired"     : "Relax and let the music take over 😌",
    "bored"     : "Take a trip down memory lane 🌅",
    "lonely"    : "You're not alone, music is here 💙",
    "stressed"  : "Breathe in, breathe out, let the music flow 🌿",
    "motivated" : "Nothing can stop you now! 🚀",
    "nostalgic" : "Golden memories coming right up 🏆",
    "devotional": "Divine music for the soul 🙏",
}

@yt_bp.route("/api/emotion_songs", methods=["POST"])
def api_emotion_songs():
    data    = request.get_json(force=True)
    emotion = (data.get("emotion") or "neutral").lower()
    mood    = EMOTION_TO_MOOD_YT.get(emotion, "Chill")
    emoji   = EMOTION_EMOJI_YT.get(emotion, "😐")
    vibe    = EMOTION_VIBE_YT.get(emotion, "Music for every mood 🎵")
    return jsonify({"mood": mood, "emoji": emoji, "emotion": emotion, "vibe": vibe})


@yt_bp.route("/api/emotion_playlist", methods=["POST"])
def api_emotion_playlist():
    """
    Dedicated emotion-based playlist endpoint — works WITHOUT city/weather.
    Frontend sends emotion + language + generation => returns songs directly.
    """
    data       = request.get_json(force=True)
    emotion    = (data.get("emotion") or "neutral").lower()
    language   = data.get("language", "Hindi")
    singer     = data.get("singer", "").strip()
    generation = data.get("generation", "All")
    target     = int(data.get("target", 20))
    exclude_ids = data.get("exclude_ids", [])

    mood  = EMOTION_TO_MOOD_YT.get(emotion, "Chill")
    emoji = EMOTION_EMOJI_YT.get(emotion, "😐")
    vibe  = EMOTION_VIBE_YT.get(emotion, "Music for every mood 🎵")

    # If singer is a placeholder, ignore it
    if singer.lower() in ("", "any", "all", "any artist"):
        singer = ""

    songs, yt_err = fetch_songs(
        singer=singer,
        language=language,
        category=mood,
        generation=generation,
        target=target,
        exclude_ids=exclude_ids
    )

    result = {
        "mood"    : mood,
        "emoji"   : emoji,
        "emotion" : emotion,
        "vibe"    : vibe,
        "songs"   : songs,
    }
    if yt_err:
        result["error"] = yt_err
    return jsonify(result)



