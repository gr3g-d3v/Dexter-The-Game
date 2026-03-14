import os
import pygame
import yaml


WIDTH, HEIGHT = 1920, 1080

DIALOGUE_FRAME_SIZE = (1200, 300)
DIALOGUE_BOTTOM_PADDING = 10
DIALOGUE_FRAME_INNER_MARGIN_X = 40
DIALOGUE_NAME_OFFSET_Y = 20
DIALOGUE_TEXT_OFFSET_Y = 80

NAV_BUTTON_SIZE = (80, 80)
NAV_BUTTON_GAP = 20

SETTINGS_BUTTON_POS = (20, 20)
SETTINGS_BUTTON_SIZE = (100, 100)

FADE_IN_DURATION_MS = 450

# Typewriter effect: seconds per character (adjust to sync with voice acting)
TYPEWRITER_SPEED = 0.05


def find_assets_dir():
    base = os.path.dirname(os.path.abspath(__file__))
    candidate = os.path.join(base, "menu_assets")
    if os.path.isdir(candidate):
        return candidate
    return base


def find_files(asset_dir, exts):
    exts = tuple(exts)
    return [f for f in os.listdir(asset_dir) if f.lower().endswith(exts)]


class Button:
    def __init__(self, text, rect, font, image=None, callback=None):
        self.text = text
        self.rect = pygame.Rect(rect)
        self.font = font
        self.image = image
        self.callback = callback
        self.hover = False

    def draw(self, surf):
        # Hover scale factor (10% increase)
        hover_scale = 1.10 if self.hover else 1.0

        if self.image:
            iw, ih = self.image.get_size()
            # scale preserving aspect ratio to fit inside button rect
            scale = min(self.rect.w / iw, self.rect.h / ih)
            new_w = max(1, int(iw * scale * hover_scale))
            new_h = max(1, int(ih * scale * hover_scale))
            img = pygame.transform.smoothscale(self.image, (new_w, new_h))
            px = self.rect.x + (self.rect.w - new_w) // 2
            py = self.rect.y + (self.rect.h - new_h) // 2

            # simply blit scaled image (no outline/glow)
            surf.blit(img, (px, py))
            return
        else:
            # draw a simple colored rectangle, scale it on hover
            rect = self.rect.copy()
            if self.hover:
                # inflate by 10% of size
                rect.inflate_ip(int(rect.w * 0.10), int(rect.h * 0.10))
                rect.center = self.rect.center

            color = (180, 20, 20) if not self.hover else (220, 40, 40)
            pygame.draw.rect(surf, color, rect, border_radius=6)
            # no border drawn

        # draw text centered
        txt = self.font.render(self.text, True, (255, 255, 255))
        tx = txt.get_rect(center=self.rect.center)
        surf.blit(txt, tx)

    def handle_event(self, ev):
        if ev.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(ev.pos)
        elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if self.rect.collidepoint(ev.pos):
                if self.callback:
                    self.callback()


def load_assets(asset_dir):
    imgs = find_files(asset_dir, ('.png', '.jpg', '.jpeg'))
    fonts = find_files(asset_dir, ('.ttf', '.otf'))

    # map known asset names to files present in the folder
    name_map = {n.lower(): os.path.join(asset_dir, n) for n in imgs}

    bg_path = None
    play_btn = None
    title_btn = None
    exit_btn = None

    # common filenames used in your assets
    if 'menu_bg.png' in name_map:
        bg_path = name_map['menu_bg.png']
    else:
        # fallback to any image
        bg_path = os.path.join(asset_dir, imgs[0]) if imgs else None

    if 'playbutton.png' in name_map:
        play_btn = name_map['playbutton.png']
    if 'titlebutton.png' in name_map:
        title_btn = name_map['titlebutton.png']
    if 'exitbutton.png' in name_map:
        exit_btn = name_map['exitbutton.png']

    font_path = os.path.join(asset_dir, fonts[0]) if fonts else None
    return bg_path, play_btn, title_btn, exit_btn, font_path


