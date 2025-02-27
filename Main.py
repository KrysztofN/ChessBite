import ChessEngine 
import numpy as np
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1' # don't display pygame prompt
import pygame as p
from constans import Color, Piece
from Move import Move



WIDTH = HEIGHT = 512
DIMENSION = 8 # 8x8 chessboard
SQ_SIZE = HEIGHT // DIMENSION
MAX_FPS = 15
IMAGES = {}

def load_images():
    pieces = ['wp', 'wR', 'wN', 'wB' ,'wK', 'wQ', 'bp', 'bR', 'bN', 'bB', 'bK', 'bQ']
    for piece in pieces:
        IMAGES[piece] = p.transform.scale(p.image.load("assets/" + piece + ".png"), (SQ_SIZE, SQ_SIZE))

def main():
    p.init()
    screen = p.display.set_mode((WIDTH, HEIGHT))
    clock = p.time.Clock()
    screen.fill(p.Color("white"))
    gs = ChessEngine.ChessBoard()
    gs.init_board()
    valid_moves = gs.get_valid_moves()
    move_made = False

    load_images()
    running = True
    sqSelected = ()
    playerClicks = []
    while running:
        for e in p.event.get():
            if e.type == p.QUIT:
                running = False
            elif e.type == p.MOUSEBUTTONDOWN:
                location = p.mouse.get_pos() # (x, y) location of mouse
                column = location[0]//SQ_SIZE 
                row = location[1]//SQ_SIZE
                if sqSelected == (row, column): # pressed the same square twice
                    sqSelected = ()
                    playerClicks = []
                else:
                    sqSelected = (row, column)
                    playerClicks.append(sqSelected)
                if len(playerClicks) == 2: # second click -> move 
                    move = Move(playerClicks[0], playerClicks[1])
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

        if move_made:
            valid_moves = gs.get_valid_moves()
            move_made = False

        draw_game_state(playerClicks, valid_moves, screen, gs)
        clock.tick(MAX_FPS)
        p.display.flip()


def draw_game_state(playerClicks, valid_moves, screen, gs):
    draw_board(screen)
    if len(playerClicks) == 1:
        highlight_possible_positions(playerClicks, valid_moves, screen, gs)
    draw_pieces(screen, gs)

def highlight_possible_positions(playerClicks, valid_moves, screen, gs):
    highlighted_squares = []
    start_r, start_c = playerClicks[0][0], playerClicks[0][1]
    for move in valid_moves:
        if start_r == move.start_row and start_c == move.start_col:
            highlighted_squares.append((move.end_row, move.end_col))
    
    # White is 0, black is 1 
    # Only allow to select a piece if it's current color's turn
    if gs.combined_color[gs.color] & np.uint64(1 << (63 - (start_r * 8 + start_c))):
        s = p.Surface((SQ_SIZE, SQ_SIZE))
        s.set_alpha(70)
        s.fill(p.Color('grey'))
        screen.blit(s, (start_c * SQ_SIZE, start_r * SQ_SIZE))

    for end_r, end_c in highlighted_squares:
        center_x = end_c * SQ_SIZE + SQ_SIZE//2
        center_y = end_r * SQ_SIZE + SQ_SIZE//2
        # if capture possible
        if gs.combined_color[~gs.color] & np.uint64(1 << (63 - (end_r * 8 + end_c))):
            p.draw.circle(screen, p.Color('grey'), (center_x, center_y), SQ_SIZE//2.5, 8)
        else:
            p.draw.circle(screen, p.Color('grey'), (center_x, center_y), SQ_SIZE//6)

def draw_board(screen):
    # colors = [p.Color(184,139,74), p.Color(227,193,111)]
    colors = [p.Color(238, 238, 210), p.Color(118, 150, 86)]
    for row in range(DIMENSION):
        for column in range(DIMENSION):
            color = colors[(row+column + 1) % 2]
            x = column * SQ_SIZE
            y = row * SQ_SIZE
            p.draw.rect(screen, color, p.Rect(x, y, SQ_SIZE, SQ_SIZE))

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