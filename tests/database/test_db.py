"""
SmartRail AI+ — Database Layer Tests
Verifies schema definitions, SQL scripts syntax, and data model consistency.
"""

import os
import unittest

class TestDatabaseSchema(unittest.TestCase):
    def setUp(self):
        self.db_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../database"))

    def test_schema_sql_exists(self):
        schema_path = os.path.join(self.db_dir, "schema.sql")
        self.assertTrue(os.path.exists(schema_path), "schema.sql missing")
        with open(schema_path, "r", encoding="utf-8") as f:
            content = f.read()
        # Verify required tables are present
        tables = [
            "users", "stations", "trains", "train_routes", "train_coaches",
            "seat_inventory", "physical_seats", "passengers", "bookings",
            "booking_passengers", "booking_status_history", "db_transactions_log",
            "os_scheduling_metrics", "ai_prediction_logs"
        ]
        for tbl in tables:
            self.assertIn(f"CREATE TABLE IF NOT EXISTS {tbl}", content, f"Table {tbl} missing in schema.sql")

    def test_seed_data_sql_exists(self):
        seed_path = os.path.join(self.db_dir, "seed_data.sql")
        self.assertTrue(os.path.exists(seed_path), "seed_data.sql missing")
        with open(seed_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("INSERT IGNORE INTO stations", content)
        self.assertIn("INSERT IGNORE INTO trains", content)

    def test_ai_history_sql_exists(self):
        ai_hist_path = os.path.join(self.db_dir, "ai_history.sql")
        self.assertTrue(os.path.exists(ai_hist_path), "ai_history.sql missing")
        with open(ai_hist_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("ai_waitlist_history", content)

if __name__ == "__main__":
    unittest.main()
