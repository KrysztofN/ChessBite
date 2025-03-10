import ChessEngine, AIMoveFinder
import numpy as np
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1' # don't display pygame prompt
import pygame as p
from Constants import Color, Piece, Player



BOARD_WIDTH = BOARD_HEIGHT = 512
MOVE_LOG_PANEL_WIDTH = 250
MOVE_LOG_PANEL_HEIGHT = BOARD_HEIGHT
DIMENSION = 8 # 8x8 chessboard
SQ_SIZE = BOARD_HEIGHT // DIMENSION
MAX_FPS = 15
IMAGES = {}

def load_images():
    pieces = ['wp', 'wR', 'wN', 'wB' ,'wK', 'wQ', 'bp', 'bR', 'bN', 'bB', 'bK', 'bQ']
    for piece in pieces:
        IMAGES[piece] = p.transform.scale(p.image.load("assets/" + piece + ".png"), (SQ_SIZE * 0.9, SQ_SIZE * 0.9))

def main():
    p.init()
    screen = p.display.set_mode((BOARD_WIDTH + MOVE_LOG_PANEL_WIDTH, BOARD_HEIGHT))
    clock = p.time.Clock()
    screen.fill(p.Color("white"))
    gs = ChessEngine.ChessBoard()
    move_log_font = p.font.SysFont("Arial", 15, False, False)
    ai = AIMoveFinder.AIMoveFinder()
    gs.init_board()
    valid_moves = gs.get_valid_moves()
    move_made = False
    game_over = False
    player_one = Player.HUMAN # player one corresponds to white
    player_two = Player.HUMAN # player two corresponds to black

    load_images()
    running = True
    sqSelected = ()
    playerClicks = []
    while running:
        human_turn = (gs.color == Color.WHITE and player_one == Player.HUMAN) or (gs.color == Color.BLACK and player_two == Player.HUMAN) # 0-Human, 1-AI
        for e in p.event.get():
            if e.type == p.QUIT:
                running = False
            elif e.type == p.MOUSEBUTTONDOWN:
                if not game_over and human_turn:
                    location = p.mouse.get_pos() # (x, y) location of mouse
                    column = location[0]//SQ_SIZE  
                    row = location[1]//SQ_SIZE
                    if sqSelected == (row, column) or column >= 8: # pressed the same square twice
                        sqSelected = ()
                        playerClicks = []
                    else:
                        sqSelected = (row, column)
                        playerClicks.append(sqSelected)
                    if len(playerClicks) == 2: # second click -> move 
                        move = ChessEngine.Move(playerClicks[0], playerClicks[1])
                        print(move.get_chess_notation())
                        for i in range(len(valid_moves)):
                            if move == valid_moves[i]:
                                gs.make_move(valid_moves[i])
                                move_made = True
                                sqSelected = () # reset user clicks
                                playerClicks = []
                        if not move_made:
                            playerClicks = [sqSelected]
            elif e.type == p.KEYDOWN:
                if e.key == p.K_r:
                    gs.undo_move() 
                    move_made = True
                    game_over = False

        # AI moves
        if not game_over and not human_turn:
            best_move = ai.find_best_move(gs, valid_moves)
            gs.make_move(best_move)
            move_made = True

        if move_made:
            score = ai.score_material(gs.pieces)
            print(score)
            valid_moves = gs.get_valid_moves()
            move_made = False

        draw_game_state(playerClicks, valid_moves, screen, gs, move_log_font)

        if not game_over:
            if gs.check_mate:
                game_over = True
                print(f"{gs.color} wins by checkmate!!!")
            elif gs.stale_mate:
                game_over = True
                print(f"Draw by stalemate!")



        clock.tick(MAX_FPS)
        p.display.flip()


def draw_game_state(playerClicks, valid_moves, screen, gs, move_log_font):
    draw_board(screen)
    if len(playerClicks) == 1:
        highlight_possible_positions(playerClicks, valid_moves, screen, gs)
    draw_pieces(screen, gs)
    draw_move_log(screen, gs, move_log_font)

