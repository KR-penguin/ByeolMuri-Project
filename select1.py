import pygame
import os
import sys
import subprocess
import traceback
import json

pygame.init()

# 색 정의 
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)
LIGHT_GRAY = (200, 200, 200)
HIGHLIGHT = (255, 200, 0)


# 간단한 Button 기본 클래스 (UI용)
class Button:
    def __init__(self, screen, rect, label, font, bg=(60, 60, 60), fg=(255, 255, 255), hover_bg=(100, 100, 100), callback=None):
        self.screen = screen
        self.rect = pygame.Rect(rect)
        self.label = label
        self.font = font
        self.bg = bg
        self.fg = fg
        self.hover_bg = hover_bg
        self.callback = callback
        self.hover = False

    def draw(self):
        color = self.hover_bg if self.hover else self.bg
        pygame.draw.rect(self.screen, color, self.rect)
        pygame.draw.rect(self.screen, (200, 200, 200), self.rect, 2)
        if self.label:
            surf = self.font.render(self.label, True, self.fg)
            pos = (self.rect.x + (self.rect.w - surf.get_width()) // 2, 
                   self.rect.y + (self.rect.h - surf.get_height()) // 2)
            self.screen.blit(surf, pos)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if callable(self.callback):
                    try:
                        self.callback()
                    except Exception:
                        traceback.print_exc()
                return True
        return False


# MapSelector는 Button을 상속받아 기본 UI 속성(화면/폰트 등)을 공유하도록 함
class MapSelector(Button):
    def __init__(self, width=1280, height=720):
        # 임시 rect, label로 Button 초기화 (MapSelector는 전체 UI 담당)
        screen = pygame.display.set_mode((width, height))
        super().__init__(screen, (0, 0, 0, 0), "", pygame.font.SysFont('malgungothic', 20))
        self.WIDTH = width
        self.HEIGHT = height
        pygame.display.set_caption('맵 선택창')

        # 색상
        self.WHITE = (255, 255, 255)
        self.GRAY = (100, 100, 100)
        self.LIGHT_GRAY = (200, 200, 200)
        self.HIGHLIGHT = (255, 200, 0)

        # 경로
        self.BASE_DIR = os.path.dirname(__file__)
        self.IMG_DIR = os.path.join(self.BASE_DIR, "picture")
        self.MAP_DIR = self.BASE_DIR

        # 그리드
        self.MAP_COUNT = 8
        self.COLS = 4
        self.ROWS = 2
        self.PADDING = 20
        self.MARGIN_TOP = 10
        self.LABEL_HEIGHT = 28

        # 슬롯 크기 계산
        usable_w = self.WIDTH - self.PADDING * (self.COLS + 1)
        usable_h = self.HEIGHT - self.MARGIN_TOP - self.PADDING * (self.ROWS + 1) - self.LABEL_HEIGHT
        self.TILE_W = usable_w // self.COLS
        self.TILE_H = usable_h // self.ROWS

        self.SLOT_SCALE = 0.75
        self.SLOT_W = int(self.TILE_W * self.SLOT_SCALE)
        self.SLOT_H = int(self.TILE_H * self.SLOT_SCALE)

        # 라벨·명령: Level 0 ~ Level 7, 파일은 level_0.json ~ level_7.json
        self.map_labels = [f"Level {i}" for i in range(0, self.MAP_COUNT)]
        self.commands = [f"level_{i}.json" for i in range(0, self.MAP_COUNT)]
        self.commands = (self.commands + [""] * self.MAP_COUNT)[:self.MAP_COUNT]

        # 이미지/섬네일
        self.image_files = self._get_image_files()
        self.image_files = (self.image_files + [""] * self.MAP_COUNT)[:self.MAP_COUNT]
        self.thumbnails = self._load_thumbnails()

        # 뒤로가기 버튼 (좌상단) — 동작은 상태에 따라 분기
        back_rect = (10, 10, 120, 36)
        self.back_button = Button(self.screen, back_rect, "뒤로가기", self.font, 
                                   bg=(50, 50, 50), hover_bg=(80, 80, 80), callback=self.on_back)

        # 상태 (menu / level)
        self.state = 'menu'
        self.current_level = None
        self.level_data = None
        self.level_lines = []
        
        # 상태
        self.clock = pygame.time.Clock()
        self.running = True

    def _get_image_files(self):
        exts = {'.png', '.jpg', '.jpeg', '.bmp', '.gif'}
        if not os.path.isdir(self.IMG_DIR):
            return []
        files = [f for f in sorted(os.listdir(self.IMG_DIR)) if os.path.splitext(f)[1].lower() in exts]
        return files

    def _load_thumbnails(self):
        thumbs = []
        for fname in self.image_files:
            if fname:
                path = os.path.join(self.IMG_DIR, fname)
                try:
                    img = pygame.image.load(path).convert_alpha()
                    thumb = pygame.transform.smoothscale(img, (self.TILE_W, self.TILE_H))
                    thumbs.append((fname, thumb))
                except Exception as e:
                    print("이미지 로드 실패:", path, e)
                    surf = pygame.Surface((self.TILE_W, self.TILE_H))
                    surf.fill(self.GRAY)
                    thumbs.append((fname, surf))
            else:
                surf = pygame.Surface((self.TILE_W, self.TILE_H))
                surf.fill(self.GRAY)
                thumbs.append((fname, surf))
        return thumbs

    def _get_tile_rect(self, index):
        col = index % self.COLS
        row = index // self.COLS
        cell_x = self.PADDING + col * (self.TILE_W + self.PADDING)
        cell_y = self.MARGIN_TOP + self.PADDING + row * (self.TILE_H + self.PADDING)
        x = cell_x + (self.TILE_W - self.SLOT_W) // 2
        y = cell_y + (self.TILE_H - self.SLOT_H) // 2
        return pygame.Rect(x, y, self.SLOT_W, self.SLOT_H)

    def on_back(self):
        """뒤로가기 동작: 메뉴에서는 창 종료, 레벨에서는 메뉴로 복귀"""
        if self.state == 'menu':
            print("뒤로가기(종료) 클릭됨")
            self.running = False
        else:
            print("레벨에서 뒤로가기 -> 메뉴로")
            self.state = 'menu'
            self.current_level = None
            self.level_data = None
            self.level_lines = []

    def launch_game(self):
        """로드된 레벨 데이터를 게임 프로그램으로 전달하여 실행"""
        if not self.current_level:
            print("레벨이 로드되지 않았습니다.")
            return
        
        try:
            # 게임 프로그램 경로
            game_script = os.path.join(self.BASE_DIR, "level_play.py")
            
            if not os.path.exists(game_script):
                print(f"게임 파일을 찾을 수 없습니다: {game_script}")
                return
            
            # 레벨 파일 경로
            level_path = os.path.join(self.MAP_DIR, self.current_level)
            
            if not os.path.exists(level_path):
                print(f"레벨 파일을 찾을 수 없습니다: {level_path}")
                return
            
            # 게임 프로그램 실행
            print(f"게임 실행 시도: {game_script}")
            print(f"레벨 파일: {level_path}")
            
            if os.name == 'nt':  # Windows
                subprocess.Popen(['python', game_script, level_path])
            else:  # Mac/Linux
                subprocess.Popen(['python3', game_script, level_path])
            
            print(f"✅ 게임 실행 완료: {self.current_level}")
            
        except Exception as e:
            print(f"❌ 게임 실행 실패: {e}")
            traceback.print_exc()

    def load_level(self, filename):
        """JSON 파일을 읽어 레벨 데이터로 로드하고 게임 실행"""
        if not filename:
            print("load_level: filename 빈값")
            return
        
        path = filename if os.path.isabs(filename) else os.path.join(self.MAP_DIR, filename)
        print("load_level 호출 ->", {"filename": filename, "MAP_DIR": self.MAP_DIR, 
                                      "path": path, "exists": os.path.exists(path)})
        
        if not os.path.exists(path):
            print("레벨 파일이 존재하지 않음:", path)
            return
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print("JSON 로드 완료. 타입:", type(data).__name__)
            if isinstance(data, dict):
                print("JSON 키:", list(data.keys())[:10])
            
            self.current_level = os.path.basename(filename)
            self.level_data = data
         
            
            print("레벨 데이터 로드 완료:", path)
            
            # ✅ 게임 실행
            self.launch_game()
            
        except Exception as e:
            print("레벨 로드 실패:", path, e)
            traceback.print_exc()

    def draw(self):
        self.screen.fill((20, 20, 20))
        
        if self.state == 'menu':
            title_surf = self.font.render("", True, self.WHITE)
            self.screen.blit(title_surf, (self.PADDING, 56))

            mx, my = pygame.mouse.get_pos()
            for i, (fname, thumb) in enumerate(self.thumbnails):
                rect = self._get_tile_rect(i)
                
                # 썸네일 그리기
                if thumb:
                    try:
                        scaled = pygame.transform.smoothscale(thumb, (rect.w, rect.h))
                        self.screen.blit(scaled, scaled.get_rect(center=rect.center))
                    except Exception:
                        self.screen.blit(thumb, thumb.get_rect(center=rect.center))
                else:
                    surf = pygame.Surface((rect.w, rect.h))
                    surf.fill(self.GRAY)
                    self.screen.blit(surf, surf.get_rect(center=rect.center))

                # 테두리
                if rect.collidepoint((mx, my)):
                    pygame.draw.rect(self.screen, self.HIGHLIGHT, rect, 4)
                else:
                    pygame.draw.rect(self.screen, self.LIGHT_GRAY, rect, 2)

                # 라벨
                label = fname if fname else self.map_labels[i]
                label_surf = self.font.render(label, True, self.WHITE)
                label_pos = (rect.x + (rect.w - label_surf.get_width()) // 2, rect.y + rect.h + 4)
                self.screen.blit(label_surf, label_pos)

        # 뒤로가기 버튼 그리기 (항상 표시)
        self.back_button.draw()

        hint = "ESC: 종료"
        hint_surf = self.font.render(hint, True, (180, 180, 180))
        self.screen.blit(hint_surf, (self.WIDTH - hint_surf.get_width() - self.PADDING, self.HEIGHT - 30))
        pygame.display.flip()

    def run(self):
        while self.running:
            try:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            if self.state == 'level':
                                self.on_back()
                            else:
                                self.running = False
                    
                    # 버튼 이벤트 처리
                    self.back_button.handle_event(event)
                    
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        mx, my = event.pos
                        if self.state == 'menu':
                            for i in range(self.MAP_COUNT):
                                rect = self._get_tile_rect(i)
                                if rect.collidepoint((mx, my)):
                                    print("선택된 맵 인덱스:", i, "파일:", self.thumbnails[i][0], 
                                          "명령:", self.commands[i])
                                    # JSON 파일은 내부 로드로 처리
                                    self.load_level(self.commands[i])
                                    break
                
                self.draw()
                self.clock.tick(60)
            except Exception:
                traceback.print_exc()
                self.running = False
        
        pygame.quit()
        try:
            sys.exit(0)
        except SystemExit:
            pass


if __name__ == "__main__":
    selector = MapSelector()
    selector.run()