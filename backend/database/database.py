import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

# 1. Actually execute the load_dotenv function!
load_dotenv()

# 2. Updated fallback host to "db" instead of "host.docker.internal"
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://myuser:mypassword@db:5432/failsafe_db",
)

engine = create_engine(DATABASE_URL)


def get_engine():
    return engine
