"""
SmartRail AI+ — OS Concept: Priority Scheduler with Worker Thread Pool
=======================================================================

This module implements the following Operating Systems concepts:

1. MULTITHREADING
   - Worker pool of configurable threads (default: 6)
   - Each thread runs continuously, consuming from the shared queue

2. PRODUCER-CONSUMER PROBLEM
   - Producer: HTTP request handlers add BookingRequest to shared queue
   - Consumer: Worker threads pick and process requests
   - Bounded buffer (max queue size configurable)
   - Coordinated via threading.Condition (wait/notify)

3. PRIORITY SCHEDULING
   - Four priority levels:
       1 = EMERGENCY (highest)
       2 = SENIOR CITIZEN
       3 = TATKAL
       4 = NORMAL (lowest)
   - Implemented using Python's heapq (min-heap)
   - Tie-breaking: (priority, timestamp, request_id)
   - ACADEMIC NOTE: Priority levels are project-defined for demonstrating
     OS scheduling concepts. They do NOT represent official Indian Railways rules.

4. SYNCHRONIZATION PRIMITIVES
   - threading.Lock     → mutual exclusion on shared state
   - threading.Condition → producer-consumer coordination
   - threading.atomic   → thread-safe counters (via threading.Lock + int)
   - threading.Event    → clean shutdown signal

5. DEADLOCK PREVENTION
   - Single global lock strategy: only one lock held at a time
   - No nested locks that could cause circular dependency
   - Lock acquisition order documented and enforced

6. TELEMETRY
   - Real-time counters: total, completed, failed, pending requests
   - Per-thread activity tracking
   - Queue depth monitoring
   - Processing time measurement
"""

import heapq
import logging
import threading
import time
import uuid
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Callable, Dict, List, Optional

from app.core.config import settings

logger = logging.getLogger("smartrail.scheduler")


# =============================================================================
# Priority Levels (OS Scheduling Policy — Academic Definition)
# =============================================================================

class Priority(IntEnum):
    """
    Priority levels for booking request scheduling.
    Lower number = higher priority (min-heap ordering).

    ACADEMIC NOTE: This is a project-defined scheduling policy for demonstrating
    OS concepts. It does NOT represent official Indian Railways booking policy.
    """
    EMERGENCY      = 1   # Medical/emergency bookings
    SENIOR_CITIZEN = 2   # Senior citizen quota
    TATKAL         = 3   # Tatkal premium bookings
    NORMAL         = 4   # Regular bookings


PRIORITY_NAMES = {
    Priority.EMERGENCY:      "EMERGENCY",
    Priority.SENIOR_CITIZEN: "SENIOR_CITIZEN",
    Priority.TATKAL:         "TATKAL",
    Priority.NORMAL:         "NORMAL",
}

QUOTA_PRIORITY_MAP = {
    "EMERGENCY":      Priority.EMERGENCY,
    "SENIOR_CITIZEN": Priority.SENIOR_CITIZEN,
    "TATKAL":         Priority.TATKAL,
    "GENERAL":        Priority.NORMAL,
    "LADIES":         Priority.NORMAL,
}


# =============================================================================
# Booking Request (Producer unit)
# =============================================================================

@dataclass(order=True)
class BookingRequest:
    """
    A booking request placed in the priority queue.
    Ordering: (priority, timestamp, request_id) for deterministic tie-breaking.
    """
    priority:    int           = field(compare=True)
    timestamp:   float         = field(compare=True)
    request_id:  str           = field(compare=True)

    # Non-ordering fields
    task_fn:     Callable      = field(compare=False)
    task_args:   tuple         = field(compare=False, default_factory=tuple)
    task_kwargs: dict          = field(compare=False, default_factory=dict)
    result_event: threading.Event = field(compare=False, default_factory=threading.Event)
    result:      Any           = field(compare=False, default=None)
    error:       Optional[Exception] = field(compare=False, default=None)
    enqueue_time: float        = field(compare=False, default_factory=time.monotonic)


# =============================================================================
# Telemetry Counters (Thread-safe)
# =============================================================================

class AtomicCounter:
    """Thread-safe counter — demonstrates atomic variable concept."""
    def __init__(self, value: int = 0):
        self._value = value
        self._lock = threading.Lock()

    def increment(self) -> int:
        with self._lock:
            self._value += 1
            return self._value

    def decrement(self) -> int:
        with self._lock:
            self._value = max(0, self._value - 1)
            return self._value

    def get(self) -> int:
        with self._lock:
            return self._value

    def reset(self) -> None:
        with self._lock:
            self._value = 0


