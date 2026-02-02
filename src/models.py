from datetime import date
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class Competition(SQLModel, table=True):
    id: int = Field(primary_key=True, sa_column_kwargs={
                    "autoincrement": False})
    name: str
    gender: str


class Match(SQLModel, table=True):
    id: int = Field(primary_key=True, sa_column_kwargs={
                    "autoincrement": False})
    competition_id: int = Field(foreign_key="competition.id")
    match_date: date
    home_team: str
    away_team: str
    home_score: int
    away_score: int


class Player(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    position: Optional[str] = None


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
