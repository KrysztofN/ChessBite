from constans import Color, Piece, File, Rank
import numpy as np

class GameState():
    def __init__(self):
        self.pieces = np.zeros((2,6), dtype=np.uint64) 
        self.combined_color = np.zeros(2, dtype=np.uint64) 
        self.combined_all = np.uint64(0) 
        self.color = Color.WHITE 

        self.pieces[Color.WHITE][Piece.PAWN] = np.uint64(0x000000000000FF00)
        self.pieces[Color.WHITE][Piece.KNIGHT] = np.uint64(0x0000000000000042)
        self.pieces[Color.WHITE][Piece.BISHOP] = np.uint64(0x0000000000000024)
        self.pieces[Color.WHITE][Piece.ROOK] = np.uint64(0x0000000000000081)
        self.pieces[Color.WHITE][Piece.QUEEN] = np.uint64(0x0000000000000008)
        self.pieces[Color.WHITE][Piece.KING] = np.uint64(0x0000000000000010)

        self.pieces[Color.BLACK][Piece.PAWN] = np.uint64(0x00FF000000000000)
        self.pieces[Color.BLACK][Piece.KNIGHT] = np.uint64(0x4200000000000000)
        self.pieces[Color.BLACK][Piece.BISHOP] = np.uint64(0x2400000000000000)
        self.pieces[Color.BLACK][Piece.ROOK] = np.uint64(0x8100000000000000)
        self.pieces[Color.BLACK][Piece.QUEEN] = np.uint64(0x0800000000000000)
        self.pieces[Color.BLACK][Piece.KING] = np.uint64(0x1000000000000000)
    
        for p in Piece:
            for c in Color:
                self.combined_color[c] |= self.pieces[c][p]
        
        self.combined_all = self.combined_color[Color.WHITE] | self.combined_color[Color.BLACK]
    
