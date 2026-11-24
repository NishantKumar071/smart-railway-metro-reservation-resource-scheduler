# SmartRail AI+ — Operating System Concepts Implementation

## Academic Overview
SmartRail AI+ implements concrete, measurable Operating Systems (OS) mechanisms to manage booking requests in a high-concurrency multi-user environment.

---

## 1. Multithreading
- **Worker Thread Pool:** Initializes 6 persistent background worker threads on application startup.
- **Thread Lifecycle:** Worker threads run a continuous consumption loop, processing requests from a shared queue and yielding CPU cycles when idle.

---

## 2. Producer-Consumer Pattern
- **Producer:** Incoming HTTP request handlers enqueue incoming booking jobs.
- **Consumer:** Worker threads poll and consume tasks.
- **Coordination:** Implemented using `threading.Condition` (wrapping a `threading.Lock`) in Python and `std::condition_variable` with `std::unique_lock` in C++.
- **Bounded Buffer:** Bounded queue prevents memory exhaustion during load spikes.

---

## 3. Priority Scheduling Policy
Requests are ordered according to a project-defined academic priority hierarchy:
1. **EMERGENCY (Priority 1):** Highest dispatch priority.
2. **SENIOR_CITIZEN (Priority 2):** Priority for senior travelers.
3. **TATKAL (Priority 3):** Premium expedited booking.
4. **NORMAL / GENERAL (Priority 4):** Standard booking request.

### Deterministic Tie-Breaking
When two requests hold the same priority level, tie-breaking is determined deterministically:
$$\text{Order} = (\text{Priority Level}, \text{Arrival Timestamp}, \text{Request UUID})$$

> **Academic Note:** This scheduling policy is implemented for pedagogical demonstration of OS CPU and queue scheduling concepts. It is not an official Indian Railways booking rule.

---

## 4. Synchronization & Race-Condition Prevention
- **Mutex Locks:** Protect queue modifications and thread-state registries.
- **Condition Variables:** Avoid busy-waiting (spinning) by putting idle consumer threads to sleep until a task is enqueued.
- **Atomic Counters:** Thread-safe counters track active threads, completed tasks, and wait times.

---

## 5. Deadlock Prevention Strategy
To guarantee avoidance of circular-wait and hold-and-wait conditions:
1. **Single-Lock Hierarchy:** Only the queue condition lock is held during queue mutations.
2. **No Nested Lock Acquisition:** No worker thread holds a queue lock while executing a database transaction or external call.
3. **Lock Release on Block:** Condition variable `wait()` atomically releases the underlying mutex before blocking.

---

## 6. Live OS Telemetry
The telemetry dashboard (`pages/telemetry.html`) inspects real-time scheduler state:
- Number of active worker threads
- Live priority queue depth
- Average task queue wait duration (ms)
- Average task execution duration (ms)
- Lock contention frequency
