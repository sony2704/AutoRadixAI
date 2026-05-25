# AutoRadixAI 🧠

> **AI-powered Core Radiology Intelligence Platform** — Automates medical imaging workflows end-to-end.

*Auto → AI-driven automation · Radix → Latin for "root/core" · AI → Intelligence*

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                          AutoRadixAI                            │
│                                                                  │
│  ┌──────────────┐    ┌─────────────────────────────────────┐   │
│  │   Frontend   │    │           Backend (FastAPI)          │   │
│  │  Next.js 15  │◄──►│                                     │   │
│  │  TailwindCSS │    │  ┌──────────────────────────────┐   │   │
│  │  Cornerstone │    │  │      8 AI Agents              │   │   │
│  └──────────────┘    │  │  1. File Identifier           │   │   │
│                       │  │  2. DICOM Anonymizer          │   │   │
│  ┌──────────────┐    │  │  3. Feature Extractor         │   │   │
│  │ Celery Queue │◄──►│  │  4. Model Matcher             │   │   │
│  │  (Redis)     │    │  │  5. Preprocessing Advisor     │   │   │
│  └──────────────┘    │  │  6. Inference Engine          │   │   │
│                       │  │  7. Explainability Engine     │   │   │
│  ┌──────────────┐    │  │  8. Report Generator          │   │   │
│  │  PostgreSQL  │◄──►│  └──────────────────────────────┘   │   │
│  └──────────────┘    └─────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌────────────────┐   │
│  │   Orthanc    │    │    MinIO     │    │  PyTorch/MONAI │   │
│  │  PACS/WADO   │    │  S3 Storage  │    │  AI Models     │   │
│  └──────────────┘    └──────────────┘    └────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
medical-ai-platform/
├── backend/
│   ├── app/
│   │   ├── main.py                   # FastAPI app factory
│   │   ├── config.py                 # Settings (pydantic-settings)
│   │   ├── dependencies.py           # DI: DB session, auth
│   │   ├── api/v1/
│   │   │   ├── router.py             # API v1 aggregator
│   │   │   └── routes/
│   │   │       ├── auth.py           # JWT login/register
│   │   │       ├── upload.py         # DICOM/ZIP/batch upload
│   │   │       ├── studies.py        # Study CRUD
│   │   │       ├── inference.py      # AI inference trigger/status
│   │   │       ├── reports.py        # Report generation/download
│   │   │       └── websocket.py      # Real-time WS updates
│   │   ├── agents/
│   │   │   ├── file_identifier_agent.py      # Agent 1
│   │   │   ├── anonymizer_agent.py           # Agent 2
│   │   │   ├── feature_extraction_agent.py   # Agent 3
│   │   │   ├── model_matcher_agent.py        # Agent 4
│   │   │   ├── preprocessing_agent.py        # Agent 5
│   │   │   ├── inference_agent.py            # Agent 6
│   │   │   ├── explainability_agent.py       # Agent 7
│   │   │   └── report_agent.py               # Agent 8
│   │   ├── core/
│   │   │   ├── security.py           # JWT, password hashing
│   │   │   ├── logging_config.py     # JSON structured logging
│   │   │   ├── exceptions.py         # Exception hierarchy
│   │   │   └── middleware.py         # Audit, security headers
│   │   ├── models/                   # SQLAlchemy ORM models
│   │   ├── repositories/             # DB access layer
│   │   ├── services/                 # Business logic
│   │   └── workers/                  # Celery tasks
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── app/                      # Next.js App Router pages
│   │   │   ├── page.tsx              # Landing page
│   │   │   ├── dashboard/page.tsx    # Main dashboard
│   │   │   ├── upload/page.tsx       # Upload interface
│   │   │   └── viewer/page.tsx       # DICOM viewer
│   │   ├── components/
│   │   │   ├── layout/               # Sidebar, Header
│   │   │   ├── dashboard/            # Stats, charts, queues
│   │   │   ├── upload/               # Drop zone, progress
│   │   │   └── viewer/               # Cornerstone.js viewer
│   │   ├── hooks/                    # useUpload, useInference
│   │   ├── lib/                      # API client (Axios)
│   │   └── store/                    # Zustand auth store
│   ├── package.json
│   ├── tailwind.config.ts
│   └── Dockerfile
│
├── docker/
│   └── docker-compose.yml            # Full-stack compose
│
├── kubernetes/
│   └── deployment.yaml               # K8s manifests + HPA
│
├── tests/
│   ├── conftest.py                   # Fixtures, DICOM generators
│   ├── unit/                         # Per-agent unit tests
│   └── api/                          # Integration API tests
│
└── pytest.ini
```

---

## Quick Start

### Option A: Docker Compose (Recommended)

```bash
# 1. Clone the workspace
cd "f:/AutoRadix AI/medical-ai-platform"

# 2. Copy environment file
cp backend/.env.example backend/.env
# Edit backend/.env — at minimum change SECRET_KEY

# 3. Start all services
docker compose -f docker/docker-compose.yml up --build

# Services started:
#   http://localhost:3000   — Frontend (Next.js)
#   http://localhost:8000   — Backend API
#   http://localhost:8000/api/docs — Swagger UI
#   http://localhost:5555   — Celery Flower (monitoring)
#   http://localhost:5432   — PostgreSQL
#   http://localhost:6379   — Redis
```

### Option B: Local Development

**Backend:**
```bash
cd medical-ai-platform/backend

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate       # Windows
source .venv/bin/activate    # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env

# Start PostgreSQL and Redis (Docker)
docker run -d --name pg -e POSTGRES_USER=autoradix -e POSTGRES_PASSWORD=autoradix -e POSTGRES_DB=autoradixai -p 5432:5432 postgres:16-alpine
docker run -d --name redis -p 6379:6379 redis:7-alpine

