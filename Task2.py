import pygame
import sys


TILE_SIZE = 24
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
ORANGE= (255,160,0)

# MAZE
class Maze:
    def __init__(self, maze_file):
        self.maze_file = maze_file
        self.maze = []

        self.load_maze()

    def load_maze(self):
        with open(self.maze_file, "r") as f:
            for line in f:
                self.maze.append(list(line.strip()))

    def display(self):
        for row in self.maze:
            print("".join(row))

    def get_width(self):
        return len(self.maze[0])

    def get_height(self):
        return len(self.maze)

    def is_wall(self, x, y):
        return self.maze[y][x] == '%'

    def is_dot(self, x, y):
        return self.maze[y][x] == '.'

    def is_pie(self, x, y):
        return self.maze[y][x] == 'O'

    def is_exit(self):
        return self.maze.maze[self.y][self.x] == 'E'

    def remove_dot(self, x, y):
        if self.is_dot(x, y):
            self.maze[y][x] = ' '

    def find_char(self, c):
        for y, row in enumerate(self.maze):
            for x, cell in enumerate(row):
                if cell == c:
                    return (x, y)
        return None

    def find_all_ghosts(self):
        ghosts = []
        for y, row in enumerate(self.maze):
            for x, cell in enumerate(row):
                if cell == 'G':
                    ghosts.append((x, y))
        return ghosts

    def draw(self, screen, path=None):
        """Vẽ mê cung lên màn hình, có thể thêm đường đi (path)"""
        for y, row in enumerate(self.maze):
            for x, cell in enumerate(row):
                px, py = x * TILE_SIZE, y * TILE_SIZE
                if cell == "%":
                    pygame.draw.rect(screen, BLUE, (px, py, TILE_SIZE, TILE_SIZE))
                elif cell == ".":
                    pygame.draw.circle(screen, WHITE, (px + TILE_SIZE // 2, py + TILE_SIZE // 2), 3)
                elif cell == "O":
                    pygame.draw.circle(screen, ORANGE, (px + TILE_SIZE //2 , py + TILE_SIZE // 2), 7)
                elif cell == "P":
                    pygame.draw.circle(screen, YELLOW, (px + TILE_SIZE // 2, py + TILE_SIZE // 2), 10)
                elif cell == "G":
                    pygame.draw.circle(screen, RED, (px + TILE_SIZE // 2, py + TILE_SIZE // 2), 10)
                elif cell =='E':
                    pygame.draw.circle(screen,GREEN,(px + TILE_SIZE // 2, py + TILE_SIZE // 2), 10)
                else:
                    pygame.draw.rect(screen, BLACK, (px, py, TILE_SIZE, TILE_SIZE))

        # Vẽ đường đi (nếu có)
        if path:
            for (x, y) in path:
                pygame.draw.rect(screen, GREEN, (x*TILE_SIZE+6, y*TILE_SIZE+6, TILE_SIZE-12, TILE_SIZE-12))

class Ghost:
    def __init__(self, maze: Maze, x,y):
        self.maze = maze   
        # vị trí bắt đầu
        self.x=x
        self.y=y    

        self.direction = (0, 0)  # dx, dy
        self.dx, self.dy =(1,0) 

    def move(self):
        new_x = self.x + self.dx
        new_y = self.y + self.dy
        if self.maze.is_wall(new_x, new_y):
            self.dx, self.dy = -self.dx, -self.dy
            new_x = self.x + self.dx
            new_y = self.y + self.dy
        else:
            self.maze.maze[self.y][self.x] = ' '
            self.x = new_x
            self.y = new_y
            self.maze.maze[self.y][self.x] = 'G'
    
    def get_position(self):
        return (self.x, self.y)

    def __str__(self):
        return f"Ghost(x={self.x}, y={self.y}, dir=({self.dx},{self.dy}))"


class Pacman:
    def __init__(self, maze: Maze):
        self.maze = maze   
        self.x, self.y = maze.find_char('P')  # vị trí bắt đầu
        self.score = 0  
        self.lives = 3
        self.direction = (0, 0)  # dx, dy
        w = self.maze.get_width()
        h = self.maze.get_height()
        self.corners = [
            (0, 1),  # góc trên trái
            (1,0),
            (w-1,1),
            (w - 2, 1),  # góc trên phải
            (0, h-2),
            (1,h -1),
            (1,h),  # góc dưới trái
            (w-2, h -1),
            (w-2,0),
            (w - 1, h - 2)  # góc dưới phải
        ]

    def move(self, dx, dy):
        new_x = self.x + dx
        new_y = self.y + dy
        print(new_x,new_y)
        if (new_x , new_y)  in self.corners:
            teleport_to = self.check_teleport(dx, dy)
            if teleport_to:
                self.update_position(teleport_to[0], teleport_to[1])  


        if self.get_position()== self.maze.find_char('O'):
            for i in range(5):
                return self.maze.is_wall(x, y)

        # move normally   
        if self._can_move_to(new_x, new_y):
            # update position 
            self.update_position(new_x, new_y)
        else:
            print("💥 Va vào tường!")



    def move_up(self): self.move(0, -1)
    def move_down(self): self.move(0, 1)
    def move_left(self): self.move(-1, 0)
    def move_right(self): self.move(1, 0)

    def update_position(self, new_x, new_y):
        self.maze.maze[self.y][self.x]=" " 
        self.x = new_x
        self.y = new_y
        self.maze.maze[self.y][self.x] = 'P'
        self._check_dot()

    def _can_move_to(self, x, y):
        if x < 0 or y < 0 or x >= self.maze.get_width() or y >= self.maze.get_height():
            return False
        
        return not self.maze.is_wall(x, y)

    def check_teleport(self, dx, dy):
        """Kiểm tra nếu Pacman đang ở góc và đâm vào tường thì teleport."""
        current_pos = (self.x, self.y)
        top_left = (1, 1)
        top_right = (self.maze.get_width() - 2, 1)
        bottom_left = (1, self.maze.get_height() - 2)
        bottom_right = (self.maze.get_width() - 2, self.maze.get_height() - 2)

        # Logic teleport (4 góc trong)
        if current_pos == top_left and (dx == -1 or dy == -1):
            return bottom_right
        elif current_pos == top_right and (dx == 1 or dy == -1):
            return bottom_left
        elif current_pos == bottom_left and (dx == -1 or dy == 1):
            return top_right
        elif current_pos == bottom_right and (dx == 1 or dy == 1):
            return top_left

        return None  # Không teleport

    def _check_dot(self):
        if self.maze.is_dot(self.x, self.y):
            self.maze.remove_dot(self.x, self.y)
            self.score += 10
            print(f"🍒 Ăn được 1 điểm! Tổng điểm: {self.score}")
        elif self.maze.maze[self.y][self.x] == 'O':
            self.maze.maze[self.y][self.x] = ' '  # xoá vật phẩm
            self.can_phase = True
            self.phase_end_time = time.time() + 5  # hiệu lực 5 giây
            print("💫 Ăn vật phẩm O! Pacman có thể đi xuyên tường trong 5 giây!")



    def get_position(self):
        return (self.x, self.y)

    def __str__(self):
        return f"Pacman(x={self.x}, y={self.y}, score={self.score})"



# =========================
# 2️⃣  CLASS PROBLEM
# =========================
class Problem:
    def __init__(self, pacman: Pacman, initial_pos, goal=None):
        self.pacman = pacman
        self.goal = goal  # (x, y)
        self.initial_pos = initial_pos

    def is_goal(self):
        return self.goal == self.pacman.get_position()

    def possible_actions(self):
        actions = []
        x, y = self.pacman.get_position()
        for dx, dy, name in [(0, -1, 'UP'), (0, 1, 'DOWN'), (-1, 0, 'LEFT'), (1, 0, 'RIGHT')]:
            if not self.pacman.maze.is_wall(x + dx, y + dy):
                actions.append(name)
        return actions
    
import time

class Game:
    
    def __init__(self, maze_file, agent=None):
        
        pygame.init()
        pygame.display.set_caption("Pacman")

        # --- Tạo đối tượng ---
        self.maze = Maze(maze_file)
        self.pacman = Pacman(self.maze)
        ghost_positions = self.maze.find_all_ghosts()
        self.ghosts = [Ghost(self.maze, x, y) for (x, y) in ghost_positions]
        # --- Màn hình ---
        self.WIDTH = self.maze.get_width() * TILE_SIZE
        self.HEIGHT = self.maze.get_height() * TILE_SIZE
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))

        # --- Game State ---
        self.font = pygame.font.Font(None, 36)
        self.clock = pygame.time.Clock()
        self.MOVE_DELAY = 0
        self.last_move_time = 0
        self.running = True

        # --- Lưu lịch sử hành động ---
        self.actions_taken = []

    def get_possible_actions(self):
        """Các hướng khả dụng (không đụng tường)."""
        actions = []
        x, y = self.pacman.get_position()
        for dx, dy, name in [(0, -1, 'UP'), (0, 1, 'DOWN'), (-1, 0, 'LEFT'), (1, 0, 'RIGHT')]:
            if not self.pacman.maze.is_wall(x + dx, y + dy):
                actions.append(name)
        return actions

    # 🎮 Vòng lặp chính
    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(10)

        # 🏁 Khi kết thúc game → trả về danh sách hành động
        pygame.quit()
        return self.actions_taken

    # 🧭 Xử lý phím
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            self.pacman.direction = (0, -1)
            self.last_action = "UP"
        elif keys[pygame.K_DOWN]:
            self.pacman.direction = (0, 1)
            self.last_action = "DOWN"
        elif keys[pygame.K_LEFT]:
            self.pacman.direction = (-1, 0)
            self.last_action = "LEFT"
        elif keys[pygame.K_RIGHT]:
            self.pacman.direction = (1, 0)
            self.last_action = "RIGHT"
        else:
            self.pacman.direction = (0, 0)
            self.last_action = None

    # 🧠 Cập nhật game
    def update(self):
        now = time.time()
        if now - self.last_move_time >= self.MOVE_DELAY:
            dx, dy = self.pacman.direction
            if dx != 0 or dy != 0:
                self.pacman.move(dx, dy)

                # 📝 Ghi lại hành động đã đi
                if self.last_action:
                    self.actions_taken.append(self.last_action)

            self.last_move_time = now

        # 👻 Kiểm tra va chạm với ghost
        for ghost in self.ghosts:
            ghost.move()
            if self.pacman.get_position() == ghost.get_position():
                print(f"Pacman mất 1 mạng! Còn {self.pacman.lives} mạng.")
                if self.pacman.lives <= 0:
                    print("💀 Game Over!")
                    self.running = False

    # 🎨 Vẽ màn hình
    def render(self):
        self.maze.draw(self.screen)

        # Vẽ Pacman
        px, py = self.pacman.get_position()
        pygame.draw.circle(
            self.screen, YELLOW,
            (px * TILE_SIZE + TILE_SIZE // 2, py * TILE_SIZE + TILE_SIZE // 2),
            TILE_SIZE // 2 - 4
        )

        # Vẽ Ghosts
        for ghost in self.ghosts:
            gx, gy = ghost.get_position()
            pygame.draw.circle(
                self.screen, RED,
                (gx * TILE_SIZE + TILE_SIZE // 2, gy * TILE_SIZE + TILE_SIZE // 2),
                TILE_SIZE // 2 - 4
            )

        # Hiển thị điểm và mạng
        score_text = self.font.render(f"Score: {self.pacman.score}", True, WHITE)
        lives_text = self.font.render(f"Lives: {self.pacman.lives}", True, WHITE)
        self.screen.blit(score_text, (10, self.HEIGHT - 30))
        self.screen.blit(lives_text, (200, self.HEIGHT - 30))

        pygame.display.flip()


# 🧩 Hàm main
def main():
    game = Game("task02_pacman_example_map.txt")
    path = game.run()   # khi game kết thúc → trả về path
    print("\n📍 Path Pacman đã đi:")
    print(path)
    print(f"Tổng số bước: {len(path)}")

if __name__ == "__main__":
    main()