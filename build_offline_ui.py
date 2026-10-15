import os

html_content = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>MoodWave — Offline Local Player</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #1a1a24;
      --panel: rgba(255, 255, 255, 0.05);
      --panel-hover: rgba(255, 255, 255, 0.08);
      --border: rgba(255, 255, 255, 0.1);
      --accent1: #ff6b6b;
      --accent2: #feca57;
      --accent-grad: linear-gradient(135deg, var(--accent1), var(--accent2));
      --text-main: #ffffff;
      --text-muted: #a0a0b0;
      --shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
      --radius: 20px;
      --tr: 0.3s ease;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Outfit', sans-serif; }
    
    body {
      background-color: var(--bg);
      background-image: radial-gradient(circle at 10% 20%, rgba(255, 107, 107, 0.15) 0%, transparent 40%),
                        radial-gradient(circle at 90% 80%, rgba(254, 202, 87, 0.15) 0%, transparent 40%);
      background-attachment: fixed;
      color: var(--text-main);
      height: 100vh;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }

    /* GLASSMORPHISM UTILS */
    .glass {
      background: var(--panel);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
    }

    /* HEADER */
    header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 15px 30px;
      margin: 15px 20px 0;
      z-index: 10;
    }
    
    .logo {
      font-size: 1.5rem;
      font-weight: 800;
      display: flex;
      align-items: center;
      gap: 10px;
      background: var(--accent-grad);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    .logo img { width: 32px; height: 32px; border-radius: 8px; }

    .nav-buttons {
      display: flex;
      gap: 15px;
    }
    
    .nav-btn {
      text-decoration: none;
      color: var(--text-main);
      padding: 10px 20px;
      border-radius: 30px;
      font-weight: 600;
      font-size: 0.9rem;
      border: 1px solid var(--border);
      background: rgba(255,255,255,0.05);
      transition: var(--tr);
      cursor: pointer;
    }
    .nav-btn:hover { background: rgba(255,255,255,0.1); transform: translateY(-2px); }
    .nav-btn.active { background: var(--accent-grad); border: none; color: #000; }

    /* MAIN LAYOUT */
    main {
      flex: 1;
      display: flex;
      gap: 20px;
      padding: 20px;
      overflow: hidden;
    }

    /* LEFT SIDEBAR - FILTERS & WEATHER */
    aside {
      width: 350px;
      display: flex;
      flex-direction: column;
      gap: 20px;
      overflow-y: auto;
    }
    
    /* WEATHER CARD */
    .weather-widget {
      padding: 25px;
      position: relative;
      overflow: hidden;
    }
    .weather-widget::before {
      content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 100%;
      background: var(--accent-grad); opacity: 0.1; z-index: -1;
    }
    .weather-top { display: flex; justify-content: space-between; align-items: flex-start; }
    .w-temp { font-size: 3rem; font-weight: 800; line-height: 1; }
    .w-cond { font-size: 1.2rem; font-weight: 600; color: var(--accent2); margin-top: 5px; }
    .w-mood { margin-top: 15px; font-size: 0.9rem; color: var(--text-muted); }
    .w-mood span { color: var(--text-main); font-weight: 600; }

    /* FILTER SECTION */
    .filter-section {
      padding: 20px;
      display: flex;
      flex-direction: column;
      gap: 20px;
    }
    .filter-group-title {
      font-size: 0.9rem;
      text-transform: uppercase;
      letter-spacing: 1px;
      color: var(--text-muted);
      margin-bottom: 10px;
      font-weight: 600;
    }
    .pill-container {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
    .pill {
      background: rgba(255,255,255,0.05);
      border: 1px solid var(--border);
      color: var(--text-muted);
      padding: 6px 14px;
      border-radius: 20px;
      font-size: 0.85rem;
      cursor: pointer;
      transition: var(--tr);
    }
    .pill:hover { background: rgba(255,255,255,0.1); color: var(--text-main); }
    .pill.active { background: var(--accent-grad); color: #000; border-color: transparent; font-weight: 600; }

    /* RIGHT AREA - PLAYLIST */
    .playlist-area {
      flex: 1;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      padding: 20px;
    }
    .playlist-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;
    }
    .playlist-header h2 { font-size: 1.8rem; font-weight: 800; }
    .track-count { color: var(--text-muted); font-size: 0.9rem; }

    .songs-list {
      flex: 1;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 10px;
      padding-right: 10px;
    }
    .songs-list::-webkit-scrollbar { width: 6px; }
    .songs-list::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.2); border-radius: 10px; }

    .song-item {
      display: flex;
      align-items: center;
      padding: 12px 15px;
      border-radius: 12px;
      background: rgba(255,255,255,0.02);
      border: 1px solid transparent;
      cursor: pointer;
      transition: var(--tr);
      gap: 15px;
    }
    .song-item:hover {
      background: rgba(255,255,255,0.06);
      border-color: var(--border);
    }
    .song-item.playing {
      background: rgba(255, 107, 107, 0.1);
      border-color: var(--accent1);
    }
    
    .song-idx { width: 25px; text-align: center; color: var(--text-muted); font-size: 0.9rem; font-weight: 600; }
    .song-item.playing .song-idx { color: var(--accent1); }
    
    .song-icon {
      width: 45px; height: 45px;
      border-radius: 10px;
      background: rgba(255,255,255,0.05);
      display: flex; justify-content: center; align-items: center;
      color: var(--accent2);
    }
    .song-info { flex: 1; overflow: hidden; }
    .song-title { font-weight: 600; font-size: 1rem; color: var(--text-main); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-bottom: 4px; }
    .song-meta { font-size: 0.8rem; color: var(--text-muted); display: flex; gap: 10px; }
    .meta-tag { background: rgba(255,255,255,0.08); padding: 2px 8px; border-radius: 10px; font-size: 0.7rem; }

    /* BOTTOM PLAYER */
    .player-dock {
      height: 90px;
      margin: 0 20px 20px;
      padding: 0 30px;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    
    .now-playing-info {
      display: flex;
      align-items: center;
      gap: 15px;
      width: 30%;
    }
    .np-icon {
      width: 50px; height: 50px;
      border-radius: 12px;
      background: var(--accent-grad);
      display: flex; justify-content: center; align-items: center;
      box-shadow: 0 4px 15px rgba(255, 107, 107, 0.4);
    }
    .np-text { overflow: hidden; }
    .np-title { font-weight: 800; font-size: 1.1rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .np-artist { font-size: 0.85rem; color: var(--text-muted); }

    .player-controls {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 8px;
    }
    .control-buttons {
      display: flex;
      align-items: center;
      gap: 20px;
    }
    .ctrl-btn {
      background: none; border: none; color: var(--text-muted);
      cursor: pointer; transition: var(--tr);
      display: flex; align-items: center; justify-content: center;
    }
    .ctrl-btn:hover { color: var(--text-main); transform: scale(1.1); }
    .play-btn {
      width: 45px; height: 45px; border-radius: 50%;
      background: var(--text-main); color: var(--bg);
    }
    .play-btn:hover { background: var(--accent2); }

    .progress-container {
      width: 100%; max-width: 500px;
      display: flex; align-items: center; gap: 10px;
      font-size: 0.75rem; color: var(--text-muted);
    }
    .progress-bar {
      flex: 1; height: 6px; background: rgba(255,255,255,0.1);
      border-radius: 3px; cursor: pointer; position: relative;
    }
    .progress-fill {
      position: absolute; top: 0; left: 0; height: 100%; width: 0%;
      background: var(--accent-grad); border-radius: 3px;
    }

    .player-right {
      width: 30%;
      display: flex;
      justify-content: flex-end;
      align-items: center;
      gap: 15px;
    }
    .vol-container {
      display: flex; align-items: center; gap: 8px; width: 120px;
    }
    .vol-bar {
      flex: 1; height: 5px; background: rgba(255,255,255,0.1);
      border-radius: 3px; cursor: pointer; position: relative;
    }
    .vol-fill {
      position: absolute; top: 0; left: 0; height: 100%; width: 100%;
      background: var(--text-main); border-radius: 3px;
    }

    /* EMOTION MODE OVERLAY - UPDATED TO NEW THEME */
    #emo-overlay {
      position: fixed; top: 0; left: 0; width: 100%; height: 100%;
      background: rgba(26, 26, 36, 0.95);
      backdrop-filter: blur(20px);
      z-index: 9999; display: none;
      flex-direction: column; padding: 30px;
    }
    .emo-header {
      display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px;
    }
    .emo-title { font-size: 2rem; font-weight: 800; background: var(--accent-grad); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .close-emo {
      background: rgba(255,255,255,0.1); border: 1px solid var(--border);
      color: white; padding: 10px 20px; border-radius: 30px; cursor: pointer;
    }
    .emo-content {
      display: flex; gap: 30px; flex: 1; overflow: hidden;
    }
    .emo-cam-box {
      flex: 1; background: var(--panel); border: 1px solid var(--border);
      border-radius: var(--radius); display: flex; flex-direction: column; padding: 20px;
    }
    .emo-cam-view {
      flex: 1; background: #000; border-radius: 12px; margin: 15px 0;
      position: relative; overflow: hidden; display: flex; justify-content: center; align-items: center;
    }
    #emo-video { width: 100%; height: 100%; object-fit: cover; display: none; }
    .emo-result-box {
      width: 400px; background: var(--panel); border: 1px solid var(--border);
      border-radius: var(--radius); padding: 30px; display: flex; flex-direction: column; align-items: center; text-align: center;
    }
    .emo-emoji { font-size: 5rem; margin: 20px 0; }
    .emo-mood-text { font-size: 2rem; font-weight: 800; margin-bottom: 10px; color: var(--accent2); text-transform: capitalize; }
    
  </style>
</head>
<body>

  <!-- HEADER -->
  <header class="glass">
    <div class="logo">
      <img src="/static/logo.png" alt="Logo">
      LocalWave
    </div>
    <div class="nav-buttons">
      <button class="nav-btn" onclick="location.href='/'">Spotify Stream</button>
      <button class="nav-btn" onclick="location.href='/yt/'">YouTube Stream</button>
      <button class="nav-btn active">Offline Local</button>
      <button class="nav-btn" style="background: var(--accent-grad); color: #000; border: none; display: flex; align-items: center; gap: 8px;" onclick="openEmotionMode()">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm3.15-5.93C14.17 12.59 13.13 12 12 12c-1.13 0-2.17.59-2.98 1.54-.25.29-.68.32-.96.07-.29-.25-.32-.68-.07-.96C9.07 11.4 10.45 10.5 12 10.5c1.55 0 2.93.9 4.01 2.15.25.28.22.71-.07.96-.28.25-.71.22-.96-.07-.05-.06-.11-.11-.18-.16zM9 8.5C8.17 8.5 7.5 9.17 7.5 10s.67 1.5 1.5 1.5S10.5 10.83 10.5 10 9.83 8.5 9 8.5zm6 0c-.83 0-1.5.67-1.5 1.5s.67 1.5 1.5 1.5 1.5-.67 1.5-1.5-.67-1.5-1.5-1.5z"/></svg>
        AI Emotion Mode
      </button>
    </div>
  </header>

  <main>
    <!-- LEFT SIDEBAR -->
    <aside>
      <div class="weather-widget glass">
        <div class="weather-top">
          <div>
            <div class="w-temp">{{ weather.temp }}&deg;C</div>
            <div class="w-cond">{{ weather.condition }}</div>
          </div>
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="var(--accent2)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v2M12 19v2M5.636 5.636l1.414 1.414M16.95 16.95l1.414 1.414M3 12h2M19 12h2M5.636 18.364l1.414-1.414M16.95 7.05l1.414-1.414"/><circle cx="12" cy="12" r="4"/></svg>
        </div>
        <div class="w-mood">Suggested Mood: <span>{{ suggested_mood }}</span></div>
      </div>

      <form id="filterForm" method="POST" action="/offline" style="display:none;">
        <input type="hidden" name="singer" id="in_singer" value="{{ sel_singer }}">
        <input type="hidden" name="mood" id="in_mood" value="{{ sel_mood }}">
        <input type="hidden" name="lang" id="in_lang" value="{{ sel_lang }}">
        <input type="hidden" name="manual_weather" value="{{ sel_weather }}">
      </form>

      <div class="filter-section glass">
        <div class="filter-group-title">Languages</div>
        <div class="pill-container">
          {% for l in langs %}
            <div class="pill {% if l == sel_lang %}active{% endif %}" onclick="setFilter('lang', '{{ l }}')">{{ l }}</div>
          {% endfor %}
        </div>

        <div class="filter-group-title" style="margin-top:15px;">Singers</div>
        <div class="pill-container">
          {% for s in singers %}
            <div class="pill {% if s == sel_singer %}active{% endif %}" onclick="setFilter('singer', '{{ s }}')">{{ s }}</div>
          {% endfor %}
        </div>

        <div class="filter-group-title" style="margin-top:15px;">Moods</div>
        <div class="pill-container">
          {% for m in moods %}
            <div class="pill {% if m == sel_mood %}active{% endif %}" onclick="setFilter('mood', '{{ m }}')">{{ m }}</div>
          {% endfor %}
        </div>
      </div>
    </aside>

    <!-- RIGHT PLAYLIST -->
    <div class="playlist-area glass">
      <div class="playlist-header">
        <h2>Local Library</h2>
        <div class="track-count">{{ songs|length }} tracks found</div>
      </div>
      
      <div class="songs-list" id="songsList">
        {% for song in songs %}
        <div class="song-item" onclick='playTrack({{ loop.index0 }}, {{ song | tojson }})' id="song-idx-{{ loop.index0 }}">
          <div class="song-idx">{{ loop.index }}</div>
          <div class="song-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18V5l12-2v13"></path><circle cx="6" cy="18" r="3"></circle><circle cx="18" cy="16" r="3"></circle></svg>
          </div>
          <div class="song-info">
            <div class="song-title">{{ song.title }}</div>
            <div class="song-meta">
              <span>{{ song.singer }}</span> &bull; 
              <span class="meta-tag">{{ song.lang }}</span>
              <span class="meta-tag" style="background: rgba(254, 202, 87, 0.15); color: var(--accent2);">{{ song.mood }}</span>
            </div>
          </div>
          <div class="song-action">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" style="opacity:0.6"><path d="M8 5v14l11-7z"/></svg>
          </div>
        </div>
        {% endfor %}
        
        {% if not songs %}
        <div style="text-align: center; padding: 40px; color: var(--text-muted);">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" style="margin-bottom:15px;"><path d="M9 18V5l12-2v13"></path><circle cx="6" cy="18" r="3"></circle><circle cx="18" cy="16" r="3"></circle></svg>
          <p>No tracks matched your filters.<br>Try selecting "All".</p>
        </div>
        {% endif %}
      </div>
    </div>
  </main>

  <!-- BOTTOM PLAYER -->
  <div class="player-dock glass">
    <div class="now-playing-info">
      <div class="np-icon">
        <svg id="np-svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#000" stroke-width="2"><path d="M9 18V5l12-2v13"></path><circle cx="6" cy="18" r="3"></circle><circle cx="18" cy="16" r="3"></circle></svg>
      </div>
      <div class="np-text">
        <div class="np-title" id="pTitle">Ready to play</div>
        <div class="np-artist" id="pArtist">Select a track</div>
      </div>
    </div>
    
    <div class="player-controls">
      <div class="control-buttons">
        <button class="ctrl-btn" onclick="prevSong()"><svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M6 6h2v12H6zm3.5 6l8.5 6V6z"/></svg></button>
        <button class="ctrl-btn play-btn" id="playBtn" onclick="togglePlay()"><svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" id="playIcon"><path d="M8 5v14l11-7z"/></svg></button>
        <button class="ctrl-btn" onclick="nextSong()"><svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M6 18l8.5-6L6 6v12zM16 6v12h2V6h-2z"/></svg></button>
      </div>
      <div class="progress-container">
        <span id="cTime">0:00</span>
        <div class="progress-bar" id="pBar" onclick="seek(event)">
          <div class="progress-fill" id="pFill"></div>
        </div>
        <span id="tTime">0:00</span>
      </div>
    </div>
    
    <div class="player-right">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path></svg>
      <div class="vol-container">
        <div class="vol-bar" id="vBar" onclick="setVol(event)">
          <div class="vol-fill" id="vFill"></div>
        </div>
      </div>
    </div>
  </div>

  <!-- AUDIO ELEMENT -->
  <audio id="audioPlayer"></audio>

  <!-- EMOTION OVERLAY -->
  <div id="emo-overlay">
    <div class="emo-header">
      <div class="emo-title">AI Emotion Detect</div>
      <button class="close-emo" onclick="closeEmotionMode()">Close Mode</button>
    </div>
    <div class="emo-content">
      <div class="emo-cam-box">
        <div style="display:flex; justify-content:space-between; margin-bottom:10px;">
          <h3 style="font-weight:600;">Camera Feed</h3>
          <span id="emo-faces" style="color:var(--accent1); font-weight:600; font-size:0.9rem;">0 faces</span>
        </div>
        <div class="emo-cam-view" id="cam-container">
          <div id="cam-placeholder" style="color:var(--text-muted);">Click Start Camera</div>
          <video id="emo-video" autoplay muted playsinline></video>
        </div>
        <div style="display:flex; gap:10px;">
          <button class="nav-btn active" style="flex:1; text-align:center;" onclick="startEmotionCam()">Start</button>
          <button class="nav-btn" style="flex:1; text-align:center;" onclick="stopEmotionCam()">Stop</button>
        </div>
      </div>
      
      <div class="emo-result-box">
        <h3 style="color:var(--text-muted); font-weight:400; letter-spacing:1px; text-transform:uppercase; font-size:0.9rem;">Detected Mood</h3>
        <div class="emo-emoji" id="emo-emoji">🤔</div>
        <div class="emo-mood-text" id="emo-text">Analyzing...</div>
        <p style="color:var(--text-muted); font-size:0.9rem; margin-bottom:30px;" id="emo-sub">Please look at the camera.</p>
        
        <button class="nav-btn" style="width:100%; padding:15px; background:var(--accent-grad); color:#000; border:none; font-size:1.1rem; display:none;" id="emo-generate-btn" onclick="generateEmotionPlaylist()">
          Play Suggested Tracks
        </button>
      </div>
    </div>
  </div>

  <!-- SCRIPTS -->
  <script src="/static/models/face-api.min.js"></script>
  <script>
    // --- FILTERS ---
    function setFilter(type, val) {
      document.getElementById('in_' + type).value = val;
      document.getElementById('filterForm').submit();
    }

    // --- PLAYER LOGIC ---
    let currentSongs = {{ songs | tojson | safe }};
    let currentIndex = -1;
    const audio = document.getElementById("audioPlayer");
    const playBtn = document.getElementById("playBtn");
    const playIcon = document.getElementById("playIcon");
    const pTitle = document.getElementById("pTitle");
    const pArtist = document.getElementById("pArtist");
    const pFill = document.getElementById("pFill");
    const cTime = document.getElementById("cTime");
    const tTime = document.getElementById("tTime");
    
    function playTrack(idx, songObj) {
      if(!currentSongs || currentSongs.length === 0) return;
      currentIndex = idx;
      let song = songObj || currentSongs[idx];
      
      // Update UI
      document.querySelectorAll('.song-item').forEach(el => el.classList.remove('playing'));
      const activeEl = document.getElementById('song-idx-' + idx);
      if(activeEl) {
        activeEl.classList.add('playing');
        activeEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
      
      pTitle.innerText = song.title;
      pArtist.innerText = song.singer;
      
      audio.src = song.url;
      audio.play().then(() => updatePlayIcon(true)).catch(e => console.error(e));
    }

    function togglePlay() {
      if(currentIndex === -1 && currentSongs.length > 0) { playTrack(0); return; }
      if(audio.paused) { audio.play(); updatePlayIcon(true); }
      else { audio.pause(); updatePlayIcon(false); }
    }
    function nextSong() {
      if(currentSongs.length === 0) return;
      let nx = currentIndex + 1;
      if(nx >= currentSongs.length) nx = 0;
      playTrack(nx);
    }
    function prevSong() {
      if(currentSongs.length === 0) return;
      let pv = currentIndex - 1;
      if(pv < 0) pv = currentSongs.length - 1;
      playTrack(pv);
    }
    
    function updatePlayIcon(isPlaying) {
      if(isPlaying) {
        playIcon.innerHTML = '<path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/>';
      } else {
        playIcon.innerHTML = '<path d="M8 5v14l11-7z"/>';
      }
    }

    audio.addEventListener("timeupdate", () => {
      if(!audio.duration) return;
      const pct = (audio.currentTime / audio.duration) * 100;
      pFill.style.width = pct + "%";
      cTime.innerText = fmtTime(audio.currentTime);
      tTime.innerText = fmtTime(audio.duration);
    });
    audio.addEventListener("ended", nextSong);

    function fmtTime(sec) {
      let m = Math.floor(sec / 60);
      let s = Math.floor(sec % 60);
      return m + ":" + (s<10?'0':'') + s;
    }
    function seek(e) {
      const b = document.getElementById("pBar");
      const r = b.getBoundingClientRect();
      const pct = (e.clientX - r.left) / r.width;
      if(audio.duration) audio.currentTime = pct * audio.duration;
    }
    function setVol(e) {
      const b = document.getElementById("vBar");
      const r = b.getBoundingClientRect();
      let pct = (e.clientX - r.left) / r.width;
      pct = Math.max(0, Math.min(1, pct));
      audio.volume = pct;
      document.getElementById("vFill").style.width = (pct*100) + "%";
    }
    
    // --- AI EMOTION OFFLINE ---
    let emoStream = null;
    let emoInterval = null;
    const video = document.getElementById('emo-video');
    const ph = document.getElementById('cam-placeholder');
    const emoResult = { emoji: '🤔', text: 'Analyzing...', count: 0 };
    let finalEmotion = null;

    async function loadModels() {
      await faceapi.nets.tinyFaceDetector.loadFromUri('/static/models');
      await faceapi.nets.faceExpressionNet.loadFromUri('/static/models');
    }
    loadModels();

    function openEmotionMode() { document.getElementById('emo-overlay').style.display = 'flex'; }
    function closeEmotionMode() { stopEmotionCam(); document.getElementById('emo-overlay').style.display = 'none'; }

    async function startEmotionCam() {
      ph.style.display = 'none';
      video.style.display = 'block';
      document.getElementById('emo-emoji').innerText = '⏳';
      document.getElementById('emo-text').innerText = 'Starting Camera...';
      try {
        emoStream = await navigator.mediaDevices.getUserMedia({ video: true });
        video.srcObject = emoStream;
        
        video.addEventListener('play', () => {
          if(emoInterval) clearInterval(emoInterval);
          emoInterval = setInterval(async () => {
            const detections = await faceapi.detectAllFaces(video, new faceapi.TinyFaceDetectorOptions()).withFaceExpressions();
            document.getElementById('emo-faces').innerText = detections.length + " faces";
            
            if(detections.length > 0) {
              const exps = detections[0].expressions;
              let maxE = 'neutral', maxV = 0;
              for(const [e, v] of Object.entries(exps)) {
                if(v > maxV) { maxV = v; maxE = e; }
              }
              if(maxV > 0.4) {
                finalEmotion = maxE;
                const emap = { happy:'😄', sad:'😢', angry:'😠', fearful:'😨', disgusted:'🤢', surprised:'😲', neutral:'😐' };
                document.getElementById('emo-emoji').innerText = emap[maxE] || '🤔';
                document.getElementById('emo-text').innerText = maxE;
                document.getElementById('emo-sub').innerText = "Confidence: " + Math.round(maxV*100) + "%";
                document.getElementById('emo-generate-btn').style.display = 'block';
              }
            } else {
              document.getElementById('emo-emoji').innerText = '👀';
              document.getElementById('emo-text').innerText = 'No face found';
            }
          }, 500);
        });
      } catch(e) {
        ph.style.display = 'block'; video.style.display = 'none';
        ph.innerText = 'Camera access denied.';
      }
    }

    function stopEmotionCam() {
      if(emoInterval) clearInterval(emoInterval);
      if(emoStream) emoStream.getTracks().forEach(t => t.stop());
      video.style.display = 'none'; ph.style.display = 'block';
      document.getElementById('emo-faces').innerText = "0 faces";
    }

    function generateEmotionPlaylist() {
      if(!finalEmotion) return;
      fetch('/offline/api/emotion_playlist', {
        method: 'POST',
        body: JSON.stringify({ emotion: finalEmotion }),
        headers: { 'Content-Type': 'application/json' }
      })
      .then(r => r.json())
      .then(data => {
        closeEmotionMode();
        currentSongs = data.songs;
        // Rewrite DOM list
        const sl = document.getElementById('songsList');
        sl.innerHTML = currentSongs.map((s,i) => `
          <div class="song-item" onclick='playTrack(${i})' id="song-idx-${i}">
            <div class="song-idx">${i+1}</div>
            <div class="song-icon"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18V5l12-2v13"></path><circle cx="6" cy="18" r="3"></circle><circle cx="18" cy="16" r="3"></circle></svg></div>
            <div class="song-info">
              <div class="song-title">${s.title}</div>
              <div class="song-meta"><span>${s.singer}</span> &bull; <span class="meta-tag">${s.lang}</span><span class="meta-tag" style="background: rgba(254, 202, 87, 0.15); color: var(--accent2);">${s.mood}</span></div>
            </div>
          </div>
        `).join('');
        document.querySelector('.track-count').innerText = "AI " + data.mood + " Playlist (" + currentSongs.length + " tracks)";
        playTrack(0);
      });
    }

    // Auto-init volume
    audio.volume = 0.8;
    document.getElementById("vFill").style.width = "80%";
  </script>
</body>
</html>
"""

with open(r"templates\offline_index.html", "w", encoding="utf-8") as f:
    f.write(html_content)
print("Wrote templates/offline_index.html")
