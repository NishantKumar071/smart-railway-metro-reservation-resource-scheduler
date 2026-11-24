# SmartRail AI+ — Architecture Specification

## Academic Project Information
- **Project Title:** SmartRail AI+ — Smart Railway Reservation & Resource Scheduler with AI-Based Prediction and Recommendation
- **Domain:** Operating Systems, Database Management Systems, Artificial Intelligence
- **University:** Graphic Era (Deemed to be University), Dehradun
- **Academic Session:** 2026–2027 (5th Semester)
- **Team ID:** OSDBMS-V-2026-T281
- **Project Mentor:** Dr. Deepak Gaur
- **Team Members:**
  1. Nishant Kumar (Team Lead & Developer)
  2. Robert Sandi Thomas (Developer & Tester)

---

## 1. High-Level Architectural Diagram

```mermaid
flowchart TD
    subgraph ClientLayer ["Client Layer (Port 3000)"]
        UI["Web UI: HTML5, CSS3, Vanilla JS, Chart.js"]
        Dashboard["Passenger & Admin Dashboards"]
    end

    subgraph BackendLayer ["Backend Scheduling Layer (Port 8080)"]
        API["FastAPI / C++ HTTP Gateway"]
        Producer["Producer: Booking Request Enqueuer"]
        PQueue["Priority Queue (Min-Heap / Condition Variable)"]
        WorkerPool["Worker Thread Pool (6 Daemon Threads)"]
        BookingEngine["Booking & Cancellation Engine"]
        Telemetry["Telemetry Tracker & Lock Monitor"]
    end

    subgraph AILayer ["AI / ML Service Layer (Port 8000)"]
        FastAPI_AI["FastAPI Inference Service"]
        WLModel["Waitlist Predictor (Logistic Regression / RF)"]
        RecModel["Train Recommender (Multi-factor Scorer)"]
        SeatModel["Berth Allocator (Layout & Demographic Scorer)"]
    end

    subgraph DatabaseLayer ["Database Layer (MySQL 8.0 / InnoDB)"]
        MySQL[("MySQL 8.0 InnoDB Database")]
        Tables["14 Normalized Tables + Stored Procedures"]
        Locking["Row-Level Locking: SELECT FOR UPDATE"]
    end

    UI -->|REST API Calls| API
    UI -->|Inference Queries| FastAPI_AI
    API --> Producer
    Producer -->|Thread Safe Push| PQueue
    PQueue -->|Condition Variable Wait / Pop| WorkerPool
    WorkerPool --> BookingEngine
    BookingEngine -->|ACID Transactions| MySQL
    BookingEngine --> Telemetry
    FastAPI_AI -->|Pretrained Joblib Models| WLModel
    FastAPI_AI -->|Pretrained Joblib Models| RecModel
    FastAPI_AI -->|Pretrained Joblib Models| SeatModel
```

---

## 2. Layer Responsibilities

### Client Presentation Layer
- Built with standard modern web technologies (HTML5, CSS3, responsive Flexbox/Grid, Chart.js).
- Provides dedicated panels for:
  - Train Search & Live Inventory Checking
  - Passenger Detail Entry & PNR Generation
  - Real-time PNR Tracking and Cancellation
  - AI Waitlist Probability Meter
  - AI Train and Seat Recommendations
  - Live OS Telemetry & Worker Inspection
  - System Administrator Transaction Audit Logs

### Core Reservation & OS Scheduling Layer
- Serves as the authoritative engine for booking confirmations, physical seat assignments, and database modifications.
- Implements multithreaded worker pools with strict deadlock prevention and deterministic tie-breaking.
- Protects shared seat inventory from race conditions using transactions with row-level locks.

### AI/ML Prediction Service Layer
- Independent FastAPI microservice providing probabilistic estimations.
- Serves serialized Scikit-Learn pipelines without directly altering database booking states.
