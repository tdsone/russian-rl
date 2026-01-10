import { useState, useCallback, useMemo } from 'react';
import { cn } from '@/lib/utils';

interface Move {
  from: [number, number];
  to: [number, number];
}

interface GameBoardProps {
  board: number[][];
  legalMoves: Move[];
  isMyTurn: boolean;
  myColor: 'white' | 'black';
  onMove: (from: [number, number], to: [number, number]) => void;
}

export function GameBoard({ board, legalMoves, isMyTurn, myColor, onMove }: GameBoardProps) {
  const [selectedPiece, setSelectedPiece] = useState<[number, number] | null>(null);

  // Get all valid destinations for the selected piece
  const validDestinations = useMemo(() => {
    if (!selectedPiece) return new Set<string>();
    return new Set(
      legalMoves
        .filter(m => m.from[0] === selectedPiece[0] && m.from[1] === selectedPiece[1])
        .map(m => `${m.to[0]},${m.to[1]}`)
    );
  }, [selectedPiece, legalMoves]);

  // Get all pieces that can move
  const movablePieces = useMemo(() => {
    return new Set(legalMoves.map(m => `${m.from[0]},${m.from[1]}`));
  }, [legalMoves]);

  const handleCellClick = useCallback((row: number, col: number) => {
    if (!isMyTurn) return;

    const cellValue = board[row][col];
    const myPieceValue = myColor === 'white' ? 1 : -1;
    const cellKey = `${row},${col}`;

    // If clicking on own piece that can move, select it
    if (cellValue === myPieceValue && movablePieces.has(cellKey)) {
      setSelectedPiece([row, col]);
      return;
    }

    // If a piece is selected and clicking on valid destination, make move
    if (selectedPiece && validDestinations.has(cellKey)) {
      onMove(selectedPiece, [row, col]);
      setSelectedPiece(null);
      return;
    }

    // Otherwise, deselect
    setSelectedPiece(null);
  }, [isMyTurn, board, myColor, movablePieces, selectedPiece, validDestinations, onMove]);

  return (
    <div className="inline-block p-4 bg-board-dark rounded-lg shadow-xl">
      {/* Column labels */}
      <div className="flex mb-1">
        <div className="w-8" />
        {Array.from({ length: 8 }, (_, i) => (
          <div key={i} className="w-12 h-6 flex items-center justify-center text-sm font-medium text-muted-foreground">
            {i}
          </div>
        ))}
      </div>

      {/* Board rows */}
      {board.map((row, rowIndex) => (
        <div key={rowIndex} className="flex">
          {/* Row label */}
          <div className="w-8 h-12 flex items-center justify-center text-sm font-medium text-muted-foreground">
            {rowIndex}
          </div>

          {/* Cells */}
          {row.map((cell, colIndex) => {
            const isLightSquare = (rowIndex + colIndex) % 2 === 0;
            const cellKey = `${rowIndex},${colIndex}`;
            const isSelected = selectedPiece?.[0] === rowIndex && selectedPiece?.[1] === colIndex;
            const isValidDest = validDestinations.has(cellKey);
            const isMovable = movablePieces.has(cellKey) && cell === (myColor === 'white' ? 1 : -1);

            return (
              <div
                key={colIndex}
                onClick={() => handleCellClick(rowIndex, colIndex)}
                className={cn(
                  'w-12 h-12 flex items-center justify-center transition-all duration-150',
                  isLightSquare ? 'bg-board-light' : 'bg-board-dark',
                  isSelected && 'ring-2 ring-selected ring-inset',
                  isValidDest && 'ring-2 ring-highlight ring-inset cursor-pointer',
                  isMovable && isMyTurn && !isSelected && 'cursor-pointer hover:brightness-110',
                  !isMyTurn && 'cursor-default'
                )}
              >
                {cell !== 0 && (
                  <div
                    className={cn(
                      'w-9 h-9 rounded-full shadow-md transition-transform',
                      cell === 1 
                        ? 'bg-piece-white border-2 border-gray-300' 
                        : 'bg-piece-black border-2 border-gray-700',
                      isSelected && 'scale-110',
                      isMovable && isMyTurn && 'hover:scale-105'
                    )}
                  />
                )}
                {cell === 0 && isValidDest && (
                  <div className="w-4 h-4 rounded-full bg-highlight/50" />
                )}
              </div>
            );
          })}
        </div>
      ))}
    </div>
  );
}