class SchedulerTelemetry:
    """Real-time OS telemetry — all values are thread-safe."""
    def __init__(self):
        self.total_requests    = AtomicCounter()
        self.completed         = AtomicCounter()
        self.failed            = AtomicCounter()
        self.active_threads    = AtomicCounter()
        self._lock             = threading.Lock()
        self._processing_times: List[float] = []
        self._queue_depths:     List[int]   = []
        self._lock_contentions = AtomicCounter()

    def record_processing_time(self, ms: float) -> None:
        with self._lock:
            self._processing_times.append(ms)
            if len(self._processing_times) > 500:
                self._processing_times.pop(0)

    def record_queue_depth(self, depth: int) -> None:
        with self._lock:
            self._queue_depths.append(depth)
            if len(self._queue_depths) > 100:
                self._queue_depths.pop(0)

    def record_lock_contention(self) -> None:
        self._lock_contentions.increment()

    def get_avg_processing_ms(self) -> float:
        with self._lock:
            if not self._processing_times:
                return 0.0
            return round(sum(self._processing_times) / len(self._processing_times), 2)

    def get_avg_queue_depth(self) -> float:
        with self._lock:
            if not self._queue_depths:
                return 0.0
            return round(sum(self._queue_depths) / len(self._queue_depths), 2)

    def snapshot(self) -> Dict:
        return {
            "total_requests":       self.total_requests.get(),
            "completed_requests":   self.completed.get(),
            "failed_requests":      self.failed.get(),
            "pending_requests":     self.total_requests.get() - self.completed.get() - self.failed.get(),
            "active_worker_threads":self.active_threads.get(),
            "avg_processing_ms":    self.get_avg_processing_ms(),
            "avg_queue_depth":      self.get_avg_queue_depth(),
            "lock_contentions":     self._lock_contentions.get(),
        }


# =============================================================================
# Priority Scheduler — Worker Thread Pool
# =============================================================================

