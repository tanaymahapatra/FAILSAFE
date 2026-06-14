import numpy as np
import pandas as pd
import joblib
import shap
import os

# ---------------------------------------------------------
# 1. INITIALIZE VARIABLES, MODELS & DESCRIPTIONS
# ---------------------------------------------------------
explainer_demo = None
explainer_g2 = None
explainer_g1 = None
model_pipeline_demo = None
model_pipeline_g2 = None
model_pipeline_g1 = None


# This gets the directory where pipeline.py lives (which is 'ml')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# This creates the full path to your saved_models folder
MODELS_DIR = os.path.join(BASE_DIR, "saved_models")

# Load models using the absolute path
try:
    model_pipeline_demo = joblib.load(
        os.path.join(MODELS_DIR, "failsafe_demo_model.pkl")
    )
    model_demo = model_pipeline_demo.named_steps["classifier"]
    explainer_demo = shap.TreeExplainer(model_demo)
except Exception as e:
    print(f"Error loading demo model: {e}")
    model_pipeline_demo = None

try:
    model_pipeline_g2 = joblib.load(os.path.join(MODELS_DIR, "failsafe_g2_model.pkl"))
    model_g2 = model_pipeline_g2.named_steps["classifier"]
    explainer_g2 = shap.TreeExplainer(model_g2)
except Exception as e:
    print(f"Error loading g2 model: {e}")
    model_pipeline_g2 = None

try:
    model_pipeline_g1 = joblib.load(os.path.join(MODELS_DIR, "failsafe_g1_model.pkl"))
    model_g1 = model_pipeline_g1.named_steps["classifier"]
    explainer_g1 = shap.TreeExplainer(model_g1)
except Exception as e:
    print(f"Error loading g1 model: {e}")
    model_pipeline_g1 = None

# --- NEW: FEATURE DESCRIPTION DICTIONARY ---
FEATURE_DICTIONARY = {
    "Medu": "Mother's Education Level",
    "Fedu": "Father's Education Level",
    "failures": "Number of Past Class Failures",
    "subject": "Enrolled Subject (Math/Portuguese)",
    "school": "School Attended",
    "age_failures": "Compound Risk of Age & Failures",
    "Parent_Edu_Sum": "Combined Parental Education Level",
    "Social_Life": "Amount of Going Out & Free Time",
    "Health_Absence": "Impact of Health Issues on Absences",
    "Study_per_Absent": "Ratio of Study Time to Absences",
    "traveltime": "Commute Time to School",
    "parent_support": "Combined Parental Education & Support",
    "Total_Alcohol": "Total Weekend & Workday Alcohol Consumption",
    "Risk_Index": "Overall Calculated Behavioral Risk Index",
    "Study_vs_Social": "Balance of Study Time vs Social Life",
    "G1": "First Period Grade",
    "G2": "Second Period Grade",
    "G1_below_pass": "Failed First Period",
    "G2_below_pass": "Failed Second Period",
    "Both_failing": "Failed Both Grading Periods",
    "G2_G1_delta": "Grade Trajectory (Difference between G2 & G1)",
    "G_avg_P1P2": "Average Grade Across P1 and P2",
    "studytime": "Weekly Study Time",
    "absences": "Total School Absences",
    "absences_log": "Logarithmic Scale of Absences",
    "studytime_sq": "Squared Impact of Study Time",
    "Fail_Burden": "Compound Burden of Failures and Alcohol",
    "Study_Support": "Total Academic Support (Family, School, Paid)",
    "Support_per_Fail": "Academic Support Relative to Past Failures",
    "sex": "Student Gender",
    "age": "Student Age",
}


