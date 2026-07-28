"""
Python Redstone Engine - Beta 1.0
=================================
A modular 2D Redstone Logic Simulator built with Pygame.

Features:
- Full GUI Inventory system with page-based navigation (27 slots/page).
- Dynamic Redstone logic: Repeaters, Comparators, Pistons, Observers, Sculk Sensors.
- Built-in procedural Pixel Art textures for stand-alone execution.
- Keyboard shortcuts: [E] Inventory, [R] Clear Map, [Middle Click] Pick Block.

Author: GitHub Community
License: MIT
"""

import pygame
import sys
import time
import math

# --- SİMÜLATÖR YAPILANDIRMASI ---
GRID_SIZE = 55
COLS, ROWS = 16, 12
WIDTH, HEIGHT = COLS * GRID_SIZE, ROWS * GRID_SIZE

# --- RENK PALETİ ---
COLOR_BG = (15, 15, 20)
COLOR_GRID = (30, 30, 40)
COLOR_TEXT = (220, 220, 220)
COLOR_ACCENT = (0, 230, 200)

# --- MODÜLER BLOK VERİTABANI ---
# Yeni bir blok eklemek için bu listeye bir id ve name eklemeniz yeterlidir.
ALL_TOOLS = [
    {"id": 1, "name": "Kati Blok"},
    {"id": 2, "name": "Kablo"},
    {"id": 3, "name": "Salter"},
    {"id": 4, "name": "Lamba"},
    {"id": 5, "name": "Mesale"},
    {"id": 6, "name": "Repeater"},
    {"id": 7, "name": "Karsilastirici"},
    {"id": 8, "name": "Piston"},
    {"id": 9, "name": "Sticky P."},
    {"id": 10, "name": "Observer"},
    {"id": 11, "name": "Redstone B."},
    {"id": 12, "name": "Cam"},
    {"id": 13, "name": "Sculk Sensor"}
]

