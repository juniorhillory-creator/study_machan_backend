# app/routers/messaging.py
# Real-time chat conversations, message inbox, and notification alerts.

import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from app.database import supabase
from app.dependencies import get_current_user
from app.schemas.messaging import (
    ConversationSummary,
    MessageItem,
    MessageSendRequest,
    NotificationItem,
)

router = APIRouter(tags=["Messaging & Alerts"])


# --- CONVERSATIONS LIST ---
@router.get("/conversations/", response_model=List[ConversationSummary], summary="List active conversations for logged-in user")
def list_conversations(current_user=Depends(get_current_user)):
    try:
        conv_resp = (
            supabase.table("conversations")
            .select("*")
            .or_(f"student_id.eq.{current_user.id},tutor_id.eq.{current_user.id}")
            .order("last_message_at", desc=True)
            .execute()
        )
        summaries = []
        for c in (conv_resp.data or []):
            other_id = c["tutor_id"] if c["student_id"] == current_user.id else c["student_id"]
            other_prof = supabase.table("profiles").select("full_name, avatar_url").eq("id", other_id).maybe_single().execute()
            prof_data = other_prof.data or {}

            # Count unread
            unread = (
                supabase.table("messages")
                .select("id")
                .eq("conversation_id", c["id"])
                .neq("sender_id", current_user.id)
                .eq("is_read", False)
                .execute()
            )

            summaries.append(ConversationSummary(
                id=c["id"],
                student_id=c["student_id"],
                tutor_id=c["tutor_id"],
                participant_name=prof_data.get("full_name", "StudyMachan User"),
                participant_avatar=prof_data.get("avatar_url"),
                last_message=c.get("last_message"),
                last_message_at=c.get("last_message_at"),
                unread_count=len(unread.data or []),
            ))
        return summaries
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to load conversations.") from e


# --- GET CONVERSATION MESSAGES ---
@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageItem], summary="Get messages in a conversation")
def get_conversation_messages(conversation_id: str, current_user=Depends(get_current_user)):
    try:
        conv = supabase.table("conversations").select("student_id, tutor_id").eq("id", conversation_id).maybe_single().execute()
        if not conv or not conv.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
        row = conv.data
        if row["student_id"] != current_user.id and row["tutor_id"] != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view these messages.")

        # Mark messages as read
        supabase.table("messages").update({"is_read": True}).eq("conversation_id", conversation_id).neq("sender_id", current_user.id).execute()

        res = supabase.table("messages").select("*").eq("conversation_id", conversation_id).order("created_at", desc=False).execute()
        return [MessageItem(**m) for m in (res.data or [])]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to load messages.") from e


# --- SEND MESSAGE ---
@router.post("/conversations/{conversation_id}/messages", response_model=MessageItem, status_code=status.HTTP_201_CREATED, summary="Send message in a conversation")
def send_message(conversation_id: str, payload: MessageSendRequest, current_user=Depends(get_current_user)):
    try:
        conv = supabase.table("conversations").select("student_id, tutor_id").eq("id", conversation_id).maybe_single().execute()
        if not conv or not conv.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
        row = conv.data
        if row["student_id"] != current_user.id and row["tutor_id"] != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to send messages here.")

        msg_id = str(uuid.uuid4())
        msg_row = {
            "id": msg_id,
            "conversation_id": conversation_id,
            "sender_id": current_user.id,
            "content": payload.content,
            "is_read": False,
        }
        res = supabase.table("messages").insert(msg_row).execute()
        supabase.table("conversations").update({"last_message": payload.content}).eq("id", conversation_id).execute()
        return MessageItem(**res.data[0])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to send message.") from e


# --- NOTIFICATIONS FEED ---
@router.get("/notifications/", response_model=List[NotificationItem], summary="Get notification alerts feed")
def get_notifications(current_user=Depends(get_current_user)):
    try:
        res = (
            supabase.table("notifications")
            .select("*")
            .eq("user_id", current_user.id)
            .order("created_at", desc=True)
            .limit(50)
            .execute()
        )
        return [NotificationItem(**n) for n in (res.data or [])]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to load notifications.") from e


# --- MARK NOTIFICATION READ ---
@router.patch("/notifications/{notification_id}/read", summary="Mark a notification as read")
def mark_notification_read(notification_id: str, current_user=Depends(get_current_user)):
    try:
        supabase.table("notifications").update({"is_read": True}).eq("id", notification_id).eq("user_id", current_user.id).execute()
        return {"status": "success", "id": notification_id}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to mark notification read.") from e


# --- MARK ALL NOTIFICATIONS READ ---
@router.patch("/notifications/read-all", summary="Mark all notifications as read")
def mark_all_notifications_read(current_user=Depends(get_current_user)):
    try:
        supabase.table("notifications").update({"is_read": True}).eq("user_id", current_user.id).execute()
        return {"status": "success", "message": "All notifications marked as read."}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update notifications.") from e
