# ASCII Video Converter

Client-side ASCII video converter. Convert video files to ASCII art directly in your browser.

## ✨ Features

- 🎥 **Video til ASCII konvertering** - Konverterer enhver videofil til ASCII art
- 🔊 **Lyd support** - Bevarer original lyd fra videoen (moviepy/ffmpeg)
- 🎨 **Justerbare indstillinger** - ASCII bredde, kontrast, font størrelse, karaktersæt
- 🌐 **Web interface** - Modern React frontend med real-time progress
- 🐍 **Python backend** - Server-baseret processing for bedre performance
- 📊 **Real-time logs** - Se conversion progress live

## Quick Start (Serverless – in the browser)

### 1) Start Frontend

```bash
npm install
npm run dev
```

Open the Vite URL (typically http://localhost:5173). Conversion runs 100% in your browser – no backend required.

## 📋 Requirements

### Python Backend
- Python 3.8+
- opencv-python
- pillow
- numpy
- flask
- flask-cors
- moviepy (optional, for audio support)

### Frontend
- Node.js 16+
- React + TypeScript
- Vite

## 🎛️ Indstillinger

- **ASCII Bredde**: 30-120 karakterer (påvirker detaljeniveau)
- **Kontrast**: 0.5-3.0 (justerer ASCII kontrast)
- **Font Størrelse**: 6-16px (størrelse af ASCII tekst i output)
- **Karaktersæt**:
  - Detaljeret: `@%#*+=-:. ` (mange detaljer)
  - Simpel: `█▓▒░ ` (blokke)
  - Blokke: `████▓▓▓▒▒▒░░░   ` (varierende tæthed)
- **Lyd**: Inkluder original lyd (kræver moviepy/ffmpeg)

## 📁 Projekt Struktur

```
project/
├── backend/
│   ├── app.py              # Flask API server
│   ├── start.py            # Setup og starter script
│   ├── requirements.txt    # Python dependencies
│   ├── uploads/           # Uploaded videofiler
│   └── outputs/           # Konverterede ASCII videoer
├── src/
│   ├── App.tsx            # React frontend
│   ├── main.tsx           # React entry point
│   └── styles.css         # Styling
├── index.html             # HTML template
├── package.json           # Node.js dependencies
└── README.md             # Dette dokument
```

## (Optional) Legacy Python backend

Not required anymore. If you want to use it, start it from `backend/` and point the client to the API.

## 🎯 Hvordan Det Virker

1. **Upload**: Videofil uploades til Python backend
2. **Processing**: Backend konverterer hver frame til ASCII art
3. **Rendering**: ASCII frames renderes til video med PIL/OpenCV
4. **Audio**: Original lyd tilføjes med moviepy/ffmpeg
5. **Download**: Færdig ASCII video downloades automatisk

## 🐛 Troubleshooting

### Browser/MediaRecorder issues
- Use a modern browser (Chrome/Edge) – MediaRecorder is required.
- Safari/iOS may restrict recording.

### Ingen lyd i output
- Installér moviepy: `pip install moviepy`
- Eller installér ffmpeg og tilføj til PATH
- Tjek backend logs for audio fejl

### No audio in output
- Ensure the video actually has an audio track.
- Browser must allow audio playback (autoplay might need muted or user interaction).

### Conversion fejler
- Tjek at videofilen er i supporteret format (mp4, avi, mov, etc.)
- Se detaljerede logs i frontend
- Tjek backend console for fejl

## 🎨 Eksempler

### Detaljeret ASCII (anbefalet)
- ASCII Bredde: 80
- Kontrast: 1.5
- Karaktersæt: Detaljeret
- Font: 10px

### Retro Blok Stil
- ASCII Bredde: 60
- Kontrast: 2.0
- Karaktersæt: Blokke
- Font: 12px

### Høj Detalje
- ASCII Bredde: 120
- Kontrast: 1.2
- Karaktersæt: Detaljeret
- Font: 8px

## 📄 Licens

MIT License - Se LICENSE fil for detaljer

## 🤝 Bidrag

Pull requests er velkomne! For større ændringer, åbn først et issue for at diskutere hvad du gerne vil ændre.

