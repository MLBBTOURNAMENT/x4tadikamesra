import pygame
from pygame import mixer
import random
import sys
import os
import traceback
import math
import random
import asyncio
import streamlit as st

st.title("My Pygame Project")
st.write("This is a web interface for my Pygame project")

# Add more Streamlit components as needed


# Initialize Pygame and mixer
pygame.init()
mixer.init()

# Constants
WIDTH = 1200
HEIGHT = 800
FPS = 60

# Create window
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Adventure Game")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (147, 0, 211)
CYAN = (0, 255, 255)

async def main():
    global COUNT_DOWN

    # avoid this kind declaration, prefer the way above
    COUNT_DOWN = 3

    while True:
        
        await asyncio.sleep(0)  # Very important, and keep it 0

        if not COUNT_DOWN:
            return

def load_sprite_sheets(dir1, width, height, direction=False):
    path = os.path.join("assets", dir1)
    
    if '/' in dir1:
        path = os.path.join("assets", *dir1.split('/'))
    
    images = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]

    all_sprites = {}

    for image in images:
        sprite_sheet = pygame.image.load(os.path.join(path, image)).convert_alpha()
        
        sprites = []
        for i in range(sprite_sheet.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheet, (0, 0), rect)
            sprites.append(pygame.transform.scale2x(surface))

        if direction:
            all_sprites[image.replace(".png", "") + "_right"] = sprites
            all_sprites[image.replace(".png", "") + "_left"] = [
                pygame.transform.flip(sprite, True, False) for sprite in sprites
            ]
        else:
            all_sprites[image.replace(".png", "")] = sprites

    return all_sprites

