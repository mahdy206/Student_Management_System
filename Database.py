import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Support both SQL Server (production) and SQLite (testing/docker)
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Docker / environment-configured DB (PostgreSQL or SQLite)
    if DATABASE_URL.startswith("sqlite"):
        engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    else:
        engine = create_engine(DATABASE_URL)
else:
    # Default: SQL Server via Windows auth (local dev)
    SQLALCHEMY_DATABASE_URL = (
        "mssql+pyodbc://@Mariam\SQLEXPRESS/Student_Management_System"
        "?driver=ODBC+Driver+17+for+SQL+Server"
        "&trusted_connection=yes"
    )

    engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
