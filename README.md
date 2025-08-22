# 🎬 ASCII Video Converter

Python-baseret ASCII video converter med React frontend. Konverterer videofiler til ASCII art videoer med original lyd support!

## ✨ Features

- 🎥 **Video til ASCII konvertering** - Konverterer enhver videofil til ASCII art
- 🔊 **Lyd support** - Bevarer original lyd fra videoen (moviepy/ffmpeg)
- 🎨 **Justerbare indstillinger** - ASCII bredde, kontrast, font størrelse, karaktersæt
- 🌐 **Web interface** - Modern React frontend med real-time progress
- 🐍 **Python backend** - Server-baseret processing for bedre performance
- 📊 **Real-time logs** - Se conversion progress live

## 🚀 Quick Start

### 1. Start Python Backend

```bash
cd backend
python start.py
```

Starter scriptet vil:
- Tjekke Python version (3.8+ påkrævet)
- Installere nødvendige packages automatisk
- Oprette nødvendige directories
- Starte Flask server på port 5000

### 2. Start Frontend

```bash
npm install
npm run dev
```

Frontend kører på: http://localhost:5174/

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

## 🔧 API Endpoints

- `GET /api/health` - Backend status og audio support
- `POST /api/upload` - Upload videofil
- `POST /api/convert` - Start ASCII konvertering
- `GET /api/status/{job_id}` - Hent conversion status
- `GET /api/download/{job_id}` - Download konverteret video
- `GET /api/logs/{job_id}` - Hent detaljerede logs

## 🎯 Hvordan Det Virker

1. **Upload**: Videofil uploades til Python backend
2. **Processing**: Backend konverterer hver frame til ASCII art
3. **Rendering**: ASCII frames renderes til video med PIL/OpenCV
4. **Audio**: Original lyd tilføjes med moviepy/ffmpeg
5. **Download**: Færdig ASCII video downloades automatisk

## 🐛 Troubleshooting

### Backend starter ikke
- Tjek at Python 3.8+ er installeret
- Kør `python backend/start.py` for automatisk setup
- Installér packages manuelt: `pip install -r backend/requirements.txt`

### Ingen lyd i output
- Installér moviepy: `pip install moviepy`
- Eller installér ffmpeg og tilføj til PATH
- Tjek backend logs for audio fejl

### Frontend kan ikke forbinde
- Tjek at backend kører på port 5000
- Åbn http://localhost:5000/api/health i browser
- Tjek CORS indstillinger

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