class Player(pygame.sprite.Sprite):
    def __init__(self, game):
        super().__init__()
        self.game = game  # Store the game instance
        
        # Animation setup
        self.SPRITES = load_sprite_sheets("Mask Dude", 32, 32, True)
        self.animation_count = 0
        self.animation_delay = 3
        self.current_sprite = 0
        
        # Basic setup
        self.image = self.SPRITES["idle_right"][0]
        self.rect = self.image.get_rect()
        
        self.jump_sound = pygame.mixer.Sound('assets/Jump Sound Effect.mp3')
        self.walk_sound = pygame.mixer.Sound('assets/Sound Effects - Footsteps.mp3')
        self.walk_sound.set_volume(0.5)  # Adjust volume as needed
        self.walk_sound_timer = 0
        
        # Position and movement
        self.rect.centerx = WIDTH // 2
        self.rect.bottom = HEIGHT - 100
        
        # Movement attributes
        self.vel_x = 0
        self.vel_y = 0
        self.acceleration = 0.8
        self.friction = 0.85
        self.max_speed = 8
        self.jump_power = -16
        self.gravity = 0.5
        self.ground_y = HEIGHT - 100
        
        # State attributes
        self.jumping = False
        self.double_jump_available = True
        self.facing_right = True
        
        self.max_speed = 5  # Kecepatan maksimum
        self.acceleration = 0.5  # Percepatan
        
        print("Available animations:", list(self.SPRITES.keys()))

    def apply_movement(self):
        # Apply gravity
        self.vel_y += self.gravity
        
        # Apply friction
        self.vel_x *= self.friction
        
        # Limit horizontal speed
        self.vel_x = max(-self.max_speed, min(self.max_speed, self.vel_x))
        
        # Update position horizontally first
        self.rect.x += int(self.vel_x)
        self.handle_horizontal_collision()
        # Check for horizontal collisions
        blocks_hit = pygame.sprite.spritecollide(self, self.game.blocks, False)
        for block in blocks_hit:
            if self.vel_x > 0:  # Moving right
                self.rect.right = min(WIDTH, self.rect.right)
            elif self.vel_x < 0:  # Moving left
                self.rect.left = max(0, self.rect.left)
            self.vel_x = 0
    
        # Update position vertically
        self.rect.y += int(self.vel_y)
        self.handle_vertical_collision()
        
        # Check for vertical collisions
        blocks_hit = pygame.sprite.spritecollide(self, self.game.blocks, False)
        for block in blocks_hit:
            if self.vel_y > 0:  # Moving down
                self.rect.bottom = block.rect.top
                self.vel_y = 0
                self.jumping = False
                self.double_jump_available = True
            elif self.vel_y < 0:  # Moving up
                self.rect.top = block.rect.bottom
                self.vel_y = 0
    
        # Ground collision (optional, you might want to remove this if using only blocks)
        if self.rect.bottom >= self.ground_y:
            self.rect.bottom = self.ground_y
            self.vel_y = 0
            self.jumping = False
            self.double_jump_available = True
    def update_sprite(self):
        try:
            sprite_sheet = "idle"
            if self.vel_y < 0:
                if not self.double_jump_available:
                    sprite_sheet = "double_jump"
                else:
                    sprite_sheet = "jump"
            elif self.vel_y > self.gravity * 2:
                sprite_sheet = "fall"
            elif abs(self.vel_x) > 0.5:
                sprite_sheet = "run"

            sprite_sheet_name = sprite_sheet + "_right" if self.facing_right else sprite_sheet + "_left"
            
            # Check if sprite sheet exists
            if sprite_sheet_name not in self.SPRITES:
                sprite_sheet_name = "idle_right" if self.facing_right else "idle_left"
                
            sprites = self.SPRITES[sprite_sheet_name]
            
            # Make sure current_sprite stays within bounds
            if len(sprites) > 0:  # Check if sprites list is not empty
                if self.animation_count >= self.animation_delay:
                    self.current_sprite = (self.current_sprite + 1) % len(sprites)
                    self.animation_count = 0
                
                self.image = sprites[min(self.current_sprite, len(sprites) - 1)]
                self.animation_count += 1
            else:
                # Fallback to a default sprite if no sprites are available
                self.image = self.SPRITES["idle_right"][0]
                
        except Exception as e:
            print(f"Error in update_sprite: {e}")
            # Fallback to first idle sprite
            self.image = self.SPRITES["idle_right"][0]
            self.current_sprite = 0
            self.animation_count = 0

    def jump(self):
        try:
            if not self.jumping:
                self.vel_y = self.jump_power
                self.jumping = True
                self.jump_sound.play()
            elif self.double_jump_available:
                self.vel_y = self.jump_power
                self.double_jump_available = False
                print("Double jump executed")
                self.jump_sound.play()
        except Exception as e:
            print(f"Error in jump method: {e}")
            traceback.print_exc()

    def update(self):
        # Get joystick input
        joy_x, joy_y = self.game.joystick.get_value()

        # Apply horizontal movement
        if abs(joy_x) > 0.1:  # Dead zone
            self.vel_x += joy_x * self.acceleration
        else:
            self.vel_x *= 0.9  # Friction when no input

        # Limit horizontal speed
        self.vel_x = max(-self.max_speed, min(self.max_speed, self.vel_x))

        # Update facing direction
        if self.vel_x > 0:
            self.facing_right = True
        elif self.vel_x < 0:
            self.facing_right = False
            
        if abs(self.vel_x) > 0.5 and not self.jumping:
            self.walk_sound_timer += 1
            if self.walk_sound_timer >= 20:  # Adjust this value to change the frequency of the sound
                self.walk_sound.play()
                self.walk_sound_timer = 0
        else:
            self.walk_sound_timer = 0

        self.apply_gravity()
        self.apply_movement()
        self.update_sprite()
        
    def jump(self):
        try:
            if not self.jumping:
                self.vel_y = self.jump_power
                self.jumping = True
                print("First jump executed")
            elif self.double_jump_available:
                self.vel_y = self.jump_power
                self.double_jump_available = False
                print("Double jump executed")
        except Exception as e:
            print(f"Error in jump method: {e}")
            traceback.print_exc()

    def move_left(self):
        self.vel_x -= self.acceleration
        self.facing_right = False

    def move_right(self):
        self.vel_x += self.acceleration
        self.facing_right = True
        
    def apply_gravity(self):
        self.vel_y += self.gravity
        if self.vel_y > 10:  # Terminal velocity
            self.vel_y = 10
    
    def apply_movement(self):
        # Update horizontal position
        self.rect.x += int(self.vel_x)
        self.handle_horizontal_collision()
        
        # Update vertical position
        self.rect.y += int(self.vel_y)
        self.handle_vertical_collision()
    
    def handle_horizontal_collision(self):
        hits = pygame.sprite.spritecollide(self, self.game.blocks, False)
        if hits:
            if self.vel_x > 0:
                self.rect.right = hits[0].rect.left
            if self.vel_x < 0:
                self.rect.left = hits[0].rect.right
            self.vel_x = 0
    
    def handle_vertical_collision(self):
        hits = pygame.sprite.spritecollide(self, self.game.blocks, False)
        if hits:
            if self.vel_y > 0:
                self.rect.bottom = hits[0].rect.top
                self.vel_y = 0
                self.jumping = False
                self.double_jump_available = True
            if self.vel_y < 0:
                self.rect.top = hits[0].rect.bottom
                self.vel_y = 0

