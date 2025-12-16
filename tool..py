import pygame
import math
import json

# 모듈 임포트
from objects import (Button, Emitter, Target, Mirror, Lens, Blackhole, Portal,
                     COLORS, RADIUS)
from utils import near, angle_wrap, vec_from_angle, advance, refract_angle, N_AIR

# --- 기본 설정 ---
WIDTH, HEIGHT = 1000, 700
FPS = 60

# 그리드 설정
GRID_SIZE = 25  # 그리드 한 칸의 크기 (작을수록 그리드 개수 증가)
GRID_OFFSET_X = 50  # 그리드 시작 X 위치
GRID_OFFSET_Y = 300  # 그리드 시작 Y 위치 (버튼 아래)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Light Puzzle - Map Editor")
clock = pygame.time.Clock()
FONT = pygame.font.SysFont("Malgun Gothic", 22)
FONT_BIG = pygame.font.SysFont("Malgun Gothic", 28)

# --- 그리드 함수 ---
def snap_to_grid(x, y):
    """마우스 좌표를 가장 가까운 그리드 중심으로 스냅"""
    grid_x = round((x - GRID_OFFSET_X) / GRID_SIZE) * GRID_SIZE + GRID_OFFSET_X
    grid_y = round((y - GRID_OFFSET_Y) / GRID_SIZE) * GRID_SIZE + GRID_OFFSET_Y
    return grid_x, grid_y

def draw_grid(surface):
    """그리드 그리기"""
    grid_color = (50, 50, 50)
    # 수직선
    x = GRID_OFFSET_X
    while x < WIDTH:
        pygame.draw.line(surface, grid_color, (x, GRID_OFFSET_Y), (x, HEIGHT), 1)
        x += GRID_SIZE
    # 수평선
    y = GRID_OFFSET_Y
    while y < HEIGHT:
        pygame.draw.line(surface, grid_color, (GRID_OFFSET_X, y), (WIDTH, y), 1)
        y += GRID_SIZE

# --- 오브젝트 리스트 ---
emitters, targets, mirrors, lenses, blackholes = [], [], [], [], []
portals_a, portals_b = [], []  # 포탈 A(입구), B(출구)

# --- 모드/상태 ---
object_mode = None  # 'emitter'|'target'|'mirror'|'lens'|'blackhole'|'portal_a'|'portal_b'|'eraser'
game_started = False
input_mode = None  # 'save' | 'load' | None
input_text = ""    # 입력 중인 맵 번호

# --- 버튼들 ---
btn_start     = Button( 20, 20, 120, 40, "게임 시작")
btn_emitter   = Button(160, 20, 120, 40, "W 발사")
btn_target    = Button(300, 20, 120, 40, "W 목표")
btn_mirror    = Button(440, 20, 120, 40, "거울")
btn_lens      = Button(580, 20, 120, 40, "렌즈")
btn_blackhole = Button(720, 20, 120, 40, "블랙홀")

btn_eraser = Button( 20, 70, 120, 40, "지우개")
btn_stop   = Button(160, 70, 120, 40, "중단")
btn_clear  = Button(300, 70, 120, 40, "클리어")
btn_save   = Button(440, 70, 120, 40, "맵 저장")
btn_load   = Button(580, 70, 120, 40, "맵 불러오기")

# 포탈 버튼 (3번째 줄)
btn_portal_a = Button( 20, 120, 80, 40, "포탈 A")
btn_portal_b = Button(110, 120, 80, 40, "포탈 B")

buttons = [btn_start, btn_emitter, btn_target, btn_mirror, btn_lens, btn_blackhole,
           btn_eraser, btn_stop, btn_clear, btn_save, btn_load,
           btn_portal_a, btn_portal_b]