def draw_move_log(screen, gs, font):
    move_log_rectangle = p.Rect(BOARD_WIDTH, 0, MOVE_LOG_PANEL_WIDTH, MOVE_LOG_PANEL_HEIGHT)
    p.draw.rect(screen, p.Color("#36454F"), move_log_rectangle)
    move_log = gs.move_log
    padding = 5
    move_texts = []
    moves_per_row = 3

    for i in range(0, len(move_log), 2):
        move_string = str(i//2 + 1) + ". " + str(move_log[i]) + " "
        if i+1 < len(move_log):
            move_string  += str(move_log[i+1]) + " "
        move_texts.append(move_string)


    space_text = padding
    for i in range(0, len(move_texts), moves_per_row):
        text = ""
        for j in range(moves_per_row):
            if i + j < len(move_texts):
                text += move_texts[i+j]
        text_obj = font.render(text, True, p.Color('white'))
        text_location = move_log_rectangle.move(padding, space_text)
        screen.blit(text_obj, text_location)
        space_text += text_obj.get_height()

def highlight_possible_positions(playerClicks, valid_moves, screen, gs):
    valid_moves_for_piece = []
    start_r, start_c = playerClicks[0][0], playerClicks[0][1]
    for move in valid_moves:
        if start_r == move.start_row and start_c == move.start_col:
            valid_moves_for_piece.append((move))
    
    # White is 0, black is 1 
    # Only allow to select a piece if it's current color's turn
    if gs.combined_color[gs.color] & np.uint64(1 << (63 - (start_r * 8 + start_c))):
        s = p.Surface((SQ_SIZE, SQ_SIZE))
        s.set_alpha(70)
        s.fill(p.Color('grey'))
        screen.blit(s, (start_c * SQ_SIZE, start_r * SQ_SIZE))

    for move in valid_moves_for_piece:
        end_r, end_c = move.end_row, move.end_col
        center_x = end_c * SQ_SIZE + SQ_SIZE//2
        center_y = end_r * SQ_SIZE + SQ_SIZE//2

        # if capture possible
        if gs.combined_color[~gs.color] & np.uint64(1 << (63 - (end_r * 8 + end_c))):
            p.draw.circle(screen, p.Color('grey'), (center_x, center_y), SQ_SIZE//2.5, 8)
        elif move.is_en_passant_move:
            p.draw.circle(screen, p.Color('grey'), (center_x, center_y), SQ_SIZE//2.5, 8)
        else:
            p.draw.circle(screen, p.Color('grey'), (center_x, center_y), SQ_SIZE//6)
      

def draw_board(screen):
    colors = [p.Color(184,139,74), p.Color(227,193,111)]
    # colors = [p.Color(118, 150, 86), p.Color(238, 238, 210)]

    dark_square = colors[0]
    light_square = colors[1]
    text_color_on_dark = colors[1]
    text_color_on_white = colors[0]

    font = p.font.SysFont("Arial", SQ_SIZE // 4)

    for row in range(DIMENSION):
        for column in range(DIMENSION):
            color = colors[(row+column + 1) % 2]
            x = column * SQ_SIZE
            y = row * SQ_SIZE
            p.draw.rect(screen, color, p.Rect(x, y, SQ_SIZE, SQ_SIZE))

            if column == 0:
                text_color = text_color_on_dark if color == dark_square else text_color_on_white
                rank_text = font.render(str(8-row), True, text_color)
                screen.blit(rank_text, (x+5, y+5))
            
            if row == 7:
                text_color = text_color_on_dark if color == dark_square else text_color_on_white
                file_text = font.render(chr(97+column), True, text_color)
                screen.blit(file_text, (x+SQ_SIZE - 10, y+SQ_SIZE - 20))

def draw_pieces(screen, gs):

    piece_mapping = {
        (Color.WHITE, Piece.PAWN): 'wp',
        (Color.WHITE, Piece.ROOK): 'wR',
        (Color.WHITE, Piece.KNIGHT): 'wN',
        (Color.WHITE, Piece.BISHOP): 'wB',
        (Color.WHITE, Piece.QUEEN): 'wQ',
        (Color.WHITE, Piece.KING): 'wK',
        (Color.BLACK, Piece.PAWN): 'bp',
        (Color.BLACK, Piece.ROOK): 'bR',
        (Color.BLACK, Piece.KNIGHT): 'bN',
        (Color.BLACK, Piece.BISHOP): 'bB',
        (Color.BLACK, Piece.QUEEN): 'bQ',
        (Color.BLACK, Piece.KING): 'bK',
    }

    for row in range(DIMENSION):
        for column in range(DIMENSION):
            square = row * 8 + column
            square_mask = 1 << (63 - square)
            for color in Color:
                for piece_type in Piece:
                    if gs.pieces[color][piece_type] & square_mask:
                        piece_key = piece_mapping.get((color, piece_type))
                        if piece_key in IMAGES:
                            x = column * SQ_SIZE
                            y = row * SQ_SIZE
                            screen.blit(IMAGES[piece_key], p.Rect(x, y, SQ_SIZE, SQ_SIZE))

if __name__ == "__main__":
    main()