class RedstoneEngine:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Python Redstone Engine - Beta 1.0 [GitHub Edition]")
        self.clock = pygame.time.Clock()

        # Izgara & Sinyal Durumları
        self.grid = [[0 for _ in range(COLS)] for _ in range(ROWS)]
        self.power_grid = [[0 for _ in range(COLS)] for _ in range(ROWS)]
        self.piston_extended = [[False for _ in range(COLS)] for _ in range(ROWS)]

        # Bileşen Durum Depoları
        self.switch_states = {} 
        self.repeater_ticks = {}
        self.repeater_timers = {}
        self.repeater_dirs = {}    
        self.comparator_modes = {} 
        self.comparator_dirs = {}  
        self.observer_prev_states = {}
        self.sculk_active_until = {}

        # Sistem Durumları
        self.selected_tool_id = 1 
        self.game_state = "GAME"
        self.current_page = 0
        self.SLOTS_PER_PAGE = 27

        # Girdi Durumları
        self.is_mouse_down_left = False
        self.is_mouse_down_right = False
        self.last_action_cell = None

        # Fontlar
        self.font_title = pygame.font.SysFont(None, 28)
        self.font_btn = pygame.font.SysFont(None, 20)
        self.font_sub = pygame.font.SysFont(None, 12)
        self.font_arrow = pygame.font.SysFont(None, 36)

    def draw_texture(self, surface, rect, tool_id, p_level=0, is_active=False, extra_data=None):
        """Tüm blokların piksellerini çizen prosedürel doku motoru."""
        x, y, w, h = rect
        
        if tool_id == 1: # Katı Taş
            pygame.draw.rect(surface, (110, 110, 115), rect)
            pygame.draw.rect(surface, (80, 80, 85), rect, 2)
            pygame.draw.rect(surface, (130, 130, 135), (x+6, y+6, 12, 10))
            pygame.draw.rect(surface, (70, 70, 75), (x+25, y+15, 18, 8))

        elif tool_id == 2: # Redstone Kablosu
            col = (min(255, 60 + p_level * 13), 15, 15) if p_level > 0 else (70, 20, 20)
            pygame.draw.rect(surface, col, rect.inflate(-20, -20), border_radius=3)
            if p_level > 0:
                pygame.draw.rect(surface, (255, 120, 120), (x+w//2-3, y+h//2-3, 6, 6))

        elif tool_id == 3: # Şalter
            pygame.draw.rect(surface, (90, 90, 95), (x+10, y+35, 35, 12))
            lever_col = (50, 220, 50) if is_active else (180, 50, 50)
            if is_active:
                pygame.draw.line(surface, lever_col, (x+20, y+38), (x+38, y+12), 5)
            else:
                pygame.draw.line(surface, lever_col, (x+35, y+38), (x+15, y+12), 5)

        elif tool_id == 4: # Redstone Lambası
            bg = (240, 190, 40) if p_level > 0 else (50, 35, 15)
            pygame.draw.rect(surface, bg, rect.inflate(-4, -4), border_radius=4)
            pygame.draw.rect(surface, (30, 20, 10), rect.inflate(-4, -4), 3, border_radius=4)

        elif tool_id == 5: # Meşale
            pygame.draw.rect(surface, (110, 80, 40), (x+w//2-3, y+22, 6, 20))
            head_col = (255, 210, 0) if p_level > 0 else (120, 30, 30)
            pygame.draw.rect(surface, head_col, (x+w//2-6, y+10, 12, 12), border_radius=2)

        elif tool_id == 6: # Repeater
            pygame.draw.rect(surface, (140, 140, 145), rect.inflate(-6, -6), border_radius=4)
            ticks = extra_data.get('ticks', 1) if extra_data else 1
            pygame.draw.rect(surface, (200, 30, 30), (x+12, y+20, 6, 14))
            pygame.draw.rect(surface, (200, 30, 30), (x+18 + ticks*6, y+20, 6, 14))

        elif tool_id == 7: # Comparator
            pygame.draw.rect(surface, (120, 120, 125), rect.inflate(-6, -6), border_radius=4)
            pygame.draw.circle(surface, (200, 30, 30), (x+16, y+16), 4)
            pygame.draw.circle(surface, (200, 30, 30), (x+16, y+38), 4)

        elif tool_id in (8, 9): # Pistonlar
            pygame.draw.rect(surface, (110, 110, 115), rect.inflate(-6, -6))
            head_col = (80, 180, 80) if tool_id == 9 else (160, 110, 60)
            pygame.draw.rect(surface, head_col, (x+w-16, y+5, 12, h-10), border_radius=2)

        elif tool_id == 10: # Observer
            pygame.draw.rect(surface, (60, 65, 75), rect.inflate(-4, -4), border_radius=4)
            pygame.draw.circle(surface, (40, 120, 220), (x+15, y+h//2), 7)

        elif tool_id == 11: # Redstone Bloğu
            pygame.draw.rect(surface, (180, 20, 20), rect.inflate(-4, -4))
            pygame.draw.rect(surface, (220, 60, 60), (x+8, y+8, 12, 12))

        elif tool_id == 12: # Cam
            pygame.draw.rect(surface, (160, 220, 240), rect.inflate(-4, -4), width=2)

        elif tool_id == 13: # Sculk Sensör
            pygame.draw.rect(surface, (10, 50, 60), rect.inflate(-4, -4), border_radius=6)
            col = (0, 240, 200) if is_active else (0, 100, 110)
            pygame.draw.line(surface, col, (x+18, y+18), (x+12, y+8), 3)
            pygame.draw.line(surface, col, (x+36, y+18), (x+42, y+8), 3)

    def trigger_vibration(self, source_r, source_c):
        """Sculk Sensörü kablosuz titreşim tetikleyicisi."""
        current_time = time.time()
        for r in range(ROWS):
            for c in range(COLS):
                if self.grid[r][c] == 13:
                    dist = math.sqrt((r - source_r)**2 + (c - source_c)**2)
                    if dist <= 3.5:
                        self.sculk_active_until[(r, c)] = current_time + 1.2

    def handle_pistons(self, new_power):
        """Piston itme ve çekme fiziği."""
        for r in range(ROWS):
            for c in range(COLS):
                cell_type = self.grid[r][c]
                if cell_type in (8, 9):
                    left_p = new_power[r][c-1] if c-1 >= 0 else 0
                    is_powered = (left_p > 0)
                    was_extended = self.piston_extended[r][c]

                    if is_powered and not was_extended:
                        self.trigger_vibration(r, c)
                        if c + 1 < COLS:
                            target_cell = self.grid[r][c+1]
                            if target_cell != 0 and (c + 2 < COLS and self.grid[r][c+2] == 0):
                                self.grid[r][c+2] = target_cell
                                self.grid[r][c+1] = 0
                                if (r, c+1) in self.switch_states:
                                    self.switch_states[(r, c+2)] = self.switch_states.pop((r, c+1))
                        self.piston_extended[r][c] = True

                    elif not is_powered and was_extended:
                        self.trigger_vibration(r, c)
                        if cell_type == 9:
                            if c + 2 < COLS:
                                target_cell = self.grid[r][c+2]
                                if target_cell != 0 and self.grid[r][c+1] == 0:
                                    self.grid[r][c+1] = target_cell
                                    self.grid[r][c+2] = 0
                                    if (r, c+2) in self.switch_states:
                                        self.switch_states[(r, c+1)] = self.switch_states.pop((r, c+2))
                        self.piston_extended[r][c] = False

    def update_signals(self):
        """Ana Redstone Mantık Motoru."""
        new_power = [[0 for _ in range(COLS)] for _ in range(ROWS)]
        current_time = time.time()
        
        for r in range(ROWS):
            for c in range(COLS):
                cell = self.grid[r][c]
                if cell == 11: new_power[r][c] = 15 
                elif cell == 3 and self.switch_states.get((r, c), False): new_power[r][c] = 15 
                elif cell == 13 and current_time < self.sculk_active_until.get((r, c), 0): new_power[r][c] = 15

        changed = True
        while changed:
            changed = False
            for r in range(ROWS):
                for c in range(COLS):
                    cell_type = self.grid[r][c]
                    if cell_type == 12: # Cam (Dikey Sinyal)
                        bottom_p = new_power[r+1][c] if r+1 < ROWS else 0
                        if bottom_p > new_power[r][c]: new_power[r][c] = bottom_p; changed = True
                    elif cell_type in (2, 13): # Kablo ve Sculk
                        max_neighbor_p = 0
                        for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < ROWS and 0 <= nc < COLS:
                                if self.grid[nr][nc] == 1: continue
                                if self.grid[nr][nc] == 12 and not (dr == 1 and dc == 0): continue
                                max_neighbor_p = max(max_neighbor_p, new_power[nr][nc])
                        target_p = max(0, max_neighbor_p - 1)
                        if target_p > new_power[r][c]: new_power[r][c] = target_p; changed = True
                    elif cell_type == 4: # Lamba
                        max_source_p = 0
                        for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < ROWS and 0 <= nc < COLS:
                                if self.grid[nr][nc] not in (4, 1) and new_power[nr][nc] > max_source_p:
                                    max_source_p = new_power[nr][nc]
                        if max_source_p > new_power[r][c]: new_power[r][c] = max_source_p; changed = True
                    elif cell_type == 5: # Meşale (Inverter)
                        left_p = new_power[r][c-1] if c-1 >= 0 else 0
                        if left_p == 0 and new_power[r][c] != 15: new_power[r][c] = 15; changed = True
                    elif cell_type == 6: # Repeater
                        r_dir = self.repeater_dirs.get((r, c), "L2R")
                        in_p = (new_power[r][c-1] if c-1 >= 0 else 0) if r_dir == "L2R" else (new_power[r][c+1] if c+1 < COLS else 0)
                        ticks = self.repeater_ticks.get((r, c), 1)
                        delay_time = ticks * 0.12
                        if in_p > 0:
                            if (r, c) not in self.repeater_timers: self.repeater_timers[(r, c)] = current_time + delay_time
                            elif current_time >= self.repeater_timers[(r, c)]:
                                if new_power[r][c] != 15: new_power[r][c] = 15; changed = True
                        else:
                            if (r, c) in self.repeater_timers: del self.repeater_timers[(r, c)]
                            if new_power[r][c] != 0: new_power[r][c] = 0; changed = True
                    elif cell_type == 7: # Comparator
                        c_dir = self.comparator_dirs.get((r, c), "L2R")
                        in_p = (new_power[r][c-1] if c-1 >= 0 else 0) if c_dir == "L2R" else (new_power[r][c+1] if c+1 < COLS else 0)
                        side_p = max(new_power[r-1][c] if r-1 >= 0 else 0, new_power[r+1][c] if r+1 < ROWS else 0)
                        is_subtract = self.comparator_modes.get((r, c), False)
                        out_p = max(0, in_p - side_p) if is_subtract else (in_p if in_p >= side_p else 0)
                        if new_power[r][c] != out_p: new_power[r][c] = out_p; changed = True
                    elif cell_type == 10: # Observer
                        left_p = new_power[r][c-1] if c-1 >= 0 else 0
                        prev = self.observer_prev_states.get((r, c), 0)
                        if left_p != prev:
                            if new_power[r][c] != 15: new_power[r][c] = 15; changed = True
                        self.observer_prev_states[(r, c)] = left_p

        self.handle_pistons(new_power)
        self.power_grid = new_power

    def clear_map(self):
        """Haritayı ve tüm durumları sıfırlar."""
        self.grid = [[0 for _ in range(COLS)] for _ in range(ROWS)]
        self.power_grid = [[0 for _ in range(COLS)] for _ in range(ROWS)]
        self.switch_states.clear()
        self.repeater_ticks.clear()
        self.repeater_timers.clear()
        self.comparator_modes.clear()

    def run(self):
        """Oyun Döngüsü."""
        running = True
        while running:
            mouse_pos = pygame.mouse.get_pos()
            current_time = time.time()
            total_pages = math.ceil(len(ALL_TOOLS) / self.SLOTS_PER_PAGE)

            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_e, pygame.K_ESCAPE):
                        self.game_state = "INVENTORY" if self.game_state == "GAME" else "GAME"
                        self.is_mouse_down_left = self.is_mouse_down_right = False
                    elif event.key == pygame.K_r: # Clear Map
                        self.clear_map()
                    elif pygame.K_1 <= event.key <= pygame.K_9: # Hızlı Slot Seçimi
                        idx = event.key - pygame.K_1
                        if idx < len(ALL_TOOLS): self.selected_tool_id = ALL_TOOLS[idx]["id"]

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.game_state == "GAME":
                        mx, my = event.pos
                        c, r = mx // GRID_SIZE, my // GRID_SIZE
                        if 0 <= r < ROWS and 0 <= c < COLS:
                            if event.button == 1: self.is_mouse_down_left = True
                            elif event.button == 3: self.is_mouse_down_right = True
                            elif event.button == 2 and self.grid[r][c] != 0: self.selected_tool_id = self.grid[r][c]

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
                c, r = mx // GRID_SIZE, my // GRID_SIZE
                if 0 <= r < ROWS and 0 <= c < COLS and (r, c) != self.last_action_cell:
                    if self.is_mouse_down_left and self.grid[r][c] != 0:
                        self.grid[r][c] = 0; self.trigger_vibration(r, c); self.last_action_cell = (r, c)
                    elif self.is_mouse_down_right:
                        cell = self.grid[r][c]
                        if cell == 3: self.switch_states[(r, c)] = not self.switch_states.get((r, c), False)
                        elif cell == 6: self.repeater_ticks[(r, c)] = (self.repeater_ticks.get((r, c), 1) % 4) + 1
                        elif cell == 7: self.comparator_modes[(r, c)] = not self.comparator_modes.get((r, c), False)
                        elif cell == 0:
                            self.grid[r][c] = self.selected_tool_id
                            if self.selected_tool_id == 3: self.switch_states[(r, c)] = False
                            if self.selected_tool_id == 6: self.repeater_ticks[(r, c)] = 1; self.repeater_dirs[(r, c)] = "L2R"
                            if self.selected_tool_id == 7: self.comparator_modes[(r, c)] = False; self.comparator_dirs[(r, c)] = "L2R"
                        self.trigger_vibration(r, c)
                        self.last_action_cell = (r, c)
                self.update_signals()

            self.screen.fill(COLOR_BG)

            # Çizim
            for r in range(ROWS):
                for c in range(COLS):
                    rect = pygame.Rect(c * GRID_SIZE, r * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                    pygame.draw.rect(self.screen, COLOR_GRID, rect, 1)
                    cell = self.grid[r][c]
                    if cell != 0:
                        p_level = self.power_grid[r][c]
                        is_act = self.switch_states.get((r, c), False) or self.comparator_modes.get((r, c), False) or (current_time < self.sculk_active_until.get((r, c), 0))
                        extra = {'ticks': self.repeater_ticks.get((r, c), 1)}
                        self.draw_texture(self.screen, rect, cell, p_level, is_act, extra)

            if self.game_state == "GAME":
                mx, my = mouse_pos
                c, r = mx // GRID_SIZE, my // GRID_SIZE
                if 0 <= r < ROWS and 0 <= c < COLS and self.grid[r][c] == 0:
                    pygame.draw.rect(self.screen, COLOR_ACCENT, (c * GRID_SIZE + 4, r * GRID_SIZE + 4, GRID_SIZE - 8, GRID_SIZE - 8), 2)

            # HUD
            curr_tool = next(t for t in ALL_TOOLS if t["id"] == self.selected_tool_id)
            pygame.draw.rect(self.screen, (20, 20, 30), (10, 10, 260, 35), border_radius=6)
            self.draw_texture(self.screen, pygame.Rect(15, 13, 28, 28), self.selected_tool_id)
            txt_hud = self.font_btn.render(curr_tool['name'], True, COLOR_TEXT)
            self.screen.blit(txt_hud, (50, 20))
            self.screen.blit(self.font_sub.render("[E] Env  [R] Temizle", True, (150, 150, 180)), (150, 22))

            # GUI Envanter
            if self.game_state == "INVENTORY":
                overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 180))
                self.screen.blit(overlay, (0, 0))

                inv_w, inv_h = 600, 320
                inv_x, inv_y = WIDTH // 2 - inv_w // 2, HEIGHT // 2 - inv_h // 2
                
                pygame.draw.rect(self.screen, (30, 30, 45), (inv_x, inv_y, inv_w, inv_h), border_radius=12)
                pygame.draw.rect(self.screen, COLOR_ACCENT, (inv_x, inv_y, inv_w, inv_h), 2, border_radius=12)
                
                self.screen.blit(self.font_title.render("ENVANTER (27 Slot / Sayfa)", True, COLOR_ACCENT), (inv_x + 20, inv_y + 15))
                self.screen.blit(self.font_btn.render(f"Sayfa {self.current_page + 1}/{max(1, total_pages)}", True, COLOR_TEXT), (inv_x + inv_w - 110, inv_y + 20))

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
                        txt_name = self.font_sub.render(tool["name"], True, COLOR_TEXT)
                        self.screen.blit(txt_name, txt_name.get_rect(center=(slot_rect.centerx, slot_rect.bottom - 8)))
                    else:
                        pygame.draw.rect(self.screen, (20, 20, 30), slot_rect, border_radius=6)
                        pygame.draw.rect(self.screen, (40, 40, 50), slot_rect, 1, border_radius=6)

                # Oklar
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