# --- 저장/불러오기 ---
def save_map(map_index):
    """
    맵을 JSON 파일로 저장 (인덱스별)
    모든 오브젝트 포함 (발사장치, 목표지점, 거울, 렌즈, 프리즘, 블랙홀)
    """
    level_data = {
        "map_index": map_index,
        "emitters": [{"x":e.x, "y":e.y, "color":e.color, "angle":e.angle} for e in emitters],
        "targets": [{"x":t.x, "y":t.y, "color":t.color} for t in targets],
        "mirrors": [{"x":m.x, "y":m.y, "angle":m.angle} for m in mirrors],
        "lenses": [{"x":l.x, "y":l.y, "angle":l.angle} for l in lenses],
        "portals_a": [{"x":p.x, "y":p.y} for p in portals_a],
        "portals_b": [{"x":p.x, "y":p.y} for p in portals_b],
        "blackholes": [{"x":b.x, "y":b.y} for b in blackholes],
    }
    filename = f"level_{map_index}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(level_data, f, ensure_ascii=False, indent=2)
    print(f"맵 저장 완료: {filename}")

def load_map(map_index):
    """
    JSON 파일에서 맵 불러오기 (인덱스별)
    모든 오브젝트 불러오기 (발사장치, 목표지점, 거울, 렌즈, 포탈, 블랙홀)
    """
    global emitters, targets, mirrors, lenses, portals_a, portals_b, blackholes
    try:
        filename = f"level_{map_index}.json"
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # 모든 오브젝트 초기화
        emitters.clear()
        targets.clear()
        mirrors.clear()
        lenses.clear()
        portals_a.clear()
        portals_b.clear()
        blackholes.clear()

        for e in data.get("emitters", []):
            emitters.append(Emitter(e["x"], e["y"], e.get("color","white"), e.get("angle",0)))
        for t in data.get("targets", []):
            targets.append(Target(t["x"], t["y"], t.get("color","white")))
        for m in data.get("mirrors", []):
            mirrors.append(Mirror(m["x"], m["y"], m.get("angle",0)))
        for l in data.get("lenses", []):
            lenses.append(Lens(l["x"], l["y"], l.get("angle",0)))
        for p in data.get("portals_a", []):
            portals_a.append(Portal(p["x"], p["y"], 'A'))
        for p in data.get("portals_b", []):
            portals_b.append(Portal(p["x"], p["y"], 'B'))
        for b in data.get("blackholes", []):
            blackholes.append(Blackhole(b["x"], b["y"]))
        
        print(f"맵 불러오기 완료: {filename}")
        print(f"오브젝트: 발사장치 {len(emitters)}개, 목표지점 {len(targets)}개, "
              f"거울 {len(mirrors)}개, 렌즈 {len(lenses)}개, 포탈A {len(portals_a)}개, 포탈B {len(portals_b)}개, 블랙홀 {len(blackholes)}개")
    except FileNotFoundError:
        print(f"[로드 실패] 파일을 찾을 수 없습니다: {filename}")
    except Exception as e:
        print(f"[로드 실패] {e}")

