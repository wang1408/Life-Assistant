from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.conversation import Conversation, Message
from app.schemas.conversation import ConversationCreate, ConversationRead, MessageRead

router = APIRouter()


def _conversation_read(db: Session, conversation: Conversation) -> ConversationRead:
    first_message = db.scalar(
        select(Message)
        .where(Message.conversation_id == conversation.id, Message.role == "user")
        .order_by(Message.created_at.asc(), Message.id.asc())
        .limit(1)
    )
    title = (first_message.content.strip()[:32] if first_message and first_message.content.strip() else "新会话")
    return ConversationRead(id=conversation.id, title=title, created_at=conversation.created_at)


@router.get("", response_model=list[ConversationRead])
def list_conversations(db: Session = Depends(get_db)):
    conversations = db.scalars(select(Conversation).order_by(Conversation.created_at.desc())).all()
    return [_conversation_read(db, conversation) for conversation in conversations]


@router.post("", response_model=ConversationRead)
def create_conversation(data: ConversationCreate | None = None, db: Session = Depends(get_db)):
    conversation = Conversation()
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return _conversation_read(db, conversation)


@router.get("/{conversation_id}/messages", response_model=list[MessageRead])
def list_messages(conversation_id: int, db: Session = Depends(get_db)):
    if not db.get(Conversation, conversation_id):
        raise HTTPException(404, "会话不存在")
    return db.scalars(
        select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at.asc(), Message.id.asc())
    ).all()


@router.delete("/{conversation_id}")
def delete_conversation(conversation_id: int, db: Session = Depends(get_db)):
    conversation = db.get(Conversation, conversation_id)
    if not conversation:
        raise HTTPException(404, "会话不存在")
    db.execute(delete(Message).where(Message.conversation_id == conversation_id))
    db.delete(conversation)
    db.commit()
    return {"deleted": True, "id": conversation_id}

