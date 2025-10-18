import pygame
from pygame.locals import QUIT, KEYDOWN, K_ESCAPE
import os
import heapq  # Sử dụng Hàng đợi ưu tiên cho A*
import time

# ======================
# LỚP PROBLEM (Định nghĩa bài toán tìm kiếm "lớn")
# ======================
from collections import deque

class Problem:
    def __init__(self, maze):
        self.maze = maze
        self.start_pos = self.maze.pacman_start_pos
        self.food_locations = self.maze.food_positions.union(self.maze.power_pellet_positions)
        self.total_food_count = len(self.food_locations)
        self.bfs_cache = {}  # ✅ cache BFS results để tiết kiệm thời gian

    def get_start_state(self):
        return (self.start_pos, frozenset(self.food_locations))

    def is_goal_state(self, state):
        _, food_set = state
        return not food_set

    def get_successors(self, state):
        successors = []
        pacman_pos, food_set = state
        x, y = pacman_pos
        for action in ['North', 'South', 'East', 'West']:
            dx, dy = {'North':(0,-1), 'South':(0,1), 'East':(1,0), 'West':(-1,0)}[action]
            next_x, next_y = x + dx, y + dy
            if not self.maze.is_wall(next_x, next_y):
                next_pos = (next_x, next_y)
                new_food_set = food_set - {next_pos}
                successors.append(((next_pos, new_food_set), action, 1))
        return successors

    def heuristic(self, state):
        """
        Heuristic = khoảng cách BFS xa nhất từ vị trí hiện tại
                    tới các viên thức ăn còn lại (đảm bảo admissible)
        """
        pacman_pos, food_set = state
        if not food_set:
            return 0

        # --- DÙNG CACHE nếu đã từng tính BFS từ vị trí này ---
        if pacman_pos in self.bfs_cache:
            visited = self.bfs_cache[pacman_pos]
        else:
            visited = self._bfs_from(pacman_pos)
            self.bfs_cache[pacman_pos] = visited

        # --- Lấy khoảng cách xa nhất trong số các viên thức ăn ---
        distances = [visited.get(food, float('inf')) for food in food_set]
        max_dist = max(distances) if distances else 0

        # Nếu có viên không thể tới (inf), cho h=0 để tránh lỗi
        return max_dist if max_dist != float('inf') else 0

    def _bfs_from(self, start_pos):
        """Chạy BFS từ vị trí start_pos để lấy khoảng cách tới mọi ô hợp lệ."""
        q = deque([start_pos])
        visited = {start_pos: 0}
        while q:
            x, y = q.popleft()
            for dx, dy in [(0,1), (1,0), (0,-1), (-1,0)]:
                nx, ny = x + dx, y + dy
                if not self.maze.is_wall(nx, ny) and (nx, ny) not in visited:
                    visited[(nx, ny)] = visited[(x, y)] + 1
                    q.append((nx, ny))
        return visited


# ======================
# LỚP AGENT (Tác nhân giải quyết bài toán "lớn")
# ======================
class Agent:
    def __init__(self, problem):
        self.problem = problem

    def solve(self):
        """
        Sử dụng thuật toán A* để tìm đường đi tối ưu cho toàn bộ bài toán.
        """
        start_state = self.problem.get_start_state()
        
        # Frontier là một Hàng đợi ưu tiên
        # (priority, g_cost, state, actions_list)
        frontier = []
        heapq.heappush(frontier, (self.problem.heuristic(start_state), 0, start_state, []))
        
        # visited lưu trữ chi phí (g_cost) thấp nhất để đến một trạng thái
        visited = {start_state: 0}
        
        nodes_explored = 0

        while frontier:
            nodes_explored += 1
            # if nodes_explored % 1000 == 0:
            #     print(f"🧠 Đã khám phá {nodes_explored} trạng thái...")

            _, g_cost, current_state, actions = heapq.heappop(frontier)
            
            if g_cost > visited[current_state]:
                continue
                
            # Mục tiêu: Đã ăn hết thức ăn
            if self.problem.is_goal_state(current_state):
                print(f"🧠 A* (Cách 1) đã khám phá tổng cộng {nodes_explored} trạng thái.")
                return actions # Trả về danh sách hành động

            # Khám phá các ô lân cận
            for successor_state, action, step_cost in self.problem.get_successors(current_state):
                new_g_cost = g_cost + step_cost
                
                if successor_state not in visited or new_g_cost < visited[successor_state]:
                    visited[successor_state] = new_g_cost
                    h_cost = self.problem.heuristic(successor_state)
                    priority = new_g_cost + h_cost # f(n) = g(n) + h(n)
                    
                    new_actions = actions + [action]
                    heapq.heappush(frontier, (priority, new_g_cost, successor_state, new_actions))

        print(f"🧠 A* (Cách 1) đã khám phá {nodes_explored} trạng thái nhưng không tìm thấy lời giải.")
        return [] # Không tìm thấy đường đi

