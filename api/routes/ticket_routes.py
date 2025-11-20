# api/routes/ticket_routes.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from core import models
from api.utils import require_auth

router = APIRouter(prefix="/tickets", tags=["Tickets"])

@router.get("/")
def list_tickets(db: Session = Depends(get_db), user=Depends(require_auth)):
    tickets = db.query(models.Ticket).all()
    return {"tickets": tickets}

@router.put("/{ticket_id}")
def update_ticket(ticket_id: int, payload: dict, db: Session = Depends(get_db), user=Depends(require_auth)):
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    for key, value in payload.items():
        setattr(ticket, key, value)
    db.commit()
    db.refresh(ticket)
    return {"message": "Updated", "ticket": ticket}
