import pygame
import os
import sys
import subprocess
import traceback
import json

pygame.init()

#색 정의 
WHITE = (255,255,255)
GRAY = (100,100,100)
LIGHT_GRAY = (200,200,200)
HIGHLIGHT = (255,200,0)


# 간단한 Button 기본 클래스 (UI용)
class Button:
    def __init__(self, screen, rect, label, font, bg=(60,60,60), fg=(255,255,255), hover_bg=(100,100,100), callback=None):
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
        pygame.draw.rect(self.screen, (200,200,200), self.rect, 2)
        if self.label:
            surf = self.font.render(self.label, True, self.fg)
            pos = (self.rect.x + (self.rect.w - surf.get_width())//2, self.rect.y + (self.rect.h - surf.get_height())//2)
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
        super().__init__(screen, (0,0,0,0), "", pygame.font.SysFont('malgungothic', 20))
        self.WIDTH = width
        self.HEIGHT = height
        pygame.display.set_caption('맵 선택창')

        # 색상
        self.WHITE = (255,255,255)
        self.GRAY = (100,100,100)
        self.LIGHT_GRAY = (200,200,200)
        self.HIGHLIGHT = (255,200,0)

        # 경로
        self.BASE_DIR = os.path.dirname(__file__)
        self.IMG_DIR = os.path.join(self.BASE_DIR, "picture")
        self.MAP_DIR = os.path.join(self.BASE_DIR, "map")

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
        self.back_button = Button(self.screen, back_rect, "뒤로가기", self.font, bg=(50,50,50), hover_bg=(80,80,80), callback=self.on_back)

        # 상태 (menu / level)
        self.state = 'menu'
        self.current_level = None
        self.level_data = None
        self.level_lines = []
        # 맵 렌더링 관련
        self.map_tiles = None
        self.map_w = 0
        self.map_h = 0
        self.tile_size = 0
        self.map_offset = (0, 0)
        # 레벨 오브젝트
        self.player = None            # {'x':int, 'y':int}
        self.entities = []            # [{'type':str,'x':int,'y':int}, ...]
        self.collected_items = 0
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

    def launch_command(self, cmd):
        # 기존 외부 실행용 함수는 유지 (하지만 JSON은 내부 로드로 변경됨)
        if not cmd:
            print("실행할 명령이 비어있음.")
            return
        try:
            path = cmd if os.path.isabs(cmd) else os.path.join(self.MAP_DIR, cmd)
            if not os.path.exists(path):
                print("파일 없음:", path)
                return
            ext = os.path.splitext(path)[1].lower()
            # JSON 파일은 OS 기본 애플리케이션으로 열기 (호환용, 내부 로드가 우선이면 사용 안함)
            if ext == '.json':
                if os.name == 'nt':
                    os.startfile(path)
                elif sys.platform == "darwin":
                    subprocess.Popen(['open', path])
                else:
                    subprocess.Popen(['xdg-open', path])
                print("열기:", path)
                return
            # 그 외 파일은 기존 방식으로 실행/오픈 시도
            if os.name == 'nt':
                creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
                if isinstance(cmd, str):
                    subprocess.Popen(cmd, shell=False, creationflags=creationflags)
                else:
                    subprocess.Popen(cmd, creationflags=creationflags)
            else:
                subprocess.Popen(cmd, shell=True)
            print("실행:", cmd)
        except Exception as e:
            print("명령 실행 실패:", cmd, e)

    def load_level(self, filename):
        # JSON 파일을 읽어 레벨 데이터로 로드하고 상태 전환
        if not filename:
            print("load_level: filename 빈값")
            return
        path = filename if os.path.isabs(filename) else os.path.join(self.MAP_DIR, filename)
        print("load_level 호출 ->", {"filename": filename, "MAP_DIR": self.MAP_DIR, "path": path, "exists": os.path.exists(path)})
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
            # 우선 "tiles" 키가 있는지 확인 — 2D 리스트(행렬)로 해석
            tiles = None
            if isinstance(data, dict) and 'tiles' in data and isinstance(data['tiles'], list):
                tiles = data['tiles']
            # 어떤 경우엔 data 자체가 2D 리스트일 수 있음
            if tiles is None and isinstance(data, list) and len(data) and isinstance(data[0], list):
                tiles = data
            if tiles:
                # 보장: tiles는 리스트(행) of 리스트(열)
                self.map_tiles = [list(row) for row in tiles]  # 복사
                self.map_h = len(self.map_tiles)
                self.map_w = max((len(r) for r in self.map_tiles), default=0)
                # 엔티티 초기화
                self.entities = []
                self.player = None
                self.collected_items = 0
                # tiles 내에 플레이어(5) 또는 아이템(2) 표기 있으면 엔티티로 변환
                for ry, row in enumerate(self.map_tiles):
                    for rx, val in enumerate(row):
                        if val == 5 and self.player is None:
                            self.player = {'x': rx, 'y': ry}
                            self.map_tiles[ry][rx] = 0
                        elif val == 2:
                            self.entities.append({'type': 'item', 'x': rx, 'y': ry})
                            self.map_tiles[ry][rx] = 0
                        elif val == 4:
                            self.entities.append({'type': 'enemy', 'x': rx, 'y': ry})
                            self.map_tiles[ry][rx] = 0
                # 타일 크기 계산: 화면에 맞춰 최대한 키움
                avail_w = self.WIDTH - self.PADDING * 2
                avail_h = self.HEIGHT - 140  # 상단 UI 공간 확보
                if self.map_w > 0 and self.map_h > 0:
                    self.tile_size = max(4, min(avail_w // self.map_w, avail_h // self.map_h))
                else:
                    self.tile_size = 16
                map_px_w = self.tile_size * self.map_w
                map_px_h = self.tile_size * self.map_h
                self.map_offset = ((self.WIDTH - map_px_w) // 2, 120 + (avail_h - map_px_h)//2)
                # 플래그 상태 전환
                self.state = 'level'
                # 간단한 pretty text도 준비(디버그용)
                pretty = json.dumps(data, ensure_ascii=False, indent=2)
                self.level_lines = pretty.splitlines()[:200]
                print("레벨(맵) 로드됨:", path, "size:", self.map_w, "x", self.map_h, "player:", self.player, "entities:", len(self.entities))
                return
            # tiles 없으면 텍스트 보기로 폴백
            print("tiles 키/형식 없음 — 오브젝트 좌표 추출 시도")
            # 재귀적으로 (x,y) 또는 pos를 찾아 엔티티 목록 생성
            found_positions = []
            def extract_positions(obj, hint=None):
                if isinstance(obj, dict):
                    # 명시적 x,y
                    if 'x' in obj and 'y' in obj and isinstance(obj['x'], (int,float)) and isinstance(obj['y'], (int,float)):
                        t = obj.get('type') or hint or 'obj'
                        # 메타(색상 등)를 함께 저장
                        found_positions.append({'type': t, 'x': int(obj['x']), 'y': int(obj['y']), 'meta': dict(obj)})
                        return
                    # pos: [x,y]
                    if 'pos' in obj and isinstance(obj['pos'], (list,tuple)) and len(obj['pos'])>=2:
                        px,py = obj['pos'][0], obj['pos'][1]
                        if isinstance(px,(int,float)) and isinstance(py,(int,float)):
                            t = obj.get('type') or hint or 'obj'
                            found_positions.append({'type': t, 'x': int(px), 'y': int(py), 'meta': dict(obj)})
                            return
                    # 키별 재귀
                    for k,v in obj.items():
                        extract_positions(v, k)
                elif isinstance(obj, list):
                    for item in obj:
                        extract_positions(item, hint)

            extract_positions(data)
            if found_positions:
                # 경계 계산
                xs = [p['x'] for p in found_positions]
                ys = [p['y'] for p in found_positions]
                minx, maxx = min(xs), max(xs)
                miny, maxy = min(ys), max(ys)
                pad = 1
                width = maxx - minx + 1 + pad*2
                height = maxy - miny + 1 + pad*2
                # 빈 타일 그리드 생성
                self.map_w = max(1, width)
                self.map_h = max(1, height)
                self.map_tiles = [[0 for _ in range(self.map_w)] for __ in range(self.map_h)]
                # 엔티티로 변환 (좌표 보정)
                self.entities = []
                self.player = None
                for p in found_positions:
                    gx = p['x'] - minx + pad
                    gy = p['y'] - miny + pad
                    t = p.get('type','obj')
                    # 간단한 타입 매핑
                    if isinstance(t, str):
                        low = t.lower()
                        meta = p.get('meta', {}) if isinstance(p.get('meta', {}), dict) else {}
                        color = meta.get('color')
                        if 'player' in low or 'start' in low:
                            self.player = {'x': gx, 'y': gy}
                        elif 'item' in low or 'emit' in low or 'target' in low:
                            self.entities.append({'type':'item','x':gx,'y':gy, 'color': color})
                        elif 'enemy' in low or 'mirror' in low or 'prism' in low:
                            self.entities.append({'type':'enemy','x':gx,'y':gy, 'color': color})
                        else:
                            # 기타는 아이템으로 표시
                            self.entities.append({'type':'item','x':gx,'y':gy, 'color': color})
                    else:
                        self.entities.append({'type':'item','x':gx,'y':gy, 'color': None})
                # 타일 크기 계산 및 오프셋
                avail_w = self.WIDTH - self.PADDING * 2
                avail_h = self.HEIGHT - 140
                self.tile_size = max(4, min(avail_w // self.map_w, avail_h // self.map_h))
                map_px_w = self.tile_size * self.map_w
                map_px_h = self.tile_size * self.map_h
                self.map_offset = ((self.WIDTH - map_px_w) // 2, 120 + (avail_h - map_px_h)//2)
                self.collected_items = 0
                self.state = 'level'
                print("오브젝트 기반 맵 생성: size", self.map_w, "x", self.map_h, "entities", len(self.entities), "player", bool(self.player))
                return
            # 못 찾으면 기존 텍스트 폴백
            print("좌표 정보 미발견 — 텍스트 폴백으로 전환")
            pretty = json.dumps(data, ensure_ascii=False, indent=2)
            self.level_lines = pretty.splitlines()[:200]
            self.map_tiles = None
            self.state = 'level'
            print("레벨(텍스트) 로드됨:", path)
        except Exception as e:
            print("레벨 로드 실패:", path, e)
            traceback.print_exc()

    def on_back(self):
        # 뒤로가기 동작: 메뉴에서는 창 종료, 레벨에서는 메뉴로 복귀
        if self.state == 'menu':
            print("뒤로가기(종료) 클릭됨")
            self.running = False
        else:
            print("레벨에서 뒤로가기 -> 메뉴로")
            self.state = 'menu'
            self.current_level = None
            self.level_data = None
            self.level_lines = []

    def draw(self):
        self.screen.fill((20, 20, 20))
        if self.state == 'menu':
            title_surf = self.font.render("", True, self.WHITE)
            self.screen.blit(title_surf, (self.PADDING, 56))  # 뒤로가기 버튼과 겹치지 않도록 아래로 이동

            mx, my = pygame.mouse.get_pos()
            for i, (fname, thumb) in enumerate(self.thumbnails):
                rect = self._get_tile_rect(i)
                # 썸네일을 슬롯 크기에 맞춰 그리기
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
        else:
            # 레벨 화면: JSON에 tiles가 있으면 맵 렌더, 없으면 텍스트 표시
            title = self.current_level if self.current_level else "Level"
            title_surf = self.font.render(title, True, self.WHITE)
            self.screen.blit(title_surf, (self.PADDING, 56))
 
            if self.map_tiles:
                ox, oy = self.map_offset
                # 기본 팔레트: 타일 id -> 색
                palette = {
                    0: (30, 30, 30),      # 빈
                    1: (120, 120, 120),   # 벽
                    2: (200, 180, 80),    # 바닥(원래 아이템 표시는 엔티티로 분리됨)
                    3: (80, 160, 220),    # 물
                    4: (200, 80, 80),     # 적(엔티티로 분리)
                }
                # 타일 그리기
                for ry, row in enumerate(self.map_tiles):
                    for rx in range(self.map_w):
                        try:
                            val = row[rx] if rx < len(row) else 0
                        except Exception:
                            val = 0
                        color = palette.get(val, (50, 50, 50))
                        r = pygame.Rect(ox + rx * self.tile_size, oy + ry * self.tile_size, self.tile_size, self.tile_size)
                        pygame.draw.rect(self.screen, color, r)
                        pygame.draw.rect(self.screen, (40,40,40), r, 1)
                # 엔티티 그리기 (아이템/적)
                def name_to_rgb(name):
                    if not name:
                        return None
                    n = str(name).strip().lower()
                    m = {
                        'white': (255,255,255), 'black': (0,0,0), 'red': (200,50,50),
                        'green': (80,200,120), 'blue': (80,160,220), 'yellow': (230,200,60),
                        'cyan': (80,200,200), 'magenta': (200,80,180), 'orange': (255,160,60),
                        'gray': (150,150,150)
                    }
                    if n in m:
                        return m[n]
                    # hex like #RRGGBB
                    if n.startswith('#') and len(n) == 7:
                        try:
                            r = int(n[1:3],16); g = int(n[3:5],16); b = int(n[5:7],16)
                            return (r,g,b)
                        except Exception:
                            return None
                    return None

                for ent in self.entities:
                    ex = ox + ent['x'] * self.tile_size
                    ey = oy + ent['y'] * self.tile_size
                    size = max(6, self.tile_size - 6)
                    er = pygame.Rect(ex + (self.tile_size - size)//2, ey + (self.tile_size - size)//2, size, size)
                    ent_color = name_to_rgb(ent.get('color')) or ((230,200,60) if ent['type']=='item' else (200,80,80))
                    if ent['type'] == 'item':
                        pygame.draw.ellipse(self.screen, ent_color, er)
                        pygame.draw.ellipse(self.screen, (120,100,20), er, 2)
                    elif ent['type'] == 'enemy':
                        pygame.draw.rect(self.screen, ent_color, er)
                        pygame.draw.rect(self.screen, (120,20,20), er, 2)
                    else:
                        pygame.draw.circle(self.screen, ent_color, er.center, size//2)
                    # 작은 라벨 표시 (타입 대신 원래 키가 있으면 meta에서 표시 가능)
                    try:
                        lbl_txt = ent.get('type','')
                        lbl = self.font.render(lbl_txt, True, (240,240,240))
                        self.screen.blit(lbl, (ex, ey))
                    except Exception:
                        pass
                # 플레이어 그리기
                if self.player:
                    px = ox + self.player['x'] * self.tile_size
                    py = oy + self.player['y'] * self.tile_size
                    cx = px + self.tile_size//2
                    cy = py + self.tile_size//2
                    l = max(6, self.tile_size//2)
                    pygame.draw.line(self.screen, (80,200,120), (cx-l, cy), (cx+l, cy), 3)
                    pygame.draw.line(self.screen, (80,200,120), (cx, cy-l), (cx, cy+l), 3)
                    try:
                        pl = self.font.render("PLAYER", True, (200,255,220))
                        self.screen.blit(pl, (px, py - pl.get_height()))
                    except Exception:
                        pass
                # HUD: 수집한 아이템 수
                hud = f"Items: {self.collected_items}"
                hud_s = self.font.render(hud, True, (220,220,220))
                self.screen.blit(hud_s, (self.PADDING, 92))
            else:
                # JSON 텍스트 출력 (스크롤 기능은 간단화)
                start_y = 110
                line_h = self.font.get_linesize()
                max_lines = (self.HEIGHT - start_y - 40) // line_h
                for idx, line in enumerate(self.level_lines[:max_lines]):
                    try:
                        surf = self.font.render(line, True, self.WHITE)
                    except Exception:
                        surf = self.font.render(line[:200], True, self.WHITE)
                    self.screen.blit(surf, (self.PADDING, start_y + idx * line_h))

        # 뒤로가기 버튼 그리기 (항상 표시)
        self.back_button.draw()

        hint = "ESC: 종료"
        hint_surf = self.font.render(hint, True, (180,180,180))
        self.screen.blit(hint_surf, (self.WIDTH - hint_surf.get_width() - self.PADDING, self.HEIGHT - 30))
        pygame.display.flip()

    def run(self):
        while self.running:
            try:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    elif event.type == pygame.KEYDOWN:
                        # 레벨 상태면 ESC는 메뉴로 복귀, 메뉴 상태면 종료
                        if event.key == pygame.K_ESCAPE:
                            if self.state == 'level':
                                self.on_back()
                            else:
                                self.running = False
                        # 플레이어 이동: 화살표 / WASD
                        if self.state == 'level' and self.player:
                            if event.key in (pygame.K_LEFT, pygame.K_a):
                                self._move_player(-1, 0)
                            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                                self._move_player(1, 0)
                            elif event.key in (pygame.K_UP, pygame.K_w):
                                self._move_player(0, -1)
                            elif event.key in (pygame.K_DOWN, pygame.K_s):
                                self._move_player(0, 1)
                    # 버튼 이벤트 처리
                    self.back_button.handle_event(event)
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        mx, my = event.pos
                        if self.state == 'menu':
                            for i in range(self.MAP_COUNT):
                                rect = self._get_tile_rect(i)
                                if rect.collidepoint((mx, my)):
                                    print("선택된 맵 인덱스:", i, "파일:", self.thumbnails[i][0], "명령:", self.commands[i])
                                    # JSON 파일은 내부 로드로 처리
                                    self.load_level(self.commands[i])
                                    break
                        else:
                            # 레벨 내부에서 추가 클릭 동작을 원하면 여기에 구현
                            pass
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
    # 플레이어 이동 처리 (타일 충돌, 아이템 수집)
    def _move_player(self, dx, dy):
        if not self.player or not self.map_tiles:
            return
        nx = self.player['x'] + dx
        ny = self.player['y'] + dy
        if nx < 0 or ny < 0 or ny >= self.map_h or nx >= self.map_w:
            return
        # 벽(1) 충돌 검사
        try:
            target = self.map_tiles[ny][nx] if nx < len(self.map_tiles[ny]) else 0
        except Exception:
            target = 0
        if target == 1:
            return
        # 이동 처리
        self.player['x'] = nx
        self.player['y'] = ny
        # 아이템과 충돌 검사: 엔티티 리스트에서 item을 제거하면 수집
        for i, ent in enumerate(self.entities):
            if ent['x'] == nx and ent['y'] == ny and ent['type'] == 'item':
                del self.entities[i]
                self.collected_items += 1
                print("아이템 획득, 총:", self.collected_items)
                break

if __name__ == "__main__":
    selector = MapSelector()
    selector.run()
