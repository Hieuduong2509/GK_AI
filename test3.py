import pygame
import sys
import os
import heapq
import time
from collections import deque
from pygame.locals import QUIT, KEYDOWN, K_ESCAPE 
# =========================
# CÀI ĐẶT CƠ BẢN
# =========================
TILE_SIZE = 24
INFO_HEIGHT = 40
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
ORANGE = (255, 160, 0)
BACKGROUND = (20, 20, 40)


# =========================
# LỚP MAZE
# =========================
class Maze:
    def __init__(self, filename, tile_size):
        self.tile_size = tile_size
        self.wall_color = (68, 77, 169)
        self.food_color = (255, 204, 0)
        self.power_pellet_color = (255, 128, 0)
        self.data = []
        self.load_map(filename)

        # Kiểm tra xem map có dữ liệu không
        if not self.data or not self.data[0]:
             print(f"LỖI: File map '{filename}' rỗng hoặc không hợp lệ!")
             pygame.quit()
             sys.exit()

        self.rows = len(self.data)
        self.cols = len(self.data[0])

        self.pacman_start_pos = self._find_char('P')
        if self.pacman_start_pos is None:
             print("LỖI: Không tìm thấy 'P' trong map!")
             # Gán vị trí mặc định hoặc thoát
             # self.pacman_start_pos = (1, 1) # Ví dụ
             pygame.quit()
             sys.exit()

        self.food_positions = self._find_all_chars(['.'])
        self.power_pellet_positions = self._find_all_chars(['O'])
        self.ghost_start_positions = self._find_all_chars(['G', 'E']) # Có thể có 'E' hoặc không
        
    def count_remaining_food(self):
        """Đếm tất cả thức ăn (chấm '.' và bánh 'O') còn lại trên map."""
        count = 0
        # Duyệt qua self.data vì nó chứa trạng thái map hiện tại
        for row in self.data:
            for cell in row:
                if cell == '.' or cell == 'O':
                    count += 1
        return count
    def get_width(self):
        return self.cols

    def get_height(self):
        return self.rows

    def load_map(self, filename):
        full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
        if not os.path.exists(full_path):
            print(f"LỖI: Không tìm thấy file '{filename}' tại '{full_path}'")
            pygame.quit()
            sys.exit()
        try:
            with open(full_path, 'r') as f:
                for line in f:
                    self.data.append(list(line.strip()))
        except Exception as e:
            print(f"Lỗi khi đọc file map: {e}")
            pygame.quit()
            sys.exit()


    def get_char(self, x, y):
        if 0 <= y < self.rows and 0 <= x < self.cols:
            return self.data[y][x]
        return ' ' # Trả về ký tự trống nếu ra ngoài map

    def is_wall(self, x, y):
        # Coi ngoài map là tường để BFS không chạy ra ngoài
        if not (0 <= y < self.rows and 0 <= x < self.cols):
            return True
        return self.data[y][x] == '%'

    def is_dot(self, x, y):
         # Thêm kiểm tra biên an toàn
        if 0 <= y < self.rows and 0 <= x < self.cols:
            return self.data[y][x] == '.'
        return False

    def is_pie(self, x, y):
        # Thêm kiểm tra biên an toàn
        if 0 <= y < self.rows and 0 <= x < self.cols:
            return self.data[y][x] == 'O'
        return False

    def remove_dot(self, x, y): # Hàm này được gọi bởi Pacman._check_dot
        if 0 <= y < self.rows and 0 <= x < self.cols:
            if self.data[y][x] == '.':
                 self.data[y][x] = ' '
            # Không cần remove 'O' ở đây vì _check_dot tự làm

    def _find_char(self, char):
        for r_idx, row in enumerate(self.data):
            try:
                 c_idx = row.index(char)
                 return (c_idx, r_idx)
            except ValueError:
                 continue # Không tìm thấy trong hàng này
        return None # Không tìm thấy trong toàn bộ map

    def _find_all_chars(self, chars):
        positions = set() # Dùng set để tránh trùng lặp nếu map có nhiều ghost giống nhau
        for r_idx, row in enumerate(self.data):
            for c_idx, c in enumerate(row):
                if c in chars:
                    positions.add((c_idx, r_idx))
        return positions

    def draw(self, surface):
        for y in range(self.rows):
            for x in range(self.cols):
                c = self.data[y][x] # Lấy ký tự trực tiếp từ data đã cập nhật
                rect = pygame.Rect(x * self.tile_size, y * self.tile_size, self.tile_size, self.tile_size)
                if c == '%':
                    pygame.draw.rect(surface, self.wall_color, rect)
                elif c == '.':
                    pygame.draw.circle(surface, self.food_color, rect.center, 3)
                elif c == 'O':
                    pygame.draw.circle(surface, self.power_pellet_color, rect.center, 6)
                else: # Vẽ nền đen cho ô trống và cả vị trí P, G cũ
                     pygame.draw.rect(surface, BACKGROUND, rect)


