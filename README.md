# SmartRail AI+ — Smart Railway Reservation & Resource Scheduler with AI-Based Prediction and Recommendation

> **B.Tech 5th Semester Academic Project**  
> **Domain:** Operating Systems (OS), Database Management Systems (DBMS), Artificial Intelligence (AI/ML)  
> **University:** Graphic Era (Deemed to be University), Dehradun  
> **Session:** 2026–2027  
> **Team ID:** OSDBMS-V-2026-T281  
> **Project Mentor:** Dr. Deepak Gaur  
>
> **Team Members:**  
> 1. **Nishant Kumar** — Team Lead and Developer (Architecture, C++ Backend, OS Scheduling & Concurrency, AI Integration)  
> 2. **Robert Sandi Thomas** — Developer and Tester (Database Design, MySQL Integration, DBMS Transactions, Testing & Validation)  

---

## ⚠️ Academic Disclaimer
This application is an academic demonstration project built strictly for educational purposes. It is **NOT** connected to live IRCTC or Indian Railways production systems. All train schedules, PNRs, passenger records, and historical datasets are synthetic demonstration data.

---

## 📌 Project Overview
**SmartRail AI+** is an end-to-end railway reservation and resource scheduling platform designed to demonstrate foundational Computer Science principles through an interactive, full-stack application:
- **Operating Systems:** Multithreaded worker pools, producer-consumer coordination using condition variables, priority request queues with deterministic tie-breaking, and deadlock prevention protocols.
- **Database Management Systems:** Normalized MySQL 8.0 schema (14 tables), ACID transactions, row-level locking via `SELECT ... FOR UPDATE`, and duplicate physical seat allocation prevention.
- **Artificial Intelligence / Machine Learning:** Scikit-Learn models providing waitlist confirmation probability estimation, multi-factor personalized train recommendation scoring, and demographic-aware berth allocation.

---

## 🛠️ Technology Stack
- **Backend Scheduling Engine:** C++17 architecture with Python FastAPI gateway, `threading`, `queue`, `heapq` priority queue.
- **Database:** MySQL 8.0+ (InnoDB storage engine), connection pooling, parameterization.
- **AI/ML Microservice:** Python 3, FastAPI, Pandas, NumPy, Scikit-learn, Joblib.
- **Frontend Dashboard:** HTML5, CSS3 (Modern SaaS design), Vanilla JavaScript, Chart.js.

---

## 📁 Project Directory Structure
```
ai_smartrail/
├── backend/
│   ├── CMakeLists.txt          # C++ build definition
│   ├── include/                # C++ headers (scheduler, booking, telemetry, db)
│   ├── src/                    # C++ source files
│   ├── app/                    # FastAPI backend scheduling implementation
│   ├── main.py                 # Backend entrypoint (Port 8080)
│   └── requirements.txt
├── ai-service/
│   ├── app/                    # AI microservice modules
│   ├── training/               # Model training scripts
│   ├── datasets/               # Synthetic training CSV files
│   ├── models/                 # Pretrained joblib model artifacts
│   ├── main.py                 # AI service entrypoint (Port 8000)
│   └── requirements.txt
├── frontend/
│   ├── index.html              # Landing page
│   ├── css/                    # Custom CSS stylesheet
│   ├── js/                     # API client & app scripts
│   └── pages/                  # 11 functional UI views
├── database/
│   ├── schema.sql              # 14 tables, procedures, views
│   ├── seed_data.sql           # Realistic demonstration records
│   └── ai_history.sql          # Synthetic AI training history
├── tests/
│   ├── concurrency/            # Critical 10-concurrent-requests test
│   ├── backend/                # Unit & security tests
│   ├── database/               # Schema integrity tests
│   ├── ai/                     # Model inference tests
│   └── integration/            # End-to-end integration tests
├── scripts/
│   ├── setup_database.bat      # Windows database setup
│   ├── setup_database.ps1      # PowerShell database setup
│   ├── build_backend.bat       # C++ build script
│   ├── start_backend.bat       # Start backend server
│   ├── start_ai_service.bat    # Start AI microservice
│   ├── start_all.bat           # Master one-click startup
│   └── start_all.ps1           # PowerShell master launcher
├── docs/                       # Architectural & design documentation
├── .env.example
├── .gitignore
└── README.md
```

---

## 🚀 Quick Start Guide (Windows)

### Prerequisites
1. **Python 3.10+** (Python 3.14 verified)
2. **MySQL Server 8.0+** running locally on port 3306

### Step 1: Database Setup
Run the automated setup script to create tables and load sample data:
```cmd
scripts\setup_database.bat
```
*(Or in PowerShell: `powershell -ExecutionPolicy Bypass -File scripts\setup_database.ps1`)*

### Step 2: One-Click Master Startup
Double-click or run:
```cmd
scripts\start_all.bat
```
This automatically launches:
- **Frontend Web UI:** `http://localhost:3000`
- **Backend API:** `http://localhost:8080` (Docs: `http://localhost:8080/docs`)
- **AI Service:** `http://localhost:8000` (Docs: `http://localhost:8000/docs`)

---

## 🧪 Automated Testing
Execute the complete test suite including the critical concurrency test:
```cmd
python tests/concurrency/test_concurrency.py
python tests/backend/test_backend.py
python tests/ai/test_ai.py
python tests/database/test_db.py
python tests/integration/test_integration.py
```

### Critical Concurrency Test Verification
- **Scenario:** 10 concurrent booking requests compete for only 2 available physical seats.
- **Result:** Exactly 2 confirmed bookings, 8 waitlisted bookings, 0 duplicate physical seats. **VERIFIED PASS.**

---

## 🔑 Demo Login Credentials
- **Passenger Account:** `nishant@smartrail.local` | Password: `Demo@123`
- **Administrator Account:** `admin@smartrail.local` | Password: `Demo@123`
