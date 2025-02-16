from constans import Color, Piece, File, Rank, PieceMapping
import numpy as np

class ChessBoard():
    def __init__(self):
        self.pieces = np.zeros((2,6), dtype=np.uint64) 
        self.combined_color = np.zeros(2, dtype=np.uint64) 
        self.board = np.uint64(0)
        self.color = Color.WHITE
        self.move_log = [] 
    
    def make_move(self, move):
        for piece_type in Piece:
            if self.pieces[self.color][piece_type] & move.piece_moved:
                self.pieces[self.color][piece_type] &= ~(np.uint64(move.piece_moved))  
                self.pieces[self.color][piece_type] |= np.uint64(move.piece_captured)
        
        self.combined_color = np.zeros(2, dtype=np.uint64) 
        for p in Piece:
            for c in Color:
                self.combined_color[c] |= self.pieces[c][p]
        
        self.board = self.combined_color[Color.WHITE] | self.combined_color[Color.BLACK]

        self.move_log.append(move)
        self.color = ~self.color
    
    def undo_move(self):
        if self.move_log:
            move = self.move_log.pop()
            self.color = ~self.color

            for piece_type in Piece:
                if self.pieces[self.color][piece_type] & move.piece_captured:
                    self.pieces[self.color][piece_type] &= ~(np.uint64(move.piece_captured))
                    self.pieces[self.color][piece_type] |= np.uint64(move.piece_moved)
            
            # TODO: Restore captured piece if any

            self.combined_color = np.zeros(2, dtype=np.uint64) 
            for p in Piece:
                for c in Color:
                    self.combined_color[c] |= self.pieces[c][p]
            
            self.board = self.combined_color[Color.WHITE] | self.combined_color[Color.BLACK]

    def get_valid_moves(self):
        return self.get_all_possible_moves()

    def get_all_possible_moves(self):
        moves = []
        row = 8
        col = 8
        current_pieces = self.combined_color[self.color]

        while current_pieces:
            
            rightmost_piece = current_pieces & (~current_pieces+1)
            print(bin(rightmost_piece))
            current_pieces = current_pieces & ~rightmost_piece
            print(bin(current_pieces))
            square = (63 - int(np.log2(rightmost_piece)))
            row = square // 8
            col = square % 8
            for piece_type in Piece:
                if self.piece[self.color][self.piece_type] & square:
                    if piece_type == Piece.PAWN:
                        self.get_pawn_oves(row, col, moves)
                    elif piece_type == Piece.ROOK:
                        self.get_rook_moves(row, col, moves)
                    elif piece_type == Piece.BISHOP:
                        self.get_bishop_moves(row, col, moves)
                    elif piece_type == Piece.KNIGHT:
                        self.get_knight_moves(row, col, moves)
                    elif piece_type == Piece.KING:
                        self.get_king_moves(row, col, moves)
                    elif piece_type == Piece.QUEEN:
                        self.get_queen_moves(row, col, moves)
                    


    
    def init_board(self):
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
        
        self.board = self.combined_color[Color.WHITE] | self.combined_color[Color.BLACK]


    def __str__(self):
        board = bin(self.board)[2:]
        rank = 8
        file = 8
        output = []
        output.append("")
        for i in range(8):
            row = f"{rank}   "
            for j in range(8):
                row += board[i*8+j:i*8+j+1] + " "
            output.append(row)
            rank -= 1               
        output.append("")
        output.append("    A B C D E F G H")

        return "\n".join(output)
