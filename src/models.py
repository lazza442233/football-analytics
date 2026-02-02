from datetime import date
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, Relationship, SQLModel


class Competition(SQLModel, table=True):
    id: int = Field(primary_key=True, sa_column_kwargs={
                    "autoincrement": False})
    name: str
    gender: str

    matches: List["Match"] = Relationship(back_populates="competition")


class Match(SQLModel, table=True):
    id: int = Field(primary_key=True, sa_column_kwargs={
                    "autoincrement": False})
    competition_id: int = Field(foreign_key="competition.id")
    match_date: date
    home_team: str
    away_team: str
    home_score: int
    away_score: int

    competition: Optional[Competition] = Relationship(back_populates="matches")
    events: List["Event"] = Relationship(back_populates="match")


class Player(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    position: Optional[str] = None

    events: List["Event"] = Relationship(back_populates="player")


class Event(SQLModel, table=True):
    id: UUID = Field(primary_key=True)
    match_id: int = Field(foreign_key="match.id")
    minute: int
    second: int
    type: str
    player_id: Optional[int] = Field(default=None, foreign_key="player.id")
    team_id: int
    location_x: Optional[float] = None
    location_y: Optional[float] = None
    attributes: Dict[str, Any] = Field(default={}, sa_column=Column(JSONB))

    match: Optional[Match] = Relationship(back_populates="events")
    player: Optional[Player] = Relationship(back_populates="events")
