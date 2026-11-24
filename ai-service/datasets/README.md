# SmartRail AI+ — Training Datasets

## DISCLAIMER
All data in these CSV files is SYNTHETIC (algorithmically generated)
for academic demonstration purposes only.

This data does NOT represent real Indian Railways booking records,
cancellation patterns, or operational data.

## Files

### waitlist_training_data.csv
Features for predicting waitlist confirmation probability.
Target column: `was_confirmed` (1=confirmed, 0=remained on waitlist)

### recommendation_training_data.csv
Features for scoring train recommendations based on user preferences.
Target column: `recommendation_score` (0.0–1.0)

## Academic Note
Trained models are for demonstration of ML concepts in the context of
a railway reservation system. Predictions must NOT be used for real
booking decisions.
