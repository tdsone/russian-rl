"""WebSocket handler for game communication.

All game interactions (vs AI and PvP) go through WebSocket for consistency.
"""

import json
import asyncio
from datetime import datetime
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.database import Game, User, async_session_maker
from backend.services.auth import decode_token
from backend.services.elo import calculate_elo_change
from agents.random_agent import RandomAgent
from games.ugolki import Ugolki

# Store active WebSocket connections per game
# game_id -> {user_id: websocket}
active_connections: dict[int, dict[int, WebSocket]] = {}

# Store active game instances
# game_id -> Ugolki instance
active_games: dict[int, Ugolki] = {}

# AI agent instance
ai_agent = RandomAgent()


async def get_user_from_token(token: str, db: AsyncSession) -> User | None:
    """Validate token and get user."""
    payload = decode_token(token)
    if payload is None:
        return None
    
    user_id = payload.get("sub")
    if user_id is None:
        return None
    
    result = await db.execute(select(User).where(User.id == int(user_id)))
    return result.scalar_one_or_none()


async def send_message(websocket: WebSocket, msg_type: str, data: dict[str, Any]) -> None:
    """Send a typed message through WebSocket."""
    await websocket.send_json({"type": msg_type, "data": data})


async def broadcast_to_game(game_id: int, msg_type: str, data: dict[str, Any], exclude_user: int | None = None) -> None:
    """Broadcast a message to all players in a game."""
    if game_id not in active_connections:
        return
    
    for user_id, ws in active_connections[game_id].items():
        if exclude_user is not None and user_id == exclude_user:
            continue
        await send_message(ws, msg_type, data)


def board_to_list(game: Ugolki) -> list[list[int]]:
    """Convert Ugolki board tensor to list for JSON serialization."""
    return game.board.tolist()


def get_game_state(game: Ugolki, db_game: Game) -> dict[str, Any]:
    """Get current game state as dict."""
    return {
        "game_id": db_game.id,
        "board": board_to_list(game),
        "turn": game.turn,
        "status": db_game.status,
        "game_type": db_game.game_type,
        "white_player_id": db_game.white_player_id,
        "black_player_id": db_game.black_player_id,
        "legal_moves": [
            {"from": list(from_pos), "to": list(to_pos)}
            for from_pos, to_pos in game.get_legal_actions()
        ],
    }


async def handle_create_game(
    websocket: WebSocket,
    user: User,
    data: dict[str, Any],
    db: AsyncSession,
) -> None:
    """Handle game creation request."""
    game_type = data.get("game_type", "ai")  # "ai" or "pvp"
    
    # Create new Ugolki game
    ugolki = Ugolki.create_game()
    
    # Create database record
    db_game = Game(
        white_player_id=user.id,
        black_player_id=None,
        game_type=game_type,
        status="active" if game_type == "ai" else "waiting",
        board_state=json.dumps(board_to_list(ugolki)),
        current_turn="white",
    )
    db.add(db_game)
    await db.commit()
    await db.refresh(db_game)
    
    # Store game instance
    active_games[db_game.id] = ugolki
    
    # Store connection
    if db_game.id not in active_connections:
        active_connections[db_game.id] = {}
    active_connections[db_game.id][user.id] = websocket
    
    # Send game state
    await send_message(websocket, "game_created", get_game_state(ugolki, db_game))


async def handle_join_game(
    websocket: WebSocket,
    user: User,
    data: dict[str, Any],
    db: AsyncSession,
) -> None:
    """Handle joining an existing game."""
    game_id = data.get("game_id")
    if game_id is None:
        await send_message(websocket, "error", {"message": "game_id required"})
        return
    
    # Get game from database
    result = await db.execute(select(Game).where(Game.id == game_id))
    db_game = result.scalar_one_or_none()
    
    if db_game is None:
        await send_message(websocket, "error", {"message": "Game not found"})
        return
    
    if db_game.status != "waiting":
        await send_message(websocket, "error", {"message": "Game is not available to join"})
        return
    
    if db_game.white_player_id == user.id:
        await send_message(websocket, "error", {"message": "Cannot join your own game"})
        return
    
    # Join as black player
    db_game.black_player_id = user.id
    db_game.status = "active"
    await db.commit()
    
    # Get or create game instance
    if game_id not in active_games:
        # Restore from database
        board_list = json.loads(db_game.board_state)
        import torch
        board = torch.tensor(board_list, dtype=torch.long)
        ugolki = Ugolki(board)
        ugolki.turn = db_game.current_turn
        active_games[game_id] = ugolki
    else:
        ugolki = active_games[game_id]
    
    # Store connection
    if game_id not in active_connections:
        active_connections[game_id] = {}
    active_connections[game_id][user.id] = websocket
    
    # Notify both players
    game_state = get_game_state(ugolki, db_game)
    await broadcast_to_game(game_id, "game_started", game_state)


