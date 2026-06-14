from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
import pandas as pd
from sqlalchemy import text

# Import your database engine
from database.database import get_engine

# Import your ML pipeline functions
# (If you moved ml_pipeline.py into an "ml" folder, change this to: from ml.pipeline import ...)
from ml.pipeline import (
    engineer_features,
    generate_predictions_g1,
    generate_predictions_g2,
    generate_predictions_demo,
)

# Import the authentication dependency

from routers.auth import get_current_user

# Initialize the Router
router = APIRouter(tags=["Predictions"])
engine = get_engine()

# ==========================================
# PREDICTION ENDPOINTS
# ==========================================


@router.get("/predict_risk")
def predict_risk(
    teacher_filter: Optional[str] = None, current_user: dict = Depends(get_current_user)
):
    """
    Merges demographic and grade data from Postgres, runs feature engineering,
    applies role-based data isolation, and passes the data through the FULL model.
    """
    join_query = text("""
        SELECT p.*, g."G1", g."G2", g."Teacher_ID"
        FROM student_profiles p
        INNER JOIN student_grades g ON p."Student_ID" = g."Student_ID"
    """)

    try:
        merged_df = pd.read_sql(join_query, con=engine)
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Database error. Ensure both CSVs have been uploaded.",
        )

    if merged_df.empty:
        raise HTTPException(
            status_code=404,
            detail="No matching students found to predict. Make sure Student_IDs match in both files.",
        )

    # ROLE-BASED FILTERING
    if current_user.get("role") == "Teacher":
        merged_df = merged_df[merged_df["Teacher_ID"] == current_user["username"]]
    elif current_user.get("role") == "HOD" and teacher_filter:
        merged_df = merged_df[merged_df["Teacher_ID"] == teacher_filter]

    if merged_df.empty:
        raise HTTPException(
            status_code=404,
            detail="No student data found for your access level or the selected filter.",
        )

    processing_df = merged_df.drop(columns=["Teacher_ID"])
    ready_df = engineer_features(processing_df)

    try:
        risk_report = generate_predictions_g2(ready_df)

        teacher_lookup = dict(zip(merged_df["Student_ID"], merged_df["Teacher_ID"]))
        for student in risk_report:
            student["Teacher_ID"] = teacher_lookup.get(student["Student_ID"], "Unknown")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model execution failed: {str(e)}")

    return {
        "Requested_By": current_user["username"],
        "Role": current_user.get("role"),
        "Viewing_Teacher_Data": (
            teacher_filter
            if teacher_filter
            else (
                "ALL (HOD View)"
                if current_user.get("role") == "HOD"
                else current_user["username"]
            )
        ),
        "Total_Students_Evaluated": len(ready_df),
        "At_Risk_Count": len(risk_report),
        "At_Risk_Students": risk_report,
    }


@router.get("/predict_risk_demo_only")
def predict_risk_demo_only(
    teacher_filter: Optional[str] = None, current_user: dict = Depends(get_current_user)
):
    """
    Predicts risk using Demographic data ONLY.
    Uses a LEFT JOIN so Teachers are restricted to their own students.
    """
    join_query = text("""
        SELECT p.*, g."Teacher_ID"
        FROM student_profiles p
        LEFT JOIN student_grades g ON p."Student_ID" = g."Student_ID"
    """)

    try:
        df = pd.read_sql(join_query, con=engine)
    except Exception:
        raise HTTPException(status_code=500, detail="Database error.")

    if df.empty:
        raise HTTPException(status_code=404, detail="No demographic data found.")

    # ROLE-BASED FILTERING
    if current_user.get("role") == "Teacher":
        df = df[df["Teacher_ID"] == current_user["username"]]
    elif current_user.get("role") == "HOD" and teacher_filter:
        df = df[df["Teacher_ID"] == teacher_filter]

    if df.empty:
        raise HTTPException(
            status_code=404,
            detail="No student data found for your access level or the selected filter.",
        )

    df["G1"] = 0
    df["G2"] = 0

    # Save lookup dict before dropping Teacher_ID
    teacher_lookup = dict(zip(df["Student_ID"], df["Teacher_ID"].fillna("Unassigned")))
    processing_df = df.drop(columns=["Teacher_ID"])
    ready_df = engineer_features(processing_df)

    try:
        risk_report = generate_predictions_demo(ready_df)

        # Attach the proper teacher ID to the payload
        for student in risk_report:
            student["Teacher_ID"] = teacher_lookup.get(
                student["Student_ID"], "Unassigned"
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model execution failed: {str(e)}")

    return {
        "Requested_By": current_user["username"],
        "Role": current_user.get("role"),
        "Viewing_Teacher_Data": (
            teacher_filter
            if teacher_filter
            else (
                "ALL (HOD View)"
                if current_user.get("role") == "HOD"
                else current_user["username"]
            )
        ),
        "Total_Students_Evaluated": len(ready_df),
        "At_Risk_Count": len(risk_report),
        "At_Risk_Students": risk_report,
    }


@router.get("/predict_risk_demo_g1")
def predict_risk_demo_g1(
    teacher_filter: Optional[str] = None, current_user: dict = Depends(get_current_user)
):
    """
    Predicts risk using Demographic data + G1 grades.
    """
    join_query = text("""
        SELECT p.*, g."G1", g."Teacher_ID"
        FROM student_profiles p
        INNER JOIN student_grades g ON p."Student_ID" = g."Student_ID"
    """)

    df = pd.read_sql(join_query, con=engine)
    df["G2"] = 0

    if current_user.get("role") == "Teacher":
        df = df[df["Teacher_ID"] == current_user["username"]]
    elif current_user.get("role") == "HOD" and teacher_filter:
        df = df[df["Teacher_ID"] == teacher_filter]

    if df.empty:
        raise HTTPException(
            status_code=404,
            detail="No student data found for your access level or the selected filter.",
        )

    processing_df = df.drop(columns=["Teacher_ID"])
    ready_df = engineer_features(processing_df)

    try:
        risk_report = generate_predictions_g1(ready_df)

        teacher_lookup = dict(zip(df["Student_ID"], df["Teacher_ID"]))
        for student in risk_report:
            student["Teacher_ID"] = teacher_lookup.get(student["Student_ID"], "Unknown")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model execution failed: {str(e)}")

    return {
        "Requested_By": current_user["username"],
        "Role": current_user.get("role"),
        "Viewing_Teacher_Data": (
            teacher_filter
            if teacher_filter
            else (
                "ALL (HOD View)"
                if current_user.get("role") == "HOD"
                else current_user["username"]
            )
        ),
        "Total_Students_Evaluated": len(ready_df),
        "At_Risk_Count": len(risk_report),
        "At_Risk_Students": risk_report,
    }
