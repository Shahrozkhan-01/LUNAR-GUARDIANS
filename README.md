# 🌙 LUNAR GUARDIANS — Junior Astronaut Mission Trainer

> **NASA Space Apps Challenge Project**

A browser-based educational space survival simulation designed for children aged 7–12. Players manage a lunar outpost and make real decisions about survival resources — powered by real NASA data.

---

## 🚀 Project Overview

LUNAR GUARDIANS puts young players in charge of a lunar base. They must monitor and manage critical life-support systems to keep their crew alive, learning real concepts used by NASA astronauts along the way.

The game integrates NASA open data APIs (including the DONKI Space Weather API) to introduce real space weather events and their effects on lunar operations.

---

## 🏆 Challenge Description

**NASA Space Apps Challenge** — an international hackathon where teams use NASA's open data to build solutions to challenges facing Earth and space.

This project targets the challenge of making space science and astronaut training accessible and engaging for the next generation of space explorers.

---

## 👦👧 Target Audience

- **Primary:** Children aged 7–12
- **Secondary:** Teachers and parents using the tool for STEM education
- **Context:** Classroom or home learning environment

---

## 🎮 Main Planned Features

| Feature | Description |
|---------|-------------|
| 🌬️ Oxygen & Life Support | Monitor and manage breathable air levels |
| 💧 Water Management | Recycle and ration water supply |
| ⚡ Power Allocation | Distribute limited solar electricity |
| ☢️ Radiation Protection | Shield the crew during radiation events |
| 🌱 Food Production | Manage lunar greenhouse crops |
| 🌩️ Solar Storm Events | Real NASA DONKI data drives space weather events |
| 🏅 Mission Survival | Multi-day survival decisions with consequences |

---

## 🛠️ Technology Stack

### Frontend
| Tool | Version | Purpose |
|------|---------|---------|
| React | 18+ | UI framework |
| Vite | 6+ | Build tool and dev server |
| React Router DOM | 7+ | Client-side routing |
| Axios | 1+ | HTTP requests to backend & NASA APIs |
| Framer Motion | 12+ | Animations and transitions |
| Recharts | 2+ | Data visualization / resource gauges |
| Lucide React | Latest | Icon library |

### Backend
| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.14+ | Server language |
| FastAPI | Latest | REST API framework |
| Uvicorn | Latest | ASGI server |
| Pandas | Latest | Data processing |
| NumPy | Latest | Numerical computations |
| python-dotenv | Latest | Environment variable management |
| Requests | Latest | HTTP calls to NASA APIs |

---

## 📁 Project Directory Structure

```
LUNAR-GUARDIANS/
│
├── frontend/               # React + Vite application
│   ├── src/
│   │   ├── assets/        # Images, icons, audio
│   │   ├── components/    # Reusable UI components
│   │   ├── pages/         # Route-level page components
│   │   ├── hooks/         # Custom React hooks
│   │   ├── context/       # React context (global state)
│   │   ├── services/      # API service layer (axios)
│   │   └── utils/         # Helper functions
│   ├── public/            # Static public assets
│   ├── package.json
│   └── vite.config.js
│
├── backend/                # FastAPI Python server
│   ├── main.py            # FastAPI app entry point
│   ├── routers/           # API route modules
│   ├── services/          # Business logic (NASA API, game logic)
│   ├── models/            # Pydantic data models
│   ├── utils/             # Utility functions
│   ├── venv/              # Python virtual environment (git-ignored)
│   ├── .env               # Environment variables (git-ignored)
│   ├── .env.example       # Template for required env vars
│   └── requirements.txt   # Python dependencies
│
├── documentation/          # Project documentation
│   └── project_overview.md
│
├── datasets/               # NASA open datasets (CSV, JSON)
│
├── .gitignore
└── README.md
```

---

## ▶️ Running the Project

### Prerequisites
- Node.js v18+ and npm v9+
- Python 3.10+
- Git

---

### 🖥️ Start the Frontend (React)

```bash
# Navigate to the frontend folder
cd LUNAR-GUARDIANS/frontend

# Install dependencies (first time only)
npm install

# Start the development server
npm run dev
```

The app will be available at: **http://localhost:5173**

---

### 🐍 Start the Backend (FastAPI)

```bash
# Navigate to the backend folder
cd LUNAR-GUARDIANS/backend

# Activate the Python virtual environment (Windows)
venv\Scripts\activate

# Activate the Python virtual environment (macOS/Linux)
source venv/bin/activate

# Install dependencies (first time only)
pip install -r requirements.txt

# Start the FastAPI development server
uvicorn main:app --reload --port 8000
```

The API will be available at: **http://localhost:8000**
Interactive API docs: **http://localhost:8000/docs**

---

## 🔑 Environment Variables

Create a `.env` file inside the `backend/` folder (never commit this file):

```env
# NASA Open APIs — Get a free key at: https://api.nasa.gov/
NASA_API_KEY=your_nasa_api_key_here

# Server configuration
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
```

---

## 📝 Notes

- No database is introduced in this initial setup.
- No API keys are hardcoded anywhere.
- No real NASA data is fabricated or simulated in this setup phase.
- Game mechanics are not yet implemented — this is the initial scaffold.

---

## 👥 Team

NASA Space Apps Challenge — 2024/2025

---

*Built with ❤️ for the next generation of space explorers.*
