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

  // Flip the board so player's pieces are always in the lower right corner
  // White pieces start at upper left (low indices), black at lower right (high indices)
  // When playing black, we flip the board so black pieces appear at lower right
  const shouldFlip = myColor === 'white';

  // Transform board coordinates: visual -> logical
  const toLogical = useCallback((visualRow: number, visualCol: number): [number, number] => {
    if (shouldFlip) {
      return [7 - visualRow, 7 - visualCol];
    }
    return [visualRow, visualCol];
  }, [shouldFlip]);

  // Get all valid destinations for the selected piece (in logical coordinates)
  const validDestinations = useMemo(() => {
    if (!selectedPiece) return new Set<string>();
    return new Set(
      legalMoves
        .filter(m => m.from[0] === selectedPiece[0] && m.from[1] === selectedPiece[1])
        .map(m => `${m.to[0]},${m.to[1]}`)
    );
  }, [selectedPiece, legalMoves]);

  // Get all pieces that can move (in logical coordinates)
  const movablePieces = useMemo(() => {
    return new Set(legalMoves.map(m => `${m.from[0]},${m.from[1]}`));
  }, [legalMoves]);

  const handleCellClick = useCallback((visualRow: number, visualCol: number) => {
    if (!isMyTurn) return;

    // Convert visual coordinates to logical board coordinates
    const [logicalRow, logicalCol] = toLogical(visualRow, visualCol);

    const cellValue = board[logicalRow][logicalCol];
    const myPieceValue = myColor === 'white' ? 1 : -1;
    const cellKey = `${logicalRow},${logicalCol}`;

    // If clicking on own piece that can move, select it
    if (cellValue === myPieceValue && movablePieces.has(cellKey)) {
      setSelectedPiece([logicalRow, logicalCol]);
      return;
    }

    // If a piece is selected and clicking on valid destination, make move
    if (selectedPiece && validDestinations.has(cellKey)) {
      onMove(selectedPiece, [logicalRow, logicalCol]);
      setSelectedPiece(null);
      return;
    }

    // Otherwise, deselect
    setSelectedPiece(null);
  }, [isMyTurn, board, myColor, movablePieces, selectedPiece, validDestinations, onMove, toLogical]);

  // Generate row indices for display (flipped if needed)
  const displayRows = useMemo(() => {
    return shouldFlip ? Array.from({ length: 8 }, (_, i) => 7 - i) : Array.from({ length: 8 }, (_, i) => i);
  }, [shouldFlip]);

  // Generate column indices for display (flipped if needed)
  const displayCols = useMemo(() => {
    return shouldFlip ? Array.from({ length: 8 }, (_, i) => 7 - i) : Array.from({ length: 8 }, (_, i) => i);
  }, [shouldFlip]);

  return (
    <div className="inline-block p-4 bg-board-dark rounded-lg shadow-xl">
      {/* Column labels */}
      <div className="flex mb-1">
        <div className="w-8" />
        {displayCols.map((colIndex) => (
          <div key={colIndex} className="w-12 h-6 flex items-center justify-center text-sm font-medium text-muted-foreground">
            {colIndex}
          </div>
        ))}
      </div>

      {/* Board rows */}
      {displayRows.map((logicalRowIndex, visualRowIndex) => (
        <div key={logicalRowIndex} className="flex">
          {/* Row label */}
          <div className="w-8 h-12 flex items-center justify-center text-sm font-medium text-muted-foreground">
            {logicalRowIndex}
          </div>

          {/* Cells */}
          {displayCols.map((logicalColIndex, visualColIndex) => {
            const cell = board[logicalRowIndex][logicalColIndex];
            // Use logical coordinates for square coloring to maintain consistent pattern
            const isLightSquare = (logicalRowIndex + logicalColIndex) % 2 === 0;
            const cellKey = `${logicalRowIndex},${logicalColIndex}`;
            const isSelected = selectedPiece?.[0] === logicalRowIndex && selectedPiece?.[1] === logicalColIndex;
            const isValidDest = validDestinations.has(cellKey);
            const isMovable = movablePieces.has(cellKey) && cell === (myColor === 'white' ? 1 : -1);

            return (
              <div
                key={logicalColIndex}
                onClick={() => handleCellClick(visualRowIndex, visualColIndex)}
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
