import os
import pygame
import yaml


WIDTH, HEIGHT = 1920, 1080


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
        if self.image:
            iw, ih = self.image.get_size()
            # scale preserving aspect ratio to fit inside button rect
            scale = min(self.rect.w / iw, self.rect.h / ih)
            new_w = int(iw * scale)
            new_h = int(ih * scale)
            img = pygame.transform.smoothscale(self.image, (new_w, new_h))
            px = self.rect.x + (self.rect.w - new_w) // 2
            py = self.rect.y + (self.rect.h - new_h) // 2
            # optional hover scale (slight grow) removed to avoid white overlay; keep image unchanged
            surf.blit(img, (px, py))
            return
        else:
            color = (180, 20, 20) if not self.hover else (220, 40, 40)
            pygame.draw.rect(surf, color, self.rect, border_radius=6)
            pygame.draw.rect(surf, (30, 10, 10), self.rect, 4, border_radius=6)

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
    
    def __init__(self, screen, clock, font_large, font_small, base_dir):
        self.screen = screen
        self.clock = clock
        self.font_large = font_large
        self.font_small = font_small
        self.base_dir = base_dir
        self.scenes = []
        self.current_scene_idx = 0
        self.current_dialogue_idx = 0
        self.background = None
        self.character_image = None
        self.is_running = True
        
        # Load dialogues from YAML
        self.load_dialogues()
        
        # Load initial scene
        if self.scenes:
            self.load_scene(0)
    
    def load_dialogues(self):
        """Load narrative from dialogues.yml"""
        yaml_path = os.path.join(self.base_dir, 'dialogues.yml')
        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                if data and 'scenes' in data:
                    self.scenes = data['scenes']
                    print(f"Loaded {len(self.scenes)} scenes from dialogues.yml")
        except FileNotFoundError:
            print(f"dialogues.yml not found at {yaml_path}")
        except yaml.YAMLError as e:
            print(f"Error parsing dialogues.yml: {e}")
    
    def load_scene(self, scene_idx):
        """Load a scene by index"""
        if scene_idx >= len(self.scenes):
            self.is_running = False
            return
        
        self.current_scene_idx = scene_idx
        self.current_dialogue_idx = 0
        scene = self.scenes[scene_idx]
        
        # Load background if specified
        if 'background' in scene and scene['background']:
            bg_path = os.path.join(self.base_dir, scene['background'])
            self.background = self.load_image(bg_path)
        else:
            self.background = None
        
        print(f"Loaded scene: {scene.get('scene', 'Unknown')}")
    
    def load_image(self, path):
        """Safely load an image file"""
        if path and os.path.isfile(path):
            try:
                img = pygame.image.load(path)
                img = pygame.transform.smoothscale(img, (WIDTH, HEIGHT))
                return img.convert()
            except Exception as e:
                print(f"Error loading image {path}: {e}")
        return None
    
    def get_current_dialogue(self):
        """Get the current dialogue line"""
        if self.current_scene_idx < len(self.scenes):
            scene = self.scenes[self.current_scene_idx]
            if 'dialogues' in scene and self.current_dialogue_idx < len(scene['dialogues']):
                return scene['dialogues'][self.current_dialogue_idx]
        return None
    
    def next_dialogue(self):
        """Move to next dialogue or next scene"""
        scene = self.scenes[self.current_scene_idx]
        if self.current_dialogue_idx < len(scene['dialogues']) - 1:
            self.current_dialogue_idx += 1
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
                # Advance dialogue on click
                self.next_dialogue()
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_SPACE:
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
        
        dialogue = self.get_current_dialogue()
        if dialogue:
            character_name = dialogue.get('character', 'Unknown')
            dialogue_text = dialogue.get('text', '')
            
            # Draw dialogue box (semi-transparent dark rectangle at bottom)
            box_height = 280
            box_rect = pygame.Rect(0, HEIGHT - box_height, WIDTH, box_height)
            # Semi-transparent background
            s = pygame.Surface((WIDTH, box_height), pygame.SRCALPHA)
            pygame.draw.rect(s, (0, 0, 0, 200), (0, 0, WIDTH, box_height))
            s.set_colorkey((0, 0, 0))
            self.screen.blit(s, (0, HEIGHT - box_height))
            # Border
            pygame.draw.rect(self.screen, (220, 20, 20), box_rect, 3)
            
            # Draw character name
            name_surf = self.font_large.render(character_name.upper(), True, (220, 20, 20))
            self.screen.blit(name_surf, (40, HEIGHT - box_height + 20))
            
            # Draw dialogue text with word wrapping
            margin_x = 40
            margin_y = HEIGHT - box_height + 80
            max_width = WIDTH - 2 * margin_x
            
            # Simple word wrapping
            words = dialogue_text.split()
            lines = []
            current_line = ""
            
            for word in words:
                test_line = current_line + " " + word if current_line else word
                text_width = self.font_small.size(test_line)[0]
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
                    line_surf = self.font_small.render(line, True, (255, 255, 255))
                    self.screen.blit(line_surf, (margin_x, margin_y + i * 50))
            
            # Draw "click to continue" hint
            hint_text = "Нажмите ЛКМ для продолжения (Click to continue...)"
            hint_surf = self.font_small.render(hint_text, True, (150, 150, 150))
            hint_rect = hint_surf.get_rect(bottomright=(WIDTH - 40, HEIGHT - 20))
            self.screen.blit(hint_surf, hint_rect)
        
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
    background = None
    if bg_path and os.path.isfile(bg_path):
        try:
            background = pygame.image.load(bg_path).convert()
            background = pygame.transform.smoothscale(background, (WIDTH, HEIGHT))
        except Exception:
            background = None

    # load button images
    def load_img(path, convert_alpha=True):
        if path and os.path.isfile(path):
            try:
                img = pygame.image.load(path)
                print(f'Loaded image: {os.path.basename(path)} size={img.get_size()}')
                return img.convert_alpha() if convert_alpha else img.convert()
            except Exception:
                return None
        return None

    play_img = load_img(play_btn_path)
    title_img = load_img(title_btn_path)
    exit_img = load_img(exit_btn_path)

    # load font
    if font_path and os.path.isfile(font_path):
        try:
            base_font = pygame.font.Font(font_path, 56)
            small_font = pygame.font.Font(font_path, 36)
        except Exception:
            base_font = pygame.font.SysFont(None, 56)
            small_font = pygame.font.SysFont(None, 36)
    else:
        base_font = pygame.font.SysFont(None, 56)
        small_font = pygame.font.SysFont(None, 36)

    
    btn_w, btn_h = 900, 220
    left_x = -90
    start_y = 360
    gap = 5

    # Game state management
    state = {'current': 'menu', 'game': None}

    def on_play():
        """Start the game"""
        state['current'] = 'game'
        state['game'] = Game(screen, clock, base_font, small_font, os.path.dirname(os.path.abspath(__file__)))

    def on_quit():
        state['current'] = 'quit'

    # Play button now starts the game
    btn_play = Button('ИГРАТЬ', (left_x, start_y, btn_w, btn_h), base_font, image=play_img, callback=on_play)
    btn_credits = Button('ТИТРЫ', (left_x, start_y + (btn_h + gap), btn_w, btn_h), base_font, image=title_img, callback=None)
    btn_quit = Button('ВЫХОД', (left_x, start_y + 2 * (btn_h + gap), btn_w, btn_h), base_font, image=exit_img, callback=on_quit)

    buttons = [btn_play, btn_credits, btn_quit]

    # Main loop
    running = True
    while running:
        if state['current'] == 'menu':
            # Menu state
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    running = False
                for b in buttons:
                    b.handle_event(ev)
            
            if state['current'] != 'menu':
                # State changed (e.g., to game), don't render menu
                continue

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
            # After game ends, return to menu
            state['current'] = 'menu'
        
        elif state['current'] == 'quit':
            running = False

    pygame.quit()



if __name__ == '__main__':
    main()

