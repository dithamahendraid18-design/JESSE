from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class Button(BaseModel):
    label: str
    intent: str


class Message(BaseModel):
    """
    Tipe pesan untuk UI:
    - text: tampil sebagai bubble text
    - image: tampil sebagai card gambar
    """
    type: Literal["text", "image"]
    text: str | None = None
    url: str | None = None
    alt: str | None = None

    @model_validator(mode="after")
    def _validate_fields(self):
        if self.type == "text" and not self.text:
            raise ValueError("Message type 'text' requires 'text'")
        if self.type == "image" and not self.url:
            raise ValueError("Message type 'image' requires 'url'")
        return self


class ChatRequest(BaseModel):
    client_id: str = Field(..., description="Client ID")
    message: str | None = Field(default=None, description="User typed message")
    intent: str | None = Field(default=None, description="Button click intent")
    user_id: str | None = Field(default=None, description="Optional user id/ip")


class ChatResponse(BaseModel):
    """
    reply: untuk kompatibilitas (frontend lama)
    messages: format baru (multi bubble + image)
    """
    reply: str = ""
    messages: list[Message] = []
    buttons: list[Button] = []
    meta: dict = {}