# ======================
# LỚP MAZE (MÊ CUNG)
# (Không thay đổi)
# ======================
class Maze:
    def __init__(self, filename, tile_size):
        self.tile_size = tile_size
        self.wall_color = (68, 77, 169)
        self.food_color = (255, 204, 0)
        self.power_pellet_color = (255, 128, 0)
        self.data = []
        self.load_map(filename)
        
        self.rows = len(self.data)
        self.cols = len(self.data[0])

        self.pacman_start_pos = self._find_char('P')
        self.food_positions = self._find_all_chars(['.'])
        self.power_pellet_positions = self._find_all_chars(['O'])
        self.ghost_start_positions = self._find_all_chars(['G', 'E'])

    def load_map(self, filename):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(current_dir, filename)
        
        if not os.path.exists(full_path):
            print(f"LỖI: Không thể tìm thấy file '{filename}' tại '{full_path}'.")
            print("Hãy chắc chắn bạn có file 'map.txt' trong cùng thư mục với file .py")
            pygame.quit()
            exit()
        
        with open(full_path, 'r') as f:
            for line in f:
                self.data.append(line.strip())

    def get_char(self, x, y):
        if 0 <= y < self.rows and 0 <= x < self.cols:
            return self.data[y][x]
        return ' '

    def is_wall(self, x, y):
        return self.get_char(x, y) == '%'
        
    def _find_char(self, char):
        for r_idx, row in enumerate(self.data):
            if char in row:
                return (row.find(char), r_idx)
        return None

    def _find_all_chars(self, chars):
        positions = []
        for r_idx, row in enumerate(self.data):
            for c_idx, c in enumerate(row):
                if c in chars:
                    positions.append((c_idx, r_idx))
        return set(positions)

    def draw_walls(self, surface):
        for y in range(self.rows):
            for x in range(self.cols):
                if self.is_wall(x, y):
                    rect = pygame.Rect(x * self.tile_size, y * self.tile_size, self.tile_size, self.tile_size)
                    pygame.draw.rect(surface, self.wall_color, rect)
                    
