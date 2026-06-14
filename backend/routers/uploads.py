from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pydantic import ValidationError
import pandas as pd
from sqlalchemy import text, inspect

# Import your database engine and schemas
from database.database import get_engine
import database.schemas as schemas

# Import the authentication dependency
from routers.auth import get_current_user

# Initialize the Router
router = APIRouter(tags=["Data Uploads"])
engine = get_engine()

# ==========================================
# 2. DATA UPLOAD ENDPOINTS
# ==========================================


@router.post("/Upload_demographics")
def upload_demographics(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """
    HOD uploads behavioral/demographic CSV. Validated row-by-row before saving.
    """
    if current_user.get("role") != "HOD":
        raise HTTPException(
            status_code=403,
            detail="Access Denied: Only the HOD can upload demographic data.",
        )

    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed.")

    try:
        df_demographics = pd.read_csv(file.file)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid CSV file format.")

    required_cols = [
        "Student_ID",
        "school",
        "sex",
        "age",
        "address",
        "famsize",
        "Pstatus",
        "Medu",
        "Fedu",
        "Mjob",
        "Fjob",
        "reason",
        "guardian",
        "traveltime",
        "studytime",
        "failures",
        "schoolsup",
        "famsup",
        "paid",
        "activities",
        "nursery",
        "higher",
        "internet",
        "romantic",
        "famrel",
        "freetime",
        "goout",
        "Dalc",
        "Walc",
        "health",
        "absences",
        "subject",
    ]

    missing_cols = [col for col in required_cols if col not in df_demographics.columns]
    if missing_cols:
        raise HTTPException(
            status_code=400, detail=f"CSV missing required columns: {missing_cols}"
        )

    # Clean data and prevent duplicate entries!
    df_demographics = df_demographics.dropna(subset=["Student_ID"])
    df_demographics = df_demographics.drop_duplicates(
        subset=["Student_ID"], keep="last"
    )

    records = df_demographics.to_dict(orient="records")
    validated_data = []

    for index, row in enumerate(records):
        try:
            valid_row = schemas.DemographicUploadRow(**row)
            validated_data.append(valid_row.model_dump())
        except ValidationError as e:
            raise HTTPException(
                status_code=422,
                detail=f"Data error on row {index + 1} for Student {row.get('Student_ID', 'Unknown')}: {e.errors()}",
            )

    clean_df = pd.DataFrame(validated_data)
    clean_df.to_sql("student_profiles", con=engine, if_exists="replace", index=False)

    return {
        "message": f"Successfully verified and saved profiles for {len(clean_df)} students."
    }


@router.post("/upload_grades", response_model=schemas.UploadResponse)
def upload_grades(
    file: UploadFile = File(...), current_user: dict = Depends(get_current_user)
):
    """
    Teacher uploads G1 and G2 grades CSV. Validated row-by-row before saving.
    """
    if current_user.get("role") != "Teacher":
        raise HTTPException(
            status_code=403, detail="Access Denied: Only Teachers can upload grades."
        )

    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed.")

    try:
        df_grades = pd.read_csv(file.file)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid CSV file format.")

    required_columns = ["Student_ID", "G1", "G2"]
    if not all(col in df_grades.columns for col in required_columns):
        raise HTTPException(
            status_code=400, detail=f"CSV must contain: {required_columns}"
        )

    # Clean data and prevent duplicate entries!
    df_grades = df_grades.dropna(subset=["Student_ID", "G1", "G2"])
    df_grades = df_grades.drop_duplicates(subset=["Student_ID"], keep="last")

    records = df_grades.to_dict(orient="records")
    validated_data = []

    for index, row in enumerate(records):
        try:
            valid_row = schemas.GradeUploadRow(**row)
            validated_data.append(valid_row.model_dump())
        except ValidationError as e:
            raise HTTPException(
                status_code=422,
                detail=f"Data error on row {index + 1} for Student {row.get('Student_ID', 'Unknown')}: {e.errors()}",
            )

    clean_df = pd.DataFrame(validated_data)
    teacher_username = current_user["username"]
    clean_df["Teacher_ID"] = teacher_username

    inspector = inspect(engine)

    if not inspector.has_table("student_grades"):
        clean_df.to_sql("student_grades", con=engine, if_exists="replace", index=False)
    else:
        existing_columns = [
            col["name"] for col in inspector.get_columns("student_grades")
        ]

        if "Teacher_ID" not in existing_columns:
            clean_df.to_sql(
                "student_grades", con=engine, if_exists="replace", index=False
            )
        else:
            with engine.connect() as conn:
                conn.execute(
                    text(
                        f"DELETE FROM student_grades WHERE \"Teacher_ID\" = '{teacher_username}'"
                    )
                )
                conn.commit()
            clean_df.to_sql(
                "student_grades", con=engine, if_exists="append", index=False
            )

    return {
        "message": f"Successfully verified and saved grades for {len(clean_df)} students under teacher: {teacher_username}."
    }


@router.post("/upload_grades_g1")
def upload_grades_g1(
    file: UploadFile = File(...), current_user: dict = Depends(get_current_user)
):
    """
    Teacher uploads G1 grades only CSV.
    """
    if current_user.get("role") != "Teacher":
        raise HTTPException(
            status_code=403, detail="Access Denied: Only Teachers can upload grades."
        )

    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed.")

    try:
        df_grades = pd.read_csv(file.file)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid CSV file format.")

    required_columns = ["Student_ID", "G1"]
    if not all(col in df_grades.columns for col in required_columns):
        raise HTTPException(
            status_code=400, detail=f"CSV must contain: {required_columns}"
        )

    # Clean data and prevent duplicate entries!
    df_grades = df_grades.dropna(subset=["Student_ID", "G1"])
    df_grades = df_grades.drop_duplicates(subset=["Student_ID"], keep="last")

    df_grades["G2"] = 0

    records = df_grades.to_dict(orient="records")
    validated_data = []

    for index, row in enumerate(records):
        try:
            valid_row = schemas.GradeUploadRow(**row)
            validated_data.append(valid_row.model_dump())
        except ValidationError as e:
            raise HTTPException(
                status_code=422,
                detail=f"Data error on row {index + 1} for Student {row.get('Student_ID', 'Unknown')}: {e.errors()}",
            )

    clean_df = pd.DataFrame(validated_data)
    teacher_username = current_user["username"]
    clean_df["Teacher_ID"] = teacher_username

    inspector = inspect(engine)

    if not inspector.has_table("student_grades"):
        clean_df.to_sql("student_grades", con=engine, if_exists="replace", index=False)
    else:
        existing_columns = [
            col["name"] for col in inspector.get_columns("student_grades")
        ]

        if "Teacher_ID" not in existing_columns:
            clean_df.to_sql(
                "student_grades", con=engine, if_exists="replace", index=False
            )
        else:
            with engine.connect() as conn:
                conn.execute(
                    text(
                        f"DELETE FROM student_grades WHERE \"Teacher_ID\" = '{teacher_username}'"
                    )
                )
                conn.commit()
            clean_df.to_sql(
                "student_grades", con=engine, if_exists="append", index=False
            )

    return {
        "message": f"Successfully verified and saved G1 grades for {len(clean_df)} students under teacher: {teacher_username}."
    }
