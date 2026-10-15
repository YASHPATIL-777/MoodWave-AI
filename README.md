# 🎵 MOOD-WAVE

A powerful, intelligent web application that recommends and plays music based on your facial expressions and local weather conditions. 

MoodWave seamlessly blends cloud streaming (Spotify & YouTube) with a completely self-contained **Offline Mode** that utilizes built-in AI emotion tracking and a local music library.

## ✨ Features

- **🌩️ Weather-Based Intelligence:** Automatically detects your local weather, season, and time of day to curate the perfect musical vibe.
- **🤖 Offline Facial AI:** Built-in `face-api.js` Neural Network runs entirely on your local machine to detect your mood via webcam and generate custom playlists—zero internet required.
- **☁️ Cloud Integrations:** Connects directly to YouTube and Spotify APIs for endless online streaming.
- **🎧 True Offline Mode:** A fully self-contained local player. No Wi-Fi? No problem. The offline mode scans your local library, analyzes song titles, and strictly filters music by Singers, Moods, and Languages.
- **🎨 Glassmorphism UI:** A sleek, modern, dynamic user interface built from scratch without bulky CSS frameworks.

## 🚀 How to Run Locally

### 1. Clone the Repository
```bash
git clone https://github.com/Ranjitpatra26/MOOD-WAVE.git
cd MOOD-WAVE
```

### 2. Install Dependencies
Ensure you have Python installed, then run:
```bash
pip install -r requirements.txt
```
*(If `requirements.txt` is not yet generated, you will need `flask`, `requests`, `python-dotenv`, and `spotipy`)*

### 3. Setup Environment Variables
Create a `.env` file in the root directory and add your API keys. **Never commit this file to GitHub!**
```env
OPENWEATHERMAP_API_KEY=your_key_here
YOUTUBE_API_KEY=your_key_here
SPOTIPY_CLIENT_ID=your_key_here
SPOTIPY_CLIENT_SECRET=your_key_here
SPOTIPY_REDIRECT_URI=http://localhost:5000/callback
```

### 4. Start the Application
Run the startup script:
```bash
START_MOODWAVE.bat
```
*(Or manually run `python run_all.py`)*

The server will start on `http://127.0.0.1:5000`. 
To access the True Offline mode, navigate directly to `http://127.0.0.1:5000/offline`.

## 📂 Project Structure
- `/app.py` - The main Flask server handling online API routing.
- `/offline_app.py` - The dedicated server logic for the Offline Mode and local music scanning.
- `/templates/` - HTML files for the UI.
- `/static/audio/` - Your local MP3 library (organized by Singer).
- `/static/models/` - The neural network weights for the offline Face AI.

---
*Built with ❤️ for music lovers.*