# ======================
# LỚP PACMANGAME (GAME CHÍNH)
# ======================
class PacManGame:
    def __init__(self, filename='map.txt', tile_size=20):
        pygame.init()
        self.tile_size = tile_size
        self.maze = Maze(filename, tile_size)
        
        self.screen_width = self.maze.cols * self.tile_size
        self.screen_height = self.maze.rows * self.tile_size
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Pac-Man AI Agent (Approach 1)")
        
        self.clock = pygame.time.Clock()
        self.fps = 60
        
        self.background_color = (36, 32, 70)
        self.pacman_color = (255, 220, 0)
        self.ghost_colors = {'G': (255, 100, 100), 'E': (100, 200, 255)}

        self.pacman_pos = self.maze.pacman_start_pos
        self.ghost_positions = self.maze.ghost_start_positions
        self.food_positions = self.maze.food_positions.copy()
        self.power_pellet_positions = self.maze.power_pellet_positions.copy()
        self.score = 0
        self.total_steps_taken = 0 # <<< KHỞI TẠO BIẾN ĐẾM
        
        # --- TÍCH HỢP AGENT (Cách 1) ---
        print("🤖 Bắt đầu giải bài toán (Cách 1)... Việc này có thể mất rất nhiều thời gian!")
        start_time = time.time()
        
        problem = Problem(self.maze)
        agent = Agent(problem)
        self.moves = agent.solve() # <<< GỌI HÀM GIẢI "LỚN"
        
        end_time = time.time()
        
        if self.moves:
            print(f"✅ Đã tìm thấy lời giải TỐI ƯU với {len(self.moves)} bước!")
            print(f"   (Thời gian giải: {end_time - start_time:.4f} giây)")
        else:
            print("❌ Không tìm thấy lời giải!")
            
        self.move_index = 0
        self.move_timer = 0
        self.move_delay = 100
        
        self.game_over = False
        self.game_over_message_shown = False

    def run(self):
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                    running = False

            if not self.game_over:
                self.update()
            elif not self.game_over_message_shown:
                # <<< IN TỔNG SỐ BƯỚC ĐI KHI KẾT THÚC >>>
                print("🎉 Pac-Man đã ăn hết thức ăn!")
                print(f"🏆 Tổng số bước đã đi (Cách 1): {self.total_steps_taken}")
                self.game_over_message_shown = True
            
            self.draw()

        pygame.quit()

    def update(self):
        """ 
        Cập nhật trạng thái của game.
        Cách 1: Chỉ cần đi theo danh sách 'self.moves' đã được tính toán trước.
        """
        self.move_timer += 1
        if self.move_timer < self.move_delay:
            return
            
        self.move_timer = 0
        
        if self.move_index < len(self.moves):
            action = self.moves[self.move_index]
            self.total_steps_taken += 1 # <<< TĂNG BIẾN ĐẾM
            
            x, y = self.pacman_pos
            if action == 'North': self.pacman_pos = (x, y - 1)
            elif action == 'South': self.pacman_pos = (x, y + 1)
            elif action == 'East':  self.pacman_pos = (x + 1, y)
            elif action == 'West':  self.pacman_pos = (x - 1, y)
            
            # Ăn thức ăn (nếu có)
            if self.pacman_pos in self.food_positions:
                self.food_positions.remove(self.pacman_pos)
                self.score += 10
            
            if self.pacman_pos in self.power_pellet_positions:
                self.power_pellet_positions.remove(self.pacman_pos)
                self.score += 50
                
            self.move_index += 1
        else:
            if not self.food_positions and not self.power_pellet_positions:
                self.game_over = True

    def draw(self):
        self.screen.fill(self.background_color)
        self.maze.draw_walls(self.screen)
        self.draw_collectibles()
        self.draw_pacman()
        pygame.display.flip()

    def draw_collectibles(self):
        for pos in self.food_positions:
            center = (pos[0] * self.tile_size + self.tile_size // 2, pos[1] * self.tile_size + self.tile_size // 2)
            pygame.draw.circle(self.screen, self.maze.food_color, center, self.tile_size // 5)
        
        for pos in self.power_pellet_positions:
            center = (pos[0] * self.tile_size + self.tile_size // 2, pos[1] * self.tile_size + self.tile_size // 2)
            pygame.draw.circle(self.screen, self.maze.power_pellet_color, center, self.tile_size // 3)
            pygame.draw.circle(self.screen, self.maze.food_color, center, self.tile_size // 4)

    def draw_pacman(self):
        if self.pacman_pos:
            x, y = self.pacman_pos
            center = (x * self.tile_size + self.tile_size // 2, y * self.tile_size + self.tile_size // 2)
            pygame.draw.circle(self.screen, self.pacman_color, center, self.tile_size // 2 - 2)
            eye_pos = (center[0] + self.tile_size // 6, center[1] - self.tile_size // 6)
            pygame.draw.circle(self.screen, (0, 0, 0), eye_pos, self.tile_size // 8)

if __name__ == "__main__":
    game = PacManGame(filename='map.txt')
    game.run()