class NPC(pygame.sprite.Sprite):
    def __init__(self, x, y, name):
        super().__init__()
        self.SPRITES = load_sprite_sheets("Rock Head", 42, 42, True)
        self.animation_count = 0
        self.animation_delay = 5
        self.current_sprite = 0
        try:
                # Load blink animation (adjust path as needed)
            self.blink_sprites = load_sprite_sheets("Rock Head", 42, 42, False)
            self.has_blink = True
        except Exception as e:
            print(f"Could not load blink animation: {e}")
            self.has_blink = False
        
        self.animation_count = 0
        self.animation_delay = 5
        self.current_sprite = 0
        
        # Blink animation settings
        self.is_blinking = False
        self.blink_timer = 0
        self.blink_interval = random.randint(120, 240)  # Random interval between blinks
        
        # Make sure we start with a valid sprite
        self.image = self.SPRITES["idle_right"][0] if "idle_right" in self.SPRITES else pygame.Surface((42, 42))
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y
        self.name = name
        
        # Quiz setup
        self.questions = [
            {
                "question": "Apa kepanjangan dari BPJS?",
                "options": [
                    "A. Badan Penyelenggara Jaminan Sosial",
                    "B. Badan Pelayanan Jaminan Sosial",
                    "C. Badan Pemberi Jaminan Sosial",
                    "D. Badan Penyedia Jaminan Sosial"
                ],
                "correct": 0  # Index of correct answer (A)
            },
            {
                "question": "Berapa iuran BPJS Kesehatan kelas 3?",
                "options": [
                    "A. Rp35.000",
                    "B. Rp42.000",
                    "C. Rp50.000",
                    "D. Rp45.000"
                ],
                "correct": 1  # Index of correct answer (B)
            },
            {
                "question": "Apa yang TIDAK termasuk dalam layanan BPJS Kesehatan?",
                "options": [
                    "A. Rawat Inap",
                    "B. Rawat Jalan",
                    "C. Operasi Plastik Kecantikan",
                    "D. Persalinan"
                ],
                "correct": 2  # Index of correct answer (C)
            }
        ]
        
        # Quiz state
        self.current_question_index = 0
        self.score = 0
        self.answered_questions = set()
        self.show_dialog = False
        self.show_result = False
        self.result_message = ""
        self.result_timer = 0
        
        # Dialog box settings
        self.dialog_box_color = (50, 50, 50, 200)
        self.dialog_box_padding = 20
        self.font = pygame.font.Font(None, 32)
        
        # Interaction distance
        self.interaction_distance = 100
        
        self.dialog_alpha = 0
        self.question_y = HEIGHT
        self.options_x = [WIDTH] * 4
        
        # Button settings
        self.button_color = (100, 100, 255)
        self.button_hover_color = (150, 150, 255)
        self.correct_color = (100, 255, 100)
        self.wrong_color = (255, 100, 100)
        self.buttons = []
        
        # Add back button initialization here
        self.back_button = {
            'rect': pygame.Rect(WIDTH - 120, HEIGHT - 60, 100, 40),
            'text': 'Back',
            'hover': False
        }
        
        self.font = pygame.font.Font(None, 32)
        self.title_font = pygame.font.Font(None, 48)
        self.question_font = pygame.font.Font(None, 36)


        self.question_timer = 15  # waktu dalam detik untuk setiap pertanyaan
        self.timer_start = 0
        self.timer_running = False
        self.font_timer = pygame.font.Font(None, 48)
        
        self.create_buttons()
        
    def handle_hover(self, pos):
        if self.show_dialog:
            # Update hover state untuk tombol back
            self.back_button['hover'] = self.back_button['rect'].collidepoint(pos)

            # Update hover state untuk tombol opsi
            for button in self.buttons:
                button['hover'] = button['rect'].collidepoint(pos)

    def create_buttons(self):
        try:
            # Pengaturan ukuran dan jarak
            button_width = WIDTH * 0.6
            button_height = 50
            button_spacing = 30
            
            current_q = self.questions[self.current_question_index]
            total_buttons = len(current_q['options'])
            
            # Hitung total tinggi yang dibutuhkan untuk semua button
            total_height = (button_height * total_buttons) + (button_spacing * (total_buttons - 1))
            
            # Hitung posisi Y awal
            start_y = (HEIGHT - total_height) // 2 + 50
            
            self.buttons = []
            
            # Buat button hanya untuk jumlah opsi yang tersedia
            for i in range(total_buttons):
                x = (WIDTH - button_width) // 2
                y = start_y + (i * (button_height + button_spacing))
                
                button_rect = pygame.Rect(x, y, button_width, button_height)
                self.buttons.append({
                    'rect': button_rect,
                    'index': i,
                    'hover': False
                })
        except Exception as e:
            print(f"Error in create_buttons: {e}")
            self.buttons = []  # Reset buttons jika terjadi error
    
    def draw_dialog(self, screen):
        if self.show_dialog:
            try:
                # Background semi-transparan
                dialog_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                pygame.draw.rect(dialog_surface, (0, 0, 0, 200), dialog_surface.get_rect())
                screen.blit(dialog_surface, (0, 0))

                # Judul Quiz
                title_text = "BPJS Quiz"
                title_surface = self.title_font.render(title_text, True, WHITE)
                title_rect = title_surface.get_rect(centerx=WIDTH//2, top=50)
                screen.blit(title_surface, title_rect)
                
                back_button_rect = pygame.Rect(20, 20, 150, 40)  # Position in top-left corner
                back_color = (100, 100, 255) if self.back_button['hover'] else (70, 70, 200)
                pygame.draw.rect(screen, back_color, back_button_rect, border_radius=5)
            

                # Timer display
                if self.timer_running:
                    current_time = pygame.time.get_ticks()
                    elapsed_time = (current_time - self.timer_start) // 1000
                    remaining_time = max(0, self.question_timer - elapsed_time)

                    # Jika waktu habis, pindah ke pertanyaan berikutnya
                    if remaining_time == 0:
                        self.result_message = "Time's up!"
                        self.show_result = True
                        self.result_timer = 60
                        self.move_to_random_question()
                        return

                    # Tampilkan timer
                    timer_text = f"Time: {remaining_time}"
                    timer_color = RED if remaining_time <= 5 else WHITE
                    timer_surface = self.font_timer.render(timer_text, True, timer_color)
                    timer_rect = timer_surface.get_rect(centerx=WIDTH//2, top=10)
                    screen.blit(timer_surface, timer_rect)

                # Score dan nomor pertanyaan
                score_text = f"Score: {self.score}"
                score_surface = self.font.render(score_text, True, WHITE)
                screen.blit(score_surface, (20, 20))

                question_num_text = f"Question {self.current_question_index + 1}/{len(self.questions)}"
                question_num_surface = self.font.render(question_num_text, True, WHITE)
                screen.blit(question_num_surface, (WIDTH - question_num_surface.get_width() - 20, 20))

                # Pertanyaan
                current_q = self.questions[self.current_question_index]
                question_surface = self.question_font.render(current_q['question'], True, WHITE)
                question_rect = question_surface.get_rect(centerx=WIDTH//2, top=150)
                screen.blit(question_surface, question_rect)

                # Opsi jawaban
                options = current_q['options']
                button_width = WIDTH * 0.7
                button_height = 60
                button_spacing = 20
                start_y = 250

                for i, (button, option) in enumerate(zip(self.buttons, options)):
                    button_rect = pygame.Rect((WIDTH - button_width) // 2,
                                            start_y + i * (button_height + button_spacing),
                                            button_width, button_height)
                    button['rect'] = button_rect  # Update button rect

                    # Warna button
                    color = self.button_hover_color if button['hover'] else self.button_color
                    pygame.draw.rect(screen, color, button_rect, border_radius=10)

                    # Teks opsi
                    text_surface = self.font.render(option, True, WHITE)
                    text_rect = text_surface.get_rect(center=button_rect.center)
                    screen.blit(text_surface, text_rect)

                # Pesan hasil jika ada
                if self.show_result and self.result_timer > 0:
                    result_surface = self.font.render(self.result_message, True, WHITE)
                    result_rect = result_surface.get_rect(centerx=WIDTH//2, bottom=HEIGHT-20)
                    screen.blit(result_surface, result_rect)

                # Tombol back di pojok kanan bawah
                pygame.draw.rect(screen,
                               self.button_hover_color if self.back_button['hover'] else self.button_color,
                               self.back_button['rect'],
                               border_radius=5)
                back_text_surface = self.font.render(self.back_button['text'], True, WHITE)
                back_text = self.font.render("Back to Game", True, WHITE)
                back_text_rect = back_text.get_rect(center=back_button_rect.center)
                screen.blit(back_text, back_text_rect)

            except Exception as e:
                print(f"Error in draw_dialog: {e}")
    def handle_click(self, pos):
        if self.show_dialog:
            # Check for back button click
            if self.back_button['rect'].collidepoint(pos):
                self.show_dialog = False
                self.show_result = False
                self.timer_running = False
                return True

            current_q = self.questions[self.current_question_index]

            for button in self.buttons:
                if button['rect'].collidepoint(pos):
                    if button['index'] == current_q['correct']:
                        self.score += 1
                        self.result_message = "Correct!"
                        self.show_correct_animation(button['rect'])
                    else:
                        self.result_message = "Wrong! The correct answer was: " + current_q['options'][current_q['correct']]
                        self.show_wrong_animation(button['rect'])

                    self.show_result = True
                    self.result_timer = 60
                    self.timer_running = False
                    self.move_to_random_question()
                    return True
        return False

    def move_to_random_question(self):
        available_questions = [i for i in range(len(self.questions)) 
                             if i != self.current_question_index]
        if available_questions:
            self.current_question_index = random.choice(available_questions)
            # Reset timer untuk pertanyaan baru
            self.timer_start = pygame.time.get_ticks()
            self.timer_running = True
        self.create_buttons()

    def can_interact(self, player):
        # Calculate distance between NPC and player
        dx = self.rect.centerx - player.rect.centerx
        dy = self.rect.centery - player.rect.centery
        distance = (dx ** 2 + dy ** 2) ** 0.5
        return distance <= self.interaction_distance

    def update_sprite(self):
        try:
            if self.has_blink and self.is_blinking:
                # Play blink animation
                sprite_sheet = "Blink"
                if sprite_sheet in self.blink_sprites:
                    sprites = self.blink_sprites[sprite_sheet]
                    if len(sprites) > 0:
                        if self.animation_count >= self.animation_delay:
                            self.current_sprite = (self.current_sprite + 1) % len(sprites)
                            self.animation_count = 0
                            
                            # Check if blink animation is complete
                            if self.current_sprite == 0:
                                self.is_blinking = False
                                self.blink_timer = 0
                        
                        self.image = sprites[self.current_sprite]
                        self.animation_count += 1
            else:
                # Normal idle animation
                sprite_sheet = "idle_right"
                if sprite_sheet in self.SPRITES:
                    sprites = self.SPRITES[sprite_sheet]
                    if len(sprites) > 0:
                        if self.animation_count >= self.animation_delay:
                            self.current_sprite = (self.current_sprite + 1) % len(sprites)
                            self.animation_count = 0
                        
                        self.image = sprites[self.current_sprite]
                        self.animation_count += 1
                else:
                    print(f"Warning: '{sprite_sheet}' animation not found in sprites")
        except Exception as e:
            print(f"Error in update_sprite: {e}")


    def update(self):
        
        self.update_sprite()

        # Update result timer
        if self.result_timer > 0:
            self.result_timer -= 1
            if self.result_timer == 0:
                self.show_result = False

        # Check timer jika dialog sedang aktif
        if self.show_dialog and self.timer_running:
            current_time = pygame.time.get_ticks()
            elapsed_time = (current_time - self.timer_start) // 1000
            if elapsed_time >= self.question_timer:
                self.result_message = "Time's up!"
                self.show_result = True
                self.result_timer = 60
                self.timer_running = False
                self.move_to_random_question()
                
        if not self.is_blinking:
            self.blink_timer += 1
            if self.blink_timer >= self.blink_interval:
                self.is_blinking = True
                self.current_sprite = 0
                self.animation_count = 0
                self.blink_interval = random.randint(120, 240)  # Set new random interval
            
            self.update_sprite()
            
        if self.has_blink and not self.is_blinking:
            self.blink_timer += 1
            if self.blink_timer >= self.blink_interval:
                self.is_blinking = True
                self.current_sprite = 0
                self.animation_count = 0
                self.blink_interval = random.randint(120, 240)  # Set new random interval
    
    def create_buttons(self):
        current_q = self.questions[self.current_question_index]
        for i, option in enumerate(current_q['options']):
            rect = pygame.Rect(100 + (i % 2) * 300, 250 + (i // 2) * 50, 250, 40)
            self.buttons.append({'rect': rect, 'index': i, 'hover': False})

    def update_sprite(self):
        sprite_sheet_name = "Idle_right"  # Default animation
        
        if "Idle_right" in self.SPRITES:
            sprites = self.SPRITES["Idle_right"]
            
            if self.animation_count >= self.animation_delay:
                self.current_sprite = (self.current_sprite + 1) % len(sprites)
                self.animation_count = 0

            self.image = sprites[self.current_sprite]
            self.animation_count += 1
        else:
            print("Warning: 'Idle_right' animation not found in sprites")
    
    def show_correct_animation(self, rect):
        # Implementasikan animasi jawaban benar di sini
        # Misalnya, buat efek kilat hijau
        for _ in range(5):
            pygame.draw.rect(screen, GREEN, rect, border_radius=10)
            pygame.display.flip()
            pygame.time.wait(50)
            pygame.draw.rect(screen, self.button_color, rect, border_radius=10)
            pygame.display.flip()
            pygame.time.wait(50)

    def show_wrong_animation(self, rect):
        # Implementasikan animasi jawaban salah di sini
        # Misalnya, buat efek getaran
        original_x = rect.x
        for _ in range(5):
            rect.x = original_x - 5
            pygame.draw.rect(screen, RED, rect, border_radius=10)
            pygame.display.flip()
            pygame.time.wait(50)
            rect.x = original_x + 5
            pygame.draw.rect(screen, RED, rect, border_radius=10)
            pygame.display.flip()
            pygame.time.wait(50)
        rect.x = original_x
        
    def update(self):
        self.update_sprite()
class Block(pygame.sprite.Sprite):
    def __init__(self, x, y, terrain_type, size=32):
        super().__init__()
        try:
            # Load the terrain sprite sheet
            sprite_sheet = pygame.image.load(os.path.join("assets", "Terrain (16x16).png")).convert_alpha()
            
            # Define the positions of different terrain types in the sprite sheet
            terrain_positions = {
                "grass": (0, 0),
                "dirt": (0, 16),
                "stone": (0, 32),
                # Add more terrain types as needed
            }
            
            # Get the position of the desired terrain type
            sheet_x, sheet_y = terrain_positions.get(terrain_type, (0, 0))
            
            # Create a surface for our block
            self.image = pygame.Surface((size, size), pygame.SRCALPHA)
            
            # Scale and draw the terrain texture onto our block
            terrain_surface = sprite_sheet.subsurface((sheet_x, sheet_y, 16, 16))
            scaled_terrain = pygame.transform.scale(terrain_surface, (size, size))
            self.image.blit(scaled_terrain, (0, 0))
            
            pygame.mixer.music.load('assets/Skyfall x Attack on Titan.mp3')  # Make sure to have this file
            pygame.mixer.music.set_volume(0.5)  # Set volume to 50%
            pygame.mixer.music.play(-1)  # -1 means loop indefinitely
            
        except pygame.error as e:
            print(f"Error loading sprite: {e}")
            self.image = pygame.Surface((size, size))
            self.image.fill((100, 100, 100))  # Gray color for missing texture
            print("Could not load background music")
        
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        
        
# Add these new classes after the existing imports

class VirtualJoystick:
    def __init__(self):
        self.radius = 50
        self.position = (100, HEIGHT - 100)  # Bottom left position
        self.touch_position = None
        self.active = False
        
    def draw(self, screen):
        # Draw base circle
        pygame.draw.circle(screen, (100, 100, 100), self.position, self.radius, 2)
        
        # Draw joystick knob
        if self.active and self.touch_position:
            knob_pos = self.get_constrained_knob_pos()
            pygame.draw.circle(screen, (200, 200, 200), knob_pos, self.radius//2)
        else:
            pygame.draw.circle(screen, (200, 200, 200), self.position, self.radius//2)
    
    def get_constrained_knob_pos(self):
        if not self.touch_position:
            return self.position
            
        dx = self.touch_position[0] - self.position[0]
        dy = self.touch_position[1] - self.position[1]
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance <= self.radius:
            return self.touch_position
        else:
            angle = math.atan2(dy, dx)
            x = self.position[0] + math.cos(angle) * self.radius
            y = self.position[1] + math.sin(angle) * self.radius
            return (int(x), int(y))
        
    def update(self):
        # Update joystick state based on mouse input
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]  # Left mouse button

        if mouse_pressed:
            if self.active or math.dist(mouse_pos, self.position) <= self.radius:
                self.active = True
                self.touch_position = mouse_pos
        else:
            self.active = False
            self.touch_position = None
    
    def get_value(self):
        if not self.active or not self.touch_position:
            return (0, 0)
            
        knob_pos = self.get_constrained_knob_pos()
        dx = knob_pos[0] - self.position[0]
        dy = knob_pos[1] - self.position[1]
        
        # Normalize values between -1 and 1
        return (dx/self.radius, dy/self.radius)

class TouchButton:
    def __init__(self, x, y, width, height, text):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.pressed = False
        self.font = pygame.font.Font(None, 36)
        
    def draw(self, screen):
        color = (150, 150, 150) if self.pressed else (100, 100, 100)
        pygame.draw.rect(screen, color, self.rect, border_radius=10)
        pygame.draw.rect(screen, (200, 200, 200), self.rect, 2, border_radius=10)
        
        text_surface = self.font.render(self.text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

# Modify the Game class to include touch controls
class Game:
    def __init__(self):
        
        # Add touch controls
        self.joystick = VirtualJoystick()
        self.jump_button = TouchButton(WIDTH - 150, HEIGHT - 150, 100, 100, "Jump")
        self.interact_button = TouchButton(WIDTH - 150, HEIGHT - 270, 100, 100, "Action")
        self.all_sprites = pygame.sprite.Group()
        self.blocks = pygame.sprite.Group()
        
        self.create_level()
        
        
    def create_level(self):
        # Contoh sederhana pembuatan level
        # Anda bisa mengubah ini sesuai dengan desain level yang diinginkan
        ground_y = HEIGHT - 64  # 64 piksel dari bawah layar
        
        # Membuat tanah
        for x in range(0, WIDTH, 32):
            if x == 0 or x == WIDTH - 32:
                # Blok ujung menggunakan tekstur rumput
                block = Block(x, ground_y, "grass")
            else:
                # Blok tengah menggunakan tekstur tanah
                block = Block(x, ground_y, "dirt")
            self.all_sprites.add(block)
            self.blocks.add(block)
        
        # Membuat beberapa platform
        platforms = [
            (200, HEIGHT - 200, 5, "stone"),  # (x, y, width, type)
            (500, HEIGHT - 300, 7, "grass"),
            (800, HEIGHT - 150, 4, "stone"),
        ]
        
        for plat in platforms:
            x, y, width, terrain_type = plat
            for i in range(width):
                block = Block(x + i * 32, y, terrain_type)
                self.all_sprites.add(block)
                self.blocks.add(block)
        
    def events(self):
        try:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_m:  # Press M to mute/unmute
                        self.toggle_music()
                    elif event.key == pygame.K_UP:  # Volume up
                        current_volume = pygame.mixer.music.get_volume()
                        self.set_music_volume(min(1.0, current_volume + 0.1))
                    elif event.key == pygame.K_DOWN:  # Volume down
                        current_volume = pygame.mixer.music.get_volume()
                        self.set_music_volume(max(0.0, current_volume - 0.1))
                    if event.key == pygame.K_SPACE:
                        self.player.jump()
                    elif event.key == pygame.K_ESCAPE:
                        if self.npc.show_dialog:
                            self.npc.show_dialog = False
                            self.npc.show_result = False
                        else:
                            self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()
                    if math.dist(pos, self.joystick.position) <= self.joystick.radius:
                        self.joystick.active = True
                        self.joystick.touch_position = pos
                    elif self.jump_button.rect.collidepoint(pos):
                        self.jump_button.pressed = True
                        self.player.jump()
                    elif self.interact_button.rect.collidepoint(pos):
                        self.interact_button.pressed = True
                        if self.npc.can_interact(self.player):
                            self.npc.show_dialog = True
                    elif self.npc.show_dialog:
                        self.npc.handle_click(pos)
                elif event.type == pygame.MOUSEBUTTONUP:
                    self.joystick.active = False
                    self.joystick.touch_position = None
                    self.jump_button.pressed = False
                    self.interact_button.pressed = False
                elif event.type == pygame.MOUSEMOTION:
                    mouse_pos = pygame.mouse.get_pos()  # Get current mouse position
                    if self.joystick.active:
                        self.joystick.touch_position = mouse_pos
                    if self.npc.show_dialog:
                        self.npc.handle_hover(mouse_pos)

            # Handle joystick movement
            if self.joystick.active:
                x_value, _ = self.joystick.get_value()
                if x_value < -0.2:
                    self.player.move_left()
                elif x_value > 0.2:
                    self.player.move_right()

            # Handle continuous key presses
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.player.move_left()
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.player.move_right()

        except Exception as e:
            print(f"Error in events: {e}")
            
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.jump_button.rect.collidepoint(event.pos):
                    self.player.jump()

        # Handle continuous joystick input
        joy_x, joy_y = self.joystick.get_value()
        if abs(joy_x) > 0.1:  # Apply dead zone
            self.player.vel_x = joy_x * self.player.max_speed
        else:
            self.player.vel_x *= 0.9  # Apply friction when no input

    def draw(self):
        screen.fill(BLACK)
        self.all_sprites.draw(screen)
        
        # Draw touch controls
        self.joystick.draw(screen)
        self.jump_button.draw(screen)
        self.interact_button.draw(screen)
        
        pygame.display.flip()

class Game:
    def __init__(self):
        self.running = True
        self.debug_font = pygame.font.Font(None, 36)

        # Create sprite groups
        self.all_sprites = pygame.sprite.Group()
        self.blocks = pygame.sprite.Group()
        self.npcs = pygame.sprite.Group()

        # Create player
        self.player = Player(self)
        self.all_sprites.add(self.player)

        # Create NPC
        self.npc = NPC(WIDTH // 2, 100, "Rock Head")
        self.all_sprites.add(self.npc)
        self.npcs.add(self.npc)

        # Create level
        self.create_level()

        # Add touch controls
        self.joystick = VirtualJoystick()
        self.jump_button = TouchButton(WIDTH - 150, HEIGHT - 150, 100, 100, "Jump")
        self.interact_button = TouchButton(WIDTH - 150, HEIGHT - 270, 100, 100, "Action")

        # Initialize meme-related attributes
        self.meme_font = pygame.font.Font(None, 36)
        self.meme_text = ""
        self.meme_timer = 0
        self.memes = [
            "I don't always test my code, but when I do, I do it in production.",
            "It's not a bug, it's an undocumented feature.",
            "Why do programmers prefer dark mode? Because light attracts bugs.",
            "I'm not lazy, I'm on energy saving mode.",
            "There are 10 types of people in the world: those who understand binary, and those who don't.",
            "My code doesn't work, I have no idea why. My code works, I have no idea why.",
            "It works on my machine!",
            "The best thing about a boolean is even if you're wrong you're only off by a bit.",
            "Debugging: Removing the needles from the haystack.",
            "If debugging is the process of removing software bugs, then programming must be the process of putting them in."
        ]

        # Add background music
        try:
            pygame.mixer.music.load('assets/Skyfall x Attack on Titan.mp3')
            pygame.mixer.music.set_volume(0.5)
            pygame.mixer.music.play(-1)
        except:
            print("Could not load background music")

    def create_level(self):
        # Contoh sederhana pembuatan level
        # Anda bisa mengubah ini sesuai dengan desain level yang diinginkan
        ground_y = HEIGHT - 64  # 64 piksel dari bawah layar
        
        # Membuat tanah
        for x in range(0, WIDTH, 32):
            if x == 0 or x == WIDTH - 32:
                # Blok ujung menggunakan tekstur rumput
                block = Block(x, ground_y, "grass")
            else:
                # Blok tengah menggunakan tekstur tanah
                block = Block(x, ground_y, "dirt")
            self.all_sprites.add(block)
            self.blocks.add(block)
        
        # Membuat beberapa platform
        platforms = [
            (200, HEIGHT - 200, 5, "stone"),  # (x, y, width, type)
            (500, HEIGHT - 300, 7, "grass"),
            (800, HEIGHT - 150, 4, "stone"),
        ]
        
        for plat in platforms:
            x, y, width, terrain_type = plat
            for i in range(width):
                block = Block(x + i * 32, y, terrain_type)
                self.all_sprites.add(block)
                self.blocks.add(block)

    def events(self):
        try:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_m:  # Press M to mute/unmute
                        self.toggle_music()
                    elif event.key == pygame.K_UP:  # Volume up
                        current_volume = pygame.mixer.music.get_volume()
                        self.set_music_volume(min(1.0, current_volume + 0.1))
                    elif event.key == pygame.K_DOWN:  # Volume down
                        current_volume = pygame.mixer.music.get_volume()
                        self.set_music_volume(max(0.0, current_volume - 0.1))
                    if event.key == pygame.K_SPACE:
                        self.player.jump()
                    elif event.key == pygame.K_ESCAPE:
                        if self.npc.show_dialog:
                            self.npc.show_dialog = False
                            self.npc.show_result = False
                        else:
                            self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()
                    if math.dist(pos, self.joystick.position) <= self.joystick.radius:
                        self.joystick.active = True
                        self.joystick.touch_position = pos
                    elif self.jump_button.rect.collidepoint(pos):
                        self.jump_button.pressed = True
                        self.player.jump()
                    elif self.interact_button.rect.collidepoint(pos):
                        self.interact_button.pressed = True
                        if self.npc.can_interact(self.player):
                            self.npc.show_dialog = True
                    elif self.npc.show_dialog:
                        self.npc.handle_click(pos)
                elif event.type == pygame.MOUSEBUTTONUP:
                    self.joystick.active = False
                    self.joystick.touch_position = None
                    self.jump_button.pressed = False
                    self.interact_button.pressed = False
                elif event.type == pygame.MOUSEMOTION:
                    mouse_pos = pygame.mouse.get_pos()  # Get current mouse position
                    if self.joystick.active:
                        self.joystick.touch_position = mouse_pos
                    if self.npc.show_dialog:
                        self.npc.handle_hover(mouse_pos)

            # Handle joystick movement
            if self.joystick.active:
                x_value, _ = self.joystick.get_value()
                if x_value < -0.2:
                    self.player.move_left()
                elif x_value > 0.2:
                    self.player.move_right()

            # Handle continuous key presses
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.player.move_left()
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.player.move_right()

        except Exception as e:
            print(f"Error in events: {e}")

    def update(self):
        self.all_sprites.update()
        self.joystick.update() 
        
        self.meme_timer += 1
        if self.meme_timer >= FPS * 5:  # Every 5 seconds
            self.meme_text = random.choice(self.memes)
            self.meme_timer = 0

    def draw(self):
        screen.fill(BLACK)
        self.all_sprites.draw(screen)

        # Draw touch controls
        self.joystick.draw(screen)
        self.jump_button.draw(screen)
        self.interact_button.draw(screen)

        if self.npc.show_dialog:
            self.npc.draw_dialog(screen)

        if self.meme_text:
            meme_surface = self.meme_font.render(self.meme_text, True, WHITE)
            meme_rect = meme_surface.get_rect(center=(WIDTH // 2, 50))
            screen.blit(meme_surface, meme_rect)
        
        pygame.display.flip()

    def run(self):
        while self.running:
            self.events()
            self.update()
            self.draw()
            pygame.time.Clock().tick(FPS)

    def set_music_volume(self, volume):
        try:
            pygame.mixer.music.set_volume(volume)
        except:
            print("Could not adjust music volume")

    def toggle_music(self):
        try:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.pause()
            else:
                pygame.mixer.music.unpause()
        except:
            print("Could not toggle music")

    def quit(self):
        pygame.quit()
        sys.exit()
# Main game loop
if __name__ == "__main__":
    try:
        game = Game()
        game.run()
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
    finally:
        pygame.quit()
        sys.exit()