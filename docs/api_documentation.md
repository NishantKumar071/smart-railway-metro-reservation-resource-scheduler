# SmartRail AI+ — API Documentation

## Service Ports
- **Backend API:** `http://localhost:8080`
- **AI Microservice:** `http://localhost:8000`
- **Interactive Swagger Docs:** `http://localhost:8080/docs` & `http://localhost:8000/docs`

---

## 1. Authentication Endpoints

### `POST /api/auth/register`
Creates a new passenger account.
- **Request Body:**
```json
{
  "email": "user@example.com",
  "username": "user123",
  "password": "Password123",
  "full_name": "User Name",
  "phone": "9876543210",
  "gender": "MALE"
}
```
- **Response:** `201 Created`

### `POST /api/auth/login`
Authenticates a user and returns a signed HS256 JWT bearer token.
- **Form Data:** `username`, `password`
- **Response:**
```json
{
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "role": "PASSENGER"
  }
}
```

---

## 2. Train Search & Inventory Endpoints

### `GET /api/trains/search`
Query trains operating between source and destination.
- **Query Params:** `source=NDLS`, `destination=HWH`, `journey_date=2026-12-01`, `travel_class=3AC`, `quota=GENERAL`
- **Response:** Array of matched trains, stops, fares, and real-time seat availability counts.

### `GET /api/trains/{train_number}`
Returns route halts, intermediate distances, and coach configurations.

---

## 3. Booking & Cancellation Endpoints

### `POST /api/bookings`
Enqueues booking request to OS Priority Scheduler for thread-pool execution.
- **Request Body:**
```json
{
  "train_id": 2,
  "coach_id": 8,
  "journey_date": "2026-12-01",
  "source_station": "NDLS",
  "dest_station": "HWH",
  "travel_class": "3AC",
  "quota": "GENERAL",
  "preferred_berth": "LOWER",
  "total_fare": 1245.00,
  "passengers": [
    {
      "full_name": "Nishant Kumar",
      "age": 21,
      "gender": "MALE",
      "id_type": "AADHAAR"
    }
  ]
}
```

### `GET /api/pnr/{pnr}`
Fetches status of booking by 10-digit PNR.

### `POST /api/bookings/{pnr}/cancel`
Cancels booking and automatically promotes eligible waitlisted passengers.

---

## 4. AI Service Endpoints (Port 8000)

### `POST /ai/waitlist-prediction`
Infers probability of waitlisted ticket confirming.
- **Request Body:**
```json
{
  "train_number": "12301",
  "travel_class": "3AC",
  "quota": "GENERAL",
  "journey_date": "2026-12-01",
  "waitlist_number": 4,
  "days_before_journey": 18,
  "historical_cancel_rate": 0.28,
  "is_holiday_period": false
}
```

### `POST /ai/train-recommendations`
Ranks and recommends trains based on departure time preference and budget.

### `POST /ai/seat-recommendations`
Recommends physical berths based on demographic age and coach layouts.
