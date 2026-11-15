# 🚀 YouTube to Instagram Reels Automation — AI Skill

A self-contained, production-grade AI workflow that automates the repurposing of YouTube videos into high-retention 9:16 Instagram Reels.

Developed for content creators, agencies, social media managers, and autonomous AI agents.

---

## 📦 What's Inside This Package

```
reels-pipeline-skill/
├── SKILL.md                 # Agent operational specification & prompt rules
├── README.md                # Quickstart and package overview
├── requirements.txt         # Complete Python dependencies
├── .env.example             # Clean configuration template
├── Dockerfile               # Container deployment specification
├── docker-compose.yml       # Multi-service container orchestration
├── pytest.ini               # Test configuration
├── app/                     # Modular backend architecture
│   ├── config.py            # Pydantic Settings
│   ├── database.py          # SQLAlchemy ORM
│   ├── main.py              # FastAPI server & Dashboard
│   ├── api/                 # REST API endpoints
│   ├── dashboard/           # Tailwind + Alpine.js Web UI
│   ├── models/              # Database models
│   ├── schemas/             # Pydantic validation schemas
│   └── services/            # Ingestion, Transcription, AI, CV, QC, Publishing
├── scripts/
│   ├── healthcheck.py       # Diagnostic verification tool
│   ├── run_pipeline.py      # Standalone single-video CLI runner
│   └── migrate_existing.py  # 30-40 video channel batch migration
├── references/              # Detailed guides & API documentation
│   ├── API_REFERENCE.md
│   ├── CONFIGURATION.md
│   ├── META_GRAPH_API_GUIDE.md
│   └── GOOGLE_DRIVE_SETUP.md
├── examples/                # Real sample inputs & output payloads
│   ├── sample_ai_decision.json
│   ├── sample_clip_metadata.json
│   ├── sample_transcript.json
│   └── sample_post_response.json
└── tests/                   # 13 comprehensive automated test suites
```

---

## ⚡ Quick Start in 3 Steps

### 1. Install Dependencies
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Verify System
```bash
python scripts/healthcheck.py
```

### 3. Run Your First Video
```bash
# Process via CLI directly:
python scripts/run_pipeline.py --video "https://www.youtube.com/watch?v=YOUR_VIDEO_ID" --style smart_face_track

# Or start the Web Dashboard:
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
# Visit: http://localhost:8000
```

---

## 🧪 Run Tests
```bash
pytest -v
```

---

## 📄 License
MIT License.
