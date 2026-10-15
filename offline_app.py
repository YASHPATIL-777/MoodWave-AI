import os, random, hashlib
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, url_for

offline_bp = Blueprint("offline_bp", __name__)

# ─── Singer metadata ───────────────────────────────────────────────────────────
SINGER_META = {
    "A.R. Rahman":       {"lang": "Tamil/Hindi", "moods": ["Energetic","Party","Happy","Motivational"]},
    "Arijit Singh":      {"lang": "Hindi",        "moods": ["Romantic","Sad","Chill","Happy"]},
    "Atif Aslam":        {"lang": "Hindi/Urdu",   "moods": ["Romantic","Sad","Nostalgic","Chill"]},
    "Dua Lipa":          {"lang": "English",       "moods": ["Party","Energetic","Happy","Pop"]},
    "Ed Sheeran":        {"lang": "English",       "moods": ["Romantic","Chill","Sad","Acoustic"]},
    "Jubin Nautiyal":    {"lang": "Hindi",         "moods": ["Romantic","Sad","Devotional","Chill"]},
    "Kishore Kumar":     {"lang": "Hindi",         "moods": ["Classic","Nostalgic","Happy","Romantic"]},
    "Lata Mangeshkar":   {"lang": "Hindi/Marathi", "moods": ["Classic","Devotional","Nostalgic","Romantic"]},
    "Neha Kakkar":       {"lang": "Hindi/Punjabi", "moods": ["Party","Happy","Punjabi","Energetic"]},
    "Shreya Ghoshal":    {"lang": "Hindi/Telugu",  "moods": ["Romantic","Classic","Devotional","Chill"]},
    "Sid Sriram":        {"lang": "Telugu/Tamil",  "moods": ["Romantic","Chill","Sad","South"]},
    "SPB (S.P. Balasubrahmanyam)": {"lang": "Telugu/Tamil/Hindi", "moods": ["Classic","Romantic","Devotional","South"]},
    "Taylor Swift":      {"lang": "English",       "moods": ["Pop","Happy","Breakup","Energetic"]},
    "The Weeknd":        {"lang": "English",       "moods": ["Party","Night","Energetic","Dark"]},
}

# ─── Weather → mood mapping ───────────────────────────────────────────────────
WEATHER_MOOD = {
    "Sunny":   ["Happy","Party","Energetic"],
    "Rainy":   ["Sad","Romantic","Chill","Nostalgic"],
    "Cloudy":  ["Chill","Nostalgic","Classic"],
    "Night":   ["Night","Dark","Chill","Romantic"],
    "Winter":  ["Classic","Chill","Nostalgic","Romantic"],
    "Monsoon": ["Romantic","Sad","Nostalgic","Chill"],
    "Summer":  ["Party","Happy","Energetic","Pop"],
    "Autumn":  ["Classic","Nostalgic","Chill"],
}


# ─── Song name cleanup ────────────────────────────────────────────────────────
def clean_title(filename):
    name = os.path.splitext(filename)[0]
    # remove common suffixes from download sites
    for pat in [" - Djjohal.fm", " (Djjohal.fm)", " (PenduJatt.Com.Se)",
                " (Mr-Punjab.Com)", "-128kb", "_128 Kbps", " 128 Kbps",
                " 320 Kbps", "(PenduJatt.Com.Se)", "SpotiDown.App - ",
                "(MP3.co)", " (1)", " (2)", " (3)"]:
        name = name.replace(pat, "").replace(pat.strip(), "")
    return name.strip().strip("_").strip("-").strip()

def assign_mood(filename, singer_moods):
    t = filename.lower()
    # Keyword mapping for somewhat accurate deterministic moods
    if any(w in t for w in ["sad", "broken", "tear", "cry", "akela", "tanha", "judai", "alone", "miss"]): return "Sad"
    if any(w in t for w in ["love", "heart", "dil", "pyar", "ishq", "romantic", "lover", "meri", "tere", "tum"]): return "Romantic"
    if any(w in t for w in ["party", "dance", "club", "dj", "remix", "beat", "naach", "thug"]): return "Party"
    if any(w in t for w in ["happy", "smile", "joy", "good", "life", "beautiful"]): return "Happy"
    if any(w in t for w in ["night", "dark", "moon", "midnight", "sham", "raat"]): return "Night"
    if any(w in t for w in ["breakup", "ex", "never", "over", "bad", "hate", "sorry"]): return "Breakup"
    if any(w in t for w in ["bhagwan", "ram", "krishna", "allah", "god", "prayer", "bhakti", "shree", "om"]): return "Devotional"
    
    # Fallback to deterministic hash so the mood is always the same for the same file
    idx = int(hashlib.md5(filename.encode()).hexdigest(), 16) % len(singer_moods)
    return singer_moods[idx]

