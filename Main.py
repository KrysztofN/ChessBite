import ChessEngine 
import pygame as p

WIDTH = HEIGHT = 512
DIMENSION = 8 # 8x8 chessboard
SQ_SIZE = HEIGHT // DIMENSION
MAX_FPS = 15
IMAGES = {}

def load_images():
    pieces = ['wp', 'wR', 'wN', 'wK', 'wQ', 'bp', 'bR', 'bN', 'bB', 'bK', 'bQ']
    for piece in pieces:
        IMAGES[piece] = p.transform.scale(p.image.load("assets/" + piece + ".png"), (SQ_SIZE, SQ_SIZE))

def main():
    p.init()
    screen = p.display.set_mode(WIDTH, HEIGHT)
    clock = p.time.Clock()
    screen.fill(p.Color("white"))
    gs = ChessEngine.GameState()
    load_images()
    running = True
    while running:
        for e in p.event.get():
            if e.type == p.QUIT:
                running = False
        draw_game_state(screen, gs)
        clock.tick(MAX_FPS)
        p.display.flip()

def draw_game_state(screen, gs):
    drawBoard(screen)
    drawPieces(screen, gs.board)

if __name__ == "__main__":
    main()