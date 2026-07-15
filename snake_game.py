import pygame
import random
import json
import os
import math

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Get display info for true fullscreen
display_info = pygame.display.Info()
SCREEN_WIDTH = display_info.current_w
SCREEN_HEIGHT = display_info.current_h

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
DARK_GREEN = (0, 200, 0)
RED = (255, 0, 0)
DARK_RED = (200, 0, 0)
BLUE = (0, 100, 255)
DARK_BLUE = (0, 70, 200)
NEON_GREEN = (57, 255, 20)
NEON_PINK = (255, 20, 147)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
BROWN = (139, 69, 19)
DARK_BROWN = (101, 67, 33)
WALL_COLOR = (100, 50, 20)
PANEL_BG = (25, 25, 35)
PANEL_BORDER = (100, 100, 150)
BOX_BG = (35, 35, 50)
BOX_BORDER = (0, 200, 100)

# Calculate cell size and panel width
PANEL_WIDTH = 330
GAME_WIDTH = SCREEN_WIDTH - PANEL_WIDTH
CELL_SIZE = max(20, min(35, GAME_WIDTH // 40))
GRID_WIDTH = GAME_WIDTH // CELL_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // CELL_SIZE

# Wall thickness (in cells)
WALL_THICKNESS = 2

def create_beep_sound(frequency, duration, volume=0.5):
    sample_rate = 44100
    frames = int(duration * sample_rate)
    arr = []
    for i in range(frames):
        t = float(i) / sample_rate
        value = int(32767.0 * volume * math.sin(2.0 * math.pi * frequency * t))
        arr.append([value, value])
    
    sound = pygame.sndarray.make_sound(arr)
    return sound

try:
    EAT_SOUND = create_beep_sound(880, 0.1, 0.3)
    LEVEL_UP_SOUND = create_beep_sound(440, 0.3, 0.4)
    GAME_OVER_SOUND = create_beep_sound(220, 0.5, 0.5)
except:
    EAT_SOUND = LEVEL_UP_SOUND = GAME_OVER_SOUND = None

def play_sound(sound):
    if sound:
        sound.play()

class WallHurdle:
    def __init__(self, x, y, length, direction):
        self.x = x
        self.y = y
        self.length = length
        self.direction = direction
        self.pulse = 0
        self.pulse_direction = 1
        self.cells = self.get_cells()
    
    def get_cells(self):
        cells = []
        if self.direction == 'horizontal':
            for i in range(self.length):
                cells.append((self.x + i, self.y))
        else:
            for i in range(self.length):
                cells.append((self.x, self.y + i))
        return cells
    
    def update(self):
        self.pulse += 0.03 * self.pulse_direction
        if self.pulse >= 1:
            self.pulse = 1
            self.pulse_direction = -1
        elif self.pulse <= 0:
            self.pulse = 0
            self.pulse_direction = 1
    
    def draw(self, screen, cell_size):
        intensity = int(100 + self.pulse * 40)
        color = (intensity, intensity - 40, intensity - 80)
        
        for cell in self.cells:
            x, y = cell
            pygame.draw.rect(screen, color, 
                           (x * cell_size, y * cell_size, cell_size - 1, cell_size - 1))
            pygame.draw.rect(screen, DARK_BROWN, 
                           (x * cell_size, y * cell_size, cell_size - 1, cell_size - 1), 2)
        
        if self.direction == 'horizontal':
            start_x = self.x * cell_size
            start_y = self.y * cell_size + cell_size // 2
            end_x = (self.x + self.length) * cell_size
            pygame.draw.line(screen, (60, 40, 20), (start_x, start_y), (end_x, start_y), 3)
            for i in range(self.length):
                x_pos = (self.x + i) * cell_size + cell_size // 2
                pygame.draw.line(screen, (60, 40, 20), (x_pos, start_y - 5), (x_pos, start_y + 5), 2)
        else:
            start_x = self.x * cell_size + cell_size // 2
            start_y = self.y * cell_size
            end_y = (self.y + self.length) * cell_size
            pygame.draw.line(screen, (60, 40, 20), (start_x, start_y), (start_x, end_y), 3)
            for i in range(self.length):
                y_pos = (self.y + i) * cell_size + cell_size // 2
                pygame.draw.line(screen, (60, 40, 20), (start_x - 5, y_pos), (start_x + 5, y_pos), 2)

class Snake:
    def __init__(self):
        self.body = [(GRID_WIDTH // 2, GRID_HEIGHT // 2)]
        self.direction = (1, 0)
        self.grow_flag = False
        self.color = GREEN
    
    def move(self):
        head = self.body[0]
        new_head = (head[0] + self.direction[0], head[1] + self.direction[1])
        self.body.insert(0, new_head)
        if not self.grow_flag:
            self.body.pop()
        else:
            self.grow_flag = False
    
    def grow(self):
        self.grow_flag = True
    
    def check_collision(self, wall_hurdles):
        head = self.body[0]
        if head[0] < WALL_THICKNESS or head[0] >= GRID_WIDTH - WALL_THICKNESS or head[1] < WALL_THICKNESS or head[1] >= GRID_HEIGHT - WALL_THICKNESS:
            return True
        if head in self.body[1:]:
            return True
        for hurdle in wall_hurdles:
            if head in hurdle.cells:
                return True
        return False
    
    def draw(self, screen):
        for i, segment in enumerate(self.body):
            color = self.color if i == 0 else DARK_GREEN
            pygame.draw.rect(screen, color, 
                           (segment[0] * CELL_SIZE, segment[1] * CELL_SIZE, 
                            CELL_SIZE - 2, CELL_SIZE - 2))
            if i == 0:
                eye_size = max(3, CELL_SIZE // 6)
                eye_offset = CELL_SIZE // 4
                if self.direction == (1, 0):
                    pygame.draw.circle(screen, WHITE, (segment[0] * CELL_SIZE + CELL_SIZE - eye_offset, segment[1] * CELL_SIZE + eye_offset), eye_size)
                    pygame.draw.circle(screen, WHITE, (segment[0] * CELL_SIZE + CELL_SIZE - eye_offset, segment[1] * CELL_SIZE + CELL_SIZE - eye_offset), eye_size)
                elif self.direction == (-1, 0):
                    pygame.draw.circle(screen, WHITE, (segment[0] * CELL_SIZE + eye_offset, segment[1] * CELL_SIZE + eye_offset), eye_size)
                    pygame.draw.circle(screen, WHITE, (segment[0] * CELL_SIZE + eye_offset, segment[1] * CELL_SIZE + CELL_SIZE - eye_offset), eye_size)
                elif self.direction == (0, -1):
                    pygame.draw.circle(screen, WHITE, (segment[0] * CELL_SIZE + eye_offset, segment[1] * CELL_SIZE + eye_offset), eye_size)
                    pygame.draw.circle(screen, WHITE, (segment[0] * CELL_SIZE + CELL_SIZE - eye_offset, segment[1] * CELL_SIZE + eye_offset), eye_size)
                elif self.direction == (0, 1):
                    pygame.draw.circle(screen, WHITE, (segment[0] * CELL_SIZE + eye_offset, segment[1] * CELL_SIZE + CELL_SIZE - eye_offset), eye_size)
                    pygame.draw.circle(screen, WHITE, (segment[0] * CELL_SIZE + CELL_SIZE - eye_offset, segment[1] * CELL_SIZE + CELL_SIZE - eye_offset), eye_size)

class Food:
    def __init__(self):
        self.position = (0, 0)
        self.pulse = 0
        self.pulse_direction = 1
    
    def randomize(self, snake_body, wall_hurdles):
        max_attempts = 2000
        attempts = 0
        while attempts < max_attempts:
            pos = (random.randint(WALL_THICKNESS, GRID_WIDTH - WALL_THICKNESS - 1), 
                   random.randint(WALL_THICKNESS, GRID_HEIGHT - WALL_THICKNESS - 1))
            if pos in snake_body:
                attempts += 1
                continue
            
            on_hurdle = False
            for hurdle in wall_hurdles:
                if pos in hurdle.cells:
                    on_hurdle = True
                    break
            if not on_hurdle:
                self.position = pos
                return
        
        for x in range(WALL_THICKNESS, GRID_WIDTH - WALL_THICKNESS):
            for y in range(WALL_THICKNESS, GRID_HEIGHT - WALL_THICKNESS):
                pos = (x, y)
                if pos not in snake_body:
                    on_hurdle = False
                    for hurdle in wall_hurdles:
                        if pos in hurdle.cells:
                            on_hurdle = True
                            break
                    if not on_hurdle:
                        self.position = pos
                        return
    
    def update(self):
        self.pulse += 0.1 * self.pulse_direction
        if self.pulse >= 1:
            self.pulse = 1
            self.pulse_direction = -1
        elif self.pulse <= 0:
            self.pulse = 0
            self.pulse_direction = 1
    
    def draw(self, screen):
        glow_size = int(CELL_SIZE * (0.8 + self.pulse * 0.3))
        offset = (CELL_SIZE - glow_size) // 2
        pygame.draw.rect(screen, DARK_RED,
                        (self.position[0] * CELL_SIZE + offset, self.position[1] * CELL_SIZE + offset,
                         glow_size, glow_size))
        pygame.draw.rect(screen, RED,
                        (self.position[0] * CELL_SIZE + 2, self.position[1] * CELL_SIZE + 2,
                         CELL_SIZE - 4, CELL_SIZE - 4))

class Button:
    def __init__(self, x, y, width, height, text, color, hover_color, action=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.action = action
        self.is_hovered = False
    
    def draw(self, screen, font):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(screen, color, self.rect, border_radius=10)
        pygame.draw.rect(screen, WHITE, self.rect, 2, border_radius=10)
        text_surface = font.render(self.text, True, WHITE)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.is_hovered and self.action:
                return self.action()
        return None

# Difficulty settings
DIFFICULTY = {
    "Easy": {
        "color": GREEN,
        "points": 1,
        "start_speed": 5,
        "min_speed": 1,
        "max_speed": 20,
        "level_up_foods": 10,
        "speed_increase": 1,
        "has_hurdles": False,
        "base_walls": 0,
        "wall_increase": 0
    },
    "Medium": {
        "color": YELLOW,
        "points": 2,
        "start_speed": 8,
        "min_speed": 3,
        "max_speed": 22,
        "level_up_foods": 8,
        "speed_increase": 1,
        "has_hurdles": False,
        "base_walls": 0,
        "wall_increase": 0
    },
    "Hard": {
        "color": ORANGE,
        "points": 3,
        "start_speed": 12,
        "min_speed": 5,
        "max_speed": 25,
        "level_up_foods": 6,
        "speed_increase": 2,
        "has_hurdles": True,
        "base_walls": 2,
        "wall_increase": 1
    },
    "Expert": {
        "color": RED,
        "points": 5,
        "start_speed": 15,
        "min_speed": 8,
        "max_speed": 30,
        "level_up_foods": 5,
        "speed_increase": 2,
        "has_hurdles": True,
        "base_walls": 3,
        "wall_increase": 2
    }
}

# ========== NAME INPUT FUNCTION ==========
def get_player_name(screen):
    """Get player name at game start"""
    font_large = pygame.font.Font(None, 48)
    font_medium = pygame.font.Font(None, 36)
    clock = pygame.time.Clock()
    
    name = ""
    waiting = True
    
    while waiting:
        screen.fill(BLACK)
        
        # Title
        title = font_large.render("SNAKE GAME", True, NEON_GREEN)
        title_rect = title.get_rect(center=(SCREEN_WIDTH//2, 150))
        screen.blit(title, title_rect)
        
        # Prompt
        prompt = font_medium.render("Enter Your Name:", True, YELLOW)
        prompt_rect = prompt.get_rect(center=(SCREEN_WIDTH//2, 260))
        screen.blit(prompt, prompt_rect)
        
        # Input box background
        input_box = pygame.Rect(SCREEN_WIDTH//2 - 200, 320, 400, 60)
        pygame.draw.rect(screen, BOX_BG, input_box)
        pygame.draw.rect(screen, NEON_GREEN, input_box, 3)
        
        # Name text
        display_text = name if name else " "
        name_surface = font_medium.render(display_text, True, WHITE)
        name_rect = name_surface.get_rect(center=input_box.center)
        screen.blit(name_surface, name_rect)
        
        # Instructions
        info = font_medium.render("Type your name (max 15 chars) and press ENTER", True, GRAY)
        info_rect = info.get_rect(center=(SCREEN_WIDTH//2, 420))
        screen.blit(info, info_rect)
        
        default = font_medium.render("Press ENTER without typing for PLAYER", True, GRAY)
        default_rect = default.get_rect(center=(SCREEN_WIDTH//2, 480))
        screen.blit(default, default_rect)
        
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if name.strip():
                        return name.strip()[:15]
                    else:
                        return "PLAYER"
                elif event.key == pygame.K_BACKSPACE:
                    name = name[:-1]
                else:
                    if len(name) < 15 and event.unicode.isprintable():
                        name += event.unicode
        
        clock.tick(60)

class Game:
    def __init__(self, player_name):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
        pygame.display.set_caption("Snake Game")
        
        self.player_name = player_name
        self.clock = pygame.time.Clock()
        
        self.font_title = pygame.font.Font(None, 80)
        self.font_large = pygame.font.Font(None, 52)
        self.font_medium = pygame.font.Font(None, 38)
        self.font_small = pygame.font.Font(None, 28)
        self.font_button = pygame.font.Font(None, 34)
        self.font_stats = pygame.font.Font(None, 26)
        self.font_controls = pygame.font.Font(None, 24)
        
        self.game_state = "menu"
        self.difficulty = "Medium"
        self.load_high_scores()
        
        self.create_menu_buttons()
        self.create_difficulty_buttons()
        self.reset_game()
    
    def create_menu_buttons(self):
        button_width = 300
        button_height = 60
        start_x = SCREEN_WIDTH // 2 - button_width // 2
        start_y = SCREEN_HEIGHT // 2 - 100
        
        self.menu_buttons = [
            Button(start_x, start_y, button_width, button_height, "START GAME", 
                   DARK_GREEN, NEON_GREEN, self.start_game),
            Button(start_x, start_y + 80, button_width, button_height, "DIFFICULTY", 
                   DARK_BLUE, BLUE, self.show_difficulty),
            Button(start_x, start_y + 160, button_width, button_height, "HIGH SCORES", 
                   DARK_GRAY, GRAY, self.show_high_scores),
            Button(start_x, start_y + 240, button_width, button_height, "QUIT", 
                   DARK_RED, RED, self.quit_game)
        ]
        
        self.back_button = Button(SCREEN_WIDTH - 120, SCREEN_HEIGHT - 60, 
                                   100, 40, "BACK", DARK_GRAY, GRAY, self.go_back)
    
    def create_difficulty_buttons(self):
        button_width = 200
        button_height = 55
        start_x = SCREEN_WIDTH // 2 - button_width // 2
        start_y = SCREEN_HEIGHT // 2 - 80
        
        self.diff_buttons = [
            Button(start_x, start_y, button_width, button_height, "EASY", 
                   DARK_GREEN, GREEN, lambda: self.set_difficulty("Easy")),
            Button(start_x, start_y + 65, button_width, button_height, "MEDIUM", 
                   DARK_GREEN, YELLOW, lambda: self.set_difficulty("Medium")),
            Button(start_x, start_y + 130, button_width, button_height, "HARD", 
                   DARK_GREEN, ORANGE, lambda: self.set_difficulty("Hard")),
            Button(start_x, start_y + 195, button_width, button_height, "EXPERT", 
                   DARK_GREEN, RED, lambda: self.set_difficulty("Expert")),
        ]
    
    def start_game(self):
        self.game_state = "playing"
        self.reset_game()
        return None
    
    def show_difficulty(self):
        self.game_state = "difficulty"
        return None
    
    def show_high_scores(self):
        self.game_state = "high_scores"
        return None
    
    def quit_game(self):
        return "quit"
    
    def set_difficulty(self, diff):
        self.difficulty = diff
        self.game_state = "menu"
        return None
    
    def go_back(self):
        self.game_state = "menu"
        return None
    
    def load_high_scores(self):
        self.high_scores = []
        if os.path.exists("snake_scores.json"):
            try:
                with open("snake_scores.json", "r") as f:
                    self.high_scores = json.load(f)
            except:
                self.high_scores = []
        
        while len(self.high_scores) < 5:
            self.high_scores.append({"name": "---", "score": 0, "level": 0, "difficulty": "Easy"})
    
    def save_high_scores(self):
        scores_to_save = [s for s in self.high_scores if s["score"] > 0]
        with open("snake_scores.json", "w") as f:
            json.dump(scores_to_save, f, indent=2)
    
    def add_high_score(self, score, level):
        new_entry = {
            "name": self.player_name[:15],
            "score": score,
            "level": level,
            "difficulty": self.difficulty
        }
        
        self.high_scores.append(new_entry)
        self.high_scores.sort(key=lambda x: x["score"], reverse=True)
        self.high_scores = self.high_scores[:5]
        self.save_high_scores()
    
    def generate_wall_hurdles(self):
        diff = DIFFICULTY[self.difficulty]
        walls = []
        
        if not diff["has_hurdles"]:
            return walls
        
        base_walls = diff["base_walls"]
        wall_increase = diff["wall_increase"]
        wall_count = base_walls + (self.level - 1) * wall_increase
        wall_count = min(wall_count, 8)
        
        attempts = 0
        
        while len(walls) < wall_count and attempts < 100:
            is_horizontal = random.choice([True, False])
            
            if is_horizontal:
                length = random.randint(4, min(8, GRID_WIDTH // 3))
                x = random.randint(WALL_THICKNESS, GRID_WIDTH - length - WALL_THICKNESS)
                y = random.randint(WALL_THICKNESS + 2, GRID_HEIGHT - WALL_THICKNESS - 2)
                
                new_cells = [(x + i, y) for i in range(length)]
                
                overlap = False
                for wall in walls:
                    for cell in new_cells:
                        if cell in wall.cells:
                            overlap = True
                            break
                    if overlap:
                        break
                
                start_area = [(GRID_WIDTH//2 + dx, GRID_HEIGHT//2 + dy) for dx in range(-3, 4) for dy in range(-3, 4)]
                if any(cell in start_area for cell in new_cells):
                    overlap = True
                
                if not overlap:
                    walls.append(WallHurdle(x, y, length, 'horizontal'))
            else:
                length = random.randint(4, min(8, GRID_HEIGHT // 3))
                x = random.randint(WALL_THICKNESS + 2, GRID_WIDTH - WALL_THICKNESS - 2)
                y = random.randint(WALL_THICKNESS, GRID_HEIGHT - length - WALL_THICKNESS)
                
                new_cells = [(x, y + i) for i in range(length)]
                
                overlap = False
                for wall in walls:
                    for cell in new_cells:
                        if cell in wall.cells:
                            overlap = True
                            break
                    if overlap:
                        break
                
                start_area = [(GRID_WIDTH//2 + dx, GRID_HEIGHT//2 + dy) for dx in range(-3, 4) for dy in range(-3, 4)]
                if any(cell in start_area for cell in new_cells):
                    overlap = True
                
                if not overlap:
                    walls.append(WallHurdle(x, y, length, 'vertical'))
            
            attempts += 1
        
        return walls
    
    def reset_game(self):
        diff = DIFFICULTY[self.difficulty]
        
        self.snake = Snake()
        self.food = Food()
        self.wall_hurdles = []
        self.food.randomize(self.snake.body, self.wall_hurdles)
        self.score = 0
        self.level = 1
        self.game_over = False
        self.paused = False
        self.food_eaten_count = 0
        self.score_saved = False
        
        self.speed = diff["start_speed"]
        self.min_speed = diff["min_speed"]
        self.max_speed = diff["max_speed"]
        self.points_per_food = diff["points"]
        self.level_up_foods = diff["level_up_foods"]
        self.speed_increase = diff["speed_increase"]
        self.snake.color = diff["color"]
        
        if diff["has_hurdles"]:
            self.wall_hurdles = self.generate_wall_hurdles()
            self.food.randomize(self.snake.body, self.wall_hurdles)
        
        self.frame_count = 0
    
    def update_level(self):
        old_level = self.level
        self.level = (self.food_eaten_count // self.level_up_foods) + 1
        if self.level > old_level:
            if DIFFICULTY[self.difficulty]["has_hurdles"]:
                self.wall_hurdles = self.generate_wall_hurdles()
                self.food.randomize(self.snake.body, self.wall_hurdles)
        if self.level > 1:
            self.speed = min(self.max_speed, self.speed + self.speed_increase)
    
    def increase_speed(self):
        if self.speed < self.max_speed and not self.game_over and not self.paused:
            self.speed += 1
            play_sound(EAT_SOUND)
    
    def decrease_speed(self):
        if self.speed > self.min_speed and not self.game_over and not self.paused:
            self.speed -= 1
            play_sound(EAT_SOUND)
    
    def draw_wall_borders(self):
        for x in range(GRID_WIDTH):
            for y in range(GRID_HEIGHT):
                if y < WALL_THICKNESS:
                    intensity = 100 + (y * 30)
                    color = (intensity, intensity - 50, intensity - 100)
                    pygame.draw.rect(self.screen, color, 
                                   (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE))
                elif y >= GRID_HEIGHT - WALL_THICKNESS:
                    intensity = 100 + ((GRID_HEIGHT - y - 1) * 30)
                    color = (intensity, intensity - 50, intensity - 100)
                    pygame.draw.rect(self.screen, color, 
                                   (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE))
                elif x < WALL_THICKNESS:
                    intensity = 100 + (x * 30)
                    color = (intensity, intensity - 50, intensity - 100)
                    pygame.draw.rect(self.screen, color, 
                                   (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE))
                elif x >= GRID_WIDTH - WALL_THICKNESS:
                    intensity = 100 + ((GRID_WIDTH - x - 1) * 30)
                    color = (intensity, intensity - 50, intensity - 100)
                    pygame.draw.rect(self.screen, color, 
                                   (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE))
        
        inner_x = (WALL_THICKNESS - 1) * CELL_SIZE
        inner_y = (WALL_THICKNESS - 1) * CELL_SIZE
        inner_width = (GRID_WIDTH - (WALL_THICKNESS - 1) * 2) * CELL_SIZE
        inner_height = (GRID_HEIGHT - (WALL_THICKNESS - 1) * 2) * CELL_SIZE
        pygame.draw.rect(self.screen, WHITE, (inner_x, inner_y, inner_width, inner_height), 3)
    
    def draw_grid(self):
        for x in range(WALL_THICKNESS, GRID_WIDTH - WALL_THICKNESS):
            for y in range(WALL_THICKNESS, GRID_HEIGHT - WALL_THICKNESS):
                pygame.draw.rect(self.screen, DARK_GRAY, 
                               (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE), 1)
    
    def draw_panel(self):
        panel_x = GAME_WIDTH
        panel_rect = pygame.Rect(panel_x, 0, PANEL_WIDTH, SCREEN_HEIGHT)
        pygame.draw.rect(self.screen, PANEL_BG, panel_rect)
        pygame.draw.line(self.screen, NEON_GREEN, (panel_x, 0), (panel_x, SCREEN_HEIGHT), 4)
        
        title = self.font_large.render("S N A K E", True, NEON_GREEN)
        title_rect = title.get_rect(center=(panel_x + PANEL_WIDTH//2, 50))
        self.screen.blit(title, title_rect)
        
        # Player name display
        name_text = self.font_small.render(f"Player: {self.player_name}", True, NEON_GREEN)
        name_rect = name_text.get_rect(center=(panel_x + PANEL_WIDTH//2, 85))
        self.screen.blit(name_text, name_rect)
        
        pygame.draw.line(self.screen, BOX_BORDER, (panel_x + 20, 105), (panel_x + PANEL_WIDTH - 20, 105), 2)
        
        stats_box = pygame.Rect(panel_x + 15, 115, PANEL_WIDTH - 30, 340)
        pygame.draw.rect(self.screen, BOX_BG, stats_box, border_radius=15)
        pygame.draw.rect(self.screen, NEON_GREEN, stats_box, 3, border_radius=15)
        
        stats_header = self.font_medium.render("📊 STATISTICS", True, YELLOW)
        stats_header_rect = stats_header.get_rect(center=(panel_x + PANEL_WIDTH//2, 145))
        self.screen.blit(stats_header, stats_header_rect)
        
        diff = DIFFICULTY[self.difficulty]
        y_offset = 180
        
        stats_items = [
            ("SCORE", str(self.score), WHITE, NEON_GREEN),
            ("LEVEL", str(self.level), WHITE, NEON_GREEN),
            ("DIFFICULTY", self.difficulty, WHITE, diff["color"]),
            ("POINTS PER FOOD", str(self.points_per_food), WHITE, YELLOW),
            ("CURRENT SPEED", str(self.speed), WHITE, BLUE),
            ("MIN SPEED", str(self.min_speed), WHITE, GRAY),
            ("MAX SPEED", str(self.max_speed), WHITE, GRAY),
            ("WALLS", str(len(self.wall_hurdles)), WHITE, ORANGE),
        ]
        
        for label, value, label_color, value_color in stats_items:
            label_text = self.font_stats.render(label + ":", True, label_color)
            self.screen.blit(label_text, (panel_x + 25, y_offset))
            value_text = self.font_stats.render(value, True, value_color)
            value_rect = value_text.get_rect(right=panel_x + PANEL_WIDTH - 25, centery=y_offset + 12)
            self.screen.blit(value_text, value_rect)
            y_offset += 30
        
        foods_needed = self.level_up_foods - (self.food_eaten_count % self.level_up_foods)
        next_level_text = f"NEXT LEVEL: {foods_needed} more food"
        next_level_render = self.font_stats.render(next_level_text, True, ORANGE)
        next_level_rect = next_level_render.get_rect(center=(panel_x + PANEL_WIDTH//2, y_offset + 15))
        self.screen.blit(next_level_render, next_level_rect)
        
        controls_box = pygame.Rect(panel_x + 15, 470, PANEL_WIDTH - 30, 200)
        pygame.draw.rect(self.screen, BOX_BG, controls_box, border_radius=15)
        pygame.draw.rect(self.screen, NEON_GREEN, controls_box, 3, border_radius=15)
        
        controls_header = self.font_medium.render("🎮 CONTROLS", True, YELLOW)
        controls_header_rect = controls_header.get_rect(center=(panel_x + PANEL_WIDTH//2, 500))
        self.screen.blit(controls_header, controls_header_rect)
        
        y_offset = 535
        controls_items = [
            ("↑ ↓ ← →", "Move Snake", NEON_GREEN),
            ("+ / -", "Speed Up / Down", BLUE),
            ("P", "Pause / Resume", ORANGE),
            ("R", "Restart Game", RED),
            ("ESC", "Main Menu", GRAY)
        ]
        
        for key, action, color in controls_items:
            key_text = self.font_controls.render(key, True, color)
            self.screen.blit(key_text, (panel_x + 25, y_offset))
            action_text = self.font_controls.render(action, True, WHITE)
            self.screen.blit(action_text, (panel_x + 120, y_offset))
            y_offset += 32
        
        tip_box = pygame.Rect(panel_x + 15, SCREEN_HEIGHT - 95, PANEL_WIDTH - 30, 75)
        pygame.draw.rect(self.screen, (45, 45, 60), tip_box, border_radius=10)
        pygame.draw.rect(self.screen, NEON_PINK, tip_box, 2, border_radius=10)
        
        tip_text1 = self.font_small.render("💡 TIP", True, NEON_PINK)
        tip_text1_rect = tip_text1.get_rect(center=(panel_x + PANEL_WIDTH//2, SCREEN_HEIGHT - 80))
        self.screen.blit(tip_text1, tip_text1_rect)
        
        tip_text2 = self.font_controls.render("Higher difficulty = MORE points!", True, WHITE)
        tip_text2_rect = tip_text2.get_rect(center=(panel_x + PANEL_WIDTH//2, SCREEN_HEIGHT - 50))
        self.screen.blit(tip_text2, tip_text2_rect)
    
    def draw_gradient_background(self):
        for y in range(SCREEN_HEIGHT):
            color_value = int(10 + (y / SCREEN_HEIGHT) * 50)
            pygame.draw.line(self.screen, (0, 0, color_value), (0, y), (SCREEN_WIDTH, y))
    
    def draw_menu(self):
        self.draw_gradient_background()
        
        title_text = self.font_title.render("SNAKE GAME", True, NEON_GREEN)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, 100))
        self.screen.blit(title_text, title_rect)
        
        name_display = self.font_small.render(f"Player: {self.player_name}", True, NEON_GREEN)
        name_rect = name_display.get_rect(center=(SCREEN_WIDTH//2, 170))
        self.screen.blit(name_display, name_rect)
        
        for button in self.menu_buttons:
            button.draw(self.screen, self.font_button)
        
        diff = DIFFICULTY[self.difficulty]
        diff_text = self.font_small.render(f"Current Difficulty: {self.difficulty}", True, diff["color"])
        diff_rect = diff_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 120))
        self.screen.blit(diff_text, diff_rect)
        
        controls = ["↑ ↓ ← →: Move | +: Speed Up | -: Speed Down | P: Pause | R: Restart | ESC: Quit"]
        text = self.font_small.render(controls[0], True, GRAY)
        text_rect = text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 60))
        self.screen.blit(text, text_rect)
    
    def draw_difficulty_menu(self):
        self.draw_gradient_background()
        
        title_text = self.font_large.render("SELECT DIFFICULTY", True, YELLOW)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, 100))
        self.screen.blit(title_text, title_rect)
        
        for button in self.diff_buttons:
            button.draw(self.screen, self.font_button)
        
        diff = DIFFICULTY[self.difficulty]
        current_text = self.font_small.render(f"Current: {self.difficulty}", True, diff["color"])
        current_rect = current_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 150))
        self.screen.blit(current_text, current_rect)
        
        self.back_button.draw(self.screen, self.font_small)
    
    def draw_high_scores(self):
        self.draw_gradient_background()
        
        title_text = self.font_large.render("HIGH SCORES", True, YELLOW)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, 80))
        self.screen.blit(title_text, title_rect)
        
        headers = ["#", "NAME", "SCORE", "LEVEL", "DIFFICULTY"]
        x_positions = [SCREEN_WIDTH//2 - 350, SCREEN_WIDTH//2 - 230, 
                       SCREEN_WIDTH//2 - 50, SCREEN_WIDTH//2 + 100, 
                       SCREEN_WIDTH//2 + 230]
        for i, header in enumerate(headers):
            text = self.font_small.render(header, True, NEON_GREEN)
            self.screen.blit(text, (x_positions[i], 150))
        
        y_start = 190
        for i, score in enumerate(self.high_scores):
            if score["score"] > 0:
                color = YELLOW if i == 0 else WHITE
                values = [str(i+1), score["name"][:15], str(score["score"]), 
                         str(score["level"]), score["difficulty"]]
                for j, value in enumerate(values):
                    text = self.font_small.render(value, True, color)
                    self.screen.blit(text, (x_positions[j], y_start + i * 40))
            else:
                values = [str(i+1), "---", "0", "0", "---"]
                for j, value in enumerate(values):
                    text = self.font_small.render(value, True, GRAY)
                    self.screen.blit(text, (x_positions[j], y_start + i * 40))
        
        self.back_button.draw(self.screen, self.font_small)
    
    def draw_game(self):
        game_rect = pygame.Rect(0, 0, GAME_WIDTH, SCREEN_HEIGHT)
        pygame.draw.rect(self.screen, BLACK, game_rect)
        self.draw_wall_borders()
        self.draw_grid()
        
        for wall in self.wall_hurdles:
            wall.update()
            wall.draw(self.screen, CELL_SIZE)
        
        self.snake.draw(self.screen)
        self.food.draw(self.screen)
        self.draw_panel()
        
        if self.paused:
            overlay = pygame.Surface((GAME_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(180)
            overlay.fill(BLACK)
            self.screen.blit(overlay, (0, 0))
            
            pause_text = self.font_large.render("PAUSED", True, WHITE)
            text_rect = pause_text.get_rect(center=(GAME_WIDTH//2, SCREEN_HEIGHT//2))
            self.screen.blit(pause_text, text_rect)
            sub_text = self.font_small.render("Press P to resume", True, GRAY)
            sub_rect = sub_text.get_rect(center=(GAME_WIDTH//2, SCREEN_HEIGHT//2 + 50))
            self.screen.blit(sub_text, sub_rect)
    
    def draw_game_over(self):
        overlay = pygame.Surface((GAME_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        game_over_text = self.font_large.render("GAME OVER", True, RED)
        text_rect = game_over_text.get_rect(center=(GAME_WIDTH//2, SCREEN_HEIGHT//2 - 60))
        self.screen.blit(game_over_text, text_rect)
        
        score_text = self.font_medium.render(f"Final Score: {self.score}", True, WHITE)
        score_rect = score_text.get_rect(center=(GAME_WIDTH//2, SCREEN_HEIGHT//2))
        self.screen.blit(score_text, score_rect)
        
        level_text = self.font_medium.render(f"Level Reached: {self.level}", True, NEON_GREEN)
        level_rect = level_text.get_rect(center=(GAME_WIDTH//2, SCREEN_HEIGHT//2 + 40))
        self.screen.blit(level_text, level_rect)
        
        is_high_score = False
        for hs in self.high_scores:
            if self.score > hs["score"]:
                is_high_score = True
                break
        if len(self.high_scores) < 5 and self.score > 0:
            is_high_score = True
        
        if is_high_score and self.score > 0:
            new_record_text = self.font_medium.render("NEW HIGH SCORE! Press ENTER to save", True, YELLOW)
            record_rect = new_record_text.get_rect(center=(GAME_WIDTH//2, SCREEN_HEIGHT//2 + 100))
            self.screen.blit(new_record_text, record_rect)
        
        restart_text = self.font_small.render("Press R to Restart | ESC for Menu", True, GRAY)
        restart_rect = restart_text.get_rect(center=(GAME_WIDTH//2, SCREEN_HEIGHT//2 + 160))
        self.screen.blit(restart_text, restart_rect)
    
    def handle_menu_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
            
            for button in self.menu_buttons:
                result = button.handle_event(event)
                if result == "quit":
                    return False
        
        return True
    
    def handle_difficulty_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.game_state = "menu"
            
            for button in self.diff_buttons:
                button.handle_event(event)
            self.back_button.handle_event(event)
        
        return True
    
    def handle_high_scores_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.game_state = "menu"
            
            self.back_button.handle_event(event)
        
        return True
    
    def handle_game_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.game_state = "menu"
                    self.reset_game()
                elif event.key == pygame.K_p and not self.game_over:
                    self.paused = not self.paused
                    play_sound(EAT_SOUND)
                elif event.key == pygame.K_r:
                    self.reset_game()
                elif event.key == pygame.K_RETURN and self.game_over and not self.score_saved:
                    if self.score > 0:
                        self.add_high_score(self.score, self.level)
                        self.score_saved = True
                        play_sound(LEVEL_UP_SOUND)
                elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                    self.increase_speed()
                elif event.key == pygame.K_MINUS:
                    self.decrease_speed()
                
                if not self.game_over and not self.paused:
                    if event.key == pygame.K_UP and self.snake.direction != (0, 1):
                        self.snake.direction = (0, -1)
                    elif event.key == pygame.K_DOWN and self.snake.direction != (0, -1):
                        self.snake.direction = (0, 1)
                    elif event.key == pygame.K_LEFT and self.snake.direction != (1, 0):
                        self.snake.direction = (-1, 0)
                    elif event.key == pygame.K_RIGHT and self.snake.direction != (-1, 0):
                        self.snake.direction = (1, 0)
        return True
    
    def update_game(self):
        if self.game_over or self.paused:
            return
        
        self.frame_count += 1
        if self.frame_count < 60 // self.speed:
            return
        self.frame_count = 0
        
        self.snake.move()
        
        if self.snake.check_collision(self.wall_hurdles):
            self.game_over = True
            play_sound(GAME_OVER_SOUND)
            self.score_saved = False
            return
        
        if self.snake.body[0] == self.food.position:
            self.snake.grow()
            self.score += self.points_per_food
            self.food_eaten_count += 1
            self.update_level()
            self.food.randomize(self.snake.body, self.wall_hurdles)
            play_sound(EAT_SOUND)
        
        self.food.update()
    
    def run(self):
        running = True
        while running:
            if self.game_state == "menu":
                running = self.handle_menu_input()
                self.draw_menu()
            elif self.game_state == "difficulty":
                running = self.handle_difficulty_input()
                self.draw_difficulty_menu()
            elif self.game_state == "high_scores":
                running = self.handle_high_scores_input()
                self.draw_high_scores()
            elif self.game_state == "playing":
                running = self.handle_game_input()
                self.update_game()
                self.draw_game()
                if self.game_over:
                    self.draw_game_over()
            
            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()

# ========== RUN THE GAME ==========
if __name__ == "__main__":
    # Create temporary screen for name input
    temp_screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
    player_name = get_player_name(temp_screen)
    
    # Start game with player name
    game = Game(player_name)
    game.run()