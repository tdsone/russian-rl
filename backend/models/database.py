import json
from datetime import datetime
from typing import AsyncGenerator

from sqlalchemy import String, Integer, Float, DateTime, Text, ForeignKey, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    elo: Mapped[float] = mapped_column(Float, default=1200.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    games_as_white: Mapped[list["Game"]] = relationship(
        "Game", foreign_keys="Game.white_player_id", back_populates="white_player"
    )
    games_as_black: Mapped[list["Game"]] = relationship(
        "Game", foreign_keys="Game.black_player_id", back_populates="black_player"
    )


class Game(Base):
    __tablename__ = "games"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    white_player_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    black_player_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )  # None for AI games or waiting for opponent
    game_type: Mapped[str] = mapped_column(
        String(10), nullable=False
    )  # "ai" or "pvp"
    status: Mapped[str] = mapped_column(
        String(20), default="waiting"
    )  # "waiting", "active", "completed"
    winner_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    board_state: Mapped[str] = mapped_column(Text, nullable=False)  # JSON serialized board
    current_turn: Mapped[str] = mapped_column(String(10), default="white")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    white_player: Mapped["User"] = relationship(
        "User", foreign_keys=[white_player_id], back_populates="games_as_white"
    )
    black_player: Mapped["User | None"] = relationship(
        "User", foreign_keys=[black_player_id], back_populates="games_as_black"
    )

    def get_board_as_list(self) -> list[list[int]]:
        """Deserialize board state from JSON."""
        return json.loads(self.board_state)

    def set_board_from_list(self, board: list[list[int]]) -> None:
        """Serialize board state to JSON."""
        self.board_state = json.dumps(board)


# Database setup
import os
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///./ugolki.db")

engine = create_async_engine(DATABASE_URL, echo=False)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database sessions."""
    async with async_session_maker() as session:
        yield session