async def handle_move(
    websocket: WebSocket,
    user: User,
    data: dict[str, Any],
    db: AsyncSession,
) -> None:
    """Handle a move from a player."""
    game_id = data.get("game_id")
    from_pos = data.get("from")  # [row, col]
    to_pos = data.get("to")  # [row, col]
    
    if game_id is None or from_pos is None or to_pos is None:
        await send_message(websocket, "error", {"message": "game_id, from, and to required"})
        return
    
    # Get game from database
    result = await db.execute(select(Game).where(Game.id == game_id))
    db_game = result.scalar_one_or_none()
    
    if db_game is None:
        await send_message(websocket, "error", {"message": "Game not found"})
        return
    
    if db_game.status != "active":
        await send_message(websocket, "error", {"message": "Game is not active"})
        return
    
    # Get game instance
    if game_id not in active_games:
        await send_message(websocket, "error", {"message": "Game not loaded"})
        return
    
    ugolki = active_games[game_id]
    
    # Validate it's the user's turn
    is_white = db_game.white_player_id == user.id
    is_black = db_game.black_player_id == user.id
    
    if ugolki.turn == "white" and not is_white:
        await send_message(websocket, "error", {"message": "Not your turn"})
        return
    if ugolki.turn == "black" and not is_black:
        await send_message(websocket, "error", {"message": "Not your turn"})
        return
    
    # Validate move is legal
    action = (tuple(from_pos), tuple(to_pos))
    legal_actions = ugolki.get_legal_actions()
    if action not in legal_actions:
        await send_message(websocket, "error", {"message": "Illegal move"})
        return
    
    # Apply the move
    step_result = ugolki.step(action)
    
    # Update database
    db_game.board_state = json.dumps(board_to_list(ugolki))
    db_game.current_turn = ugolki.turn
    
    if step_result.done:
        db_game.status = "completed"
        db_game.completed_at = datetime.utcnow()
        winner = step_result.info.get("winner")
        if winner == "white":
            db_game.winner_id = db_game.white_player_id
        elif winner == "black":
            db_game.winner_id = db_game.black_player_id
        
        # Update ELO for PvP games
        if db_game.game_type == "pvp" and db_game.black_player_id:
            await update_elo_after_game(db, db_game, winner)
    
    await db.commit()
    
    # Broadcast updated state
    game_state = get_game_state(ugolki, db_game)
    await broadcast_to_game(game_id, "game_state", game_state)
    
    if step_result.done:
        await broadcast_to_game(game_id, "game_over", {
            "winner": step_result.info.get("winner"),
            "winner_id": db_game.winner_id,
        })
        return
    
    # If playing against AI and it's AI's turn, make AI move
    if db_game.game_type == "ai" and ugolki.turn == "black":
        await make_ai_move(game_id, db)


async def make_ai_move(game_id: int, db: AsyncSession) -> None:
    """Make an AI move and broadcast the result."""
    if game_id not in active_games:
        return
    
    ugolki = active_games[game_id]
    
    # Small delay to make it feel more natural
    await asyncio.sleep(0.5)
    
    # Get AI move
    action = ai_agent.select_action(ugolki)
    step_result = ugolki.step(action)
    
    # Update database
    result = await db.execute(select(Game).where(Game.id == game_id))
    db_game = result.scalar_one_or_none()
    
    if db_game is None:
        return
    
    db_game.board_state = json.dumps(board_to_list(ugolki))
    db_game.current_turn = ugolki.turn
    
    if step_result.done:
        db_game.status = "completed"
        db_game.completed_at = datetime.utcnow()
        winner = step_result.info.get("winner")
        if winner == "white":
            db_game.winner_id = db_game.white_player_id
        elif winner == "black":
            db_game.winner_id = None  # AI doesn't have an ID
    
    await db.commit()
    
    # Broadcast updated state
    game_state = get_game_state(ugolki, db_game)
    await broadcast_to_game(game_id, "game_state", game_state)
    
    if step_result.done:
        await broadcast_to_game(game_id, "game_over", {
            "winner": step_result.info.get("winner"),
            "winner_id": db_game.winner_id,
        })