# Start API server
uvicorn app.main:app --reload --port 8000

# Start Celery worker (new terminal)
celery -A app.workers.celery_app worker -Q inference,processing,reporting -c 4 --loglevel=info
```

**Frontend:**
```bash
cd medical-ai-platform/frontend

npm install
npm run dev
# → http://localhost:3000
```

### Option C: With PACS (Orthanc)
```bash
docker compose -f docker/docker-compose.yml --profile pacs up --build
# Orthanc PACS: http://localhost:8042
```

---

## AI Agents

| # | Agent | Responsibility | Key Libraries |
|---|-------|---------------|---------------|
| 1 | **File Identifier** | Detect type, validate DICOM, organize studies/series | pydicom |
| 2 | **Anonymizer** | Remove PHI per DICOM PS3.15 Annex E | pydicom |
| 3 | **Feature Extractor** | Radiomics: mean, std, GLCM, LBP, shape | numpy, scikit-image, OpenCV |
| 4 | **Model Matcher** | Route images to correct AI pipeline | dynamic registry |
| 5 | **Preprocessing Advisor** | Recommend windowing, resize, denoise, normalize | domain rules |
| 6 | **Inference Engine** | Run PyTorch/MONAI models, GPU/CPU | torch, monai |
| 7 | **Explainability** | GradCAM heatmaps, saliency maps | torch, OpenCV, PIL |
| 8 | **Report Generator** | Structured JSON/HTML/PDF reports | jinja2, weasyprint |

---

## API Documentation

After starting the server, visit:
- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/auth/register` | Register new user |
| `POST` | `/api/v1/auth/token` | Login → JWT tokens |
| `POST` | `/api/v1/upload/dicom` | Upload DICOM/ZIP/PNG |
| `POST` | `/api/v1/upload/batch` | Batch upload (≤100 files) |
| `GET`  | `/api/v1/studies` | List all studies |
| `GET`  | `/api/v1/studies/{id}` | Get study details |
| `POST` | `/api/v1/inference/run` | Trigger AI inference |
| `GET`  | `/api/v1/inference/status/{id}` | Poll inference status |
| `POST` | `/api/v1/reports/generate` | Generate AI report |
| `GET`  | `/api/v1/reports/download/{id}` | Download report (JSON/HTML/PDF) |
| `WS`   | `/api/v1/ws/inference/{study_id}` | Real-time inference progress |

---

## Supported Modalities & AI Pipelines

| Input | Body Part | AI Task | Model |
|-------|-----------|---------|-------|
| CT | Lung/Chest | Nodule Detection | `ct_lung_nodule_detection` |
| CT | Brain/Head | Tumor Segmentation | `brain_tumor_segmentation` |
| CT | Abdomen/Liver | Liver Segmentation | `ct_liver_segmentation` |
| MR | Brain | Tumor Segmentation | `brain_tumor_segmentation` |
| CR/DX | Chest | Pneumonia Detection | `chest_xray_pneumonia` |
| Any | Any | General Classification | `generic_classification` |

---

## Running Tests

```bash
cd medical-ai-platform

# Install test dependencies
pip install -r backend/requirements.txt

# Run all tests
pytest tests/ -v

# Run unit tests only
pytest tests/unit/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific agent tests
pytest tests/unit/test_file_identifier_agent.py -v
```

---

## Security

- **Authentication**: JWT (HS256) with access + refresh tokens
- **Authorization**: Role-based (admin, radiologist, clinician, researcher, viewer)
- **DICOM Anonymization**: PS3.15 Annex E Basic Application Level Confidentiality
- **Audit Trails**: All API calls logged with user, IP, timestamp
- **Security Headers**: HSTS, X-Frame-Options, CSP, XSS-Protection
- **File Security**: ZIP path traversal prevention, file size limits
- **HIPAA-Ready**: PHI removed from tokens, anonymization pipeline, audit logging

---

## Kubernetes Deployment

```bash
# Apply all manifests
kubectl apply -f kubernetes/deployment.yaml

# Check status
kubectl get pods -n autoradixai

# Scale backend
kubectl scale deployment autoradix-backend --replicas=5 -n autoradixai
```

---

## Adding Custom AI Models

```python
# Register in model_matcher_agent.py or via API
from app.agents.model_matcher_agent import ModelEntry, ModelMatcherAgent

agent = ModelMatcherAgent()
agent.register_model(ModelEntry(
    name="my_kidney_model",
    version="1.0",
    task="kidney_segmentation",
    modalities=["CT"],
    body_parts=["KIDNEY", "ABDOMEN"],
    description_keywords=["kidney", "renal"],
    model_path="ai-models/weights/kidney_model.pt",
    preprocessing_config={"resize": [256, 256], "normalize": True},
    priority=15,
))
```

Place `.pt` weights in `ai-models/weights/`.

---

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Frontend** | Next.js 15, React 18, TailwindCSS, Cornerstone.js, Zustand, Recharts |
| **Backend** | FastAPI, Python 3.11, Pydantic v2, Uvicorn |
| **AI/ML** | PyTorch 2.5, MONAI 1.4, scikit-image, OpenCV, scipy |
| **Medical Imaging** | pydicom, pynetdicom, highdicom, dicomweb-client |
| **Database** | PostgreSQL 16, SQLAlchemy 2.0 async |
| **Queue** | Celery 5.4, Redis 7 |
| **Deployment** | Docker, Docker Compose, Kubernetes (HPA-ready) |
| **Security** | python-jose, passlib[bcrypt], OWASP headers |

---

## License

MIT License — For research and clinical decision support tools. Not certified as a medical device.
All AI outputs must be reviewed by a qualified radiologist before clinical use.
