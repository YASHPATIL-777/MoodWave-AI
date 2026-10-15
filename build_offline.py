with open("templates/offline_index.html", "r", encoding="utf-8") as f:
    html = f.read()

# 1. Change Title
html = html.replace("<title>MoodWave — YouTube Player</title>", "<title>MoodWave — Offline Local Player</title>")
html = html.replace("MoodWave YouTube Player", "MoodWave Offline Player")

# 2. Add Offline Mode to the top bar
sp_btn_html = """    <a href="/" class="sp-btn" title="Spotify Mode" style="background:linear-gradient(135deg, #1db954, #18a845);">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="#000"><path d="M12 2C6.4 2 2 6.4 2 12s4.4 10 10 10 10-4.4 10-10S17.6 2 12 2zm4.6 14.4c-.2.3-.5.4-.8.2-2.2-1.3-4.9-1.6-8.1-.9-.3.1-.7-.1-.8-.4-.1-.3.1-.7.4-.8 3.5-.8 6.5-.4 9 1.1.3.2.4.5.3.8zm1.1-2.4c-.2.4-.7.5-1 .3-2.5-1.6-6.4-2.1-9.3-1.1-.4.1-.8-.1-.9-.5-.1-.4.1-.8.5-.9 3.4-1.1 7.7-.5 10.5 1.2.3.1.5.6.2 1zm.1-2.5c-3-1.8-8.1-2-11-1.1-.5.1-.9-.2-1.1-.6-.1-.5.2-.9.6-1.1 3.4-1 9-1 12.5 1.1.4.2.6.7.4 1.1-.2.5-.8.6-1.4.6z"/></svg>
      Spotify Mode
    </a>"""

new_btns = """    <div style="display:flex;gap:10px;">
      <a href="/yt" class="sp-btn" title="YouTube Mode" style="background:linear-gradient(135deg, #ff0000, #cc0000); color:white;">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="white"><path d="M19.615 3.184c-3.604-.246-11.631-.245-15.23 0-3.897.266-4.356 2.62-4.385 8.816.029 6.185.484 8.549 4.385 8.816 3.6.245 11.626.246 15.23 0 3.897-.266 4.356-2.62 4.385-8.816-.029-6.185-.484-8.549-4.385-8.816zm-10.615 12.816v-8l8 3.993-8 4.007z"/></svg>
        YouTube
      </a>
      <a href="/" class="sp-btn" title="Spotify Mode" style="background:linear-gradient(135deg, #1db954, #18a845);">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="#000"><path d="M12 2C6.4 2 2 6.4 2 12s4.4 10 10 10 10-4.4 10-10S17.6 2 12 2zm4.6 14.4c-.2.3-.5.4-.8.2-2.2-1.3-4.9-1.6-8.1-.9-.3.1-.7-.1-.8-.4-.1-.3.1-.7.4-.8 3.5-.8 6.5-.4 9 1.1.3.2.4.5.3.8zm1.1-2.4c-.2.4-.7.5-1 .3-2.5-1.6-6.4-2.1-9.3-1.1-.4.1-.8-.1-.9-.5-.1-.4.1-.8.5-.9 3.4-1.1 7.7-.5 10.5 1.2.3.1.5.6.2 1zm.1-2.5c-3-1.8-8.1-2-11-1.1-.5.1-.9-.2-1.1-.6-.1-.5.2-.9.6-1.1 3.4-1 9-1 12.5 1.1.4.2.6.7.4 1.1-.2.5-.8.6-1.4.6z"/></svg>
        Spotify
      </a>
    </div>"""
html = html.replace(sp_btn_html, new_btns)

# 3. Change YouTube specific text to Offline
html = html.replace('<div class="yt-badge"><div class="yt-icon"><svg', '<div class="yt-badge" style="border-color:#3cf0ff"><div class="yt-icon" style="color:#3cf0ff"><svg')
html = html.replace('YouTube Player</div>', 'Offline Mode</div>')

# 4. Remove Live Location features
form_original = """      <div class="form-body">
        <div class="row2">
          <div class="fg">
            <label class="fl" for="city">City Name</label>
            <input type="text" id="city" name="city" placeholder="e.g. Mumbai" value="{{ weather_info.location if weather_info and weather_info.location else (weather_info.city if weather_info else '') }}" />
          </div>
          <div class="fg" style="justify-content: flex-end;">
            <button type="button" id="locbtn-yt" onclick="useMyLocation()">
              &#x1F4E1; Live Location
            </button>
          </div>
        </div>

        <input type="hidden" id="lat" name="lat" />
        <input type="hidden" id="lon" name="lon" />"""

form_new = """      <div class="form-body">
        <div class="row2">
          <div class="fg" style="grid-column: span 2;">
            <label class="fl" for="manual_weather">Simulate Weather</label>
            <select id="manual_weather" name="manual_weather">
              <option value="Auto">Auto (Clock-based)</option>
              <option value="Sunny">Sunny</option>
              <option value="Rainy">Rainy</option>
              <option value="Cloudy">Cloudy</option>
            </select>
          </div>
        </div>"""
html = html.replace(form_original, form_new)

# 5. Change video player div to HTML5 Audio
yt_player_html = '<div id="player"></div>'
audio_player_html = '<audio id="offline-player" controls style="width:100%; position:absolute; bottom:20px; left:0; padding:0 20px; z-index:10;"></audio>'
html = html.replace(yt_player_html, audio_player_html)

# 6. Change JS player logic
yt_script_html = """    // ── Load YouTube IFrame API ────────────────────────────────────────────────
    const ytTag = document.createElement("script");
    ytTag.src = "https://www.youtube.com/iframe_api";
    document.body.appendChild(ytTag);"""
html = html.replace(yt_script_html, "")

# 7. Change playByIndex logic
play_by_index_old = """    function playByIndex(idx) {
      if (idx < 0 || idx >= songs.length) return;
      currentIndex = idx;
      if (isReady && player) {
        const sid = songs[idx].id;
        try { player.loadVideoById(sid); } catch (e) { }
      }
      updateActiveSong();
    }"""
play_by_index_new = """    function playByIndex(idx) {
      if (idx < 0 || idx >= songs.length) return;
      currentIndex = idx;
      const audio = document.getElementById("offline-player");
      if (audio) {
        audio.src = songs[idx].url;
        audio.play().catch(e => console.error("Playback failed:", e));
      }
      updateActiveSong();
    }"""
html = html.replace(play_by_index_old, play_by_index_new)

# 8. Load Models Locally
html = html.replace("'https://cdn.jsdelivr.net/npm/@vladmandic/face-api/model/'", "'/static/models/'")
html = html.replace("https://cdn.jsdelivr.net/npm/@vladmandic/face-api/dist/face-api.min.js", "/static/js/face-api.min.js")
html = html.replace("/yt/api/emotion_playlist", "/offline/api/emotion_playlist")
html = html.replace("/yt/api/refresh", "/offline/api/refresh")

# Fix form action
html = html.replace('action="/yt"', 'action="/offline"')

with open("templates/offline_index.html", "w", encoding="utf-8") as f:
    f.write(html)
