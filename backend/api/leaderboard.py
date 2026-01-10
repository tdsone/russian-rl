"""Leaderboard API routes."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.database import User, Game, get_db

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])


class LeaderboardEntry(BaseModel):
    rank: int
    username: str
    elo: float
    games_played: int

    class Config:
        from_attributes = True


class LeaderboardResponse(BaseModel):
    entries: list[LeaderboardEntry]
    total: int


@router.get("", response_model=LeaderboardResponse)
async def get_leaderboard(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """Get the ELO leaderboard, sorted by rating descending."""
    # Get total count
    count_result = await db.execute(select(func.count()).select_from(User))
    total = count_result.scalar() or 0
    
    # Get paginated results sorted by ELO
    result = await db.execute(
        select(User)
        .order_by(User.elo.desc())
        .offset(offset)
        .limit(limit)
    )
    users = result.scalars().all()
    
    entries = []
    for i, user in enumerate(users):
        # Count games played using a separate query
        games_result = await db.execute(
            select(func.count())
            .select_from(Game)
            .where(
                or_(
                    Game.white_player_id == user.id,
                    Game.black_player_id == user.id
                )
            )
        )
        games_count = games_result.scalar() or 0
        
        entries.append(
            LeaderboardEntry(
                rank=offset + i + 1,
                username=user.username,
                elo=user.elo,
                games_played=games_count,
            )
        )
    
    return LeaderboardResponse(entries=entries, total=total)
