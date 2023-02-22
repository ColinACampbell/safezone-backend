from app.database import SessionLocal

def get_db():
    """
    It creates a database connection and returns it to the caller
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()