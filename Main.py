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
                    print(playerClicks)
                    move = Move(playerClicks[0], playerClicks[1], gs.board)
                    print(move.get_chess_notation())
                    gs.make_move(move)
                    sqSelected = () # reset user clicks
                    playerClicks = []
            elif e.type == p.KEYDOWN:
                if e.key == p.K_r:
                    gs.undo_move()

        draw_game_state(screen, gs)
        clock.tick(MAX_FPS)
        p.display.flip()

def draw_game_state(screen, gs):
    draw_board(screen)
    draw_pieces(screen, gs)


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