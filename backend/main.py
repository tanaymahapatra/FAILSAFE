from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import your cleanly separated routers
from routers.auth import router as auth_router
from routers.uploads import router as uploads_router
from routers.predictions import router as predictions_router

# Initialize the FastAPI application
app = FastAPI(
    title="Secure Student Risk Prediction API",
    description="Backend for the FAILSAFE Student Risk Dashboard",
    version="1.0.0",
)

# Allow React frontend to talk to FastAPI (CORS Middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, change "*" to your React app's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register the routes from your newly created files
app.include_router(auth_router)
app.include_router(uploads_router)
app.include_router(predictions_router)


# Optional: A simple root endpoint to verify the server is running
@app.get("/", tags=["Health Check"])
def root():
    return {
        "status": "online",
        "message": "Welcome to the FAILSAFE API. The server is running securely.",
    }
