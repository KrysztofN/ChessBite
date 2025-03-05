from constans import Color, Piece, File, Rank, PieceMapping
import numpy as np
from Move import Move

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
            
            if move.moved_piece_type == Piece.PAWN and abs(move.start_row - move.end_row) == 2:
                self.en_passant_possible = ()
            
            self.combined_color = np.zeros(2, dtype=np.uint64) 
            for p in Piece:
                for c in Color:
                    self.combined_color[c] |= self.pieces[c][p]
            
            self.board = self.combined_color[Color.WHITE] | self.combined_color[Color.BLACK]

    def get_valid_moves(self):
        # Making a copy to make sure we do not modify the original state of the board
        original_pieces = np.copy(self.pieces)
        original_combined_color = np.copy(self.combined_color)
        original_board = self.board
        original_color = self.color
        original_move_log = list(self.move_log)
        temp_en_passant_possible = self.en_passant_possible

        moves = self.get_all_possible_moves()
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
            rightmost_piece = current_pieces & (~current_pieces+1)
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
            if r > 0 and not (self.board &  np.uint64(1 << (63 - ((r-1) * 8 + c)))):
                moves.append(Move((r,c), (r-1, c)))
                if r == 6 and not(self.board & np.uint64(1 << (63 - ((r-2) * 8 + c)))):
                    moves.append(Move((r,c), (r-2,c)))
            if r > 0 and c > 0:
                if self.combined_color[Color.BLACK] & np.uint64(1 << (63 - ((r-1) * 8 + (c-1)))):
                    moves.append(Move((r,c), (r-1, c-1)))
                # TODO: when en passant is it neccesary to check whether there is a piece at the capture location?
                elif (r-1, c-1) == self.en_passant_possible and not (self.board &  np.uint64(1 << (63 - ((r-1) * 8 + (c-1))))):
                    moves.append(Move((r,c), (r-1, c-1), is_en_passant_move=True))
            if r > 0 and c < 7: 
                if self.combined_color[Color.BLACK] & np.uint64(1 << (63 - ((r-1) * 8 + (c+1)))):
                    moves.append(Move((r,c), (r-1, c+1)))
                elif (r-1, c+1) == self.en_passant_possible and not (self.board &  np.uint64(1 << (63 - ((r-1) * 8 + (c+1))))):
                    moves.append(Move((r,c), (r-1, c+1), is_en_passant_move=True))
        else:
            if r < 7 and not(self.board & np.uint64(1 << (63 - ((r+1) * 8 + c)))):
                moves.append(Move((r,c), (r+1,c)))
                if r == 1 and not (self.board & np.uint64(1 << (63 - ((r+2) * 8 + c)))):
                    moves.append(Move((r,c), (r+2,c)))
            if r < 7 and c > 0:
                if self.combined_color[Color.WHITE] & np.uint64(1 << (63 - ((r+1) * 8 + (c-1)))):
                    moves.append(Move((r,c), (r+1, c-1)))
                elif (r+1, c-1) == self.en_passant_possible and not (self.board &  np.uint64(1 << (63 - ((r+1) * 8 + (c-1))))):
                    moves.append(Move((r,c), (r+1, c-1), is_en_passant_move=True))
            if r < 7 and c < 7: 
                if self.combined_color[Color.WHITE] & np.uint64(1 << (63 - ((r+1) * 8 + (c+1)))):
                    moves.append(Move((r,c), (r+1, c+1)))
                elif (r+1, c+1) == self.en_passant_possible and not (self.board &  np.uint64(1 << (63 - ((r+1) * 8 + (c+1))))):
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
                if self.combined_color[self.color] & np.uint64(1 << (63 - (move_r * 8 + move_c))):
                    break  
                moves.append(Move((r, c), (move_r, move_c)))
                
                if self.combined_color[~self.color] & np.uint64(1 << (63 - (move_r * 8 + move_c))):
                    break  
                
                move_r += dir_r
                move_c += dir_c
    
    def perform_single_move(self, r, c, moves, directions):
        for dir_r, dir_c in directions:
            move_r, move_c = r + dir_r, c + dir_c
            
            if 0 <= move_r <= 7 and 0 <= move_c <= 7:
                if self.combined_color[self.color] & np.uint64(1 << (63 - (move_r * 8 + move_c))):
                    continue  
                moves.append(Move((r, c), (move_r, move_c)))
                
    def get_piece_at(self, row, column):
        square_mask = np.uint64(1 << (63 - (row * 8 + column)))
        for piece_type in Piece:
            for color in Color:
                if self.pieces[color][piece_type] & square_mask:
                    return (color, piece_type)
        return None

    def get_coordinates(self, bit_mask):
        square = (63 - int(np.log2(bit_mask)))
        row = square // 8
        col = square % 8
        return row, col
        
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