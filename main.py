"""
Python Redstone Engine - Beta 2.0
A modular 2D Redstone Logic Simulator built with Pygame.
"""

import pygame
import sys
import time
import math
import json

GRID_SIZE = 55
GRID_COLS, GRID_ROWS = 40, 30
VIEW_COLS, VIEW_ROWS = 16, 12
WIDTH, HEIGHT = VIEW_COLS * GRID_SIZE, VIEW_ROWS * GRID_SIZE

COLOR_BG = (15, 15, 20)
COLOR_GRID = (30, 30, 40)
COLOR_TEXT = (220, 220, 220)
COLOR_ACCENT = (0, 230, 200)

WIRE_COLORS = [
    (220, 40, 40),   # Kırmızı / Red
    (40, 120, 255),  # Mavi / Blue
    (40, 220, 90),   # Yeşil / Green
    (240, 200, 40)   # Sarı / Yellow
]

ALL_TOOLS = [
    {"id": 1, "tr": "Katı Blok", "en": "Solid Block"},
    {"id": 2, "tr": "Kablo", "en": "Wire"},
    {"id": 3, "tr": "Şalter", "en": "Lever"},
    {"id": 4, "tr": "Lamba", "en": "Lamp"},
    {"id": 5, "tr": "Meşale", "en": "Torch"},
    {"id": 6, "tr": "Repeater", "en": "Repeater"},
    {"id": 7, "tr": "Karşılaştırıcı", "en": "Comparator"},
    {"id": 8, "tr": "Piston", "en": "Piston"},
    {"id": 9, "tr": "Sticky P.", "en": "Sticky P."},
    {"id": 10, "tr": "Gözcü", "en": "Observer"},
    {"id": 11, "tr": "Redstone Bloğu", "en": "Redstone Block"},
    {"id": 12, "tr": "Cam", "en": "Glass"},
    {"id": 13, "tr": "Sculk Sensör", "en": "Sculk Sensor"},
    {"id": 14, "tr": "Not Bloku", "en": "Note Block"},
    {"id": 15, "tr": "Huni", "en": "Hopper"},
    {"id": 16, "tr": "AND Kapısı", "en": "AND Gate"},
    {"id": 17, "tr": "OR Kapısı", "en": "OR Gate"},
    {"id": 18, "tr": "XOR Kapısı", "en": "XOR Gate"}
]

LANG = {
    "TR": {
        "inv": "ENVANTER (Beta 2.0)",
        "page": "Sayfa",
        "hud_free": "[T] Dil [M] Mod [SPACE] Durdur [C/V] Kopyala [E] Env",
        "hud_paused": "[T] Dil [M] Mod [SPACE] Durdur [N] Adım [C/V] Kopyala",
        "quest_done": "Tebrikler! Tüm Macera Görevleri Bitti!",
        "quest_notif": "GÖREV TAMAMLANDI!",
        "quests": [
            {"title": "Görev 1", "desc": "Çalışma alanına bir Şalter yerleştir."},
            {"title": "Görev 2", "desc": "Devrene bir Redstone Kablosu ekle."},
            {"title": "Görev 3", "desc": "Sisteme bir AND Kapısı kur."},
            {"title": "Görev 4", "desc": "Bir Redstone Lambasına enerji vererek aydınlat."}
        ]
    },
    "EN": {
        "inv": "INVENTORY (Beta 2.0)",
        "page": "Page",
        "hud_free": "[T] Lang [M] Mode [SPACE] Pause [C/V] Copy [E] Inv",
        "hud_paused": "[T] Lang [M] Mode [SPACE] Pause [N] Step [C/V] Copy",
        "quest_done": "Congratulations! All Quests Completed!",
        "quest_notif": "QUEST COMPLETED!",
        "quests": [
            {"title": "Quest 1", "desc": "Place a Lever on the grid."},
            {"title": "Quest 2", "desc": "Add a Redstone Wire to your circuit."},
            {"title": "Quest 3", "desc": "Build an AND Gate in the system."},
            {"title": "Quest 4", "desc": "Power a Redstone Lamp to illuminate it."}
        ]
    }
}

