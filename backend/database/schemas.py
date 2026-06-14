from pydantic import BaseModel, Field
from typing import List, Literal, Optional

# ==========================================
# 1. API RESPONSE SCHEMAS (Output)
# ==========================================


class UploadResponse(BaseModel):
    """Schema for simple success messages after uploading CSVs."""

    message: str


class AtRiskStudent(BaseModel):
    """Schema for an individual flagged student."""

    Student_ID: str = Field(..., description="The unique identifier for the student")
    Risk_Probability: float = Field(
        ..., description="Probability of failing (e.g., 85.5)"
    )
    Status: str = Field(default="At-Risk")


class PredictionReport(BaseModel):
    """Schema for the final prediction report returned to the user."""

    Requested_By: str
    Total_Students_Evaluated: int
    At_Risk_Count: int
    At_Risk_Students: List[AtRiskStudent]


# ==========================================
# 2. DATA VALIDATION SCHEMAS (Input)
# ==========================================


class GradeUploadRow(BaseModel):
    """Strict validation rules for the Teacher's Grades CSV."""

    Student_ID: str

    # Enforce that G1 and G2 must be integers between 0 and 20
    G1: int = Field(..., ge=0, le=20, description="Period 1 Grade")
    G2: int = Field(..., ge=0, le=20, description="Period 2 Grade")


class DemographicUploadRow(BaseModel):
    """Strict validation rules for the HOD's Demographics CSV."""

    Student_ID: str

    # Numeric features with strict real-world bounds
    age: int = Field(..., ge=10, le=30, description="Student's age")
    absences: int = Field(..., ge=0, le=365, description="Number of school absences")
    failures: int = Field(..., ge=0, le=4, description="Number of past class failures")
    studytime: int = Field(..., ge=1, le=4, description="Weekly study time (1-4)")

    # 0-4 Scale
    Medu: int = Field(..., ge=0, le=4, description="Mother's education")
    Fedu: int = Field(..., ge=0, le=4, description="Father's education")

    # 1-5 Scale
    Dalc: int = Field(..., ge=1, le=5, description="Workday alcohol consumption")
    Walc: int = Field(..., ge=1, le=5, description="Weekend alcohol consumption")
    goout: int = Field(..., ge=1, le=5, description="Going out with friends")
    freetime: int = Field(..., ge=1, le=5, description="Free time after school")
    health: int = Field(..., ge=1, le=5, description="Current health status")

    # Strict Binary Strings (Must be exactly 'yes' or 'no' in the CSV)
    schoolsup: Literal["yes", "no"]
    famsup: Literal["yes", "no"]
    paid: Literal["yes", "no"]
    activities: Literal["yes", "no"]
    internet: Literal["yes", "no"]
    higher: Literal["yes", "no"]
    nursery: Literal["yes", "no"]
    romantic: Literal["yes", "no"]

    school: str
    sex: str
    address: str
    famsize: str
    Pstatus: str
    Mjob: str
    Fjob: str
    reason: str
    guardian: str
    traveltime: int = Field(..., ge=1, le=4)
    famrel: int = Field(..., ge=1, le=5)
    subject: str = Field(default="Math")