# ---------------------------------------------------------
# 2. FEATURE ENGINEERING
# ---------------------------------------------------------
def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    df_engineered = df.copy()

    # BASIC AGGREGATIONS
    df_engineered["Total_Alcohol"] = df_engineered["Dalc"] + df_engineered["Walc"]
    df_engineered["Parent_Edu_Sum"] = df_engineered["Medu"] + df_engineered["Fedu"]
    df_engineered["Social_Life"] = df_engineered["goout"] + df_engineered["freetime"]

    # SUPPORT & BEHAVIOUR - binary encoding
    for col in [
        "schoolsup",
        "famsup",
        "paid",
        "activities",
        "internet",
        "higher",
        "nursery",
        "romantic",
    ]:
        if col in df_engineered.columns:
            df_engineered[col + "_bin"] = df_engineered[col].map({"yes": 1, "no": 0})

    # Only calculate if the bin columns were created
    if "schoolsup_bin" in df_engineered.columns:
        df_engineered["Study_Support"] = (
            df_engineered["schoolsup_bin"]
            + df_engineered["famsup_bin"]
            + df_engineered["paid_bin"]
        )

    # RATIO / EFFICIENCY FEATURES
    df_engineered["Study_vs_Social"] = df_engineered["studytime"] / (
        df_engineered["Social_Life"] + 1
    )
    df_engineered["Study_per_Absent"] = df_engineered["studytime"] / (
        df_engineered["absences"] + 1
    )

    if "Study_Support" in df_engineered.columns:
        df_engineered["Support_per_Fail"] = df_engineered["Study_Support"] / (
            df_engineered["failures"] + 1
        )

    # COMPOUND RISK FEATURES
    df_engineered["Fail_Burden"] = (
        df_engineered["failures"] * df_engineered["Total_Alcohol"]
    )
    df_engineered["Health_Absence"] = (
        df_engineered["health"] * df_engineered["absences"]
    )
    df_engineered["Risk_Index"] = (
        df_engineered["failures"] * 2
        + df_engineered["Total_Alcohol"]
        + df_engineered["absences"] / 10
        + (5 - df_engineered["health"])
    )

    # GRADE TRAJECTORY
    if "G1" in df_engineered.columns:
        df_engineered["G1_norm"] = df_engineered["G1"] / 20.0
        df_engineered["G1_below_pass"] = (df_engineered["G1"] < 10).astype(int)

    if "G2" in df_engineered.columns:
        df_engineered["G2_norm"] = df_engineered["G2"] / 20.0
        df_engineered["G2_below_pass"] = (df_engineered["G2"] < 10).astype(int)

    if "G1" in df_engineered.columns and "G2" in df_engineered.columns:
        df_engineered["G2_G1_delta"] = df_engineered["G2"] - df_engineered["G1"]
        df_engineered["G_avg_P1P2"] = (df_engineered["G1"] + df_engineered["G2"]) / 2.0
        df_engineered["Both_failing"] = (
            df_engineered["G1_below_pass"] * df_engineered["G2_below_pass"]
        )

    # 3-F POLYNOMIAL / INTERACTION
    df_engineered["studytime_sq"] = df_engineered["studytime"] ** 2
    df_engineered["absences_log"] = np.log1p(df_engineered["absences"])
    df_engineered["age_failures"] = df_engineered["age"] * df_engineered["failures"]

    if "Study_Support" in df_engineered.columns:
        df_engineered["parent_support"] = (
            df_engineered["Parent_Edu_Sum"] * df_engineered["Study_Support"]
        )

    return df_engineered


# ---------------------------------------------------------
# 3. HELPER FUNCTION: FORMAT SHAP REASONS
# ---------------------------------------------------------
def format_shap_reasons(shap_data):
    """
    Takes raw SHAP data, cleans the scikit-learn pipeline prefixes,
    maps the feature to a description, and returns a formatted list.
    """
    top_reasons = []
    for name, val in shap_data:
        # 1. Clean the prefix (e.g., "remainder__failures" -> "failures")
        clean_name = name.split("__")[-1]

        # 2. Get the description (defaults to the clean name if not in dict)
        description = FEATURE_DICTIONARY.get(
            clean_name, clean_name.replace("_", " ").title()
        )

        # 3. Determine direction of impact
        direction = "Increases Risk" if val > 0 else "Decreases Risk"

        # 4. Format: "Medu: Mother's Education Level (Increases Risk)"
        top_reasons.append(f"{clean_name}: {description} ({direction})")

    return top_reasons