# =========================
# LỚP PACMAN
# =========================
class Pacman:
    def __init__(self, maze: Maze):
        self.maze = maze
        self.x, self.y = maze.pacman_start_pos
        self.score = 0
        self.lives = 3
        # self.direction = (0, 0) # Không cần nếu di chuyển theo AI

        # --- Định nghĩa teleport_map ở đây để nhất quán ---
        w = self.maze.get_width()
        h = self.maze.get_height()
        self.teleport_map = {
            (1, 1): (w - 2, h - 2),
            (w - 2, 1): (1, h - 2),
            (1, h - 2): (w - 2, 1),
            (w - 2, h - 2): (1, 1)
        }
        self.teleport_origins = set(self.teleport_map.keys())

    def move(self, dx, dy):
        """Di chuyển Pacman một bước, có xử lý teleport khi VA VÀO TƯỜNG ở góc."""
        current_pos = (self.x, self.y)
        next_x, next_y = self.x + dx, self.y + dy

        # --- KIỂM TRA TELEPORT KHI VA VÀO TƯỜNG Ở GÓC ---
        # Chỉ teleport nếu bước đi tiếp theo là tường VÀ đang ở góc teleport
        if self.maze.is_wall(next_x, next_y) and current_pos in self.teleport_origins:
             # Kiểm tra xem hướng đi có phải là "đâm vào tường góc" không
             is_teleport_trigger = False
             if current_pos == (1, 1) and (dx == -1 or dy == -1): is_teleport_trigger = True
             elif current_pos == (self.maze.cols - 2, 1) and (dx == 1 or dy == -1): is_teleport_trigger = True
             elif current_pos == (1, self.maze.rows - 2) and (dx == -1 or dy == 1): is_teleport_trigger = True
             elif current_pos == (self.maze.cols - 2, self.maze.rows - 2) and (dx == 1 or dy == 1): is_teleport_trigger = True

             if is_teleport_trigger:
                 teleport_to = self.teleport_map[current_pos]
                 print(f"🌀 Pacman Teleport! Từ {current_pos} đến {teleport_to}")
                 self.update_position(*teleport_to) # Cập nhật vị trí và ăn (nếu có)
                 return # Kết thúc di chuyển

        # --- DI CHUYỂN BÌNH THƯỜNG ---
        if not self.maze.is_wall(next_x, next_y):
             self.update_position(next_x, next_y)
        # else: Không làm gì nếu va tường (và không phải teleport)


    def update_position(self, new_x, new_y):
        """Cập nhật vị trí và kiểm tra ăn."""
        # Không cần xóa 'P' cũ vì Game.draw sẽ vẽ lại toàn bộ
        self.x, self.y = new_x, new_y
        self._check_dot() # Kiểm tra và ăn tại vị trí mới

    def _check_dot(self):
        """Kiểm tra và ăn thức ăn tại vị trí hiện tại."""
        # Gọi trực tiếp is_dot/is_pie để kiểm tra
        if self.maze.is_dot(self.x, self.y):
            self.maze.data[self.y][self.x] = ' ' # Xóa '.' khỏi map data
            self.score += 10
            # Cập nhật lại food_positions để A* biết
            self.maze.food_positions.discard((self.x, self.y))
        elif self.maze.is_pie(self.x, self.y):
            self.maze.data[self.y][self.x] = ' ' # Xóa 'O' khỏi map data
            self.score += 50
            # Cập nhật lại power_pellet_positions
            self.maze.power_pellet_positions.discard((self.x, self.y))

    # Hàm check_teleport không cần thiết nữa vì logic nằm trong move()
    # def check_teleport(self): ...

    def draw(self, screen):
        px, py = self.x * TILE_SIZE + TILE_SIZE // 2, self.y * TILE_SIZE + TILE_SIZE // 2
        pygame.draw.circle(screen, YELLOW, (px, py), TILE_SIZE // 2 - 3)


# =========================
# LỚP GHOST
# =========================
class Ghost:
    def __init__(self, maze, x, y, color):
        self.maze = maze
        self.x, self.y = x, y
        self.color = color
        self.dx, self.dy = 1, 0 # Hướng di chuyển ban đầu

    def move(self):
        """Di chuyển Ghost và đổi hướng khi gặp tường."""
        nx, ny = self.x + self.dx, self.y + self.dy
        if self.maze.is_wall(nx, ny):
            # Đổi hướng ngẫu nhiên hoặc theo logic phức tạp hơn (tạm thời đổi ngược)
            self.dx, self.dy = -self.dx, -self.dy
            # Tính lại vị trí sau khi đổi hướng để tránh kẹt
            nx, ny = self.x + self.dx, self.y + self.dy

        # Chỉ di chuyển nếu ô tiếp theo không phải tường
        if not self.maze.is_wall(nx, ny):
             self.x, self.y = nx, ny

    def draw(self, screen):
        px, py = self.x * TILE_SIZE + TILE_SIZE // 2, self.y * TILE_SIZE + TILE_SIZE // 2
        pygame.draw.circle(screen, self.color, (px, py), TILE_SIZE // 2 - 3)


# =========================
# LỚP PROBLEM (Đã sửa cho Teleport + BFS Heuristic)
# =========================
class Problem:
    def __init__(self, maze):
        self.maze = maze
        self.start = maze.pacman_start_pos
        # Lấy food positions từ maze LÚC KHỞI TẠO problem
        self.initial_foods = maze.food_positions.union(maze.power_pellet_positions)
        self.cache = {} # Cache cho heuristic BFS

        # --- Định nghĩa thông tin teleport ---
        w = self.maze.get_width()
        h = self.maze.get_height()
        self.teleport_map = {
            (1, 1): (w - 2, h - 2),
            (w - 2, 1): (1, h - 2),
            (1, h - 2): (w - 2, 1),
            (w - 2, h - 2): (1, 1)
        }
        self.teleport_origins = set(self.teleport_map.keys())

    def get_start(self):
        # Trạng thái bắt đầu là vị trí và tập hợp food ban đầu
        return (self.start, frozenset(self.initial_foods))

    def is_goal(self, state):
        _, foods = state # Lấy tập food từ trạng thái hiện tại
        return len(foods) == 0

    def successors(self, state):
        (x, y), foods = state # foods là frozenset các thức ăn còn lại
        result = []

        # --- 1. HÀNH ĐỘNG TELEPORT (NẾU ĐANG Ở GÓC) ---
        if (x, y) in self.teleport_origins:
            (nx, ny) = self.teleport_map[(x, y)]
            nfoods = foods - {(nx, ny)} # Ăn nếu điểm đến có thức ăn
            # Hành động Teleport có chi phí 1
            result.append(((nx, ny), nfoods, 'Teleport'))

        # --- 2. HÀNH ĐỘNG DI CHUYỂN THƯỜNG ---
        for dx, dy, act in [(0, -1, 'North'), (0, 1, 'South'), (-1, 0, 'West'), (1, 0, 'East')]:
            nx, ny = x + dx, y + dy
            if not self.maze.is_wall(nx, ny):
                nfoods = foods - {(nx, ny)} # Ăn nếu điểm đến có thức ăn
                # Hành động di chuyển có chi phí 1
                result.append(((nx, ny), nfoods, act))
        return result

    def heuristic(self, state):
        """Heuristic: Khoảng cách BFS tới viên thức ăn xa nhất, CÓ XÉT TELEPORT."""
        (x, y), foods = state
        if not foods: return 0

        # Dùng cache để tránh tính lại BFS từ cùng một vị trí (x,y)
        if (x, y) not in self.cache:
            self.cache[(x, y)] = self.bfs_with_teleport((x, y))

        dist_map = self.cache[(x, y)]
        max_dist = 0
        for food_pos in foods:
             dist = dist_map.get(food_pos, float('inf'))
             # Nếu có 1 viên không đến được, coi như heuristic vô cùng lớn
             if dist == float('inf'): return float('inf')
             max_dist = max(max_dist, dist)
        return max_dist

    def bfs_with_teleport(self, start_pos):
        """BFS tính khoảng cách từ start_pos đến mọi ô, có xét teleport."""
        q = deque([start_pos])
        dist = {start_pos: 0}
        while q:
            (cx, cy) = q.popleft()
            current_dist = dist[(cx, cy)]

            # Khám phá láng giềng (N/S/E/W)
            for dx, dy in [(0,1),(1,0),(0,-1),(-1,0)]:
                nx, ny = cx + dx, cy + dy
                neighbor_pos = (nx, ny)
                if not self.maze.is_wall(nx, ny) and neighbor_pos not in dist:
                    dist[neighbor_pos] = current_dist + 1
                    q.append(neighbor_pos)

            # Khám phá teleport (nếu đang ở góc)
            if (cx, cy) in self.teleport_origins:
                teleport_dest = self.teleport_map[(cx, cy)]
                if teleport_dest not in dist:
                     dist[teleport_dest] = current_dist + 1 # Chi phí teleport = 1
                     q.append(teleport_dest)
        return dist


# =========================
# LỚP AGENT A* (Không đổi)
# =========================
class AgentAStar:
    def __init__(self, problem):
        self.problem = problem

    def solve(self):
        start_state = self.problem.get_start() # Lấy state ban đầu (pos, foods)
        frontier = []
        # Priority = heuristic(start), g_cost = 0
        heapq.heappush(frontier, (self.problem.heuristic(start_state), 0, start_state, []))
        visited = {start_state: 0} # Lưu state và g_cost thấp nhất đến đó

        nodes_explored = 0 # Bộ đếm trạng thái

        while frontier:
            nodes_explored += 1
            # Lấy state có f_cost thấp nhất
            f, g, current_state, actions = heapq.heappop(frontier)

            # Bỏ qua nếu đã có đường tốt hơn đến state này
            if g > visited[current_state]:
                 continue

            # Kiểm tra goal
            if self.problem.is_goal(current_state):
                print(f"🧠 A* đã khám phá {nodes_explored} trạng thái.")
                return actions # Trả về list các hành động

            # Khám phá successors
            # Successor trả về ((nx, ny), nfoods, act)
            for next_pos, next_foods, action in self.problem.successors(current_state):
                new_g = g + 1 # Chi phí mỗi bước là 1
                next_state = (next_pos, next_foods) # Tạo state kế tiếp

                # Nếu chưa thăm hoặc tìm thấy đường ngắn hơn
                if next_state not in visited or new_g < visited[next_state]:
                    visited[next_state] = new_g
                    h = self.problem.heuristic(next_state)
                    # Nếu heuristic là inf, không thêm vào frontier (trừ khi bắt buộc)
                    if h == float('inf'):
                         print(f"Warning: Heuristic is infinity for state {next_state}")
                         # Có thể bỏ qua state này nếu không muốn khám phá nhánh không thể thắng
                         # continue
                         # Hoặc gán priority rất lớn để nó bị đẩy xuống cuối
                         priority = float('inf')
                    else:
                         priority = new_g + h # f = g + h

                    heapq.heappush(frontier, (priority, new_g, next_state, actions + [action]))

        print(f"🧠 A* đã khám phá {nodes_explored} trạng thái nhưng không tìm thấy lời giải.")
        return [] # Không tìm thấy


# =========================
# GAME CHÍNH
# =========================
class Game:
    def __init__(self, filename, mode="manual"):
        pygame.init()
        self.maze = Maze(filename, TILE_SIZE)
        self.pacman = Pacman(self.maze)
        # Khởi tạo Ghosts dựa trên vị trí tìm được trong Maze
        self.ghosts = [Ghost(self.maze, x, y, RED) for (x, y) in self.maze.ghost_start_positions]
        self.mode = mode
        self.width = self.maze.cols * TILE_SIZE
        self.height = self.maze.rows * TILE_SIZE # Chiều cao chỉ của map
        self.screen_height_total = self.height + INFO_HEIGHT # Tổng chiều cao màn hình
        self.screen = pygame.display.set_mode((self.width, self.screen_height_total))
        pygame.display.set_caption(f"Pac-Man ({'Auto (A*)' if mode=='auto' else 'Manual'})")
        self.clock = pygame.time.Clock()
        self.running = True
        self.font = pygame.font.Font(None, 30) # Font cho score/lives
        self.end_font = pygame.font.Font(None, 72) # Font cho màn hình kết thúc
        self.game_message = "" # Lưu thông báo win/lose
        self.message_color = WHITE

        self.actions_taken_manual = [] # Lưu path khi chơi tay

        if mode == "auto":
            print("🤖 Đang tính toán đường đi A* (có xét Teleport)...")
            start_time = time.time()
            problem = Problem(self.maze)
            agent = AgentAStar(problem)
            self.moves = agent.solve() # List các hành động ['North', 'South', ...]

            if not self.moves:
                 print("❌ A* không tìm thấy lời giải!")
                 self.running = False # Có thể dừng game luôn nếu AI không giải được
                 self.game_message = "AI FAILED!"
                 self.message_color = RED
            else:
                 print(f"✅ A* tìm thấy {len(self.moves)} bước (thời gian: {time.time()-start_time:.2f}s)")
                 self.move_idx = 0 # Index cho hành động tiếp theo của AI
                 self.total_steps_ai = len(self.moves) # Lưu tổng số bước AI tính được

    # <<< HÀM XỬ LÝ INPUT CHO MANUAL MODE >>>
    def handle_input_manual(self):
        moved = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return moved
            if event.type == pygame.KEYDOWN:
                action_name = None
                dx, dy = 0, 0
                if event.key == pygame.K_UP: dx, dy = 0, -1; action_name = "UP"
                elif event.key == pygame.K_DOWN: dx, dy = 0, 1; action_name = "DOWN"
                elif event.key == pygame.K_LEFT: dx, dy = -1, 0; action_name = "LEFT"
                elif event.key == pygame.K_RIGHT: dx, dy = 1, 0; action_name = "RIGHT"
                elif event.key == pygame.K_ESCAPE: self.running = False; return moved

                if dx != 0 or dy != 0:
                    if self.pacman.move(dx, dy): # Gọi hàm move của Pacman
                        self.actions_taken_manual.append(action_name)
                        moved = True
        return moved

    # <<< HÀM UPDATE CHÍNH >>>
    def update(self, moved_manual=False):
        """Cập nhật trạng thái Pacman (cho AI), Ghosts, kiểm tra va chạm/thắng."""

        # --- Cập nhật Pacman nếu là AUTO mode ---
        pacman_moved_this_frame = moved_manual
        if self.mode == "auto" and hasattr(self, "moves") and self.move_idx < len(self.moves):
            move = self.moves[self.move_idx]
            dx, dy = {'North': (0,-1), 'South': (0,1), 'West': (-1,0), 'East': (1,0), 'Teleport': (0,0)}[move]

            # Nếu là teleport, gọi hàm teleport đặc biệt hoặc để move xử lý
            if move == 'Teleport':
                 # Logic teleport đã nằm trong pacman.move khi va tường ở góc
                 # Ở đây chỉ cần đảm bảo vị trí được cập nhật đúng
                 current_pos = (self.pacman.x, self.pacman.y)
                 if current_pos in self.pacman.teleport_origins:
                      dest_pos = self.pacman.teleport_map[current_pos]
                      print(f"🌀 AI Teleport! Từ {current_pos} đến {dest_pos}")
                      self.pacman.update_position(*dest_pos)
                      pacman_moved_this_frame = True
                 else:
                      print("Warning: AI requested Teleport but not at origin?")
            elif dx != 0 or dy != 0:
                self.pacman.move(dx, dy) # Gọi hàm move thông thường
                pacman_moved_this_frame = True

            self.move_idx += 1

        # --- Cập nhật Ghosts (chỉ di chuyển nếu Pacman di chuyển) ---
        if pacman_moved_this_frame:
             for g in self.ghosts:
                 g.move()

        # --- Kiểm tra va chạm Ghost ---
        pacman_pos = (self.pacman.x, self.pacman.y)
        for g in self.ghosts:
            if (g.x, g.y) == pacman_pos:
                # self.pacman.lives -= 1 # Hàm lose_life đã trừ rồi
                self.pacman.lose_life()
                print("💀 Pac-Man bị Ghost bắt!")
                if self.pacman.lives <= 0:
                    self.running = False
                    self.game_message = "GAME OVER!"
                    self.message_color = RED
                return # Dừng update sau khi bị bắt

        # --- Kiểm tra thắng ---
        # Lấy số food còn lại từ Maze object nơi Pacman cập nhật
        # Không dùng lại self.maze.food_positions vì nó không được cập nhật
        if self.maze.count_remaining_food() == 0:
            print("🎉 Pac-Man đã ăn hết thức ăn!")
            self.running = False
            self.game_message = "WINNER!"
            self.message_color = GREEN


    def draw(self):
        """Vẽ toàn bộ màn hình game."""
        self.screen.fill(BACKGROUND) # Tô nền
        self.maze.draw(self.screen)  # Vẽ map (tường, thức ăn)

        # Vẽ các đối tượng động
        for g in self.ghosts:
            g.draw(self.screen)
        self.pacman.draw(self.screen)

        # Vẽ khu vực thông tin (Score/Lives)
        info_rect = pygame.Rect(0, self.height, self.width, INFO_HEIGHT)
        pygame.draw.rect(self.screen, BLACK, info_rect) # Nền đen cho khu vực info
        score_text = self.font.render(f"Score: {self.pacman.score}", True, WHITE)
        lives_text = self.font.render(f"Lives: {self.pacman.lives}", True, WHITE)
        self.screen.blit(score_text, (10, self.height + 5))
        self.screen.blit(lives_text, (self.width - 100, self.height + 5))

        pygame.display.flip() # Hiển thị lên màn hình

    def run_game_loop(self):
        """Vòng lặp chính của game."""
        while self.running:
            moved_manual = False
            if self.mode == "manual":
                moved_manual = self.handle_input_manual()
            else: # Auto mode chỉ xử lý thoát game
                 for e in pygame.event.get():
                      if e.type == pygame.QUIT or (e.type == KEYDOWN and e.key == K_ESCAPE):
                           self.running = False

            self.update(moved_manual) # Cập nhật trạng thái game
            self.draw()             # Vẽ lại màn hình
            self.clock.tick(8)     # Giới hạn tốc độ game (8 FPS)

        self.show_end_screen() # Hiển thị màn hình kết thúc
        pygame.quit()

        # Trả về kết quả phù hợp
        if self.mode == 'auto' and hasattr(self, 'total_steps_ai'):
            print(f"\nTổng số bước AI tính toán: {self.total_steps_ai}")
        elif self.mode == 'manual':
            print("\n📍 Path Pacman đã đi (Manual):")
            print(self.actions_taken_manual)
            print(f"Tổng số bước (Manual): {len(self.actions_taken_manual)}")


    def show_end_screen(self):
        """Hiển thị màn hình kết thúc (WINNER/GAME OVER)."""
        if not self.game_message: # Nếu game kết thúc do thoát (ESC)
            return

        overlay = pygame.Surface((self.width, self.screen_height_total), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        text = self.end_font.render(self.game_message, True, self.message_color)
        text_rect = text.get_rect(center=(self.width // 2, self.screen_height_total // 2))
        self.screen.blit(text, text_rect)

        pygame.display.flip()
        print(f"--- Game ended: {self.game_message} ---")
        time.sleep(3)


# =========================
# MENU CHỌN CHẾ ĐỘ
# =========================
def show_menu():
    pygame.init()
    screen = pygame.display.set_mode((600, 400))
    pygame.display.set_caption("Pac-Man Menu")
    font = pygame.font.Font(None, 48)
    running = True
    mode = None
    while running:
        screen.fill((30, 30, 60))
        title = font.render("Chọn chế độ chơi:", True, YELLOW)
        auto = font.render("A - Auto (A*)", True, WHITE) # Sửa tên cho rõ
        manual = font.render("M - Manual", True, WHITE)
        screen.blit(title, (120, 100))
        screen.blit(auto, (150, 180))
        screen.blit(manual, (150, 240))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_a: mode = "auto"; running = False
                elif event.key == pygame.K_m: mode = "manual"; running = False
    pygame.quit() # Đóng cửa sổ menu trước khi mở game
    return mode


if __name__ == "__main__":
    try:
        selected_mode = show_menu()
        if selected_mode: # Nếu người dùng đã chọn mode (không phải đóng cửa sổ)
             print("Mode đã chọn:", selected_mode)
             game = Game("map.txt", selected_mode) # <<< SỬA TÊN FILE MAP Ở ĐÂY
             game.run_game_loop() # <<< GỌI HÀM VÒNG LẶP MỚI
        else:
             print("Không chọn mode nào.")
    except Exception as e:
        print(f"⚠️ Lỗi không xác định: {e}")
        import traceback
        traceback.print_exc()
        pygame.quit() # Đảm bảo pygame được đóng nếu có lỗi