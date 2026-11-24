# SmartRail AI+ — AI/ML Model Documentation

## Academic Disclaimer
> **IMPORTANT:** All AI models are trained on **synthetic demonstration datasets** algorithmically created to simulate booking and cancellation patterns. Predictions are probabilistic estimates, not guarantees. This system is not connected to real Indian Railways data.

---

## 1. Feature 1: Waitlist Confirmation Predictor

### Problem Formulation
Given ticket parameters (WL number, days before travel, quota, historical cancellation rates), predict the probability $P(Y=1)$ that a waitlisted ticket transitions to `CONFIRMED`.

### Algorithms Trained & Evaluated
- **Logistic Regression (with StandardScaler)**
- **Random Forest Classifier (100 estimators, max depth 8)**

### Dataset
- 1,200 synthetic records (`datasets/waitlist_training_data.csv`)
- Train/Test Split: 70% training, 30% holdout test set

### Evaluation Metrics
| Metric | Logistic Regression | Random Forest Classifier |
|---|---|---|
| **Accuracy** | 64.44% | 64.44% |
| **Precision** | 62.43% | 62.72% |
| **Recall** | 63.16% | 61.99% |
| **F1-Score** | 0.6279 | 0.6235 |
| **ROC-AUC** | **0.6949** | 0.6849 |

*Model Selected:* **Logistic Regression** pipeline (serialized to `waitlist_predictor.joblib`).

---

## 2. Feature 2: Train Recommendation Scoring

### Multi-Factor Recommendation Function
The recommendation score $S \in [0, 1]$ balances four key components:
$$S = 0.30 \cdot S_{\text{time}} + 0.30 \cdot S_{\text{budget}} + 0.25 \cdot S_{\text{avail}} + 0.15 \cdot S_{\text{duration}}$$
- **Time Score:** Proximity of departure hour to user's preferred time slot.
- **Budget Score:** Inverse penalty for fares exceeding chosen budget threshold.
- **Availability Score:** Bonus for available physical seats vs. waitlist only.
- **Duration Score:** Preference for shorter transit times.

---

## 3. Feature 3: Smart Seat & Berth Allocator
- Suggests optimal berth types based on traveler demographics:
  - Passengers aged 60+ receive highest priority for Lower Berths ($Score = 0.95$) and Side Lower Berths.
  - Passengers with heavy luggage are prioritized for Lower Berths.
  - Younger passengers are offered Upper and Middle berths.
- Allocations are verified against the database before confirmation.
