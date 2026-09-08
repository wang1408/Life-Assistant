import json
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.chat import ChatRequest
from app.services.memory_service import MemoryService
from app.services.action_service import ActionService
from app.agents.graph import build_graph
from app.models.conversation import Conversation, Message
from fastapi import HTTPException

router = APIRouter()


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest, db: Session = Depends(get_db)):
    conversation = db.get(Conversation, request.conversation_id) if request.conversation_id else None
    if request.conversation_id and not conversation:
        raise HTTPException(404, "会话不存在")
    if conversation is None:
        conversation = Conversation()
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
    # 在写入本轮用户消息前读取最近历史，避免当前消息重复进入上下文。
    previous_messages = list(db.scalars(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.id.desc())
        .limit(12)
    ).all())
    history = [
        {"role": item.role, "content": item.content, "results": item.result_json}
        for item in reversed(previous_messages)
    ]
    db.add(Message(conversation_id=conversation.id, role="user", content=request.message))
    db.commit()
    memories = MemoryService(db).context()
    result = await build_graph().ainvoke({"message": request.message, "history": history, "memories": memories, "current_location": request.current_location})
    action_reads = []
    for action in result.get("actions", []):
        saved = ActionService(db).create(action["action_type"], action["payload"])
        action_reads.append({"id": saved.id, "action_type": saved.action_type, "payload": saved.payload, "label": action.get("label"), "status": saved.status})
    for candidate in result.get("results", {}).get("memory_candidates", []):
        MemoryService(db).add_candidate(candidate)
    result_payload = result.get("results") or None
    db.add(Message(conversation_id=conversation.id, role="assistant", content=result.get("response", ""), result_json=result_payload))
    db.commit()

    async def events():
        yield f"data: {json.dumps({'type': 'message', 'content': result.get('response', '')}, ensure_ascii=False)}\n\n"
        if result.get("results"):
            yield f"data: {json.dumps({'type': 'results', 'data': result['results']}, ensure_ascii=False, default=str)}\n\n"
        for action in action_reads:
            yield f"data: {json.dumps({'type': 'action', 'data': action}, ensure_ascii=False, default=str)}\n\n"
        yield "data: {\"type\": \"done\"}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")
