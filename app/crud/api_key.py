from sqlmodel import Session
from typing import Optional

from app.db_models.api_key import APIKey
from app.security import generate_api_key, hash_api_key


def create_db_api_key(db_session: Session, owner: str) -> tuple[str, APIKey]:
    """
    Create a new API key in the database.
    
    This function generates a new API key, hashes it for secure storage,
    and saves it to the database. The plaintext key is returned only once.
    
    Args:
        db_session: Database session for the transaction.
        owner: The owner/user of the API key.
        
    Returns:
        tuple[str, APIKey]: A tuple containing the plaintext API key and the database object.
    """
    # Generate new plaintext API key
    plaintext_key = generate_api_key()
    
    # Hash the key for secure database storage
    hashed_key = hash_api_key(plaintext_key)
    
    # Create database object
    db_api_key = APIKey(
        hashed_key=hashed_key,
        owner=owner,
        is_active=True
    )
    
    # Add to database session and commit
    db_session.add(db_api_key)
    db_session.commit()
    db_session.refresh(db_api_key)
    
    # Return both plaintext key (shown only once) and database object
    return plaintext_key, db_api_key


def get_db_api_key_from_hash(db_session: Session, hashed_key: str) -> Optional[APIKey]:
    """
    Retrieve an API key from the database using its hash.
    
    Args:
        db_session: Database session for the query.
        hashed_key: The SHA-256 hash of the API key to look up.
        
    Returns:
        APIKey | None: The API key object if found, None otherwise.
    """
    return db_session.query(APIKey).filter(APIKey.hashed_key == hashed_key).first() 