from __future__ import annotations
from typing import List, Optional
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, String, Boolean, Float, Text

from .database import db

class Client(db.Model):
    __tablename__ = "clients"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    bot_avatar_url: Mapped[Optional[str]] = mapped_column(String(255))
    locale: Mapped[str] = mapped_column(String(10), default="en-US")
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")
    public: Mapped[bool] = mapped_column(Boolean, default=True)
    plan_type: Mapped[str] = mapped_column(String(20), default="basic")
    
    # Feature Flags (Stored as JSON for flexibility)
    features: Mapped[dict] = mapped_column(JSON, default={})

    # Relationships
    theme: Mapped["Theme"] = relationship(back_populates="client", uselist=False, cascade="all, delete-orphan")
    channels: Mapped["Channel"] = relationship(back_populates="client", uselist=False, cascade="all, delete-orphan")
    menu_categories: Mapped[List["MenuCategory"]] = relationship(back_populates="client", cascade="all, delete-orphan")
    responses: Mapped[List["Response"]] = relationship(back_populates="client", cascade="all, delete-orphan")
    
    # Menu Meta
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    promo: Mapped[dict] = mapped_column(JSON, default={})


class Theme(db.Model):
    __tablename__ = "themes"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[str] = mapped_column(ForeignKey("clients.id"), unique=True, nullable=False)
    
    brand_name: Mapped[str] = mapped_column(String(100))
    primary_color: Mapped[str] = mapped_column(String(7))
    bubble_color: Mapped[str] = mapped_column(String(7))
    background: Mapped[str] = mapped_column(String(7))
    text_color: Mapped[str] = mapped_column(String(7))
    font_family: Mapped[str] = mapped_column(String(255))
    bot_avatar_url: Mapped[Optional[str]] = mapped_column(String(255))

    client: Mapped["Client"] = relationship(back_populates="theme")


class Channel(db.Model):
    __tablename__ = "channels"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[str] = mapped_column(ForeignKey("clients.id"), unique=True, nullable=False)
    
    data: Mapped[dict] = mapped_column(JSON, default={})

    client: Mapped["Client"] = relationship(back_populates="channels")


class Response(db.Model):
    __tablename__ = "responses"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[str] = mapped_column(ForeignKey("clients.id"), nullable=False)
    
    intent: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[dict] = mapped_column(JSON, nullable=False) # Stores reply, messages, buttons

    client: Mapped["Client"] = relationship(back_populates="responses")


class MenuCategory(db.Model):
    __tablename__ = "menu_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[str] = mapped_column(ForeignKey("clients.id"), nullable=False)
    
    category_id: Mapped[str] = mapped_column(String(50), nullable=False) # e.g. 'seafood_specials'
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    
    items: Mapped[List["MenuItem"]] = relationship(back_populates="category", cascade="all, delete-orphan")
    client: Mapped["Client"] = relationship(back_populates="menu_categories")


class MenuItem(db.Model):
    __tablename__ = "menu_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    category_db_id: Mapped[int] = mapped_column(ForeignKey("menu_categories.id"), nullable=False)
    
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    price: Mapped[float] = mapped_column(Float, default=0.0)
    desc: Mapped[Optional[str]] = mapped_column(Text)
    image: Mapped[Optional[str]] = mapped_column(String(255))
    
    # JSON Arrays
    allergens: Mapped[list] = mapped_column(JSON, default=[])
    may_contain: Mapped[list] = mapped_column(JSON, default=[])

    category: Mapped["MenuCategory"] = relationship(back_populates="items")
