import heapq
import pygame
import time
import os

class Problem:
    def __init__(self, layout_file):
        self.load_maze(layout_file)

    def load_maze(self, layout_file):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(current_dir, layout_file)
        with open(full_path, 'r') as f:
            self.maze = [list(line.strip()) for line in f]
        self.height = len(self.maze)
        self.width = len(self.maze[0])
        self.food = set()
        self.pies = set()
        self.corners = {
            (1, 1): (self.width - 2, self.height - 2),
            (1, self.height - 2): (self.width - 2, 1),
            (self.width - 2, 1): (1, self.height - 2),
            (self.width - 2, self.height - 2): (1, 1)
        }
        for y in range(self.height):
            for x in range(self.width):
                if self.maze[y][x] == 'P':
                    self.start = (x, y)
                elif self.maze[y][x] == '.':
                    self.food.add((x, y))
                elif self.maze[y][x] == 'O':
                    self.pies.add((x, y))

    def test_goal(self, state):
        _, _, food, _ = state
        return len(food) == 0

    def getSuccessors(self, state):
        return self.get_successors(state)

    def heuristic(self, state):
        _, _, food, _ = state
        return len(food)

    def get_successors(self, state):
        x, y, food, magic_steps = state
        successors = []
        directions = {'North': (0, -1), 'South': (0, 1), 'East': (1, 0), 'West': (-1, 0)}
        if (x, y) in self.corners:
            tx, ty = self.corners[(x, y)]
            successors.append(((tx, ty, food, magic_steps), "Teleport", 0))
        for action, (dx, dy) in directions.items():
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.width and 0 <= ny < self.height:
                if self.maze[ny][nx] == '%' and magic_steps == 0:
                    continue
                new_food = food - {(nx, ny)} if (nx, ny) in food else food
                new_magic_steps = 4 if (nx, ny) in self.pies else max(0, magic_steps - 1)
                successors.append(((nx, ny, new_food, new_magic_steps), action, 1))
        return successors

    def a_star_search(self, visualize_tree=False):
        start_state = (self.start[0], self.start[1], frozenset(self.food), 0)
        pq = [(self.heuristic(start_state), 0, start_state, [])]
        visited = set()
        explored_nodes = []
        while pq:
            _, cost, state, path = heapq.heappop(pq)
            if state in visited:
                continue
            visited.add(state)
            explored_nodes.append(state)
            if self.test_goal(state):
                if visualize_tree:
                    return path, cost, explored_nodes
                return path, cost
            for successor, action, step_cost in self.getSuccessors(state):
                new_cost = cost + step_cost
                heapq.heappush(pq, (new_cost + self.heuristic(successor), new_cost, successor, path + [action]))
        if visualize_tree:
            return None, float('inf'), explored_nodes
        return None, float('inf')

