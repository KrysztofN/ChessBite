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
        best_move = None
        better_move_flag = 0

        if gs.color == Color.WHITE:
            best_score = -float('inf')
        else:
            best_score = float('inf')

        for move in valid_moves:
            gs.make_move(move)
            is_maximizing = (gs.color == Color.WHITE)
            score = self.negamax(gs, is_maximizing, depth=1, alpha = -float('inf'), beta = float('inf'))
            gs.undo_move()

            if gs.color == Color.WHITE:
                if score > best_score:
                    best_score = score
                    best_move = move
                    better_move_flag +=1
            else:
                if score < best_score:
                    best_score = score
                    best_move = move
                    better_move_flag += 1
        
        if better_move_flag < 2:
            best_move = random.choice(valid_moves)

        return best_move
    
    def minimax(self, gs, is_maximizing, depth, alpha, beta):
        if depth == 0 or gs.check_mate or gs.stale_mate:
            if gs.check_mate:
                return CHECKMATE if is_maximizing else -CHECKMATE
            elif gs.stale_mate:
                return STALEMATE
            return self.score_material(gs.pieces)

        if is_maximizing: #Maximizing player
            best_score = -float('inf')
            for move in gs.get_valid_moves():
                gs.make_move(move)
                score = self.minimax(gs, not is_maximizing, depth - 1, alpha, beta)
                gs.undo_move()
                best_score = max(best_score, score)
                alpha = max(alpha, best_score)
                if beta <= alpha:
                    break
            return best_score
        else: # Minimizing player
            best_score = float('inf')
            for move in gs.get_valid_moves():
                gs.make_move(move)
                score = self.minimax(gs, not is_maximizing, depth - 1, alpha, beta)
                gs.undo_move()
                best_score = min(best_score, score)
                beta = min(beta, best_score)
                if beta <= alpha:
                    break
            return best_score
    
    def negamax(self, gs, is_maximizing, depth, alpha, beta):
        if depth == 0 or gs.check_mate or gs.stale_mate:
            if gs.check_mate:
                return  CHECKMATE if is_maximizing else -CHECKMATE
            elif gs.stale_mate:
                return STALEMATE
            return self.score_material(gs.pieces) if is_maximizing else -self.score_material(gs.pieces)
        
        score = -float('inf')
        for move in gs.get_valid_moves():
            gs.make_move(move)
            score = max(score, -self.negamax(gs, not is_maximizing, depth - 1, -beta, -alpha))
            gs.undo_move()
            alpha = max(alpha, score)
            if beta <= alpha:
                break
        return score
    

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

        

        
