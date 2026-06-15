# Failsafe: Intelligent Student Intervention Platform

Failsafe is an AI-driven, full-stack application designed to predict student academic performance and identify "At-Risk" students early. By combining machine learning with Explainable AI (SHAP), the platform provides educators with transparent, data-driven insights to plan timely academic interventions.

---

## 🚀 How to Run the Application

You can run the application either using Docker (Recommended) or manually on your local machine. Before starting, ensure you have created a `.env` file in the root directory with your database credentials and secret key.

### Method 1: Using Docker (Recommended)
This is the easiest method and requires zero manual setup of databases or environments.

**Prerequisite:** Ensure Docker Desktop is installed and running.

1. Open your terminal in the project root directory.
2. Create a `.env' in the root directory(a '.env.example' file is given as demo)file:
```env
   DATABASE_URL=postgresql://myuser:mypassword@db:5432/failsafe_db
   SECRET_KEY=super_secret_failsafe_key_2026
   ```
3. Run the following command to build and start all services:
```bash
   docker compose up --build
   ```
4. Wait for the terminal to show that the database, backend, and frontend are running.

### Method 2: Manual Setup (Without Docker)
If you prefer to run the application locally without Docker, follow these steps. 

**Prerequisites:** Python 3.11+, Node.js (v22), and a local PostgreSQL server running.

**1. Database Setup:**
*   Create a local PostgreSQL database named `failsafe_db`.
*   Update your `.env` file so the `DATABASE_URL` points to your local database (e.g., `postgresql://user:password@localhost:5432/failsafe_db`).

**2. Start the Backend (Terminal 1):**
```bash
# Navigate to the backend folder
cd backend

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the FastAPI server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**3. Start the Frontend (Terminal 2):**
```bash
# Navigate to the frontend folder
cd frontend

# Install Node modules
npm install

# Start the Vite development server
npm run dev
```

---

## 💻 How to Use the App

Once the application is running, follow these steps to test the platform:

1. **Open the Dashboard:** Navigate to http://localhost:5173 in your web browser.
2. **Log In:** Use your administrator or teacher credentials to access the secure dashboard.
3. **Upload Student Data:** 
   * Go to the bulk upload section.
   * Upload a formatted CSV file containing student records (demographics, absences, and previous grades).
4. **Analyze Predictions:** 
   * The system will automatically process the data and immediately flag "At-Risk" students.
5. **View SHAP Insights:** 
   * Click on any flagged student's profile to view their **Explainable AI (SHAP) chart**. 
   * This visualization will break down exactly *why* the student is at risk (e.g., high absences, low study time, or previous failures), allowing you to plan targeted academic interventions.

---

## 🏗 Tech Stack Overview

*   **Frontend:** React, Vite, Tailwind CSS (Runs on port `5173`)
*   **Backend:** FastAPI, Python 3.11, Uvicorn (Runs on port `8000`)
*   **Database:** PostgreSQL, SQLAlchemy ORM
*   **Machine Learning:** Scikit-learn, XGBoost, SHAP (Explainable AI)
*   **Infrastructure:** Docker, Docker Compose
