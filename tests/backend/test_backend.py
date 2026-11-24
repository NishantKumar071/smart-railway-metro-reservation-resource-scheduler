"""
SmartRail AI+ — Backend Integration Tests
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend")))

from app.core.scheduler import BookingScheduler, Priority, PRIORITY_NAMES
from app.core.security import hash_password, verify_password, create_access_token, decode_token

class TestBackendCore(unittest.TestCase):
    def test_password_hashing(self):
        pwd = "SecurePassword123!"
        hashed = hash_password(pwd)
        self.assertTrue(verify_password(pwd, hashed))
        self.assertFalse(verify_password("WrongPassword", hashed))

    def test_jwt_token(self):
        payload = {"sub": 42, "role": "ADMIN", "email": "admin@smartrail.local"}
        token = create_access_token(payload)
        decoded = decode_token(token)
        self.assertEqual(decoded["sub"], 42)
        self.assertEqual(decoded["role"], "ADMIN")

    def test_priority_scheduler_queue_order(self):
        scheduler = BookingScheduler()
        scheduler.start()

        def dummy_task(msg):
            return f"Processed: {msg}"

        # Submit task with Emergency priority
        res1 = scheduler.submit_request(dummy_task, task_args=("Emergency Task",), quota="EMERGENCY")
        self.assertEqual(res1, "Processed: Emergency Task")

        # Submit task with General priority
        res2 = scheduler.submit_request(dummy_task, task_args=("General Task",), quota="GENERAL")
        self.assertEqual(res2, "Processed: General Task")

        scheduler.stop()

if __name__ == "__main__":
    unittest.main()
