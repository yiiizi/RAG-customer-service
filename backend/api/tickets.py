from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Query

from api.schemas import TicketListResponse, TicketResponse, TicketUpdateRequest
from middleware.auth import get_current_staff_user, get_current_user
from mysql_module.dao import async_session
from mysql_module.tickets import get_ticket, list_staff_tickets, list_user_tickets

router = APIRouter(prefix="/api/tickets", tags=["tickets"])

VALID_TICKET_STATUSES = {"open", "processing", "resolved", "closed"}


def _parse_sources(raw: str | None) -> list[dict]:
    if not raw:
        return []
    try:
        value = json.loads(raw)
        return value if isinstance(value, list) else []
    except Exception:
        return []


def _serialize_ticket(ticket) -> TicketResponse:
    return TicketResponse(
        id=ticket.id,
        ticket_no=ticket.ticket_no,
        user_id=ticket.user_id,
        username=getattr(ticket.user, "username", None),
        conversation_id=ticket.conversation_id,
        message_id=ticket.message_id,
        category=ticket.category,
        priority=ticket.priority,
        status=ticket.status,
        summary=ticket.summary,
        user_question=ticket.user_question,
        ai_answer=ticket.ai_answer,
        public_sources=_parse_sources(ticket.public_sources),
        debug_sources=_parse_sources(ticket.debug_sources),
        assigned_to=ticket.assigned_to,
        assigned_username=getattr(ticket.assignee, "username", None),
        staff_note=ticket.staff_note,
        created_at=ticket.created_at.isoformat() if ticket.created_at else "",
        updated_at=ticket.updated_at.isoformat() if ticket.updated_at else "",
    )


@router.get("/mine", response_model=TicketListResponse)
async def get_my_tickets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    async with async_session() as session:
        items, total = await list_user_tickets(
            session,
            user_id=current_user["id"],
            page=page,
            page_size=page_size,
        )
        return TicketListResponse(items=[_serialize_ticket(item) for item in items], total=total)


@router.get("/queue", response_model=TicketListResponse)
async def get_ticket_queue(
    status_value: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_staff_user),
):
    if status_value and status_value not in VALID_TICKET_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid ticket status")
    async with async_session() as session:
        items, total = await list_staff_tickets(
            session,
            status_value=status_value,
            page=page,
            page_size=page_size,
        )
        return TicketListResponse(items=[_serialize_ticket(item) for item in items], total=total)


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket_detail(
    ticket_id: int,
    current_user: dict = Depends(get_current_user),
):
    async with async_session() as session:
        ticket = await get_ticket(session, ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        if current_user["role"] == "user" and ticket.user_id != current_user["id"]:
            raise HTTPException(status_code=403, detail="Forbidden")
        return _serialize_ticket(ticket)


@router.post("/{ticket_id}/claim", response_model=TicketResponse)
async def claim_ticket(
    ticket_id: int,
    current_user: dict = Depends(get_current_staff_user),
):
    async with async_session() as session:
        ticket = await get_ticket(session, ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        if ticket.assigned_to and current_user["role"] != "admin":
            raise HTTPException(status_code=409, detail="Ticket already assigned")
        ticket.assigned_to = current_user["id"]
        if ticket.status == "open":
            ticket.status = "processing"
        await session.commit()
        await session.refresh(ticket)
        ticket = await get_ticket(session, ticket_id)
        return _serialize_ticket(ticket)


@router.put("/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: int,
    req: TicketUpdateRequest,
    current_user: dict = Depends(get_current_staff_user),
):
    fields_set = getattr(req, "model_fields_set", getattr(req, "__fields_set__", set()))
    async with async_session() as session:
        ticket = await get_ticket(session, ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        is_admin = current_user["role"] == "admin"
        if not is_admin and ticket.assigned_to != current_user["id"]:
            raise HTTPException(status_code=403, detail="Only the assignee can update this ticket")

        if req.status is not None:
            if req.status not in VALID_TICKET_STATUSES:
                raise HTTPException(status_code=400, detail="Invalid ticket status")
            ticket.status = req.status

        if req.staff_note is not None:
            ticket.staff_note = req.staff_note.strip() or None

        if "assigned_to" in fields_set:
            if not is_admin:
                raise HTTPException(status_code=403, detail="Only admin can reassign tickets")
            ticket.assigned_to = req.assigned_to
            if req.assigned_to and ticket.status == "open":
                ticket.status = "processing"

        await session.commit()
        await session.refresh(ticket)
        ticket = await get_ticket(session, ticket_id)
        return _serialize_ticket(ticket)
