import pygame
from pygame.locals import QUIT, KEYDOWN, K_ESCAPE

pygame.init()

# ======================
# BẢN ĐỒ ASCII (Pac-Man Layout)
# ======================
MAP_DATA = [
    "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%",
    "%       .        P                 %",
    "% %%%%%%%%%%%%%%%%%%%%%%% %%%%%%%% %",
    "% %%   %   %G     %%%%%%%   %%O    %",
    "% %% % % % % %%%% %%%%%%%%% %% %%%%%",
    "% %% % % % % .           %% %%G    %",
    "% %% % % % % % %%%%  %%%  . %%%%%% %",
    "% %  % % %   %    %% %%%%%%%%      %",
    "% %% %O% %%%%%%%% %%    .   %% %%%%%",
    "% %% %   %%      E%%%%%%%%% %%     %",
    "%    %%%%%% %%%%%%%   .  %% %%%%%% %",
    "%%%%%%      %       %%%% %% %O     %",
    "%  O   %%%%%% %%%%% %    %% %% %%%%%",
    "% %%%%%% .   O%       %%%%% %%     %",
    "%G       %%%%%% %%%%%%%%%%% %%  %% %",
    "%%%%%%%%%%                 G%%%%%% %",
    "%.         %%%%%%%%%%%%%%%%        %",
    "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%"
]

# ======================
# CẤU HÌNH
# ======================
TILE_SIZE = 20  # kích thước mỗi ký tự trên màn hình
ROWS = len(MAP_DATA)
COLS = len(MAP_DATA[0])

SCREEN_WIDTH = COLS * TILE_SIZE
SCREEN_HEIGHT = ROWS * TILE_SIZE

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Pac-Man Map Lines")

clock = pygame.time.Clock()
FPS = 60
border_color = (78, 86, 192)
border_width = 4

# ======================
# TẠO DANH SÁCH ĐƯỜNG LINE TỪ MAP
# ======================
lines = []

# Quét ngang (tạo line theo hàng)
for y, row in enumerate(MAP_DATA):
    x_start = None
    for x, c in enumerate(row):
        if c == '%':
            if x_start is None:
                x_start = x
        else:
            if x_start is not None:
                # kết thúc đoạn tường ngang
                x1 = x_start * TILE_SIZE
                x2 = (x - 1) * TILE_SIZE + TILE_SIZE
                y_pos = y * TILE_SIZE + TILE_SIZE // 2
                lines.append(((x1, y_pos), (x2, y_pos)))
                x_start = None
    if x_start is not None:
        x1 = x_start * TILE_SIZE
        x2 = (len(row) - 1) * TILE_SIZE + TILE_SIZE
        y_pos = y * TILE_SIZE + TILE_SIZE // 2
        lines.append(((x1, y_pos), (x2, y_pos)))

# Quét dọc (tạo line theo cột)
for x in range(COLS):
    y_start = None
    for y in range(ROWS):
        if MAP_DATA[y][x] == '%':
            if y_start is None:
                y_start = y
        else:
            if y_start is not None:
                y1 = y_start * TILE_SIZE
                y2 = (y - 1) * TILE_SIZE + TILE_SIZE
                x_pos = x * TILE_SIZE + TILE_SIZE // 2
                lines.append(((x_pos, y1), (x_pos, y2)))
                y_start = None
    if y_start is not None:
        y1 = y_start * TILE_SIZE
        y2 = (ROWS - 1) * TILE_SIZE + TILE_SIZE
        x_pos = x * TILE_SIZE + TILE_SIZE // 2
        lines.append(((x_pos, y1), (x_pos, y2)))

# ======================
# VẼ
# ======================
running = True
while running:
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False
        elif event.type == KEYDOWN and event.key == K_ESCAPE:
            running = False

    screen.fill((0, 0, 0))

    # Vẽ các đường tường
    for start, end in lines:
        pygame.draw.line(screen, border_color, start, end, border_width)

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
