from constans import Piece, Color

class Move():

    ranks_to_rows = {"1" : 7, "2" : 6, "3" : 5, "4" : 4,
                     "5" : 3, "6" : 2, "7" : 1, "8" : 0}
    rows_to_ranks = {v:k for k, v in ranks_to_rows.items()}
    files_to_cols = {"a" : 0, "b" : 1, "c" : 2, "d" : 3,
                     "e" : 4, "f" : 5, "g" : 6, "h" : 7}
    cols_to_files = {v:k for k, v in files_to_cols.items()}

    def __init__(self, start_sq, end_sq):
        self.start_row = start_sq[0]
        self.start_col = start_sq[1]
        self.end_row = end_sq[0]
        self.end_col = end_sq[1]
        self.piece_moved = 1 << (63 - (self.start_row * 8 + self.start_col))
        self.piece_captured = 1 << (63 - (self.end_row * 8 + self.end_col))
        self.move_ID = self.start_row * 1000 + self.start_col * 100 + self.end_row * 10 + self.end_col
        self.is_capture = False
        self.captured_piece_type = None
        self.moved_piece_type = None
        self.moved_piece_color = None
        self.is_pawn_promotion = False 

    def __eq__(self, other):
        if isinstance(other, Move):
            return self.move_ID == other.move_ID
        return False 

    def check_pawn_promotion(self):
        if (self.moved_piece_type == Piece.PAWN and self.moved_piece_color == Color.WHITE and self.end_row == 0) or (self.moved_piece_type == Piece.PAWN and self.moved_piece_color == Color.BLACK and self.end_row == 7):
            self.is_pawn_promotion = True

    def get_chess_notation(self):
        return self.get_rank_file(self.start_row, self.start_col) + self.get_rank_file(self.end_row, self.end_col)

    def get_rank_file(self, r, c):
        return self.cols_to_files[c] + self.rows_to_ranks[r]
    