def simulate_light(surface):
    """
    빛의 경로를 시뮬레이션하고 화면에 그림
    - 렌즈: 45도 꺾기
    - 거울: 반사
    - 블랙홀: 흡수
    """
    MAX_STEPS = 20000  # 빛 최대 이동 스텝 (그리드 증가에 맞춰 늘림)
    MAX_BOUNCES = 64
    NUDGE = 2.0

    # 모든 목표지점 초기화
    for t in targets:
        t.hit = False

    # 흰색 발사장치만 처리
    all_emitters = list(emitters)
    
    for emitter in all_emitters:
        # 큐 요소: (x, y, angle, color, inside_lenses:set, bounces)
        ray_queue = [ (emitter.x, emitter.y, emitter.angle, emitter.color, set(), 0) ]

        while ray_queue:
            x, y, angle, color_name, inside_lenses, bounces = ray_queue.pop(0)
            steps = 0

            while steps < MAX_STEPS:
                steps += 1
                x += math.cos(math.radians(angle))
                y += math.sin(math.radians(angle))

                if not (0 <= x < WIDTH and 0 <= y < HEIGHT):
                    break

                # 1) 거울 반사
                reflected = False
                for m in mirrors:
                    if near(x, y, m.x, m.y):
                        angle = angle_wrap(2 * m.angle - angle)
                        x, y = advance(x, y, angle, NUDGE)
                        bounces += 1
                        reflected = True
                        break
                if reflected:
                    if bounces > MAX_BOUNCES: break
                    pygame.draw.circle(surface, COLORS[color_name], (int(x), int(y)), 2)
                    # 반사 후에도 계속 진행 (렌즈 등 체크)
                
                # 화면 밖 체크를 먼저
                if not (0 <= x < WIDTH and 0 <= y < HEIGHT):
                    break

                # 2) 렌즈: 중심 통과 시 45도 꺾기
                bent = False
                for lz in lenses:
                    lid = id(lz)
                    # 중심과의 거리 체크 (매우 가까이 있을 때만)
                    dist = math.sqrt((x - lz.x)**2 + (y - lz.y)**2)
                    if dist < 3 and lid not in inside_lenses:  # 중심 3픽셀 이내
                        # 중심 통과 시 45도 꺾기
                        angle = angle_wrap(angle + 45)
                        inside_lenses.add(lid)
                        x, y = advance(x, y, angle, NUDGE)
                        bounces += 1
                        bent = True
                        break
                if bent:
                    if bounces > MAX_BOUNCES: break
                    pygame.draw.circle(surface, COLORS[color_name], (int(x), int(y)), 2)
                
                # 렌즈를 멀리 벗어났는지 체크
                for lz in lenses:
                    lid = id(lz)
                    if lid in inside_lenses:
                        dist = math.sqrt((x - lz.x)**2 + (y - lz.y)**2)
                        if dist > RADIUS * 2:  # 렌즈에서 충분히 멀어지면 초기화
                            inside_lenses.remove(lid)

                # 3) 포탈: A에 들어가면 B로 텔레포트
                teleported = False
                for pa in portals_a:
                    if near(x, y, pa.x, pa.y):
                        # 포탈 B가 있으면 텔레포트
                        if len(portals_b) > 0:
                            pb = portals_b[0]  # 첫 번째 B 포탈로 이동
                            x, y = pb.x, pb.y
                            x, y = advance(x, y, angle, NUDGE * 2)  # 포탈에서 빠져나옴
                            teleported = True
                            break
                if teleported:
                    pygame.draw.circle(surface, COLORS[color_name], (int(x), int(y)), 2)
                    continue

                # 4) 블랙홀
                absorbed = False
                for bh in blackholes:
                    if near(x, y, bh.x, bh.y):
                        absorbed = True
                        break
                if absorbed:
                    break

                # 4) 블랙홀
                absorbed = False
                for bh in blackholes:
                    if near(x, y, bh.x, bh.y):
                        absorbed = True
                        break
                if absorbed:
                    break

                # 5) 타겟 체크 - 흰색 빛이 흰색 목표에 닿으면 hit 처리하고 광선 종료
                # 흰색 목표 체크 (white 빛만)
                for tg in targets:
                    if near(x, y, tg.x, tg.y):
                        if color_name == 'white':  # 흰색 빛만 흰색 목표에 닿음
                            tg.hit = True
                            pygame.draw.circle(surface, (255, 255, 0), (int(tg.x), int(tg.y)), RADIUS+6, 3)
                            break
                else:
                    # 목표에 닿지 않았으면 계속 진행
                    # 6) 그리기
                    pygame.draw.circle(surface, COLORS[color_name], (int(x), int(y)), 2)
                    
                    if bounces > MAX_BOUNCES:
                        break
                    continue
                # 목표에 닿았으면 광선 종료
                break

def check_game_complete():
    """
    게임 완료 조건 체크: 모든 W 목표지점이 빛을 받았는지 확인
    모든 목표가 hit=True여야만 True 반환 (AND 조건)
    """
    # 목표지점이 하나도 없으면 미완료
    if len(targets) == 0:
        return False
    
    # 모든 W 목표가 빛을 받았는지 확인
    for t in targets:
        if not t.hit:
            return False  # 하나라도 안 받았으면 미완료
    
    # 모든 목표가 빛을 받았을 때만 True
    return True

