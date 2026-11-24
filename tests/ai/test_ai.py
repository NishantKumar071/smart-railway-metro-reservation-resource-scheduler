"""
SmartRail AI+ — AI Service Automated Tests
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../ai-service")))

import joblib

class TestAIService(unittest.TestCase):
    def setUp(self):
        self.models_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../ai-service/models"))
        self.wl_model_path = os.path.join(self.models_dir, "waitlist_predictor.joblib")
        self.rec_model_path = os.path.join(self.models_dir, "recommendation_model.joblib")

    def test_model_files_exist(self):
        """Verify model serialization files exist."""
        self.assertTrue(os.path.exists(self.wl_model_path), "Waitlist model file missing")
        self.assertTrue(os.path.exists(self.rec_model_path), "Recommendation model file missing")

    def test_waitlist_model_inference(self):
        """Verify model inference works without errors and returns probabilities in [0, 1]."""
        model_data = joblib.load(self.wl_model_path)
        pipeline = model_data["pipeline"]

        # Synthetic feature vector
        import numpy as np
        # 12 features
        X = np.array([[0.2, 0.5, 0, 0.25, 0, 0, 1, 1, 6, 20, 4, 20]])
        prob = pipeline.predict_proba(X)[0][1]

        self.assertGreaterEqual(prob, 0.0)
        self.assertLessEqual(prob, 1.0)
        print(f"\n[Test AI] Waitlist Probability Inference: {prob:.4f}")

    def test_recommendation_model_inference(self):
        """Verify recommendation regression model inference."""
        model_data = joblib.load(self.rec_model_path)
        pipeline = model_data["pipeline"]

        import numpy as np
        # 7 features
        X = np.array([[1, 2, 0, 5, 2, 1, 2]])
        score = pipeline.predict(X)[0]
        self.assertIsInstance(float(score), float)
        print(f"[Test AI] Train Recommendation Score Inference: {score:.4f}")

if __name__ == "__main__":
    unittest.main()