class RedstoneEngine:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Python Redstone Engine - Beta 2.0")
        self.clock = pygame.time.Clock()

        self.camera_x = 0
        self.camera_y = 0
        self.camera_speed = 20

        self.grid = [[0 for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
        self.power_grid = [[0 for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
        self.piston_extended = [[False for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]

        self.switch_states = {} 
        self.repeater_ticks = {}
        self.repeater_timers = {}
        self.repeater_dirs = {}    
        self.comparator_modes = {} 
        self.comparator_dirs = {}  
        self.observer_prev_states = {}
        self.sculk_active_until = {}
        
        self.wire_colors = {} 
        self.clipboard = None 
        self.is_paused = False 

        self.current_lang = "TR" 
        self.game_mode = "SERBEST" 
        self.current_quest_idx = 0
        self.quest_msg_timer = 0

        self.undo_stack = []
        self.max_undo_steps = 15

        self.selected_tool_id = 1 
        self.game_state = "GAME"
        self.current_page = 0
        self.SLOTS_PER_PAGE = 27

        self.is_mouse_down_left = False
        self.is_mouse_down_right = False
        self.last_action_cell = None

        self.font_title = pygame.font.SysFont(None, 28)
        self.font_btn = pygame.font.SysFont(None, 20)
        self.font_sub = pygame.font.SysFont(None, 12)
        self.font_arrow = pygame.font.SysFont(None, 36)

    def check_quests(self):
        if self.game_mode == "MACERA":
            quests_list = LANG[self.current_lang]["quests"]
            if self.current_quest_idx < len(quests_list):
                if self.quests_check_logic(self.current_quest_idx):
                    self.current_quest_idx += 1
                    self.quest_msg_timer = time.time() + 3

    def quests_check_logic(self, idx):
        if idx == 0:
            return any(self.grid[r][c] == 3 for r in range(GRID_ROWS) for c in range(GRID_COLS))
        elif idx == 1:
            return any(self.grid[r][c] == 2 for r in range(GRID_ROWS) for c in range(GRID_COLS))
        elif idx == 2:
            return any(self.grid[r][c] == 16 for r in range(GRID_ROWS) for c in range(GRID_COLS))
        elif idx == 3:
            return any(self.grid[r][c] == 4 and self.power_grid[r][c] > 0 for r in range(GRID_ROWS) for c in range(GRID_COLS))
        return False

    def save_state_snapshot(self):
        snapshot = {
            "grid": [row[:] for row in self.grid],
            "switch_states": self.switch_states.copy(),
            "repeater_ticks": self.repeater_ticks.copy(),
            "comparator_modes": self.comparator_modes.copy(),
            "wire_colors": self.wire_colors.copy()
        }
        self.undo_stack.append(snapshot)
        if len(self.undo_stack) > self.max_undo_steps:
            self.undo_stack.pop(0)

    def undo(self):
        if self.undo_stack:
            snapshot = self.undo_stack.pop()
            self.grid = snapshot["grid"]
            self.switch_states = snapshot["switch_states"]
            self.repeater_ticks = snapshot["repeater_ticks"]
            self.comparator_modes = snapshot["comparator_modes"]
            self.wire_colors = snapshot["wire_colors"]
            self.power_grid = [[0 for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]

    def copy_blueprint(self, center_r, center_c):
        bp = {}
        for dr in range(-1, 2):
            for dc in range(-1, 2):
                r, c = center_r + dr, center_c + dc
                if 0 <= r < GRID_ROWS and 0 <= c < GRID_COLS:
                    cell = self.grid[r][c]
                    if cell != 0:
                        bp[(dr, dc)] = {
                            "cell": cell,
                            "switch": self.switch_states.get((r, c)),
                            "ticks": self.repeater_ticks.get((r, c)),
                            "color": self.wire_colors.get((r, c))
                        }
        self.clipboard = bp

    def paste_blueprint(self, target_r, target_c):
        if not self.clipboard: return
        self.save_state_snapshot()
        for (dr, dc), data in self.clipboard.items():
            r, c = target_r + dr, target_c + dc
            if 0 <= r < GRID_ROWS and 0 <= c < GRID_COLS:
                self.grid[r][c] = data["cell"]
                if data["switch"] is not None: self.switch_states[(r, c)] = data["switch"]
                if data["ticks"] is not None: self.repeater_ticks[(r, c)] = data["ticks"]
                if data["color"] is not None: self.wire_colors[(r, c)] = data["color"]

    def save_world(self, filename="redstone_world.json"):
        data = {
            "grid": self.grid,
            "switch_states": {f"{r},{c}": val for (r, c), val in self.switch_states.items()},
            "wire_colors": {f"{r},{c}": val for (r, c), val in self.wire_colors.items()},
            "repeater_ticks": {f"{r},{c}": val for (r, c), val in self.repeater_ticks.items()},
            "repeater_dirs": {f"{r},{c}": val for (r, c), val in self.repeater_dirs.items()},
            "comparator_modes": {f"{r},{c}": val for (r, c), val in self.comparator_modes.items()},
        }
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Kayıt hatası: {e}")

    def load_world(self, filename="redstone_world.json"):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.grid = data["grid"]
            self.switch_states = {tuple(map(int, k.split(','))): v for k, v in data["switch_states"].items()}
            self.wire_colors = {tuple(map(int, k.split(','))): v for k, v in data.get("wire_colors", {}).items()}
            self.repeater_ticks = {tuple(map(int, k.split(','))): v for k, v in data["repeater_ticks"].items()}
            self.repeater_dirs = {tuple(map(int, k.split(','))): v for k, v in data["repeater_dirs"].items()}
            self.comparator_modes = {tuple(map(int, k.split(','))): v for k, v in data["comparator_modes"].items()}
            self.power_grid = [[0 for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
        except FileNotFoundError:
            print("Kayıt dosyası bulunamadı.")

    def draw_texture(self, surface, rect, tool_id, p_level=0, is_active=False, extra_data=None):
        x, y, w, h = rect
        
        if tool_id == 1:
            pygame.draw.rect(surface, (110, 110, 115), rect)
            pygame.draw.rect(surface, (80, 80, 85), rect, 2)
            pygame.draw.rect(surface, (130, 130, 135), (x+6, y+6, 12, 10))
            pygame.draw.rect(surface, (70, 70, 75), (x+25, y+15, 18, 8))

        elif tool_id == 2:
            color_idx = extra_data.get('wire_color', 0) if extra_data else 0
            base_rgb = WIRE_COLORS[color_idx % len(WIRE_COLORS)]
            col = (min(255, base_rgb[0] // 2 + p_level * 10), base_rgb[1] // 3, base_rgb[2] // 3) if p_level > 0 else (40, 20, 20)
            pygame.draw.rect(surface, col, rect.inflate(-20, -20), border_radius=3)
            if p_level > 0:
                pygame.draw.rect(surface, base_rgb, (x+w//2-3, y+h//2-3, 6, 6))

        elif tool_id == 3:
            pygame.draw.rect(surface, (90, 90, 95), (x+10, y+35, 35, 12))
            lever_col = (50, 220, 50) if is_active else (180, 50, 50)
            if is_active:
                pygame.draw.line(surface, lever_col, (x+20, y+38), (x+38, y+12), 5)
            else:
                pygame.draw.line(surface, lever_col, (x+35, y+38), (x+15, y+12), 5)

        elif tool_id == 4:
            bg = (240, 190, 40) if p_level > 0 else (50, 35, 15)
            pygame.draw.rect(surface, bg, rect.inflate(-4, -4), border_radius=4)
            pygame.draw.rect(surface, (30, 20, 10), rect.inflate(-4, -4), 3, border_radius=4)

        elif tool_id == 5:
            pygame.draw.rect(surface, (110, 80, 40), (x+w//2-3, y+22, 6, 20))
            head_col = (255, 210, 0) if p_level > 0 else (120, 30, 30)
            pygame.draw.rect(surface, head_col, (x+w//2-6, y+10, 12, 12), border_radius=2)

        elif tool_id == 6:
            pygame.draw.rect(surface, (140, 140, 145), rect.inflate(-6, -6), border_radius=4)
            ticks = extra_data.get('ticks', 1) if extra_data else 1
            pygame.draw.rect(surface, (200, 30, 30), (x+12, y+20, 6, 14))
            pygame.draw.rect(surface, (200, 30, 30), (x+18 + ticks*6, y+20, 6, 14))

        elif tool_id == 7:
            pygame.draw.rect(surface, (120, 120, 125), rect.inflate(-6, -6), border_radius=4)
            pygame.draw.circle(surface, (200, 30, 30), (x+16, y+16), 4)
            pygame.draw.circle(surface, (200, 30, 30), (x+16, y+38), 4)

        elif tool_id in (8, 9):
            pygame.draw.rect(surface, (110, 110, 115), rect.inflate(-6, -6))
            head_col = (80, 180, 80) if tool_id == 9 else (160, 110, 60)
            pygame.draw.rect(surface, head_col, (x+w-16, y+5, 12, h-10), border_radius=2)

        elif tool_id == 10:
            pygame.draw.rect(surface, (60, 65, 75), rect.inflate(-4, -4), border_radius=4)
            pygame.draw.circle(surface, (40, 120, 220), (x+15, y+h//2), 7)

        elif tool_id == 11:
            pygame.draw.rect(surface, (180, 20, 20), rect.inflate(-4, -4))
            pygame.draw.rect(surface, (220, 60, 60), (x+8, y+8, 12, 12))

        elif tool_id == 12:
            pygame.draw.rect(surface, (160, 220, 240), rect.inflate(-4, -4), width=2)

        elif tool_id == 13:
            pygame.draw.rect(surface, (10, 50, 60), rect.inflate(-4, -4), border_radius=6)
            col = (0, 240, 200) if is_active else (0, 100, 110)
            pygame.draw.line(surface, col, (x+18, y+18), (x+12, y+8), 3)
            pygame.draw.line(surface, col, (x+36, y+18), (x+42, y+8), 3)

        elif tool_id == 14:
            pygame.draw.rect(surface, (120, 85, 50), rect.inflate(-4, -4), border_radius=4)
            pygame.draw.circle(surface, (60, 40, 20), (x + w//2, y + h//2), 10)
            if p_level > 0:
                pygame.draw.circle(surface, (255, 255, 100), (x + w//2, y + h//2), 4)

        elif tool_id == 15:
            pygame.draw.rect(surface, (80, 80, 90), rect.inflate(-4, -4), border_radius=4)
            pygame.draw.rect(surface, (50, 50, 60), (x + 18, y + 18, 18, 18))

        elif tool_id in (16, 17, 18):
            pygame.draw.rect(surface, (70, 70, 90), rect.inflate(-4, -4), border_radius=6)
            gate_label = "AND" if tool_id == 16 else ("OR" if tool_id == 17 else "XOR")
            col = (0, 230, 200) if p_level > 0 else (150, 150, 170)
            txt = self.font_sub.render(gate_label, True, col)
            surface.blit(txt, txt.get_rect(center=(x + w//2, y + h//2)))

    def trigger_vibration(self, source_r, source_c):
        current_time = time.time()
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                if self.grid[r][c] == 13:
                    dist = math.sqrt((r - source_r)**2 + (c - source_c)**2)
                    if dist <= 3.5:
                        self.sculk_active_until[(r, c)] = current_time + 1.2

    def handle_pistons(self, new_power):
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                cell_type = self.grid[r][c]
                if cell_type in (8, 9):
                    left_p = new_power[r][c-1] if c-1 >= 0 else 0
                    is_powered = (left_p > 0)
                    was_extended = self.piston_extended[r][c]

                    if is_powered and not was_extended:
                        self.trigger_vibration(r, c)
                        if c + 1 < GRID_COLS:
                            target_cell = self.grid[r][c+1]
                            if target_cell != 0 and (c + 2 < GRID_COLS and self.grid[r][c+2] == 0):
                                self.grid[r][c+2] = target_cell
                                self.grid[r][c+1] = 0
                                if (r, c+1) in self.switch_states:
                                    self.switch_states[(r, c+2)] = self.switch_states.pop((r, c+1))
                                if (r, c+1) in self.wire_colors:
                                    self.wire_colors[(r, c+2)] = self.wire_colors.pop((r, c+1))
                        self.piston_extended[r][c] = True

                    elif not is_powered and was_extended:
                        self.trigger_vibration(r, c)
                        if cell_type == 9:
                            if c + 2 < GRID_COLS:
                                target_cell = self.grid[r][c+2]
                                if target_cell != 0 and self.grid[r][c+1] == 0:
                                    self.grid[r][c+1] = target_cell
                                    self.grid[r][c+2] = 0
                                    if (r, c+2) in self.switch_states:
                                        self.switch_states[(r, c+1)] = self.switch_states.pop((r, c+2))
                                    if (r, c+2) in self.wire_colors:
                                        self.wire_colors[(r, c+1)] = self.wire_colors.pop((r, c+2))
                        self.piston_extended[r][c] = False

    def update_signals(self):
        new_power = [[0 for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
        current_time = time.time()
        
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                cell = self.grid[r][c]
                if cell == 11: new_power[r][c] = 15 
                elif cell == 3 and self.switch_states.get((r, c), False): new_power[r][c] = 15 
                elif cell == 13 and current_time < self.sculk_active_until.get((r, c), 0): new_power[r][c] = 15
                elif cell == 14:
                    max_source_p = 0
                    for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < GRID_ROWS and 0 <= nc < GRID_COLS:
                            max_source_p = max(max_source_p, new_power[nr][nc])
                    if max_source_p > 0: new_power[r][c] = max_source_p

        changed = True
        while changed:
            changed = False
            for r in range(GRID_ROWS):
                for c in range(GRID_COLS):
                    cell_type = self.grid[r][c]
                    if cell_type == 12:
                        bottom_p = new_power[r+1][c] if r+1 < GRID_ROWS else 0
                        if bottom_p > new_power[r][c]: new_power[r][c] = bottom_p; changed = True
                    elif cell_type in (2, 13, 15):
                        max_neighbor_p = 0
                        for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < GRID_ROWS and 0 <= nc < GRID_COLS:
                                if self.grid[nr][nc] == 1: continue
                                if self.grid[nr][nc] == 12 and not (dr == 1 and dc == 0): continue
                                max_neighbor_p = max(max_neighbor_p, new_power[nr][nc])
                        target_p = max(0, max_neighbor_p - 1)
                        if target_p > new_power[r][c]: new_power[r][c] = target_p; changed = True
                    elif cell_type in (4, 14):
                        max_source_p = 0
                        for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < GRID_ROWS and 0 <= nc < GRID_COLS:
                                if self.grid[nr][nc] not in (4, 1, 14) and new_power[nr][nc] > max_source_p:
                                    max_source_p = new_power[nr][nc]
                        if max_source_p > new_power[r][c]: new_power[r][c] = max_source_p; changed = True
                    elif cell_type == 5:
                        left_p = new_power[r][c-1] if c-1 >= 0 else 0
                        if left_p == 0 and new_power[r][c] != 15: new_power[r][c] = 15; changed = True
                    elif cell_type == 6:
                        r_dir = self.repeater_dirs.get((r, c), "L2R")
                        in_p = (new_power[r][c-1] if c-1 >= 0 else 0) if r_dir == "L2R" else (new_power[r][c+1] if c+1 < GRID_COLS else 0)
                        ticks = self.repeater_ticks.get((r, c), 1)
                        delay_time = ticks * 0.12
                        if in_p > 0:
                            if (r, c) not in self.repeater_timers: self.repeater_timers[(r, c)] = current_time + delay_time
                            elif current_time >= self.repeater_timers[(r, c)]:
                                if new_power[r][c] != 15: new_power[r][c] = 15; changed = True
                        else:
                            if (r, c) in self.repeater_timers: del self.repeater_timers[(r, c)]
                            if new_power[r][c] != 0: new_power[r][c] = 0; changed = True
                    elif cell_type == 7:
                        c_dir = self.comparator_dirs.get((r, c), "L2R")
                        in_p = (new_power[r][c-1] if c-1 >= 0 else 0) if c_dir == "L2R" else (new_power[r][c+1] if c+1 < GRID_COLS else 0)
                        side_p = max(new_power[r-1][c] if r-1 >= 0 else 0, new_power[r+1][c] if r+1 < GRID_ROWS else 0)
                        is_subtract = self.comparator_modes.get((r, c), False)
                        out_p = max(0, in_p - side_p) if is_subtract else (in_p if in_p >= side_p else 0)
                        if new_power[r][c] != out_p: new_power[r][c] = out_p; changed = True
                    elif cell_type == 10:
                        left_p = new_power[r][c-1] if c-1 >= 0 else 0
                        prev = self.observer_prev_states.get((r, c), 0)
                        if left_p != prev:
                            if new_power[r][c] != 15: new_power[r][c] = 15; changed = True
                        self.observer_prev_states[(r, c)] = left_p
                    elif cell_type in (16, 17, 18):
                        in1 = new_power[r][c-1] if c-1 >= 0 else 0
                        in2 = max(new_power[r-1][c] if r-1 >= 0 else 0, new_power[r+1][c] if r+1 < GRID_ROWS else 0)
                        
                        out_p = 0
                        if cell_type == 16:
                            if in1 > 0 and in2 > 0: out_p = 15
                        elif cell_type == 17:
                            if in1 > 0 or in2 > 0: out_p = 15
                        elif cell_type == 18:
                            if (in1 > 0) != (in2 > 0): out_p = 15

                        if new_power[r][c] != out_p: new_power[r][c] = out_p; changed = True

        self.handle_pistons(new_power)
        self.power_grid = new_power
        self.check_quests()

    def clear_map(self):
        self.save_state_snapshot()
        self.grid = [[0 for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
        self.power_grid = [[0 for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
        self.switch_states.clear()
        self.repeater_ticks.clear()
        self.repeater_timers.clear()
        self.comparator_modes.clear()
        self.wire_colors.clear()

    def run(self):
        running = True
        while running:
            mouse_pos = pygame.mouse.get_pos()
            current_time = time.time()
            total_pages = math.ceil(len(ALL_TOOLS) / self.SLOTS_PER_PAGE)

            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT]: self.camera_x = max(0, self.camera_x - self.camera_speed)
            if keys[pygame.K_RIGHT]: self.camera_x = min((GRID_COLS - VIEW_COLS) * GRID_SIZE, self.camera_x + self.camera_speed)
            if keys[pygame.K_UP]: self.camera_y = max(0, self.camera_y - self.camera_speed)
            if keys[pygame.K_DOWN]: self.camera_y = min((GRID_ROWS - VIEW_ROWS) * GRID_SIZE, self.camera_y + self.camera_speed)

            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_e, pygame.K_ESCAPE):
                        self.game_state = "INVENTORY" if self.game_state == "GAME" else "GAME"
                        self.is_mouse_down_left = self.is_mouse_down_right = False
                    elif event.key == pygame.K_r: 
                        self.clear_map()
                    elif event.key == pygame.K_s: 
                        self.save_world()
                    elif event.key == pygame.K_l: 
                        self.load_world()
                    elif event.key == pygame.K_t: 
                        self.current_lang = "EN" if self.current_lang == "TR" else "TR"
                    elif event.key == pygame.K_m: 
                        self.game_mode = "MACERA" if self.game_mode == "SERBEST" else "SERBEST"
                    elif event.key == pygame.K_SPACE:  # <-- Burası düzeltildi (K_SPACE)
                        self.is_paused = not self.is_paused
                    elif event.key == pygame.K_n and self.is_paused: 
                        self.update_signals()
                    elif event.key == pygame.K_c and not (pygame.key.get_mods() & pygame.KMOD_CTRL):
                        c = (mouse_pos[0] + self.camera_x) // GRID_SIZE
                        r = (mouse_pos[1] + self.camera_y) // GRID_SIZE
                        self.copy_blueprint(r, c)
                    elif event.key == pygame.K_v and not (pygame.key.get_mods() & pygame.KMOD_CTRL):
                        c = (mouse_pos[0] + self.camera_x) // GRID_SIZE
                        r = (mouse_pos[1] + self.camera_y) // GRID_SIZE
                        self.paste_blueprint(r, c)
                    elif event.key == pygame.K_z and (pygame.key.get_mods() & pygame.KMOD_CTRL): 
                        self.undo()
                    elif pygame.K_1 <= event.key <= pygame.K_9:
                        idx = event.key - pygame.K_1
                        if idx < len(ALL_TOOLS): self.selected_tool_id = ALL_TOOLS[idx]["id"]

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.game_state == "GAME":
                        mx, my = event.pos
                        c = (mx + self.camera_x) // GRID_SIZE
                        r = (my + self.camera_y) // GRID_SIZE
                        if 0 <= r < GRID_ROWS and 0 <= c < GRID_COLS:
                            if event.button == 1: self.is_mouse_down_left = True
                            elif event.button == 3: 
                                self.is_mouse_down_right = True
                                cell = self.grid[r][c]
                                if cell == 2: 
                                    cur_col = self.wire_colors.get((r, c), 0)
                                    self.wire_colors[(r, c)] = (cur_col + 1) % len(WIRE_COLORS)
                                elif cell == 3: self.switch_states[(r, c)] = not self.switch_states.get((r, c), False)
                                elif cell == 6: self.repeater_ticks[(r, c)] = (self.repeater_ticks.get((r, c), 1) % 4) + 1
                                elif cell == 7: self.comparator_modes[(r, c)] = not self.comparator_modes.get((r, c), False)
                            elif event.button == 2 and self.grid[r][c] != 0: 
                                self.selected_tool_id = self.grid[r][c]

                    elif self.game_state == "INVENTORY" and event.button == 1:
                        mx, my = event.pos
                        inv_w, inv_h = 600, 320
                        inv_x, inv_y = WIDTH // 2 - inv_w // 2, HEIGHT // 2 - inv_h // 2
                        
                        btn_prev = pygame.Rect(inv_x + 20, inv_y + inv_h - 45, 40, 30)
                        btn_next = pygame.Rect(inv_x + inv_w - 60, inv_y + inv_h - 45, 40, 30)

                        if btn_prev.collidepoint(mx, my) and self.current_page > 0: self.current_page -= 1
                        elif btn_next.collidepoint(mx, my) and self.current_page < total_pages - 1: self.current_page += 1

                        start_idx = self.current_page * self.SLOTS_PER_PAGE
                        page_tools = ALL_TOOLS[start_idx : start_idx + self.SLOTS_PER_PAGE]

                        for idx, tool in enumerate(page_tools):
                            slot_x = inv_x + 25 + (idx % 9) * 62
                            slot_y = inv_y + 55 + (idx // 9) * 62
                            if pygame.Rect(slot_x, slot_y, 56, 56).collidepoint(mx, my):
                                self.selected_tool_id = tool["id"]
                                self.game_state = "GAME"
                                break

                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1: self.is_mouse_down_left = False
                    elif event.button == 3: self.is_mouse_down_right = False
                    self.last_action_cell = None

            if self.game_state == "GAME":
                mx, my = mouse_pos
                c = (mx + self.camera_x) // GRID_SIZE
                r = (my + self.camera_y) // GRID_SIZE
                if 0 <= r < GRID_ROWS and 0 <= c < GRID_COLS and (r, c) != self.last_action_cell:
                    if self.is_mouse_down_left and self.grid[r][c] != 0:
                        self.save_state_snapshot()
                        self.grid[r][c] = 0
                        if (r, c) in self.wire_colors: del self.wire_colors[(r, c)]
                        self.trigger_vibration(r, c)
                        self.last_action_cell = (r, c)
                    elif self.is_mouse_down_right and self.grid[r][c] == 0:
                        self.save_state_snapshot()
                        self.grid[r][c] = self.selected_tool_id
                        if self.selected_tool_id == 3: self.switch_states[(r, c)] = False
                        if self.selected_tool_id == 6: self.repeater_ticks[(r, c)] = 1; self.repeater_dirs[(r, c)] = "L2R"
                        if self.selected_tool_id == 7: self.comparator_modes[(r, c)] = False; self.comparator_dirs[(r, c)] = "L2R"
                        self.trigger_vibration(r, c)
                        self.last_action_cell = (r, c)
                
                if not self.is_paused:
                    self.update_signals()

            self.screen.fill(COLOR_BG)

            for r in range(GRID_ROWS):
                for c in range(GRID_COLS):
                    screen_x = c * GRID_SIZE - self.camera_x
                    screen_y = r * GRID_SIZE - self.camera_y
                    
                    if -GRID_SIZE <= screen_x <= WIDTH and -GRID_SIZE <= screen_y <= HEIGHT:
                        rect = pygame.Rect(screen_x, screen_y, GRID_SIZE, GRID_SIZE)
                        pygame.draw.rect(self.screen, COLOR_GRID, rect, 1)
                        cell = self.grid[r][c]
                        if cell != 0:
                            p_level = self.power_grid[r][c]
                            is_act = self.switch_states.get((r, c), False) or self.comparator_modes.get((r, c), False) or (current_time < self.sculk_active_until.get((r, c), 0))
                            extra = {
                                'ticks': self.repeater_ticks.get((r, c), 1),
                                'wire_color': self.wire_colors.get((r, c), 0)
                            }
                            self.draw_texture(self.screen, rect, cell, p_level, is_act, extra)

            if self.game_state == "GAME":
                mx, my = mouse_pos
                c = (mx + self.camera_x) // GRID_SIZE
                r = (my + self.camera_y) // GRID_SIZE
                if 0 <= r < GRID_ROWS and 0 <= c < GRID_COLS and self.grid[r][c] == 0:
                    screen_x = c * GRID_SIZE - self.camera_x
                    screen_y = r * GRID_SIZE - self.camera_y
                    if -GRID_SIZE <= screen_x <= WIDTH and -GRID_SIZE <= screen_y <= HEIGHT:
                        pygame.draw.rect(self.screen, COLOR_ACCENT, (screen_x + 4, screen_y + 4, GRID_SIZE - 8, GRID_SIZE - 8), 2)

            curr_tool = next(t for t in ALL_TOOLS if t["id"] == self.selected_tool_id)
            tool_name = curr_tool[self.current_lang.lower()]
            pygame.draw.rect(self.screen, (20, 20, 30), (10, 10, 540, 35), border_radius=6)
            self.draw_texture(self.screen, pygame.Rect(15, 13, 28, 28), self.selected_tool_id)
            txt_hud = self.font_btn.render(f"{tool_name} [{self.game_mode}|{self.current_lang}]", True, COLOR_TEXT)
            self.screen.blit(txt_hud, (50, 20))
            
            status_text = LANG[self.current_lang]["hud_paused"] if self.is_paused else LANG[self.current_lang]["hud_free"]
            self.screen.blit(self.font_sub.render(status_text, True, (150, 150, 180)), (230, 22))

            if self.game_mode == "MACERA":
                pygame.draw.rect(self.screen, (25, 25, 35), (10, 55, 380, 55), border_radius=6)
                pygame.draw.rect(self.screen, COLOR_ACCENT, (10, 55, 380, 55), 1, border_radius=6)
                
                quests_list = LANG[self.current_lang]["quests"]
                if self.current_quest_idx < len(quests_list):
                    q = quests_list[self.current_quest_idx]
                    q_title = self.font_btn.render(f"{q['title']}: {q['desc']}", True, COLOR_ACCENT)
                    self.screen.blit(q_title, (20, 63))
                    q_prog = self.font_sub.render(f"Progress: {self.current_quest_idx}/{len(quests_list)}" if self.current_lang == "EN" else f"İlerleme: {self.current_quest_idx}/{len(quests_list)}", True, (180, 180, 200))
                    self.screen.blit(q_prog, (20, 85))
                else:
                    q_done = self.font_btn.render(LANG[self.current_lang]["quest_done"], True, (50, 240, 100))
                    self.screen.blit(q_done, (20, 72))

                if current_time < self.quest_msg_timer:
                    notif = self.font_title.render(LANG[self.current_lang]["quest_notif"], True, (255, 220, 50))
                    self.screen.blit(notif, (WIDTH // 2 - 120, 60))

            if self.game_state == "GAME":
                mx, my = mouse_pos
                c = (mx + self.camera_x) // GRID_SIZE
                r = (my + self.camera_y) // GRID_SIZE
                if 0 <= r < GRID_ROWS and 0 <= c < GRID_COLS:
                    p_val = self.power_grid[r][c]
                    tooltip_surf = self.font_sub.render(f"Power: {p_val} | ({c},{r})", True, (200, 200, 100))
                    self.screen.blit(tooltip_surf, (mx + 10, my - 15))

            if self.game_state == "INVENTORY":
                overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 180))
                self.screen.blit(overlay, (0, 0))

                inv_w, inv_h = 600, 320
                inv_x, inv_y = WIDTH // 2 - inv_w // 2, HEIGHT // 2 - inv_h // 2
                
                pygame.draw.rect(self.screen, (30, 30, 45), (inv_x, inv_y, inv_w, inv_h), border_radius=12)
                pygame.draw.rect(self.screen, COLOR_ACCENT, (inv_x, inv_y, inv_w, inv_h), 2, border_radius=12)
                
                self.screen.blit(self.font_title.render(LANG[self.current_lang]["inv"], True, COLOR_ACCENT), (inv_x + 20, inv_y + 15))
                page_text = f"{LANG[self.current_lang]['page']} {self.current_page + 1}/{max(1, total_pages)}"
                self.screen.blit(self.font_btn.render(page_text, True, COLOR_TEXT), (inv_x + inv_w - 110, inv_y + 20))

                start_idx = self.current_page * self.SLOTS_PER_PAGE
                page_tools = ALL_TOOLS[start_idx : start_idx + self.SLOTS_PER_PAGE]

                for slot_i in range(self.SLOTS_PER_PAGE):
                    slot_x = inv_x + 25 + (slot_i % 9) * 62
                    slot_y = inv_y + 55 + (slot_i // 9) * 62
                    slot_rect = pygame.Rect(slot_x, slot_y, 56, 56)

                    if slot_i < len(page_tools):
                        tool = page_tools[slot_i]
                        is_sel = (tool["id"] == self.selected_tool_id)
                        pygame.draw.rect(self.screen, (0, 90, 90) if is_sel else (40, 40, 55), slot_rect, border_radius=6)
                        pygame.draw.rect(self.screen, COLOR_ACCENT if is_sel else (70, 70, 90), slot_rect, 2, border_radius=6)

                        self.draw_texture(self.screen, pygame.Rect(slot_x + 12, slot_y + 6, 32, 32), tool["id"])
                        t_name = tool[self.current_lang.lower()]
                        txt_name = self.font_sub.render(t_name, True, COLOR_TEXT)
                        self.screen.blit(txt_name, txt_name.get_rect(center=(slot_rect.centerx, slot_rect.bottom - 8)))
                    else:
                        pygame.draw.rect(self.screen, (20, 20, 30), slot_rect, border_radius=6)
                        pygame.draw.rect(self.screen, (40, 40, 50), slot_rect, 1, border_radius=6)

                btn_prev = pygame.Rect(inv_x + 20, inv_y + inv_h - 45, 40, 30)
                btn_next = pygame.Rect(inv_x + inv_w - 60, inv_y + inv_h - 45, 40, 30)

                for btn, is_active, char in [(btn_prev, self.current_page > 0, "<"), (btn_next, self.current_page < total_pages - 1, ">")]:
                    col = COLOR_ACCENT if is_active else (60, 60, 70)
                    pygame.draw.rect(self.screen, (40, 40, 55), btn, border_radius=6)
                    pygame.draw.rect(self.screen, col, btn, 2, border_radius=6)
                    txt = self.font_arrow.render(char, True, col)
                    self.screen.blit(txt, txt.get_rect(center=btn.center))

            pygame.display.flip()
            self.clock.tick(30)

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    engine = RedstoneEngine()
    engine.run()
