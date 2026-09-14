from __future__ import annotations

from datetime import timedelta

from .models import BreakGlass, Membership, new_id, utcnow
from .store import Store


def add_membership(store: Store, user_id: str, tenant_id: str, role: str = "member") -> Membership:
    m = Membership(user_id=user_id, tenant_id=tenant_id, role=role, status="active")
    store.memberships.append(m)
    return m


def is_member(store: Store, user_id: str, tenant_id: str) -> bool:
    return any(
        m.user_id == user_id and m.tenant_id == tenant_id and m.status == "active"
        for m in store.memberships
    )


def revoke_membership(store: Store, user_id: str, tenant_id: str) -> None:
    for m in store.memberships:
        if m.user_id == user_id and m.tenant_id == tenant_id:
            m.status = "revoked"


def issue_break_glass(store: Store, tenant_id: str, actor: str, reason: str, hours: int = 2) -> BreakGlass:
    ticket = BreakGlass(
        ticket_id=new_id(),
        tenant_id=tenant_id,
        actor=actor,
        reason=reason,
        expires_at=utcnow() + timedelta(hours=hours),
    )
    store.break_glass[ticket.ticket_id] = ticket
    store.audit_event("break_glass_issued", tenant_id=tenant_id, actor=actor, detail={"reason": reason})
    return ticket


def break_glass_valid(store: Store, ticket_id: str, tenant_id: str) -> bool:
    t = store.break_glass.get(ticket_id)
    if not t or t.revoked or t.tenant_id != tenant_id:
        return False
    return t.expires_at > utcnow()
