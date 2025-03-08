import random
from Constants import Color, Piece

piece_score = {Piece.KING: 0, Piece.PAWN : 1, Piece.ROOK: 5, Piece.KNIGHT: 3, Piece.BISHOP: 3, Piece.QUEEN : 10}
CHECKMATE = 1000
STALEMATE = 0

class AIMoveFinder:
    def __init__(self):
        pass

    def find_random_move(self, valid_moves):
        return random.choice(valid_moves)

    def find_best_move(self, gs, valid_moves):
        best_move = random.choice(valid_moves)
        turn_color = gs.color
        if turn_color == Color.WHITE:
            best_score = -float('inf')
        else:
            best_score = float('inf')

        for valid_move in valid_moves:
            gs.make_move(valid_move)
            curr_score = self.score_material(gs.pieces)
            if gs.stale_mate:
                    curr_score = STALEMATE
            if turn_color == Color.WHITE:
                if gs.check_mate:
                    curr_score = CHECKMATE
                if curr_score > best_score:
                    best_score = curr_score
                    best_move = valid_move
            else:
                if gs.check_mate:
                    curr_score = -CHECKMATE
                if curr_score < best_score:
                    best_score = curr_score
                    best_move = valid_move
            gs.undo_move()

        return best_move
    

    # TODO: Scoring based on piece posiiton
    def score_material(self, pieces):
        score = 0
        for color in Color:
            for piece_type in Piece:
                current_pieces = pieces[color][piece_type]
                while current_pieces:
                    rightmost_piece = current_pieces & (~current_pieces + 1)
                    current_pieces &= ~rightmost_piece
                    if color == Color.WHITE:
                        # white maximizing
                        score += piece_score[piece_type]
                    else:
                        # black minimazing
                        score -= piece_score[piece_type]
        return score

        

        