class PacmanGame:
    def __init__(self, problem):
        self.problem = problem
        self.moves = []

    def run(self, visualize_tree=False):
        if visualize_tree:
            path, cost, explored_nodes = self.problem.a_star_search(visualize_tree=True)
            self.moves = path
            print("Path:", path)
            print("Total cost:", cost)
            print(f"Explored nodes: {len(explored_nodes)}")
            self.visualize(explored_nodes=explored_nodes)
        else:
            path, cost = self.problem.a_star_search()
            self.moves = path
            print("Path:", path)
            print("Total cost:", cost)
            self.visualize()

    def visualize(self, explored_nodes=None):
        pygame.init()
        cell_size = 30
        screen = pygame.display.set_mode((self.problem.width * cell_size, self.problem.height * cell_size))
        colors = {'%': (0, 0, 139), ' ': (255, 255, 255), 'P': (255, 255, 0), '.': (255, 0, 0), 'O': (255, 165, 0)}
        font = pygame.font.Font(None, 24)
        start_text = font.render("Press any key or click to start", True, (255, 255, 255))
        pacman_x, pacman_y = self.problem.start
        path_positions = [self.problem.start]
        current_food = self.problem.food.copy()
        current_pies = self.problem.pies.copy()
        waiting_for_start = True
        while waiting_for_start:
            screen.fill((0, 0, 0))
            if explored_nodes:
                for node in explored_nodes:
                    x, y, _, _ = node
                    pygame.draw.rect(screen, (200, 200, 200), (x * cell_size, y * cell_size, cell_size, cell_size))
            screen.blit(start_text, (self.problem.width * cell_size // 3, self.problem.height * cell_size // 2))
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
                if event.type == pygame.MOUSEBUTTONDOWN:
                    waiting_for_start = False
                if event.type == pygame.KEYDOWN:
                    waiting_for_start = False
        for move in self.moves:
            time.sleep(0.3)
            dx, dy = {'North': (0, -1), 'South': (0, 1), 'East': (1, 0), 'West': (-1, 0), "Teleport": (0, 0)}[move]
            if move == "Teleport":
                pacman_x, pacman_y = self.problem.corners[(pacman_x, pacman_y)]
            else:
                pacman_x += dx
                pacman_y += dy
                path_positions.append((pacman_x, pacman_y))
                if (pacman_x, pacman_y) in current_food:
                    current_food.remove((pacman_x, pacman_y))
                    self.problem.maze[pacman_y][pacman_x] = ' '
                if (pacman_x, pacman_y) in current_pies:
                    current_pies.remove((pacman_x, pacman_y))
                    self.problem.maze[pacman_y][pacman_x] = ' '
            screen.fill((0, 0, 0))
            if explored_nodes:
                for node in explored_nodes:
                    x, y, _, _ = node
                    pygame.draw.rect(screen, (200, 200, 200), (x * cell_size, y * cell_size, cell_size, cell_size))
            for y in range(self.problem.height):
                for x in range(self.problem.width):
                    pygame.draw.rect(screen, colors.get(self.problem.maze[y][x], (0, 0, 0)), (x * cell_size, y * cell_size, cell_size, cell_size))
            for px, py in path_positions:
                pygame.draw.circle(screen, (0, 255, 0), (px * cell_size + cell_size // 2, py * cell_size + cell_size // 2), 3)
            pygame.draw.circle(screen, (255, 255, 0), (pacman_x * cell_size + cell_size // 2, pacman_y * cell_size + cell_size // 2), cell_size // 2)
            pygame.display.flip()

        overlay = pygame.Surface((self.problem.width * cell_size, self.problem.height * cell_size), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        box_width, box_height = 400, 180
        box_x = (self.problem.width * cell_size - box_width) // 2
        box_y = (self.problem.height * cell_size - box_height) // 2
        pygame.draw.rect(overlay, (30, 180, 30), (box_x, box_y, box_width, box_height), border_radius=18)
        pygame.draw.rect(overlay, (255, 255, 255), (box_x, box_y, box_width, box_height), 4, border_radius=18)
        title_font = pygame.font.Font(None, 54)
        msg_font = pygame.font.Font(None, 32)
        title = title_font.render("GAME FINISHED!", True, (255, 255, 0))
        msg = msg_font.render("Pacman ate all the food", True, (255, 255, 255))
        hint = msg_font.render("Press any key or click to exit", True, (200, 255, 200))
        overlay.blit(title, (box_x + (box_width - title.get_width()) // 2, box_y + 20))
        overlay.blit(msg, (box_x + (box_width - msg.get_width()) // 2, box_y + 80))
        overlay.blit(hint, (box_x + (box_width - hint.get_width()) // 2, box_y + 120))
        screen.blit(overlay, (0, 0))
        pygame.display.flip()
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
                if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    waiting = False
        time.sleep(2)
        pygame.quit()
        return

if __name__ == "__main__":
    problem = Problem('task02_pacman_example_map.txt')
    game = PacmanGame(problem)
    game.run(visualize_tree=True)