def main():
    global object_mode, game_started, input_mode, input_text
    running = True

    info = [
        "좌클릭: 그리드에 오브젝트 배치 / 지우개는 근접 오브젝트 삭제",
        "마우스 휠: Emitter(상하좌우), 거울(대각선 4방향), 렌즈(자유 회전)",
        "렌즈: 중심 통과 시 45° 꺾기 | 목표: 모든 W,R,G,B 목표에 빛 도달",
    ]

    last_selected = None  # 각도 조절 대상

    while running:
        # 이벤트
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # 텍스트 입력 모드
            elif input_mode in ['save', 'load']:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:  # Enter 키
                        if input_text.isdigit():
                            map_num = int(input_text)
                            if input_mode == 'save':
                                save_map(map_num)
                            elif input_mode == 'load':
                                load_map(map_num)
                        input_mode = None
                        input_text = ""
                    elif event.key == pygame.K_ESCAPE:  # ESC 키
                        input_mode = None
                        input_text = ""
                    elif event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]
                    elif event.unicode.isdigit() and len(input_text) < 3:
                        input_text += event.unicode
                continue  # 입력 모드에서는 다른 이벤트 무시

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos

                # 버튼 처리
                if btn_start.is_clicked((mx, my)):
                    game_started = True;   continue
                if btn_stop.is_clicked((mx, my)):
                    game_started = False;  continue
                if btn_clear.is_clicked((mx, my)):
                    emitters.clear(); targets.clear(); mirrors.clear()
                    lenses.clear(); portals_a.clear(); portals_b.clear(); blackholes.clear()
                    game_started = False; object_mode = None; continue
                if btn_save.is_clicked((mx, my)):
                    input_mode = 'save'; input_text = ""; continue
                if btn_load.is_clicked((mx, my)):
                    input_mode = 'load'; input_text = ""; continue

                if btn_emitter.is_clicked((mx, my)):   object_mode = 'emitter';   continue
                if btn_target.is_clicked((mx, my)):    object_mode = 'target';    continue
                if btn_mirror.is_clicked((mx, my)):    object_mode = 'mirror';    continue
                if btn_lens.is_clicked((mx, my)):      object_mode = 'lens';      continue
                if btn_blackhole.is_clicked((mx, my)): object_mode = 'blackhole'; continue
                if btn_eraser.is_clicked((mx, my)):    object_mode = 'eraser';    continue
                
                # 포탈 버튼
                if btn_portal_a.is_clicked((mx, my)):  object_mode = 'portal_a';  continue
                if btn_portal_b.is_clicked((mx, my)):  object_mode = 'portal_b';  continue

                # 배치/삭제 (그리드에 스냅)
                gx, gy = snap_to_grid(mx, my)
                
                if object_mode == 'emitter':
                    # 발사 장치는 1개만 허용
                    if len(emitters) >= 1:
                        print("발사 장치는 1개만 배치할 수 있습니다. 기존 발사 장치를 먼저 삭제하세요.")
                    else:
                        obj = Emitter(gx, gy, 'white', 0); emitters.append(obj); last_selected = obj
                elif object_mode == 'target':
                    # 목표 지점은 1개만 허용
                    if len(targets) >= 1:
                        print("목표 지점은 1개만 배치할 수 있습니다. 기존 목표 지점을 먼저 삭제하세요.")
                    else:
                        obj = Target(gx, gy, 'white'); targets.append(obj); last_selected = obj
                elif object_mode == 'mirror':
                    obj = Mirror(gx, gy, 45); mirrors.append(obj); last_selected = obj
                elif object_mode == 'lens':
                    obj = Lens(gx, gy, 0); lenses.append(obj); last_selected = obj
                elif object_mode == 'blackhole':
                    obj = Blackhole(gx, gy); blackholes.append(obj); last_selected = obj
                elif object_mode == 'portal_a':
                    # 포탈 A는 1개만 허용
                    if len(portals_a) >= 1:
                        print("포탈 A는 1개만 배치할 수 있습니다. 기존 포탈 A를 먼저 삭제하세요.")
                    else:
                        obj = Portal(gx, gy, 'A'); portals_a.append(obj); last_selected = obj
                elif object_mode == 'portal_b':
                    # 포탈 B는 1개만 허용
                    if len(portals_b) >= 1:
                        print("포탈 B는 1개만 배치할 수 있습니다. 기존 포탈 B를 먼저 삭제하세요.")
                    else:
                        obj = Portal(gx, gy, 'B'); portals_b.append(obj); last_selected = obj
                elif object_mode == 'eraser':
                    for lst in [emitters, targets, mirrors, lenses, portals_a, portals_b, blackholes]:
                        for obj in lst[:]:
                            if hasattr(obj, 'x') and hasattr(obj, 'y') and near(mx, my, obj.x, obj.y):
                                lst.remove(obj); break

            elif event.type == pygame.MOUSEWHEEL and last_selected is not None:
                # 거울과 Emitter는 rotate() 메서드 사용 (고정 방향), 렌즈는 자유 회전
                if isinstance(last_selected, (Mirror, Emitter)):
                    last_selected.rotate()
                elif isinstance(last_selected, Lens):
                    last_selected.angle = angle_wrap(last_selected.angle + event.y * 5)

        # 그리기
        screen.fill((30, 30, 30))
        
        # 그리드 그리기
        draw_grid(screen)

        # 입력 모드 오버레이
        if input_mode in ['save', 'load']:
            # 반투명 배경
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(180)
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))
            
            # 입력 박스
            prompt = "맵 저장" if input_mode == 'save' else "맵 불러오기"
            prompt_text = FONT_BIG.render(f"{prompt} - 맵 번호를 입력하세요 (0-999)", True, (255, 255, 255))
            screen.blit(prompt_text, (WIDTH//2 - 250, HEIGHT//2 - 60))
            
            # 입력 필드
            input_box = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 - 20, 200, 50)
            pygame.draw.rect(screen, (255, 255, 255), input_box, 2)
            input_surface = FONT_BIG.render(input_text, True, (255, 255, 255))
            screen.blit(input_surface, (input_box.x + 10, input_box.y + 10))
            
            # 안내 메시지
            help_text = FONT.render("Enter: 확인 | ESC: 취소", True, (180, 180, 180))
            screen.blit(help_text, (WIDTH//2 - 100, HEIGHT//2 + 50))
            
            pygame.display.flip()
            clock.tick(FPS)
            continue

        for b in buttons:
            b.draw(screen, FONT_BIG)

        # 상태 표시
        mode_text = f"모드: {object_mode if object_mode else '없음'}  |  상태: {'실행중' if game_started else '대기'}"
        screen.blit(FONT.render(mode_text, True, (230,230,230)), (20, 170))

        # 안내 메시지
        for i, line in enumerate(info):
            screen.blit(FONT.render(line, True, (180,180,180)), (20, 200 + i*22))

        for e in emitters:   e.draw(screen)
        for t in targets:    t.draw(screen)
        for m in mirrors:    m.draw(screen)
        for l in lenses:     l.draw(screen)
        for pa in portals_a: pa.draw(screen)
        for pb in portals_b: pb.draw(screen)
        for b in blackholes: b.draw(screen)

        if game_started:
            simulate_light(screen)
            
            # 게임 완료 체크
            if check_game_complete():
                # 완료 메시지 표시
                complete_text = FONT_BIG.render("★ 퍼즐 완료! ★", True, (255, 255, 0))
                complete_rect = complete_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
                # 배경
                bg_rect = complete_rect.inflate(40, 20)
                pygame.draw.rect(screen, (0, 100, 0), bg_rect, border_radius=10)
                pygame.draw.rect(screen, (255, 255, 0), bg_rect, 3, border_radius=10)
                screen.blit(complete_text, complete_rect)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()