class Game:
    """Handles the visual novel gameplay and dialogue display"""
    
    def __init__(self, screen, clock, font_names, font_dialogues, base_dir):
        self.screen = screen
        self.clock = clock
        self.font_names = font_names
        self.font_dialogues = font_dialogues
        self.base_dir = base_dir
        self.scenes = []
        self.current_scene_idx = 0
        self.current_dialogue_idx = 0
        self.background = None
        self.dialogue_frame = None
        self.back_button = None
        self.forward_button = None
        self.back_button_rect = None
        self.forward_button_rect = None
        self.settings_icon = None
        self.settings_icon_rect = None
        self.settings_open = False
        self._fade_in_start_ms = None
        self._dialogue_start_ms = None
        self._fade_overlay = pygame.Surface((WIDTH, HEIGHT))
        self._fade_overlay.fill((0, 0, 0))
        self.is_running = True
        
        # Load dialogue frame and buttons from hud_assets
        self.load_dialogue_frame()
        self.load_navigation_buttons()
        self.load_settings_icon()
        
        # Load dialogues from YAML
        self.load_dialogues()
        
        # Load initial scene
        if self.scenes:
            self.load_scene(0)

        self._start_fade_in()

    def _start_fade_in(self):
        self._fade_in_start_ms = pygame.time.get_ticks()
    
    def load_dialogue_frame(self):
        """Load dialogue frame image from hud_assets"""
        frame_path = os.path.join(self.base_dir, 'hud_assets', 'dialogueframe.png')
        self.dialogue_frame = pygame.image.load(frame_path)
        self.dialogue_frame = pygame.transform.smoothscale(self.dialogue_frame, DIALOGUE_FRAME_SIZE).convert_alpha()
    
    def load_navigation_buttons(self):
        """Load navigation button images from hud_assets"""
        hud_dir = os.path.join(self.base_dir, 'hud_assets')
        self.back_button = pygame.image.load(os.path.join(hud_dir, 'backbutton.png'))
        self.back_button = pygame.transform.smoothscale(self.back_button, NAV_BUTTON_SIZE).convert_alpha()
        self.forward_button = pygame.image.load(os.path.join(hud_dir, 'forwardbutton.png'))
        self.forward_button = pygame.transform.smoothscale(self.forward_button, NAV_BUTTON_SIZE).convert_alpha()

    def load_settings_icon(self):
        hud_dir = os.path.join(self.base_dir, 'hud_assets')
        settings_path = os.path.join(hud_dir, 'settings.png')
        self.settings_icon = pygame.image.load(settings_path)
        self.settings_icon = pygame.transform.smoothscale(self.settings_icon, SETTINGS_BUTTON_SIZE).convert_alpha()
    
    def load_dialogues(self):
        """Load narrative from dialogues.yml"""
        yaml_path = os.path.join(self.base_dir, 'dialogues.yml')
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            self.scenes = data['scenes']

    def _get_scene_background_path(self, scene):
        return scene.get('background')

    def _get_dialogue_speaker(self, dialogue):
        return dialogue.get('speaker') or dialogue.get('character') or 'Unknown'

    def _get_dialogue_text(self, dialogue):
        return dialogue.get('text', '')

    
    def load_scene(self, scene_idx):
        """Load a scene by index"""
        if scene_idx >= len(self.scenes):
            self.is_running = False
            return
        
        self.current_scene_idx = scene_idx
        self.current_dialogue_idx = 0
        self._dialogue_start_ms = None
        scene = self.scenes[scene_idx]
        
        # Load background if specified
        bg_rel_path = self._get_scene_background_path(scene)
        if bg_rel_path:
            bg_path = os.path.join(self.base_dir, bg_rel_path)
            self.background = self.load_image(bg_path)
        else:
            self.background = None
        
        self._start_fade_in()
    
    def load_image(self, path):
        """Safely load an image file"""
        try:
            img = pygame.image.load(path)
            img = pygame.transform.smoothscale(img, (WIDTH, HEIGHT))
            return img.convert()
        except FileNotFoundError:
            return None
    
    def get_current_dialogue(self):
        """Get the current dialogue line"""
        if self.current_scene_idx < len(self.scenes):
            scene = self.scenes[self.current_scene_idx]
            if 'dialogues' in scene and self.current_dialogue_idx < len(scene['dialogues']):
                return scene['dialogues'][self.current_dialogue_idx]
        return None
    
    def previous_dialogue(self):
        """Move to previous dialogue"""
        if self.current_dialogue_idx > 0:
            self.current_dialogue_idx -= 1
            self._dialogue_start_ms = None
        elif self.current_scene_idx > 0:
            # Go to previous scene
            prev_scene_idx = self.current_scene_idx - 1
            self.load_scene(prev_scene_idx)
            scene = self.scenes[self.current_scene_idx]
            dialogues = scene.get('dialogues') or []
            self.current_dialogue_idx = max(0, len(dialogues) - 1)
            self._dialogue_start_ms = None
    
    def next_dialogue(self):
        """Move to next dialogue or next scene"""
        if self.current_scene_idx >= len(self.scenes):
            return
        
        scene = self.scenes[self.current_scene_idx]
        if self.current_dialogue_idx < len(scene['dialogues']) - 1:
            self.current_dialogue_idx += 1
            self._dialogue_start_ms = None
        else:
            # Move to next scene
            if self.current_scene_idx < len(self.scenes) - 1:
                self.load_scene(self.current_scene_idx + 1)
            else:
                # End of story
                self.is_running = False
    
    def handle_events(self):
        """Handle input events"""
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                self.is_running = False
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if self.settings_icon_rect and self.settings_icon_rect.collidepoint(ev.pos):
                    self.settings_open = not self.settings_open
                    continue
                # left arrow moves to previous dialogue, right arrow moves forward
                if self.back_button_rect and self.back_button_rect.collidepoint(ev.pos):
                    self.previous_dialogue()
                elif self.forward_button_rect and self.forward_button_rect.collidepoint(ev.pos):
                    self.next_dialogue()
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_LEFT:
                    self.previous_dialogue()
                elif ev.key == pygame.K_RIGHT:
                    self.next_dialogue()
                elif ev.key == pygame.K_ESCAPE:
                    self.is_running = False
    
    def draw(self):
        """Draw the current dialogue frame"""
        # Draw background
        if self.background:
            self.screen.blit(self.background, (0, 0))
        else:
            self.screen.fill((20, 20, 20))

        mouse_pos = pygame.mouse.get_pos()

        if self.settings_icon:
            self.settings_icon_rect = pygame.Rect(SETTINGS_BUTTON_POS, SETTINGS_BUTTON_SIZE)
            self.screen.blit(self.settings_icon, self.settings_icon_rect)
        
        dialogue = self.get_current_dialogue()
        if dialogue:
            character_name = self._get_dialogue_speaker(dialogue)
            dialogue_text = self._get_dialogue_text(dialogue)
            
            # Calculate visible text for typewriter effect
            if self._dialogue_start_ms is None:
                self._dialogue_start_ms = pygame.time.get_ticks()
            
            elapsed_ms = pygame.time.get_ticks() - self._dialogue_start_ms
            chars_to_show = int(elapsed_ms / (TYPEWRITER_SPEED * 1000))
            visible_text = dialogue_text[:chars_to_show]
            
            # Draw dialogue frame from hud_assets
            box_height = DIALOGUE_FRAME_SIZE[1]
            bottom_padding = DIALOGUE_BOTTOM_PADDING
            box_y = HEIGHT - box_height - bottom_padding

            button_size = NAV_BUTTON_SIZE[0]
            gap = NAV_BUTTON_GAP
            frame_w = self.dialogue_frame.get_width()
            total_w = button_size + gap + frame_w + gap + button_size
            start_x = (WIDTH - total_w) // 2
            forward_x = start_x
            frame_x = forward_x + button_size + gap
            back_x = frame_x + frame_w + gap

            if self.dialogue_frame:
                self.screen.blit(self.dialogue_frame, (frame_x, box_y))
            
            # Draw character name with YDKJ_The_Ride font
            name_surf = self.font_names.render(character_name.upper(), True, (220, 20, 20))
            self.screen.blit(name_surf, (frame_x + DIALOGUE_FRAME_INNER_MARGIN_X, box_y + DIALOGUE_NAME_OFFSET_Y))
            
            # Draw dialogue text with word wrapping using Caslon Antique font
            margin_x = DIALOGUE_FRAME_INNER_MARGIN_X
            margin_y = box_y + DIALOGUE_TEXT_OFFSET_Y
            max_width = frame_w - 2 * margin_x
            
            # Simple word wrapping
            words = visible_text.split()
            lines = []
            current_line = ""
            
            for word in words:
                test_line = current_line + " " + word if current_line else word
                text_width = self.font_dialogues.size(test_line)[0]
                if text_width > max_width:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
                else:
                    current_line = test_line
            
            if current_line:
                lines.append(current_line)
            
            # Draw lines
            for i, line in enumerate(lines):
                if i < 3:  # Limit to 3 lines
                    line_surf = self.font_dialogues.render(line, True, (255, 255, 255))
                    self.screen.blit(line_surf, (frame_x + margin_x, margin_y + i * 50))
            
            # Draw navigation buttons
            button_y = box_y + (box_height - NAV_BUTTON_SIZE[1]) // 2

            def blit_hover_scaled(img, rect, scale_down=0.92):
                if rect.collidepoint(mouse_pos):
                    w = max(1, int(rect.w * scale_down))
                    h = max(1, int(rect.h * scale_down))
                    scaled = pygame.transform.smoothscale(img, (w, h))
                    x = rect.x + (rect.w - w) // 2
                    y = rect.y + (rect.h - h) // 2
                    self.screen.blit(scaled, (x, y))
                else:
                    self.screen.blit(img, rect)
            
                # back arrow on left
            if self.back_button:
                self.back_button_rect = pygame.Rect(forward_x, button_y, NAV_BUTTON_SIZE[0], NAV_BUTTON_SIZE[1])
                blit_hover_scaled(self.back_button, self.back_button_rect)
            
            # forward arrow on right
            if self.forward_button:
                self.forward_button_rect = pygame.Rect(back_x, button_y, NAV_BUTTON_SIZE[0], NAV_BUTTON_SIZE[1])
                blit_hover_scaled(self.forward_button, self.forward_button_rect)
        
        if self._fade_in_start_ms is not None:
            elapsed = pygame.time.get_ticks() - self._fade_in_start_ms
            if elapsed >= FADE_IN_DURATION_MS:
                self._fade_in_start_ms = None
            else:
                alpha = int(255 * (1.0 - (elapsed / FADE_IN_DURATION_MS)))
                if alpha > 0:
                    self._fade_overlay.set_alpha(alpha)
                    self.screen.blit(self._fade_overlay, (0, 0))

        pygame.display.flip()
    
    def run(self):
        """Main game loop"""
        while self.is_running:
            self.handle_events()
            self.draw()
            self.clock.tick(60)





