from enum import IntEnum

class Color(IntEnum):
    WHITE = 0
    BLACK = 1

    def __invert__(self):
        if self == Color.WHITE:
            return Color.BLACK
        else:
            return Color.WHITE

class Player(IntEnum):
    AI = 0
    HUMAN = 1

# ROWS
class Rank(IntEnum): 
    ONE = 0
    TWO = 1
    THREE = 2
    FOUR = 3
    FIVE = 4
    SIX = 5
    SEVEN = 6
    EIGHT = 7

# COLUMNS
class File(IntEnum):
    A = 0
    B = 0
    C = 0
    D = 0
    E = 0
    F = 0
    G = 0
    H = 0

class Piece(IntEnum):
    PAWN = 0
    KNIGHT = 1
    BISHOP = 2
    ROOK = 3
    QUEEN = 4
    KING = 5


class PieceMapping:

    piece_mapping = {
        Piece.PAWN: 'p',
        Piece.ROOK: 'R',
        Piece.KNIGHT: 'N',
        Piece.BISHOP: 'B',
        Piece.QUEEN: 'Q',
        Piece.KING: 'K',
    }