# ─── Build song library from static/audio ────────────────────────────────────
def scan_songs(filter_singer=None, filter_mood=None, filter_lang=None):
    audio_dir = os.path.join("static", "audio")
    songs = []
    if not os.path.exists(audio_dir):
        return songs
    for singer in sorted(os.listdir(audio_dir)):
        singer_path = os.path.join(audio_dir, singer)
        if not os.path.isdir(singer_path):
            continue
        meta = SINGER_META.get(singer, {"lang": "Unknown", "moods": ["Chill"]})
        if filter_singer and filter_singer != "All" and filter_singer != singer:
            continue
        if filter_lang and filter_lang != "All" and filter_lang not in meta["lang"]:
            # partial match
            if not any(filter_lang.lower() in l.lower() for l in meta["lang"].split("/")):
                continue
        for f in sorted(os.listdir(singer_path)):
            if not f.lower().endswith(('.mp3', '.wav', '.m4a')):
                continue
            rel = f"audio/{singer}/{f}".replace("\\", "/")
            mood = assign_mood(f, meta["moods"])
            if filter_mood and filter_mood != "All":
                if filter_mood != mood:
                    continue
            songs.append({
                "id":     rel,
                "url":    f"/static/{rel}",
                "title":  clean_title(f),
                "singer": singer,
                "lang":   meta["lang"],
                "mood":   mood,
                "moods":  meta["moods"],
            })
    return songs

def get_all_singers():
    audio_dir = os.path.join("static", "audio")
    if not os.path.exists(audio_dir):
        return []
    return sorted([d for d in os.listdir(audio_dir) if os.path.isdir(os.path.join(audio_dir, d))])

def get_all_moods():
    moods = set()
    for m in SINGER_META.values():
        moods.update(m["moods"])
    return sorted(moods)

def get_all_langs():
    langs = set()
    for m in SINGER_META.values():
        for l in m["lang"].split("/"):
            langs.add(l.strip())
    return sorted(langs)

def mock_weather(manual=None):
    now   = datetime.now()
    hour  = now.hour
    month = now.month
    if manual and manual != "Auto":
        cond = manual
    elif not (6 <= hour <= 18):
        cond = "Night"
    elif month in (12, 1, 2):
        cond = "Winter"
    elif month in (6, 7, 8, 9):
        cond = "Monsoon"
    elif month in (3, 4, 5):
        cond = "Summer"
    else:
        cond = "Cloudy"
    temps = {"Sunny":34,"Rainy":22,"Cloudy":26,"Night":20,"Winter":14,"Monsoon":25,"Summer":38,"Autumn":23}
    return {"condition": cond, "temp": temps.get(cond, 26), "suggested_moods": WEATHER_MOOD.get(cond, ["Chill"])}

# ──────────────────────────────────────────────────────────────────────────────
@offline_bp.route("/offline", methods=["GET", "POST"])
def offline_home():
    manual_weather = request.form.get("manual_weather", "Auto")
    f_singer = request.form.get("singer", "All")
    f_mood   = request.form.get("mood", "All")
    f_lang   = request.form.get("lang", "All")

    weather  = mock_weather(manual_weather)
    # Determine actual mood filter based on user selection
    suggested_mood = weather["suggested_moods"][0]
    
    if f_mood == "All":
        actual_mood_filter = None
    elif f_mood == "Weather Match":
        actual_mood_filter = suggested_mood
    else:
        actual_mood_filter = f_mood

    songs = scan_songs(
        filter_singer = f_singer if f_singer != "All" else None,
        filter_mood   = actual_mood_filter,
        filter_lang   = f_lang   if f_lang   != "All" else None,
    )

    return render_template(
        "offline_index.html",
        songs         = songs,
        weather       = weather,
        singers       = ["All"] + get_all_singers(),
        moods         = ["All", "Weather Match"] + get_all_moods(),
        langs         = ["All"] + get_all_langs(),
        sel_singer    = f_singer,
        sel_mood      = f_mood,
        sel_lang      = f_lang,
        sel_weather   = manual_weather,
        suggested_mood= suggested_mood,
        year          = datetime.now().year,
    )

@offline_bp.route("/offline/api/songs")
def offline_api_songs():
    f_singer = request.args.get("singer", "All")
    f_mood   = request.args.get("mood",   "All")
    f_lang   = request.args.get("lang",   "All")
    f_weather= request.args.get("weather", "Auto")

    if f_mood == "All":
        actual_mood_filter = None
    elif f_mood == "Weather Match":
        actual_mood_filter = mock_weather(f_weather)["suggested_moods"][0]
    else:
        actual_mood_filter = f_mood

    songs = scan_songs(
        filter_singer = f_singer if f_singer != "All" else None,
        filter_mood   = actual_mood_filter,
        filter_lang   = f_lang   if f_lang   != "All" else None,
    )
    return jsonify(songs)

@offline_bp.route("/offline/api/weather_songs")
def offline_weather_songs():
    condition = request.args.get("condition", "Sunny")
    moods = WEATHER_MOOD.get(condition, ["Chill"])
    all_songs = scan_songs()
    playlist  = [s for s in all_songs if any(m in s["moods"] for m in moods)]
    random.shuffle(playlist)
    return jsonify({"condition": condition, "moods": moods, "songs": playlist[:20]})

# keep compat
@offline_bp.route("/offline/api/refresh", methods=["POST"])
def offline_refresh():
    weather = mock_weather()
    songs   = scan_songs()
    return jsonify({"songs": songs, "weather": weather})
