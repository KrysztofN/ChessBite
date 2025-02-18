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
        self.inCheck = False
        self.pins = []
        self.check = []
        self.captured_piece = False
    
    def make_move(self, move):

        if self.combined_color[~self.color] & move.piece_captured:
            move.is_capture = True
            for piece_type in Piece:
                if self.pieces[~self.color][piece_type] & move.piece_captured:
                    move.captured_piece_type = piece_type
                    break

        for piece_type in Piece:
            if self.pieces[self.color][piece_type] & move.piece_moved:
                self.pieces[self.color][piece_type] &= ~(np.uint64(move.piece_moved))     
                self.pieces[self.color][piece_type] |= np.uint64(move.piece_captured)
                break  
        
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

            for piece_type in Piece:
                if self.pieces[self.color][piece_type] & move.piece_captured:
                    self.pieces[self.color][piece_type] &= ~(np.uint64(move.piece_captured))
                    self.pieces[self.color][piece_type] |= np.uint64(move.piece_moved)
                    break
            
            if move.is_capture:
                self.pieces[~self.color][move.captured_piece_type] |= move.piece_captured
            
            self.combined_color = np.zeros(2, dtype=np.uint64) 
            for p in Piece:
                for c in Color:
                    self.combined_color[c] |= self.pieces[c][p]
            
            self.board = self.combined_color[Color.WHITE] | self.combined_color[Color.BLACK]

    def get_valid_moves(self):
        # Making a copy to not modify the original state of the board
        original_pieces = np.copy(self.pieces)
        original_combined_color = np.copy(self.combined_color)
        original_board = self.board
        original_color = self.color
        original_move_log = list(self.move_log)

        moves = []
        self.in_check, self.pins, self.checks = self.check_for_pins_and_checks()
        king_bitmap = self.pieces[self.color][Piece.KING]
        king_row, king_col = self.get_coordinates(king_bitmap)

        if self.in_check:
            if len(self.checks) == 1:  
                moves = self.get_all_possible_moves()
                check = self.checks[0]
                check_row = check[0]
                check_col = check[1]
                piece_checking = self.get_piece_at(check_row, check_col)
                valid_squares = []
                
                # If the checking piece is a knight, we can only capture it or move the king
                if piece_checking[1] == Piece.KNIGHT:
                    valid_squares = [(check_row, check_col)]
                else:
                    # For other pieces, we can block the check or capture the checking piece
                    for i in range(1, 8):
                        valid_square = (king_row + check[2] * i, king_col + check[3] * i)
                        valid_squares.append(valid_square)
                        if valid_square[0] == check_row and valid_square[1] == check_col:
                            break
                
                # Filter moves that don't address the check
                for i in range(len(moves) - 1, -1, -1):
                    if moves[i].piece_moved != king_bitmap:  # If not a king move
                        if not (moves[i].end_row, moves[i].end_col) in valid_squares:
                            moves.remove(moves[i])
            else:  
                self.get_king_moves(king_row, king_col, moves)
        else:
            moves = self.get_all_possible_moves()
        
        legal_moves = []
        for move in moves:
            self.make_move(move)
            self.color = ~self.color 
            in_check, _, _ = self.check_for_pins_and_checks()
            self.color = ~self.color
            self.undo_move()
            
            if not in_check:
                legal_moves.append(move)
        
        # restoring original board state
        self.pieces = original_pieces
        self.combined_color = original_combined_color
        self.board = original_board
        self.color = original_color
        self.move_log = original_move_log
        
        return legal_moves

    def is_checkmate(self):
        if not self.in_check:
            return False
        
        return len(self.get_valid_moves()) == 0

    def is_stalemate(self):
        if self.in_check:
            return False
        
        return len(self.get_valid_moves()) == 0

    def is_game_over(self):
        if self.is_checkmate():
            return True, "0-1" if self.color == Color.WHITE else "1-0"
        elif self.is_stalemate():
            return True, "1/2-1/2"
        else:
            return False, None

    def check_for_pins_and_checks(self):
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1), (-1, 0), (0, 1), (1, 0), (0, -1)]
        pins = []
        checks = []
        in_check = False
        king_bitmap = self.pieces[self.color][Piece.KING]
        start_row, start_col = self.get_coordinates(king_bitmap)

        for i in range(len(directions)):
            d = directions[i]
            possible_pin = ()
            for j in range(1, 8):
                end_row = start_row + d[0] * j
                end_col = start_col + d[1] * j
                if 0 <= end_row <= 7 and 0 <= end_col <= 7:
                    end_piece = self.get_piece_at(end_row, end_col)
                    if end_piece is None:
                        continue
                    if end_piece[0] == self.color:
                        if possible_pin == ():
                            possible_pin = (end_row, end_col, d[0], d[1])
                        else:
                            break
                    elif end_piece[0] == ~self.color:
                        type = end_piece[1]
                        if(0 <= i <= 3 and type == Piece.BISHOP) or \
                                (4 <= i <= 7 and type == Piece.ROOK) or \
                                (j == 1 and type == Piece.PAWN and ((~self.color == Color.WHITE and 6 <= i <= 7) or (~self.color == Color.BLACK and 4 <= i <= 5))) or \
                                (type == Piece.QUEEN) or (j == 1 and type == Piece.KING):
                            if possible_pin == ():
                                in_check = True
                                checks.append((end_row, end_col, d[0], d[1]))
                                break
                            else:
                                pins.append(possible_pin)
                                break
                        else:
                            break
                else:
                    break
        
        knight_moves = [(1, -2), (1, 2), (-1, -2), (-1, 2), (-2, -1), (-2, 1), (2, -1), (2, 1)]
        for m in knight_moves:
            end_row = start_row + m[0]
            end_col = start_col + m[1]
            if 0 <= end_row <= 7 and 0 <= end_col <= 7:
                end_piece = self.get_piece_at(end_row, end_col)
                if end_piece is not None and end_piece[0] == ~self.color and end_piece[1] == Piece.KNIGHT:
                    in_check = True
                    checks.append((end_row, end_col, m[0], m[1]))
        return in_check, pins, checks
                        
                        
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
            if r > 0 and c < 7: 
                if self.combined_color[Color.BLACK] & np.uint64(1 << (63 - ((r-1) * 8 + (c+1)))):
                    moves.append(Move((r,c), (r-1, c+1)))
        else:
            if r < 7 and not(self.board & np.uint64(1 << (63 - ((r+1) * 8 + c)))):
                moves.append(Move((r,c), (r+1,c)))
                if r == 1 and not (self.board & np.uint64(1 << (63 - ((r+2) * 8 + c)))):
                    moves.append(Move((r,c), (r+2,c)))
            if r < 7 and c > 0:
                if self.combined_color[Color.WHITE] & np.uint64(1 << (63 - ((r+1) * 8 + (c-1)))):
                    moves.append(Move((r,c), (r+1, c-1)))
            if r < 7 and c < 7: 
                if self.combined_color[Color.WHITE] & np.uint64(1 << (63 - ((r+1) * 8 + (c+1)))):
                    moves.append(Move((r,c), (r+1, c+1)))

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