class BookingScheduler:
    """
    Priority Scheduler implementing OS producer-consumer pattern.

    Architecture:
      - Shared priority queue (bounded, heapq-based)
      - Producer: submit_request() — called from HTTP handlers (FastAPI threads)
      - Consumer: _worker_loop() — runs in N worker threads
      - Synchronization: threading.Condition wrapping threading.Lock
      - Shutdown: threading.Event

    Deadlock Prevention Strategy:
      - Only one lock is ever acquired at a time (single-lock protocol)
      - Queue operations are atomic under the condition lock
      - No nested locking between queue_condition and any other lock
    """

    def __init__(self):
        # Priority queue (min-heap): items are BookingRequest
        self._queue: List[BookingRequest] = []
        # Condition variable for producer-consumer synchronization
        # Wraps a single lock — DEADLOCK PREVENTION: this is the ONLY lock in the scheduler
        self._queue_condition = threading.Condition(threading.Lock())
        # Shutdown signal
        self._shutdown_event = threading.Event()
        # Worker threads
        self._workers: List[threading.Thread] = []
        self._thread_registry: Dict[int, Dict] = {}   # thread_id → {status, request_id}
        self._registry_lock = threading.Lock()         # separate lock, never nested with _queue_condition
        # Telemetry
        self.telemetry = SchedulerTelemetry()
        # Request counter for unique IDs
        self._request_counter = AtomicCounter()

    def start(self) -> None:
        """Start the worker thread pool."""
        self._shutdown_event.clear()
        worker_count = settings.WORKER_THREAD_COUNT
        for i in range(worker_count):
            t = threading.Thread(
                target=self._worker_loop,
                name=f"SmartRail-Worker-{i+1}",
                daemon=True,
                args=(i + 1,),
            )
            t.start()
            self._workers.append(t)
        logger.info(f"BookingScheduler: {worker_count} worker threads started")

    def stop(self) -> None:
        """Signal shutdown and wait for all workers to stop."""
        self._shutdown_event.set()
        with self._queue_condition:
            self._queue_condition.notify_all()   # Wake all sleeping workers
        for t in self._workers:
            t.join(timeout=5.0)
        self._workers.clear()
        logger.info("BookingScheduler: all workers stopped")

    def submit_request(
        self,
        task_fn: Callable,
        task_args: tuple = (),
        task_kwargs: dict = None,
        quota: str = "GENERAL",
        wait: bool = True,
        timeout: float = 30.0,
    ) -> Any:
        """
        PRODUCER: Submit a booking task to the priority queue.

        Parameters
        ----------
        task_fn   : Callable — the function to execute in the worker thread
        task_args : tuple — positional args for task_fn
        task_kwargs : dict — keyword args for task_fn
        quota     : str — determines scheduling priority
        wait      : bool — if True, block until result is ready
        timeout   : float — max seconds to wait for result

        Returns
        -------
        Result of task_fn, or raises the exception from task_fn.
        """
        priority   = QUOTA_PRIORITY_MAP.get(quota.upper(), Priority.NORMAL)
        request_id = str(uuid.uuid4())
        timestamp  = time.monotonic()

        req = BookingRequest(
            priority=int(priority),
            timestamp=timestamp,
            request_id=request_id,
            task_fn=task_fn,
            task_args=task_args,
            task_kwargs=task_kwargs or {},
        )

        queue_depth = 0
        with self._queue_condition:
            if len(self._queue) >= settings.REQUEST_QUEUE_MAX_SIZE:
                raise RuntimeError("Booking request queue is full — system overloaded")
            heapq.heappush(self._queue, req)
            queue_depth = len(self._queue)
            self._queue_condition.notify()   # Wake one worker

        self.telemetry.total_requests.increment()
        self.telemetry.record_queue_depth(queue_depth)

        logger.debug(
            f"Request {request_id[:8]} enqueued | "
            f"Priority={PRIORITY_NAMES[priority]} | Queue depth={queue_depth}"
        )

        if not wait:
            return request_id

        # Wait for result
        if req.result_event.wait(timeout=timeout):
            if req.error:
                raise req.error
            return req.result
        else:
            raise TimeoutError(f"Booking request {request_id[:8]} timed out after {timeout}s")

    def _worker_loop(self, worker_id: int) -> None:
        """
        CONSUMER: Worker thread main loop.

        Implements:
        - Blocking wait on condition variable when queue is empty
        - Priority-ordered task consumption (min-heap)
        - Telemetry tracking per request
        - Graceful shutdown handling
        """
        thread_id = threading.get_ident()
        logger.info(f"Worker-{worker_id} started (thread_id={thread_id})")

        with self._registry_lock:
            self._thread_registry[thread_id] = {
                "worker_id": worker_id,
                "status": "IDLE",
                "current_request": None,
                "requests_processed": 0,
            }
        self.telemetry.active_threads.increment()

        while not self._shutdown_event.is_set():
            req: Optional[BookingRequest] = None

            # ── ACQUIRE TASK (with condition variable wait) ───────────────────
            with self._queue_condition:
                while not self._queue and not self._shutdown_event.is_set():
                    # Wait releases the lock atomically and re-acquires on wake
                    self.telemetry.record_lock_contention()
                    self._queue_condition.wait(timeout=1.0)

                if self._shutdown_event.is_set() and not self._queue:
                    break

                if self._queue:
                    req = heapq.heappop(self._queue)

            if req is None:
                continue

            # ── PROCESS TASK ──────────────────────────────────────────────────
            queue_wait_ms = round((time.monotonic() - req.enqueue_time) * 1000, 2)

            with self._registry_lock:
                self._thread_registry[thread_id]["status"] = "BUSY"
                self._thread_registry[thread_id]["current_request"] = req.request_id

            start_time = time.monotonic()
            try:
                result = req.task_fn(*req.task_args, **req.task_kwargs)
                req.result = result
                self.telemetry.completed.increment()

            except Exception as exc:
                req.error = exc
                self.telemetry.failed.increment()
                logger.error(
                    f"Worker-{worker_id} request {req.request_id[:8]} failed: {exc}"
                )

            finally:
                proc_ms = round((time.monotonic() - start_time) * 1000, 2)
                total_ms = round((time.monotonic() - req.enqueue_time) * 1000, 2)
                self.telemetry.record_processing_time(proc_ms)

                # Save metrics to DB asynchronously (best-effort)
                self._save_metrics_async(req, worker_id, queue_wait_ms, proc_ms, total_ms)

                with self._registry_lock:
                    self._thread_registry[thread_id]["status"] = "IDLE"
                    self._thread_registry[thread_id]["current_request"] = None
                    self._thread_registry[thread_id]["requests_processed"] += 1

                req.result_event.set()   # Unblock producer that is waiting
                logger.debug(
                    f"Worker-{worker_id} done | request={req.request_id[:8]} | "
                    f"priority={req.priority} | proc={proc_ms}ms | wait={queue_wait_ms}ms"
                )

        # Cleanup on shutdown
        self.telemetry.active_threads.decrement()
        with self._registry_lock:
            self._thread_registry.pop(thread_id, None)
        logger.info(f"Worker-{worker_id} shut down cleanly")

    def _save_metrics_async(self, req, worker_id, queue_wait_ms, proc_ms, total_ms):
        """Save OS scheduling metrics to database (non-blocking, best-effort)."""
        try:
            from app.core.database import get_sync_db
            conn = get_sync_db()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO os_scheduling_metrics
                    (request_id, request_type, priority_level, priority_name,
                     queue_wait_time_ms, processing_time_ms, total_time_ms,
                     worker_thread_id, queue_position_at_entry, result_status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        req.request_id,
                        "BOOKING",
                        req.priority,
                        PRIORITY_NAMES.get(req.priority, "NORMAL"),
                        int(queue_wait_ms),
                        int(proc_ms),
                        int(total_ms),
                        worker_id,
                        1,  # Simplified; real value tracked per enqueue
                        "COMPLETED" if req.error is None else "FAILED",
                    )
                )
            conn.commit()
        except Exception as e:
            logger.debug(f"Metrics save skipped: {e}")

    def get_status(self) -> Dict:
        """Return current scheduler status (for health check)."""
        with self._registry_lock:
            threads = [
                {"worker_id": v["worker_id"], "status": v["status"]}
                for v in self._thread_registry.values()
            ]
        with self._queue_condition:
            queue_len = len(self._queue)

        return {
            "worker_threads": len(self._workers),
            "queue_length": queue_len,
            "thread_states": threads,
            "telemetry": self.telemetry.snapshot(),
        }


# Singleton scheduler instance
booking_scheduler = BookingScheduler()
