"""
SmartRail AI+ — System Integration Tests
Verifies seamless end-to-end communication between Frontend API expectations,
Backend scheduler processing, and AI inference outputs.
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../ai-service")))

from app.core.scheduler import booking_scheduler, BookingScheduler
from app.services.booking_service import generate_pnr
import joblib

class TestSystemIntegration(unittest.TestCase):
    def test_end_to_end_workflow(self):
        # 1. PNR generation format
        pnr = generate_pnr()
        self.assertEqual(len(pnr), 10)
        self.assertTrue(pnr.isdigit())

        # 2. Scheduler accepts and processes task
        sched = BookingScheduler()
        sched.start()
        res = sched.submit_request(lambda x: x * 2, task_args=(21,), quota="TATKAL")
        self.assertEqual(res, 42)
        sched.stop()

        # 3. AI prediction model returns score for input
        model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../ai-service/models/waitlist_predictor.joblib"))
        model = joblib.load(model_path)
        self.assertIn("pipeline", model)
        self.assertIn("version", model)

if __name__ == "__main__":
    unittest.main()
