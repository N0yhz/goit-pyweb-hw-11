from typing import List
from datetime import date, timedelta
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request

from src.database.database import get_db
from src.database.models import User
from src.repository import contacts as contacts_repo
from src.schemas import ContactCreate, ContactOut
from src.repository.auth import require_verified_user, get_current_user
from src.utils.limiter import limiter

router = APIRouter()


@router.post("/contacts/", response_model=ContactOut)
@limiter.limit("5/minute") 
def create_contact(
    request: Request,
    contact: ContactCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified_user)
):
    return contacts_repo.create_contact(db=db, contact=contact, user_id=current_user.id)

@router.get("/contacts/", response_model = List[ContactOut])
@limiter.limit("5/minute") 
def read_contacts(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified_user)
):
    contacts = contacts_repo.get_contacts(db, user_id=current_user.id, skip=skip, limit=limit)
    return contacts

@router.get("/contacts/{contact_id}", response_model=ContactOut)
@limiter.limit("5/minute") 
def read_contact(
    request: Request,
    contact_id:int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified_user)
):
    contact = contacts_repo.get_contact(db, user_id=current_user.id, contact_id=contact_id)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail = "Contact not found",
                            )
    return contact

@router.put("/contacts/{contact_id}", response_model=ContactOut)
@limiter.limit("5/minute") 
def update_contact(
    request: Request,
    contact_id: int,
    contact: ContactCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified_user)
):
    updated_contact = contacts_repo.update_contact(db, user_id=current_user.id, contact_id=contact_id, contact=contact)
    if updated_contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail = "Contact not found",
                            )
    return updated_contact

@router.delete("/contacts/{contact_id}", response_model=ContactOut)
@limiter.limit("5/minute") 
def delete_contact(
    request: Request,
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified_user),
):
    deleted_contact = contacts_repo.delete_contact(db, user_id=current_user.id, contact_id=contact_id)
    if deleted_contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail = "Contact not found",
                            )
    return deleted_contact

@router.get("/contacts/search", response_model=List[ContactOut])
@limiter.limit("10/minute") 
def search_contact(
    request: Request,
    query: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    contacts = contacts_repo.search_contacts(db, user_id=current_user.id, query=query)
    return contacts

@router.get("/contacts/upcoming-birthdays", response_model=List[ContactOut])
@limiter.limit("2/minute") 
def get_upcoming_birthdays(
    request: Request,
    days: int = Query(7, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    today = date.today()
    end_date = today + timedelta(days=days)
    contacts = contacts_repo.get_upcoming_birthdays(db, user_id=current_user.id, start_date=today, end_date=end_date)
    return contacts