async def update_elo_after_game(db: AsyncSession, game: Game, winner: str) -> None:
    """Update ELO ratings after a PvP game."""
    # Get both players
    white_result = await db.execute(select(User).where(User.id == game.white_player_id))
    white_player = white_result.scalar_one_or_none()
    
    black_result = await db.execute(select(User).where(User.id == game.black_player_id))
    black_player = black_result.scalar_one_or_none()
    
    if white_player is None or black_player is None:
        return
    
    # Calculate new ELO
    white_won = winner == "white"
    new_white_elo, new_black_elo = calculate_elo_change(
        white_player.elo, black_player.elo, white_won
    )
    
    # Update players
    white_player.elo = new_white_elo
    black_player.elo = new_black_elo
    await db.commit()


async def handle_get_open_games(
    websocket: WebSocket,
    user: User,
    db: AsyncSession,
) -> None:
    """Get list of open games waiting for players."""
    result = await db.execute(
        select(Game)
        .where(Game.status == "waiting")
        .where(Game.game_type == "pvp")
        .where(Game.white_player_id != user.id)
    )
    games = result.scalars().all()
    
    open_games = []
    for game in games:
        # Get creator username
        creator_result = await db.execute(select(User).where(User.id == game.white_player_id))
        creator = creator_result.scalar_one_or_none()
        open_games.append({
            "game_id": game.id,
            "creator": creator.username if creator else "Unknown",
            "creator_elo": creator.elo if creator else 1200,
            "created_at": game.created_at.isoformat(),
        })
    
    await send_message(websocket, "open_games", {"games": open_games})


async def handle_reconnect(
    websocket: WebSocket,
    user: User,
    data: dict[str, Any],
    db: AsyncSession,
) -> None:
    """Handle reconnecting to an active game."""
    game_id = data.get("game_id")
    if game_id is None:
        await send_message(websocket, "error", {"message": "game_id required"})
        return
    
    # Get game from database
    result = await db.execute(select(Game).where(Game.id == game_id))
    db_game = result.scalar_one_or_none()
    
    if db_game is None:
        await send_message(websocket, "error", {"message": "Game not found"})
        return
    
    # Check user is part of this game
    if user.id != db_game.white_player_id and user.id != db_game.black_player_id:
        await send_message(websocket, "error", {"message": "Not part of this game"})
        return
    
    # Restore game instance if needed
    if game_id not in active_games:
        import torch
        board_list = json.loads(db_game.board_state)
        board = torch.tensor(board_list, dtype=torch.long)
        ugolki = Ugolki(board)
        ugolki.turn = db_game.current_turn
        active_games[game_id] = ugolki
    
    ugolki = active_games[game_id]
    
    # Store connection
    if game_id not in active_connections:
        active_connections[game_id] = {}
    active_connections[game_id][user.id] = websocket
    
    # Send current state
    await send_message(websocket, "game_state", get_game_state(ugolki, db_game))


async def websocket_handler(websocket: WebSocket, token: str) -> None:
    """Main WebSocket handler."""
    await websocket.accept()
    
    # Validate token and get user
    async with async_session_maker() as db:
        user = await get_user_from_token(token, db)
        
        if user is None:
            await send_message(websocket, "error", {"message": "Invalid token"})
            await websocket.close()
            return
        
        await send_message(websocket, "connected", {"user_id": user.id, "username": user.username})
        
        try:
            while True:
                data = await websocket.receive_json()
                msg_type = data.get("type")
                msg_data = data.get("data", {})
                
                # Create new session for each message
                async with async_session_maker() as msg_db:
                    # Re-fetch user to ensure fresh data
                    user = await get_user_from_token(token, msg_db)
                    if user is None:
                        await send_message(websocket, "error", {"message": "Session expired"})
                        break
                    
                    if msg_type == "create_game":
                        await handle_create_game(websocket, user, msg_data, msg_db)
                    elif msg_type == "join_game":
                        await handle_join_game(websocket, user, msg_data, msg_db)
                    elif msg_type == "move":
                        await handle_move(websocket, user, msg_data, msg_db)
                    elif msg_type == "get_open_games":
                        await handle_get_open_games(websocket, user, msg_db)
                    elif msg_type == "reconnect":
                        await handle_reconnect(websocket, user, msg_data, msg_db)
                    else:
                        await send_message(websocket, "error", {"message": f"Unknown message type: {msg_type}"})
        
        except WebSocketDisconnect:
            # Clean up connections
            for game_id, connections in list(active_connections.items()):
                if user.id in connections:
                    del connections[user.id]
                    # Notify other player
                    await broadcast_to_game(game_id, "opponent_disconnected", {"user_id": user.id})
                if not connections:
                    del active_connections[game_id]
