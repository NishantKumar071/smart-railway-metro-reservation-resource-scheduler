"""
SmartRail AI+ — Python AI FastAPI Service
==========================================
Provides AI prediction and recommendation endpoints.

DISCLAIMER: All predictions are ESTIMATES based on SYNTHETIC training data.
Not guarantees. Not connected to real Indian Railways systems.
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

logger = logging.getLogger("smartrail.ai")


# =============================================================================
# Schemas
# =============================================================================

class WaitlistPredictionRequest(BaseModel):
    train_number: str
    travel_class: str
    quota: str = "GENERAL"
    journey_date: str
    waitlist_number: int = Field(..., ge=1, le=200)
    days_before_journey: int = Field(..., ge=0, le=365)
    historical_cancel_rate: float = Field(0.25, ge=0.0, le=1.0)
    is_holiday_period: bool = False


class TrainRecommendationRequest(BaseModel):
    source_station: str
    dest_station: str
    journey_date: str
    travel_class: str = "SL"
    budget: str = "MEDIUM"   # LOW / MEDIUM / HIGH
    preferred_time: str = "EVENING"  # MORNING / AFTERNOON / EVENING / NIGHT
    max_results: int = Field(5, ge=1, le=10)


class SeatRecommendationRequest(BaseModel):
    train_id: int
    coach_id: int
    journey_date: str
    travel_class: str
    preferred_berth: str = "NO_PREFERENCE"
    passenger_age: int = Field(30, ge=1, le=120)
    passenger_gender: str = "MALE"
    has_luggage: bool = False
    is_senior: bool = False


# =============================================================================
# AI Service Application
# =============================================================================

def create_ai_app() -> FastAPI:
    app = FastAPI(
        title="SmartRail AI+ — AI Service",
        description=(
            "AI prediction and recommendation service for SmartRail AI+.\n\n"
            "⚠️ **DISCLAIMER**: All predictions use SYNTHETIC training data for academic "
            "demonstration. Predictions are ESTIMATES only, NOT guarantees. "
            "NOT connected to real Indian Railways systems."
        ),
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Model state
    models = {}

    @app.on_event("startup")
    async def load_models():
        """Load pre-trained models on startup."""
        curr_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.dirname(curr_dir)
        possible_dirs = [
            os.path.join(curr_dir, "models"),
            os.path.join(base_dir, "models"),
            os.path.join(base_dir, "ai-service", "models"),
        ]

        import joblib

        for model_name, filename in [
            ("waitlist", "waitlist_predictor.joblib"),
            ("recommendation", "recommendation_model.joblib"),
        ]:
            loaded = False
            for md in possible_dirs:
                path = os.path.join(md, filename)
                if os.path.exists(path):
                    try:
                        models[model_name] = joblib.load(path)
                        logger.info(f"✓ Loaded model: {model_name} from {path}")
                        loaded = True
                        break
                    except Exception as e:
                        logger.error(f"✗ Failed to load {model_name}: {e}")
            if not loaded:
                logger.warning(f"Model not found: {filename} in {possible_dirs}")

    @app.get("/ai/health")
    async def ai_health():
        return {
            "status": "healthy",
            "service": "SmartRail AI+ — AI Service",
            "version": "1.0.0",
            "models_loaded": list(models.keys()),
            "disclaimer": "Academic demonstration system. Predictions based on synthetic data.",
        }

    @app.get("/ai/model-status")
    async def model_status():
        statuses = {}
        for name in ["waitlist", "recommendation"]:
            if name in models:
                m = models[name]
                statuses[name] = {
                    "loaded": True,
                    "version": m.get("version", "unknown"),
                    "trained_at": m.get("trained_at", "unknown"),
                    "best_model": m.get("best_model", "N/A"),
                }
            else:
                statuses[name] = {
                    "loaded": False,
                    "message": "Model not loaded. Run python training/train_models.py",
                }
        return {"models": statuses}

    @app.get("/ai/model-metrics")
    async def model_metrics():
        if "waitlist" not in models:
            raise HTTPException(503, "Waitlist model not loaded. Run training/train_models.py first.")
        m = models["waitlist"]
        return {
            "disclaimer": m.get("data_disclaimer"),
            "version": m.get("version"),
            "trained_at": m.get("trained_at"),
            "metrics": m.get("metrics", {}),
        }

    @app.get("/ai/prediction-history")
    async def prediction_history():
        """Fetch recent AI prediction logs from DB."""
        try:
            import pymysql
            import pymysql.cursors
            from dotenv import load_dotenv
            load_dotenv()

            conn = pymysql.connect(
                host=os.getenv("DB_HOST", "localhost"),
                port=int(os.getenv("DB_PORT", 3306)),
                db=os.getenv("DB_NAME", "smartrail_db"),
                user=os.getenv("DB_USER", "root"),
                password=os.getenv("DB_PASSWORD", ""),
                cursorclass=pymysql.cursors.DictCursor,
            )
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT prediction_type, model_version, prediction_score,
                           confidence_level, created_at
                    FROM ai_prediction_logs
                    ORDER BY created_at DESC LIMIT 50
                    """
                )
                rows = cur.fetchall()
            conn.close()
            for r in rows:
                if r.get("created_at"):
                    r["created_at"] = r["created_at"].isoformat()
            return {"total": len(rows), "predictions": rows}
        except Exception as e:
            return {"total": 0, "predictions": [], "error": str(e)}

    @app.post("/ai/waitlist-prediction")
    async def predict_waitlist(req: WaitlistPredictionRequest):
        """
        Predict the probability of a waitlisted ticket getting confirmed.

        DISCLAIMER: Prediction is an estimate based on synthetic training data.
        NOT a guarantee. For academic demonstration only.
        """
        if "waitlist" not in models:
            raise HTTPException(
                503,
                "Waitlist prediction model not loaded. "
                "Run: python ai-service/training/train_models.py"
            )

        import numpy as np
        m = models["waitlist"]
        pipeline = m["pipeline"]
        class_enc = m["class_encoder"]
        quota_enc = m["quota_encoder"]
        train_enc = m["train_encoder"]

        # Feature engineering
        cls = req.travel_class.upper()
        quota = req.quota.upper()
        train_num = req.train_number

        class_max_wl = {"SL": 50, "3AC": 20, "2AC": 10, "1AC": 5, "CC": 10, "EC": 5, "2S": 50}
        max_wl = class_max_wl.get(cls, 20)
        wl_ratio = min(1.0, req.waitlist_number / max_wl)

        # Safe encoding (handle unseen labels)
        def safe_encode(encoder, value, default=0):
            try:
                return encoder.transform([value])[0]
            except ValueError:
                return default

        journey_month = int(req.journey_date.split("-")[1]) if "-" in req.journey_date else 6
        days_norm = min(1.0, req.days_before_journey / 60)

        features = [
            wl_ratio,
            days_norm,
            int(req.is_holiday_period),
            req.historical_cancel_rate,
            int(quota in ["TATKAL", "SENIOR_CITIZEN", "EMERGENCY"]),
            int(quota == "EMERGENCY"),
            safe_encode(class_enc, cls),
            safe_encode(quota_enc, quota),
            journey_month,
            req.days_before_journey,
            req.waitlist_number,
            max_wl,
        ]

        X = np.array(features).reshape(1, -1)
        prob = float(pipeline.predict_proba(X)[0][1])
        predicted_class = int(pipeline.predict(X)[0])

        # Determine risk level and category
        if prob >= 0.75:
            category = "HIGH_CONFIRMATION_CHANCE"
            risk = "LOW"
        elif prob >= 0.50:
            category = "MODERATE_CONFIRMATION_CHANCE"
            risk = "MEDIUM"
        elif prob >= 0.25:
            category = "LOW_CONFIRMATION_CHANCE"
            risk = "HIGH"
        else:
            category = "VERY_LOW_CONFIRMATION_CHANCE"
            risk = "VERY_HIGH"

        # Key factors
        factors = []
        if wl_ratio < 0.3:
            factors.append("Low waitlist position relative to maximum")
        elif wl_ratio > 0.7:
            factors.append("High waitlist position — fewer cancellations expected")
        if req.days_before_journey >= 15:
            factors.append("Sufficient time before journey for cancellations")
        elif req.days_before_journey < 5:
            factors.append("Very few days remaining — limited cancellation window")
        if req.historical_cancel_rate > 0.3:
            factors.append("High historical cancellation rate on this route")
        if quota == "EMERGENCY":
            factors.append("Emergency quota receives highest scheduling priority")
        elif quota == "SENIOR_CITIZEN":
            factors.append("Senior citizen quota receives priority allocation")
        if req.is_holiday_period:
            factors.append("Peak/holiday period — higher demand, fewer cancellations")

        # Log prediction
        _log_prediction_async(
            prediction_type="WAITLIST",
            input_data=req.model_dump(),
            output_data={"probability": prob, "category": category, "risk": risk},
            model_version=m.get("version", "1.0.0"),
            score=prob,
            confidence="HIGH" if abs(prob - 0.5) > 0.3 else "MEDIUM" if abs(prob - 0.5) > 0.15 else "LOW",
        )

        return {
            "prediction": {
                "confirmation_probability": round(prob, 4),
                "confirmation_probability_pct": f"{round(prob * 100, 1)}%",
                "predicted_outcome": "CONFIRMED" if predicted_class == 1 else "REMAINS_WAITLISTED",
                "category": category,
                "risk_level": risk,
                "key_factors": factors,
            },
            "model_info": {
                "model_type": m.get("best_model", "random_forest"),
                "version": m.get("version", "1.0.0"),
                "trained_at": m.get("trained_at", "unknown"),
            },
            "disclaimer": (
                "⚠️ ESTIMATE ONLY. Model trained on SYNTHETIC data for academic demonstration. "
                "This is NOT a guarantee. For demonstration purposes only. "
                "Not connected to real Indian Railways systems."
            ),
            "predicted_at": datetime.now().isoformat(),
        }

    @app.post("/ai/train-recommendations")
    async def recommend_trains(req: TrainRecommendationRequest):
        """
        Recommend trains based on user preferences and actual DB availability.
        Real train data from database; AI scores the recommendations.
        """
        # Fetch actual trains from DB
        trains_data = []
        try:
            import pymysql
            import pymysql.cursors
            from dotenv import load_dotenv
            load_dotenv()

            conn = pymysql.connect(
                host=os.getenv("DB_HOST", "localhost"),
                port=int(os.getenv("DB_PORT", 3306)),
                db=os.getenv("DB_NAME", "smartrail_db"),
                user=os.getenv("DB_USER", "root"),
                password=os.getenv("DB_PASSWORD", ""),
                cursorclass=pymysql.cursors.DictCursor,
            )
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT DISTINCT t.id, t.train_number, t.train_name, t.train_type,
                           t.departure_time, t.arrival_time, t.journey_duration_mins,
                           tc.coach_type, tc.id AS coach_id,
                           si.available_seats, si.waitlist_count, si.max_waitlist,
                           ROUND(tc.base_fare + tc.fare_per_km * 1000, 2) AS fare
                    FROM trains t
                    JOIN train_routes tr_src ON t.id = tr_src.train_id AND tr_src.station_code = %s
                    JOIN train_routes tr_dst ON t.id = tr_dst.train_id AND tr_dst.station_code = %s
                    JOIN train_coaches tc ON t.id = tc.train_id AND tc.coach_type = %s
                    LEFT JOIN seat_inventory si ON si.train_id = t.id AND si.coach_id = tc.id AND si.journey_date = %s
                    WHERE t.is_active = 1 AND tr_src.stop_number < tr_dst.stop_number
                    ORDER BY t.departure_time
                    """,
                    (req.source_station.upper(), req.dest_station.upper(),
                     req.travel_class.upper(), req.journey_date),
                )
                trains_data = cur.fetchall()
            conn.close()
        except Exception as e:
            logger.warning(f"DB fetch for recommendations failed: {e}")

        # Fallback to embedded SQLite database if MySQL was not reachable
        if not trains_data:
            try:
                import sqlite3
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                db_path = os.path.join(base_dir, "backend", "smartrail_embedded.db")
                if os.path.exists(db_path):
                    con = sqlite3.connect(db_path)
                    con.row_factory = sqlite3.Row
                    cur = con.cursor()
                    cur.execute(
                        """
                        SELECT DISTINCT t.id, t.train_number, t.train_name, t.train_type,
                               t.departure_time, t.arrival_time, t.journey_duration_mins,
                               tc.coach_type, tc.id AS coach_id,
                               si.available_seats, si.waitlist_count, si.max_waitlist,
                               ROUND(tc.base_fare + tc.fare_per_km * 1000, 2) AS fare
                        FROM trains t
                        JOIN train_routes tr_src ON t.id = tr_src.train_id AND tr_src.station_code = ?
                        JOIN train_routes tr_dst ON t.id = tr_dst.train_id AND tr_dst.station_code = ?
                        JOIN train_coaches tc ON t.id = tc.train_id AND tc.coach_type = ?
                        LEFT JOIN seat_inventory si ON si.train_id = t.id AND si.coach_id = tc.id AND si.journey_date = ?
                        WHERE t.is_active = 1 AND tr_src.stop_number < tr_dst.stop_number
                        ORDER BY t.departure_time
                        """,
                        (req.source_station.upper(), req.dest_station.upper(),
                         req.travel_class.upper(), req.journey_date),
                    )
                    rows = cur.fetchall()
                    trains_data = [dict(r) for r in rows]
                    con.close()
            except Exception as e2:
                logger.warning(f"SQLite fallback for recommendations failed: {e2}")

        if not trains_data:
            return {
                "recommendations": [],
                "message": "No trains found for this route/class/date.",
                "disclaimer": "No real data available. Try different stations or dates.",
            }

        import numpy as np

        # Score each train
        time_pref_hours = {
            "MORNING": 8, "AFTERNOON": 13, "EVENING": 18, "NIGHT": 22
        }.get(req.preferred_time.upper(), 18)

        budget_max = {"LOW": 500, "MEDIUM": 1500, "HIGH": 5000}.get(req.budget.upper(), 1500)

        scored_trains = []
        for t in trains_data:
            dep_str = str(t.get("departure_time", "18:00:00"))
            dep_hour = int(dep_str.split(":")[0]) if dep_str else 18
            fare = float(t.get("fare") or 500)
            avail = t.get("available_seats") or 0
            dur = t.get("journey_duration_mins") or 600

            # Scoring factors
            time_diff = abs(dep_hour - time_pref_hours)
            time_score = max(0, 1.0 - time_diff / 12)
            budget_score = max(0, 1.0 - fare / budget_max) if fare <= budget_max else 0.1
            avail_score = min(1.0, avail / 20) if avail > 0 else 0.3  # WL still usable
            dur_score = max(0, 1.0 - dur / 2000)  # shorter is better

            final_score = (
                time_score * 0.30
                + budget_score * 0.30
                + avail_score * 0.25
                + dur_score * 0.15
                + np.random.uniform(0, 0.05)  # slight randomization
            )

            reason_parts = []
            if avail > 0:
                reason_parts.append(f"{avail} seats available")
            else:
                wl = t.get("waitlist_count", 0) or 0
                max_wl = t.get("max_waitlist", 20) or 20
                reason_parts.append(f"Waitlisted (WL {wl}/{max_wl})")
            if time_score > 0.7:
                reason_parts.append(f"departure matches your preferred {req.preferred_time.lower()} time")
            if budget_score > 0.6:
                reason_parts.append("within your budget")
            dur_h = dur // 60
            dur_m = dur % 60
            reason_parts.append(f"{dur_h}h {dur_m}m journey")

            scored_trains.append({
                "train_id": t["id"],
                "train_number": t["train_number"],
                "train_name": t["train_name"],
                "train_type": t.get("train_type", "EXPRESS"),
                "departure_time": dep_str,
                "arrival_time": str(t.get("arrival_time", "")),
                "duration": f"{dur_h}h {dur_m}m",
                "coach_type": t["coach_type"],
                "fare": fare,
                "available_seats": avail,
                "recommendation_score": round(final_score, 4),
                "recommendation_pct": f"{round(final_score * 100, 1)}%",
                "reason": "; ".join(reason_parts),
            })

        scored_trains.sort(key=lambda x: x["recommendation_score"], reverse=True)
        top = scored_trains[:req.max_results]

        return {
            "source": req.source_station.upper(),
            "destination": req.dest_station.upper(),
            "journey_date": req.journey_date,
            "travel_class": req.travel_class.upper(),
            "total_found": len(trains_data),
            "recommendations": top,
            "disclaimer": (
                "Recommendations based on real database entries + AI scoring. "
                "Not connected to live IRCTC systems. For academic demonstration only."
            ),
        }

    @app.post("/ai/seat-recommendations")
    async def recommend_seat(req: SeatRecommendationRequest):
        """
        Recommend suitable berth/seat based on passenger profile and availability.
        AI recommends; C++ booking engine (Python here) verifies and allocates.
        """
        # Fetch available seats from DB
        try:
            import pymysql
            import pymysql.cursors
            from dotenv import load_dotenv
            load_dotenv()

            conn = pymysql.connect(
                host=os.getenv("DB_HOST", "localhost"),
                port=int(os.getenv("DB_PORT", 3306)),
                db=os.getenv("DB_NAME", "smartrail_db"),
                user=os.getenv("DB_USER", "root"),
                password=os.getenv("DB_PASSWORD", ""),
                cursorclass=pymysql.cursors.DictCursor,
            )
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT ps.id, ps.seat_number, ps.berth_type, ps.is_window, ps.bay_number
                    FROM physical_seats ps
                    WHERE ps.coach_id = %s
                      AND ps.id NOT IN (
                          SELECT bp.seat_id FROM booking_passengers bp
                          JOIN bookings b ON bp.booking_id = b.id
                          WHERE b.coach_id = %s AND b.journey_date = %s
                            AND bp.status IN ('CONFIRMED','RAC') AND bp.seat_id IS NOT NULL
                      )
                    ORDER BY ps.berth_type, ps.seat_number
                    LIMIT 20
                    """,
                    (req.coach_id, req.coach_id, req.journey_date),
                )
                available_seats = cur.fetchall()
            conn.close()
        except Exception as e:
            logger.warning(f"Seat DB fetch failed: {e}")
            available_seats = []

        if not available_seats:
            return {
                "recommendations": [],
                "message": "No available seats found. Train may be fully booked.",
            }

        # Scoring berths based on passenger profile
        berth_scores = {
            "LOWER": 0.5,
            "MIDDLE": 0.3,
            "UPPER": 0.4,
            "SIDE_LOWER": 0.45,
            "SIDE_UPPER": 0.35,
        }

        # Adjust scores based on passenger profile
        if req.is_senior or req.passenger_age >= 60:
            berth_scores["LOWER"] = 0.95
            berth_scores["SIDE_LOWER"] = 0.85
            berth_scores["MIDDLE"] = 0.20
            berth_scores["UPPER"] = 0.10
            berth_scores["SIDE_UPPER"] = 0.15
        elif req.passenger_age < 25:
            berth_scores["UPPER"] = 0.80
            berth_scores["MIDDLE"] = 0.65
            berth_scores["LOWER"] = 0.50
        elif req.has_luggage:
            berth_scores["LOWER"] = 0.85
            berth_scores["SIDE_LOWER"] = 0.80

        # Apply passenger preference
        pref = req.preferred_berth.upper()
        if pref != "NO_PREFERENCE":
            berth_scores[pref] = berth_scores.get(pref, 0.5) + 0.2

        scored = []
        for seat in available_seats:
            berth = seat["berth_type"]
            score = berth_scores.get(berth, 0.3)
            if seat.get("is_window"):
                score += 0.05
            reason = f"Suitable {berth.lower().replace('_', ' ')} berth"
            if req.is_senior:
                reason += " — easy access for senior citizen"
            if seat.get("is_window"):
                reason += "; window seat"

            scored.append({
                "seat_id": seat["id"],
                "seat_number": seat["seat_number"],
                "berth_type": berth,
                "bay_number": seat.get("bay_number"),
                "is_window": bool(seat.get("is_window")),
                "recommendation_score": round(min(1.0, score), 4),
                "reason": reason,
            })

        scored.sort(key=lambda x: x["recommendation_score"], reverse=True)
        top_3 = scored[:3]

        return {
            "train_id": req.train_id,
            "coach_id": req.coach_id,
            "journey_date": req.journey_date,
            "passenger_profile": {
                "age": req.passenger_age,
                "gender": req.passenger_gender,
                "is_senior": req.is_senior,
                "preferred_berth": req.preferred_berth,
            },
            "recommendations": top_3,
            "note": "AI recommends; booking engine verifies availability and performs final allocation.",
            "disclaimer": "Recommendation is a suggestion only. Actual allocation depends on seat availability at booking time.",
        }

    return app


def _log_prediction_async(prediction_type, input_data, output_data, model_version, score, confidence):
    """Log prediction to DB asynchronously (best-effort)."""
    import threading
    def _do_log():
        try:
            import pymysql, json
            from dotenv import load_dotenv
            load_dotenv()
            conn = pymysql.connect(
                host=os.getenv("DB_HOST", "localhost"),
                port=int(os.getenv("DB_PORT", 3306)),
                db=os.getenv("DB_NAME", "smartrail_db"),
                user=os.getenv("DB_USER", "root"),
                password=os.getenv("DB_PASSWORD", ""),
            )
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO ai_prediction_logs
                    (prediction_type, input_data, output_data, model_version, prediction_score, confidence_level)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (prediction_type, json.dumps(input_data), json.dumps(output_data),
                     model_version, score, confidence),
                )
            conn.commit()
            conn.close()
        except Exception:
            pass
    threading.Thread(target=_do_log, daemon=True).start()


app = create_ai_app()

if __name__ == "__main__":
    import uvicorn
    from dotenv import load_dotenv
    load_dotenv()
    port = int(os.getenv("AI_SERVICE_PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