# ---------------------------------------------------------
# 4. PREDICTION FUNCTIONS
# ---------------------------------------------------------
def generate_predictions_g2(df: pd.DataFrame) -> list:
    X_live_g2 = df.drop(columns=["Student_ID"], errors="ignore")
    probabilities = model_pipeline_g2.predict_proba(X_live_g2)[:, 1]
    predictions = (probabilities >= 0.325).astype(int)

    X_processed = model_pipeline_g2[:-1].transform(X_live_g2)
    shap_values = explainer_g2(X_processed)

    if hasattr(X_processed, "columns"):
        feature_names = X_processed.columns
    else:
        feature_names = model_pipeline_g2[:-1].get_feature_names_out()

    results = []
    for i, (student_id, prob, pred) in enumerate(
        zip(df["Student_ID"], probabilities, predictions)
    ):
        if pred == 1:
            vals = shap_values[i].values
            shap_data = sorted(
                zip(feature_names, vals), key=lambda x: abs(x[1]), reverse=True
            )[:3]

            results.append(
                {
                    "Student_ID": str(student_id),
                    "Risk_Probability": round(float(prob) * 100, 2),
                    "Status": "At-Risk",
                    "Top_Reasons": format_shap_reasons(
                        shap_data
                    ),  # <-- Uses new helper
                }
            )
    return results


def generate_predictions_g1(df: pd.DataFrame) -> list:
    cols_to_drop = ["G2", "G2_G1_delta", "G2_below_pass", "Both_failing", "Student_ID"]
    X_live_g1 = df.drop(columns=cols_to_drop, errors="ignore")
    probabilities = model_pipeline_g1.predict_proba(X_live_g1)[:, 1]
    predictions = (probabilities >= 0.260).astype(int)

    X_processed = model_pipeline_g1[:-1].transform(X_live_g1)
    shap_values = explainer_g1(X_processed)

    if hasattr(X_processed, "columns"):
        feature_names = X_processed.columns
    else:
        feature_names = model_pipeline_g1[:-1].get_feature_names_out()

    results = []
    for i, (student_id, prob, pred) in enumerate(
        zip(df["Student_ID"], probabilities, predictions)
    ):
        if pred == 1:
            vals = shap_values[i].values
            shap_data = sorted(
                zip(feature_names, vals), key=lambda x: abs(x[1]), reverse=True
            )[:3]

            results.append(
                {
                    "Student_ID": str(student_id),
                    "Risk_Probability": round(float(prob) * 100, 2),
                    "Status": "At-Risk",
                    "Top_Reasons": format_shap_reasons(
                        shap_data
                    ),  # <-- Uses new helper
                }
            )
    return results


def generate_predictions_demo(df: pd.DataFrame) -> list:
    cols_to_drop = [
        "G2",
        "G2_G1_delta",
        "G2_below_pass",
        "Both_failing",
        "G1",
        "G1_below_pass",
        "Student_ID",
        "G1_norm",
        "G2_norm",
        "G_avg_P1P2",
    ]
    X_live_demo = df.drop(columns=cols_to_drop, errors="ignore")
    probabilities = model_pipeline_demo.predict_proba(X_live_demo)[:, 1]
    predictions = (probabilities >= 0.157).astype(int)

    X_processed = model_pipeline_demo[:-1].transform(X_live_demo)
    shap_values = explainer_demo(X_processed)

    if hasattr(X_processed, "columns"):
        feature_names = X_processed.columns
    else:
        feature_names = model_pipeline_demo[:-1].get_feature_names_out()

    results = []
    for i, (student_id, prob, pred) in enumerate(
        zip(df["Student_ID"], probabilities, predictions)
    ):
        if pred == 1:
            vals = shap_values[i].values
            shap_data = sorted(
                zip(feature_names, vals), key=lambda x: abs(x[1]), reverse=True
            )[:3]

            results.append(
                {
                    "Student_ID": str(student_id),
                    "Risk_Probability": round(float(prob) * 100, 2),
                    "Status": "At-Risk",
                    "Top_Reasons": format_shap_reasons(
                        shap_data
                    ),  # <-- Uses new helper
                }
            )
    return results
