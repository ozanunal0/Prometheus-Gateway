from fastapi import HTTPException, Header, Depends
from sqlmodel import Session

from app.db_models.api_key import APIKey
from app.security import hash_api_key
from app.crud.api_key import get_db_api_key_from_hash
from app.database import engine


def get_db():
    """
    Database session dependency for FastAPI.
    
    Yields:
        Session: A database session that will be closed after use.
    """
    with Session(engine) as session:
        yield session


def get_valid_api_key(x_api_key: str = Header(...), db: Session = Depends(get_db)) -> APIKey:
    """
    Authentication dependency that validates API keys from request headers.
    
    This dependency extracts the API key from the X-API-Key header, hashes it,
    and verifies it exists in the database and is active.
    
    Args:
        x_api_key: The API key from the X-API-Key header.
        db: Database session dependency.
        
    Returns:
        APIKey: The validated API key database object.
        
    Raises:
        HTTPException: 401 Unauthorized if the key is invalid or inactive.
    """
    # Hash the incoming API key
    hashed_key = hash_api_key(x_api_key)
    
    # Look up the key in the database
    db_api_key = get_db_api_key_from_hash(db, hashed_key)
    
    # Check if key exists and is active
    if not db_api_key or not db_api_key.is_active:
        raise HTTPException(
            status_code=401,
            detail="Invalid or inactive API key"
        )
    
    return db_api_key 