def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption('Dexter - The Game (Menu)')
    clock = pygame.time.Clock()

    asset_dir = find_assets_dir()
    bg_path, play_btn_path, title_btn_path, exit_btn_path, font_path = load_assets(asset_dir)

    # load background
    background = pygame.image.load(bg_path).convert()
    background = pygame.transform.smoothscale(background, (WIDTH, HEIGHT))

    # load button images
    def load_img(path, convert_alpha=True):
        img = pygame.image.load(path)
        return img.convert_alpha() if convert_alpha else img.convert()

    play_img = load_img(play_btn_path)
    title_img = load_img(title_btn_path)
    exit_img = load_img(exit_btn_path)

    # load font
    base_font = pygame.font.Font(font_path, 56)
    
    # Load game fonts
    game_fonts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'game_fonts')
    font_names = pygame.font.Font(os.path.join(game_fonts_dir, 'YDKJ_The_Ride2_0.ttf'), 48)
    font_dialogues = pygame.font.Font(os.path.join(game_fonts_dir, 'Caslon Antique.ttf'), 36)

    
    btn_w, btn_h = 900, 220
    start_y = 360
    gap = 5

    # Game state management
    state = {'current': 'menu', 'game': None}

    def on_play():
        """Start the game"""
        state['game'] = Game(screen, clock, font_names, font_dialogues, os.path.dirname(os.path.abspath(__file__)))
        state['current'] = 'game'

    def on_quit():
        state['current'] = 'quit'

    # Play button now starts the game
    btn_play = Button('ИГРАТЬ', (-90, start_y, btn_w, btn_h), base_font, image=play_img, callback=on_play)
    btn_credits = Button('ТИТРЫ', (-90, start_y + (btn_h + gap), btn_w, btn_h), base_font, image=title_img, callback=None)
    btn_quit = Button('ВЫХОД', (-90, start_y + 2 * (btn_h + gap), btn_w, btn_h), base_font, image=exit_img, callback=on_quit)

    # menu buttons (play, credits, quit) in correct vertical order
    buttons = [btn_play, btn_credits, btn_quit]

    # Main loop
    running = True
    while running:
        if state['current'] == 'menu':
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    running = False
                for b in buttons:
                    b.handle_event(ev)

            # draw menu
            if background:
                screen.blit(background, (0, 0))
            else:
                screen.fill((10, 10, 10))
            for b in buttons:
                b.draw(screen)

            pygame.display.flip()
            clock.tick(60)

        elif state['current'] == 'game':
            # Game state
            if state['game']:
                state['game'].run()
            # После завершения игры возвращаемся в меню
            state['current'] = 'menu'

        elif state['current'] == 'quit':
            running = False

    pygame.quit()


if __name__ == '__main__':
    main()
