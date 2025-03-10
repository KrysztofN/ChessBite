from Constants import Color, Piece, File, Rank, PieceMapping
import numpy as np

class ChessBoard():
    def __init__(self):
        self.pieces = np.zeros((2,6), dtype=np.uint64) 
        self.combined_color = np.zeros(2, dtype=np.uint64) 
        self.board = np.uint64(0)
        self.color = Color.WHITE
        self.move_log = [] 
        self.check_mate = False
        self.stale_mate = False
        self.pins = []
        self.check = []
        self.captured_piece = False
        self.en_passant_possible = ()
        self.current_castling_rights = CastleRights(True, True, True, True)
        self.castle_rights_log = [CastleRights(self.current_castling_rights.wks, self.current_castling_rights.bks, 
                                               self.current_castling_rights.wqs, self.current_castling_rights.bqs)]
    
    def make_move(self, move):

        for piece_type in Piece:
            if self.pieces[self.color][piece_type] & move.piece_moved:
                move.moved_piece_type = piece_type
                move.moved_piece_color = self.color
                break

        #  En passant captures
        if move.is_en_passant_move:
            move.is_capture = True
            for piece_type in Piece:
                en_passant_captured = move.piece_captured >> 8 if self.color == Color.WHITE else move.piece_captured << 8
                if self.pieces[~self.color][piece_type] & en_passant_captured:
                    move.captured_piece_type = piece_type                
        
        #  Regular captures
        elif self.combined_color[~self.color] & move.piece_captured:
            move.is_capture = True
            for piece_type in Piece:
                if self.pieces[~self.color][piece_type] & move.piece_captured:
                    move.captured_piece_type = piece_type
                    break
        
        #  Set en passant square
        if move.moved_piece_type == Piece.PAWN and abs(move.start_row - move.end_row) == 2:
            self.en_passant_possible = ((move.start_row + move.end_row)//2, move.end_col)
        else:
            self.en_passant_possible = ()

        move.check_pawn_promotion()

        for piece_type in Piece:
            if self.pieces[self.color][piece_type] & move.piece_moved:
                self.pieces[self.color][piece_type] &= ~(np.uint64(move.piece_moved))     
                if move.is_pawn_promotion:
                    self.pieces[self.color][Piece.QUEEN] |= np.uint64(move.piece_captured)
                else:
                    self.pieces[self.color][piece_type] |= np.uint64(move.piece_captured)
                    break  
        
        if move.is_en_passant_move:
            en_passant_captured = move.piece_captured >> 8 if self.color == Color.WHITE else move.piece_captured << 8
            for piece_type in Piece:
                if self.pieces[~self.color][piece_type] & en_passant_captured:
                    self.pieces[~self.color][piece_type] &= ~(np.uint64(en_passant_captured))   
                    break  

        else:
            for piece_type in Piece:
                if self.pieces[~self.color][piece_type] & move.piece_captured:
                    self.pieces[~self.color][piece_type] &= ~(np.uint64(move.piece_captured))   
                    break  
        
        if move.is_castle_move:
            if move.end_col - move.start_col == 2: # kingside castle
                rightmost_rook_start = self.pieces[self.color][Piece.ROOK] & np.uint64(~self.pieces[self.color][Piece.ROOK] + 1)
                if rightmost_rook_start:
                    self.pieces[self.color][Piece.ROOK] &= ~rightmost_rook_start
                    rightmost_rook_end = self.get_bit_mask(move.end_row, move.end_col-1)
                    self.pieces[self.color][Piece.ROOK] |= rightmost_rook_end
            else: # queenside castle
                highest_bit = self.find_highest_set_bit_position(self.pieces[self.color][Piece.ROOK])
                if highest_bit >= 0:
                    leftmost_rook_start = self.pieces[self.color][Piece.ROOK] & np.uint64(1 << highest_bit)
                    self.pieces[self.color][Piece.ROOK] &= ~leftmost_rook_start
                    lefttmost_rook_end = self.get_bit_mask(move.end_row, move.end_col+1)
                    self.pieces[self.color][Piece.ROOK] |= lefttmost_rook_end

        # Castling rights
        self.update_castle_rights(move)
        self.castle_rights_log.append(CastleRights(self.current_castling_rights.wks, self.current_castling_rights.bks, 
                                               self.current_castling_rights.wqs, self.current_castling_rights.bqs))

        self.combined_color = np.zeros(2, dtype=np.uint64) 
        for p in Piece:
            for c in Color:
                self.combined_color[c] |= self.pieces[c][p]
        
        self.board = np.uint64(0)
        self.board = self.combined_color[Color.WHITE] | self.combined_color[Color.BLACK]

        self.move_log.append(move)
        self.color = ~self.color


    
    def undo_move(self):
        if self.move_log:
            move = self.move_log.pop()
            self.color = ~self.color

            if move.is_pawn_promotion:
                self.pieces[self.color][Piece.QUEEN] &= ~(np.uint64(move.piece_captured))
                self.pieces[self.color][Piece.PAWN] |= np.uint64(move.piece_moved)
            else:
                for piece_type in Piece:
                    if self.pieces[self.color][piece_type] & move.piece_captured:
                        self.pieces[self.color][piece_type] &= ~(np.uint64(move.piece_captured))
                        self.pieces[self.color][piece_type] |= np.uint64(move.piece_moved)
                        break
            
            if move.is_capture:
                if move.is_en_passant_move:
                    en_passant_captured = move.piece_captured >> 8 if self.color == Color.WHITE else move.piece_captured << 8
                    self.pieces[~self.color][move.captured_piece_type] |= np.uint64(en_passant_captured)
                    self.en_passant_possible = (move.end_row, move.end_col)
                else:
                    self.pieces[~self.color][move.captured_piece_type] |= move.piece_captured
            else:
                if len(self.move_log) > 0:
                    previous_move = self.move_log[-1]
    
                    if previous_move.moved_piece_type == Piece.PAWN and abs(previous_move.start_row - previous_move.end_row) == 2:
                        self.en_passant_possible = ((previous_move.start_row + previous_move.end_row)//2, previous_move.end_col)
                    else:
                        self.en_passant_possible = ()
                else:
                    self.en_passant_possible = ()
            
            # Undo castle rights
            self.castle_rights_log.pop()
            self.current_castling_rights = self.castle_rights_log[-1]

            # Undo castle moves
            if move.is_castle_move:
                if move.end_col - move.start_col == 2: # kingside castle
                    rightmost_rook_start = self.pieces[self.color][Piece.ROOK] & np.uint64(~self.pieces[self.color][Piece.ROOK] + 1)
                    if rightmost_rook_start:
                        self.pieces[self.color][Piece.ROOK] &= ~rightmost_rook_start
                        rightmost_rook_end = self.get_bit_mask(move.end_row, move.end_col+1)
                        self.pieces[self.color][Piece.ROOK] |= rightmost_rook_end
                else: # queenside castle
                    highest_bit = self.find_highest_set_bit_position(self.pieces[self.color][Piece.ROOK])
                    if highest_bit >= 0:
                        leftmost_rook_start = self.pieces[self.color][Piece.ROOK] & np.uint64(1 << highest_bit)
                        self.pieces[self.color][Piece.ROOK] &= ~leftmost_rook_start
                        lefttmost_rook_end = self.get_bit_mask(move.end_row, move.end_col-2)
                        self.pieces[self.color][Piece.ROOK] |= lefttmost_rook_end
            
            self.combined_color = np.zeros(2, dtype=np.uint64) 
            for p in Piece:
                for c in Color:
                    self.combined_color[c] |= self.pieces[c][p]
            
            self.board = self.combined_color[Color.WHITE] | self.combined_color[Color.BLACK]

    def update_castle_rights(self, move):
        if move.moved_piece_type == Piece.KING and move.moved_piece_color == Color.WHITE:
            self.current_castling_rights.wks = False
            self.current_castling_rights.wqs = False
        elif move.moved_piece_type == Piece.KING and move.moved_piece_color == Color.BLACK:
            self.current_castling_rights.bks = False
            self.current_castling_rights.bqs = False
        elif move.moved_piece_type == Piece.ROOK and move.moved_piece_color == Color.WHITE:
            if move.start_row == 7:
                if move.start_col == 0: # left rook
                    self.current_castling_rights.wqs = False
                elif move.start_col == 7: # right rook
                    self.current_castling_rights.wks = False
        elif move.moved_piece_type == Piece.ROOK and move.moved_piece_color == Color.BLACK:
            if move.start_row == 0:
                if move.start_col == 0: # left rook
                    self.current_castling_rights.bqs = False
                elif move.start_col == 7: # right rook
                    self.current_castling_rights.bks = False

    def get_valid_moves(self):
        # Making a copy to make sure we do not modify the original state of the board
        original_pieces = np.copy(self.pieces)
        original_combined_color = np.copy(self.combined_color)
        original_board = self.board
        original_color = self.color
        original_move_log = list(self.move_log)
        temp_en_passant_possible = self.en_passant_possible
        original_castle_rights_log = [CastleRights(cr.wks, cr.bks, cr.wqs, cr.bqs) for cr in self.castle_rights_log]
        temp_castling_rights = CastleRights(self.current_castling_rights.wks, self.current_castling_rights.bks, 
                                            self.current_castling_rights.wqs, self.current_castling_rights.bqs)
        moves = self.get_all_possible_moves()
        
        king_bitmap = self.pieces[self.color][Piece.KING]
        king_row, king_col = self.get_coordinates(king_bitmap)
        self.get_castle_moves(king_row, king_col, moves)

        for i in range(len(moves) - 1,-1, -1):
            self.make_move(moves[i])
            self.color = ~self.color
            if self.in_check():
                moves.remove(moves[i])
            self.color = ~self.color
            self.undo_move()
        
        if len(moves) == 0: #checkmate or stalemate
            if self.in_check():
                self.check_mate = True
            else:
                self.stale_mate = True
        else:
            self.check_mate = False
            self.stale_mate = False
        
        # restoring original board state
        self.pieces = original_pieces
        self.combined_color = original_combined_color
        self.board = original_board
        self.color = original_color
        self.move_log = original_move_log
        self.en_passant_possible = temp_en_passant_possible
        self.castle_rights_log = original_castle_rights_log
        self.current_castling_rights = temp_castling_rights

        return moves
                        
    def in_check(self):
        king_bitmap = self.pieces[self.color][Piece.KING]
        king_row, king_col = self.get_coordinates(king_bitmap)
        return self.square_under_attack(king_row, king_col)

    def square_under_attack(self, r, c):
        self.color = ~self.color
        opp_moves = self.get_all_possible_moves()
        self.color = ~self.color
        for move in opp_moves:
            if move.end_row == r and move.end_col == c:
                return True
        return False


    def get_all_possible_moves(self):
        moves = []
        current_pieces = self.combined_color[self.color]

        while current_pieces:
            
            # Get rightmost set bit 
            rightmost_piece = current_pieces & np.uint64(~current_pieces+1)
            # Zero-out rightmost piece -> consider next rightmost piece
            current_pieces = current_pieces & ~rightmost_piece
            row, col = self.get_coordinates(rightmost_piece)

            for piece_type in Piece:
                if self.pieces[self.color][piece_type] & rightmost_piece:
                    if piece_type == Piece.PAWN:
                        self.get_pawn_moves(row, col, moves)
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
        return moves

    def get_pawn_moves(self, r, c, moves):
        if self.color == Color.WHITE:
            if r > 0 and not (self.board &  self.get_bit_mask(r-1, c)):
                moves.append(Move((r,c), (r-1, c)))
                if r == 6 and not(self.board & self.get_bit_mask(r-2, c)):
                    moves.append(Move((r,c), (r-2,c)))
            if r > 0 and c > 0:
                if self.combined_color[Color.BLACK] & self.get_bit_mask(r-1, c-1):
                    moves.append(Move((r,c), (r-1, c-1)))
                elif (r-1, c-1) == self.en_passant_possible and not (self.board &  self.get_bit_mask(r-1, c-1)):
                    moves.append(Move((r,c), (r-1, c-1), is_en_passant_move=True))
            if r > 0 and c < 7: 
                if self.combined_color[Color.BLACK] & self.get_bit_mask(r-1, c+1):
                    moves.append(Move((r,c), (r-1, c+1)))
                elif (r-1, c+1) == self.en_passant_possible and not (self.board &  self.get_bit_mask(r-1, c+1)):
                    moves.append(Move((r,c), (r-1, c+1), is_en_passant_move=True))
        else:
            if r < 7 and not(self.board & self.get_bit_mask(r+1, c)):
                moves.append(Move((r,c), (r+1,c)))
                if r == 1 and not (self.board & self.get_bit_mask(r+2, c)):
                    moves.append(Move((r,c), (r+2,c)))
            if r < 7 and c > 0:
                if self.combined_color[Color.WHITE] & self.get_bit_mask(r+1, c-1):
                    moves.append(Move((r,c), (r+1, c-1)))
                elif (r+1, c-1) == self.en_passant_possible and not (self.board &  self.get_bit_mask(r+1, c-1)):
                    moves.append(Move((r,c), (r+1, c-1), is_en_passant_move=True))
            if r < 7 and c < 7: 
                if self.combined_color[Color.WHITE] & self.get_bit_mask(r+1, c+1):
                    moves.append(Move((r,c), (r+1, c+1)))
                elif (r+1, c+1) == self.en_passant_possible and not (self.board &  self.get_bit_mask(r+1, c+1)):
                    moves.append(Move((r,c), (r+1, c+1), is_en_passant_move=True))

    def get_rook_moves(self, r, c, moves):
        directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]
        self.perform_linear_move(r, c, moves, directions)

    def get_bishop_moves(self, r, c, moves):
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        self.perform_linear_move(r, c, moves, directions)

    def get_knight_moves(self, r, c, moves):
        directions = [(1, -2), (1, 2), (-1, -2), (-1, 2), (-2, -1), (-2, 1), (2, -1), (2, 1)]
        self.perform_single_move(r, c, moves, directions)

    def get_king_moves(self, r, c, moves):
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1), (-1, 0), (0, 1), (1, 0), (0, -1)]
        self.perform_single_move(r, c, moves, directions)

    def get_queen_moves(self, r, c, moves):
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1), (-1, 0), (0, 1), (1, 0), (0, -1)]
        self.perform_linear_move(r, c, moves, directions)

    def perform_linear_move(self, r, c, moves, directions):
        for dir_r, dir_c in directions:
            move_r, move_c = r + dir_r, c + dir_c
            
            while 0 <= move_r <= 7 and 0 <= move_c <= 7:
                if self.combined_color[self.color] & self.get_bit_mask(move_r, move_c):
                    break  
                moves.append(Move((r, c), (move_r, move_c)))
                
                if self.combined_color[~self.color] & self.get_bit_mask(move_r, move_c):
                    break  
                
                move_r += dir_r
                move_c += dir_c
    
    def perform_single_move(self, r, c, moves, directions):
        for dir_r, dir_c in directions:
            move_r, move_c = r + dir_r, c + dir_c
            
            if 0 <= move_r <= 7 and 0 <= move_c <= 7:
                if self.combined_color[self.color] & self.get_bit_mask(move_r, move_c):
                    continue  
                moves.append(Move((r, c), (move_r, move_c)))
    
    def get_castle_moves(self, r, c, moves):
        if self.square_under_attack(r, c):
            return # cannot castle while in check
        if (self.color == Color.WHITE and self.current_castling_rights.wks) or (self.color == Color.BLACK and self.current_castling_rights.bks):
            self.get_kingside_castle_moves(r, c, moves, self.color)
        if (self.color == Color.WHITE and self.current_castling_rights.wqs) or (self.color == Color.BLACK and self.current_castling_rights.bqs):
            self.get_queenside_castle_moves(r, c, moves, self.color)


    def get_kingside_castle_moves(self, r, c, moves, ally_color):
        if not (self.board & self.get_bit_mask(r, c+1)) and not (self.board & self.get_bit_mask(r, c+2)):
            if not self.square_under_attack(r, c + 1) and not self.square_under_attack(r, c + 2):
                moves.append(Move((r, c), (r, c+2), is_castle_move = True))

    def get_queenside_castle_moves(self, r, c, moves, ally_color):
        if not (self.board & self.get_bit_mask(r, c-1)) and not (self.board & self.get_bit_mask(r, c-2)) and not (self.board & self.get_bit_mask(r, c-3)):
            if not self.square_under_attack(r, c - 1) and not self.square_under_attack(r, c - 2):
                moves.append(Move((r, c), (r, c-2), is_castle_move = True))
                
    def get_bit_mask(self, row, column):
        bit_mask = np.uint64(1 << (63 - (row * 8 + column)))
        return bit_mask

    def get_coordinates(self, bit_mask):
        square = (63 - int(np.log2(bit_mask)))
        row = square // 8
        col = square % 8
        return row, col

    def find_highest_set_bit_position(self, bit_mask):
        if bit_mask == 0:
            return -1
        position = 0
        while bit_mask:
            position += 1
            bit_mask >>= 1
        return position - 1

    def init_board(self):
        self.pieces[Color.WHITE][Piece.PAWN] = np.uint64(0x000000000000FF00)
        self.pieces[Color.WHITE][Piece.KNIGHT] = np.uint64(0x0000000000000042)
        self.pieces[Color.WHITE][Piece.BISHOP] = np.uint64(0x0000000000000024)
        self.pieces[Color.WHITE][Piece.ROOK] = np.uint64(0x0000000000000081)
        self.pieces[Color.WHITE][Piece.KING] = np.uint64(0x0000000000000008)
        self.pieces[Color.WHITE][Piece.QUEEN] = np.uint64(0x0000000000000010)

        self.pieces[Color.BLACK][Piece.PAWN] = np.uint64(0x00FF000000000000)
        self.pieces[Color.BLACK][Piece.KNIGHT] = np.uint64(0x4200000000000000)
        self.pieces[Color.BLACK][Piece.BISHOP] = np.uint64(0x2400000000000000)
        self.pieces[Color.BLACK][Piece.ROOK] = np.uint64(0x8100000000000000)
        self.pieces[Color.BLACK][Piece.KING] = np.uint64(0x0800000000000000)
        self.pieces[Color.BLACK][Piece.QUEEN] = np.uint64(0x1000000000000000)
    
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
    



class CastleRights:
    def __init__(self, wks, bks, wqs, bqs):
        self.wks = wks
        self.bks = bks
        self.wqs = wqs
        self.bqs = bqs



class Move():

    ranks_to_rows = {"1" : 7, "2" : 6, "3" : 5, "4" : 4,
                     "5" : 3, "6" : 2, "7" : 1, "8" : 0}
    rows_to_ranks = {v:k for k, v in ranks_to_rows.items()}
    files_to_cols = {"a" : 0, "b" : 1, "c" : 2, "d" : 3,
                     "e" : 4, "f" : 5, "g" : 6, "h" : 7}
    cols_to_files = {v:k for k, v in files_to_cols.items()}

    def __init__(self, start_sq, end_sq, is_en_passant_move = False, is_castle_move = False):
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
        self.is_en_passant_move = is_en_passant_move
        self.is_castle_move = is_castle_move


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
    
