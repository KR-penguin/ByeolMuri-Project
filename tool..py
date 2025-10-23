import pygame
import math
import json

# 모듈 임포트
from objects import (Button, Emitter, Target, ColorTarget, Mirror, Lens, Prism, Blackhole, 
                     COLORS, RADIUS)
from utils import near, angle_wrap, vec_from_angle, advance, refract_angle, N_AIR

# --- 기본 설정 ---
WIDTH, HEIGHT = 1000, 700
FPS = 60

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Light Puzzle - Map Editor")
clock = pygame.time.Clock()
FONT = pygame.font.SysFont("Malgun Gothic", 22)
FONT_BIG = pygame.font.SysFont("Malgun Gothic", 28)

pygame.display.set_caption("Light Puzzle - Map Editor")
clock = pygame.time.Clock()
FONT = pygame.font.SysFont("Malgun Gothic", 22)
FONT_BIG = pygame.font.SysFont("Malgun Gothic", 28)

# --- 레벨 설정 ---
class LevelConfig:
    """레벨별 굴절률 및 설정 관리"""
    def __init__(self):
        self.refract_index = 1.5  # 기본 굴절률 (유리)
    
    def set_refract_index(self, value):
        """굴절률 설정 (1.0 ~ 3.0 범위)"""
        self.refract_index = max(1.0, min(3.0, value))
    
    def increase(self):
        """굴절률 증가 (+0.1)"""
        self.set_refract_index(self.refract_index + 0.1)
    
    def decrease(self):
        """굴절률 감소 (-0.1)"""
        self.set_refract_index(self.refract_index - 0.1)

level_config = LevelConfig()

# --- 오브젝트 리스트 ---
emitters, targets, mirrors, lenses, prisms, blackholes = [], [], [], [], [], []
color_targets = []  # RGB 목표지점 (개수 제한 없음)

# --- 모드/상태 ---
object_mode = None  # 'emitter'|'target'|'mirror'|'lens'|'prism'|'blackhole'|'eraser'|'red_target'|'green_target'|'blue_target'
game_started = False
input_mode = None  # 'save' | 'load' | None
input_text = ""    # 입력 중인 맵 번호

# --- 버튼들 ---
btn_start     = Button( 20, 20, 120, 40, "게임 시작")
btn_emitter   = Button(160, 20, 120, 40, "W 발사")
btn_target    = Button(300, 20, 120, 40, "W 목표")
btn_mirror    = Button(440, 20, 120, 40, "거울")
btn_lens      = Button(580, 20, 120, 40, "렌즈")
btn_prism     = Button(720, 20, 120, 40, "프리즘")
btn_blackhole = Button(860, 20, 120, 40, "블랙홀")

btn_eraser = Button( 20, 70, 120, 40, "지우개")
btn_stop   = Button(160, 70, 120, 40, "중단")
btn_clear  = Button(300, 70, 120, 40, "클리어")
btn_save   = Button(440, 70, 120, 40, "맵 저장")
btn_load   = Button(580, 70, 120, 40, "맵 불러오기")

btn_refract_up   = Button(720, 70, 60, 40, "n +")
btn_refract_down = Button(790, 70, 60, 40, "n -")

# RGB 목표지점 버튼 (3번째 줄)
btn_red_target   = Button( 20, 120, 80, 40, "R 목표")
btn_green_target = Button(110, 120, 80, 40, "G 목표")
btn_blue_target  = Button(200, 120, 80, 40, "B 목표")

buttons = [btn_start, btn_emitter, btn_target, btn_mirror, btn_lens, btn_prism, btn_blackhole,
           btn_eraser, btn_stop, btn_clear, btn_save, btn_load, btn_refract_up, btn_refract_down,
           btn_red_target, btn_green_target, btn_blue_target]

# --- 저장/불러오기 ---
def save_map(map_index):
    """
    맵을 JSON 파일로 저장 (인덱스별)
    모든 오브젝트 포함 (발사장치, 목표지점, 거울, 렌즈, 프리즘, 블랙홀)
    """
    level_data = {
        "map_index": map_index,
        "refract_index": level_config.refract_index,
        "emitters": [{"x":e.x, "y":e.y, "color":e.color, "angle":e.angle} for e in emitters],
        "color_targets": [{"x":t.x, "y":t.y, "color":t.color} for t in color_targets],
        "targets": [{"x":t.x, "y":t.y, "color":t.color} for t in targets],
        "mirrors": [{"x":m.x, "y":m.y, "angle":m.angle} for m in mirrors],
        "lenses": [{"x":l.x, "y":l.y, "angle":l.angle, "refract_index":l.refract_index} for l in lenses],
        "prisms": [{"x":p.x, "y":p.y, "angle":p.angle} for p in prisms],
        "blackholes": [{"x":b.x, "y":b.y} for b in blackholes],
    }
    filename = f"level_{map_index}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(level_data, f, ensure_ascii=False, indent=2)
    print(f"맵 저장 완료: {filename} (굴절률: {level_config.refract_index:.2f})")

def load_map(map_index):
    """
    JSON 파일에서 맵 불러오기 (인덱스별)
    모든 오브젝트 불러오기 (발사장치, 목표지점, 거울, 렌즈, 프리즘, 블랙홀)
    """
    global emitters, color_targets, targets, mirrors, lenses, prisms, blackholes
    try:
        filename = f"level_{map_index}.json"
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # 굴절률 로드
        level_config.set_refract_index(data.get("refract_index", 1.5))
        
        # 모든 오브젝트 초기화
        emitters.clear()
        color_targets.clear()
        targets.clear()
        mirrors.clear()
        lenses.clear()
        prisms.clear()
        blackholes.clear()

        for e in data.get("emitters", []):
            emitters.append(Emitter(e["x"], e["y"], e.get("color","white"), e.get("angle",0)))
        for t in data.get("color_targets", []):
            color_targets.append(ColorTarget(t["x"], t["y"], t.get("color","red")))
        for t in data.get("targets", []):
            targets.append(Target(t["x"], t["y"], t.get("color","white")))
        for m in data.get("mirrors", []):
            mirrors.append(Mirror(m["x"], m["y"], m.get("angle",0)))
        for l in data.get("lenses", []):
            lenses.append(Lens(l["x"], l["y"], l.get("angle",0), l.get("refract_index")))
        for p in data.get("prisms", []):
            prisms.append(Prism(p["x"], p["y"], p.get("angle",0)))
        for b in data.get("blackholes", []):
            blackholes.append(Blackhole(b["x"], b["y"]))
        
        print(f"맵 불러오기 완료: {filename} (굴절률: {level_config.refract_index:.2f})")
        print(f"오브젝트: 발사장치 {len(emitters)}개, RGB목표 {len(color_targets)}개, 목표지점 {len(targets)}개, "
              f"거울 {len(mirrors)}개, 렌즈 {len(lenses)}개, 프리즘 {len(prisms)}개, 블랙홀 {len(blackholes)}개")
    except FileNotFoundError:
        print(f"[로드 실패] 파일을 찾을 수 없습니다: {filename}")
    except Exception as e:
        print(f"[로드 실패] {e}")

def simulate_light(surface):
    """
    빛의 경로를 시뮬레이션하고 화면에 그림
    - 렌즈: 맵 굴절률 설정을 따름 (개별 설정 가능)
    - 프리즘: 진입 시 흰색 빛을 R, G, B로 분광
    - 거울: 반사
    - 블랙홀: 흡수
    """
    MAX_STEPS = 3000
    MAX_BOUNCES = 64
    NUDGE = 2.0

    # 모든 목표지점 초기화
    for t in targets:
        t.hit = False
    for t in color_targets:
        t.hit = False

    # 흰색 발사장치만 처리 (RGB는 목표지점)
    all_emitters = list(emitters)
    
    for emitter in all_emitters:
        # 큐 요소: (x, y, angle, color, inside_lenses:set, inside_prisms:set, bounces)
        ray_queue = [ (emitter.x, emitter.y, emitter.angle, emitter.color, set(), set(), 0) ]

        while ray_queue:
            x, y, angle, color_name, inside_lenses, inside_prisms, bounces = ray_queue.pop(0)
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

                # 2) 렌즈 굴절 (맵 굴절률 사용)
                for lz in lenses:
                    lid = id(lz)
                    dist_sq = (x - lz.x)**2 + (y - lz.y)**2
                    inside_now = dist_sq <= (RADIUS * RADIUS)
                    lens_n = lz.get_refract_index(level_config.refract_index)  # 맵 설정 사용
                    
                    # 진입: 공기 → 렌즈
                    if inside_now and lid not in inside_lenses:
                        # 법선: 렌즈 중심에서 빛의 위치로 향하는 방향 (외향 법선)
                        normal_deg = math.degrees(math.atan2(y - lz.y, x - lz.x))
                        new_angle, tir = refract_angle(angle, normal_deg, N_AIR, lens_n)
                        if tir:
                            # 전반사: 반사
                            angle = angle_wrap(2 * normal_deg - angle)
                            bounces += 1
                        else:
                            # 굴절
                            angle = new_angle
                        inside_lenses.add(lid)
                        x, y = advance(x, y, angle, NUDGE)
                        
                    # 이탈: 렌즈 → 공기
                    elif (lid in inside_lenses) and (not inside_now):
                        # 법선: 렌즈 중심에서 빛의 위치로 향하는 방향 (외향 법선)
                        normal_deg = math.degrees(math.atan2(y - lz.y, x - lz.x))
                        new_angle, tir = refract_angle(angle, normal_deg, lens_n, N_AIR)
                        if tir:
                            # 전반사: 렌즈 내부에서 반사
                            angle = angle_wrap(2 * normal_deg - angle)
                            bounces += 1
                        else:
                            # 굴절하여 공기로 나감
                            angle = new_angle
                            inside_lenses.remove(lid)
                        x, y = advance(x, y, angle, NUDGE)

                # 3) 프리즘 분광 (진입 1회) - 흰색 → R, G, B
                for pr in prisms:
                    pid = id(pr)
                    inside_now = ((x - pr.x)**2 + (y - pr.y)**2) <= (RADIUS*RADIUS)
                    if inside_now and pid not in inside_prisms:
                        # 흰색 빛만 분광
                        if color_name == 'white' and bounces <= MAX_BOUNCES - 2:
                            # R, G, B로 분광
                            ray_queue.append( (x, y, angle_wrap(angle - 10), 'red',
                                               set(inside_lenses), set(list(inside_prisms) + [pid]), bounces+1) )
                            ray_queue.append( (x, y, angle, 'green',
                                               set(inside_lenses), set(list(inside_prisms) + [pid]), bounces+1) )
                            ray_queue.append( (x, y, angle_wrap(angle + 10), 'blue',
                                               set(inside_lenses), set(list(inside_prisms) + [pid]), bounces+1) )
                            # 원래 흰색 빛은 흡수
                            inside_prisms.add(pid)
                            break  # 분광 후 현재 광선 종료
                        inside_prisms.add(pid)
                        x, y = advance(x, y, angle, NUDGE)
                    elif (pid in inside_prisms) and (not inside_now):
                        inside_prisms.remove(pid)

                # 4) 블랙홀
                absorbed = False
                for bh in blackholes:
                    if near(x, y, bh.x, bh.y):
                        absorbed = True
                        break
                if absorbed:
                    break

                # 5) 타겟 체크
                hit_target = False
                # 흰색 목표
                for tg in targets:
                    if near(x, y, tg.x, tg.y) and color_name == tg.color:
                        tg.hit = True
                        pygame.draw.circle(surface, (255, 255, 0), (int(tg.x), int(tg.y)), RADIUS+6, 3)
                        hit_target = True
                        break
                # RGB 목표
                for tg in color_targets:
                    if near(x, y, tg.x, tg.y) and color_name == tg.color:
                        tg.hit = True
                        pygame.draw.circle(surface, (255, 255, 0), (int(tg.x), int(tg.y)), RADIUS+6, 3)
                        hit_target = True
                        break
                if hit_target:
                    break  # 목표에 도달하면 이 광선 종료

                # 6) 그리기
                pygame.draw.circle(surface, COLORS[color_name], (int(x), int(y)), 2)

                if bounces > MAX_BOUNCES:
                    break

def check_game_complete():
    """
    게임 완료 조건 체크: 모든 목표지점(W, R, G, B)이 빛을 받았는지 확인
    """
    # 목표지점이 하나도 없으면 미완료
    if len(targets) == 0 and len(color_targets) == 0:
        return False
    
    # 모든 목표지점이 빛을 받았는지 확인
    for t in targets:
        if not t.hit:
            return False
    for t in color_targets:
        if not t.hit:
            return False
    
    return True

def main():
    global object_mode, game_started, input_mode, input_text
    running = True

    info = [
        "좌클릭: 현재 모드 오브젝트 배치 / 지우개는 근접 오브젝트 삭제",
        "마우스 휠: 마지막 배치한 Emitter/거울/렌즈/프리즘 각도 조절",
        f"굴절률(n): {level_config.refract_index:.2f} | 스넬의 법칙: n1*sin(θ1) = n2*sin(θ2)",
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
                    emitters.clear(); color_targets.clear(); targets.clear(); mirrors.clear()
                    lenses.clear(); prisms.clear(); blackholes.clear()
                    game_started = False; object_mode = None; continue
                if btn_save.is_clicked((mx, my)):
                    input_mode = 'save'; input_text = ""; continue
                if btn_load.is_clicked((mx, my)):
                    input_mode = 'load'; input_text = ""; continue
                if btn_refract_up.is_clicked((mx, my)):
                    level_config.increase(); continue
                if btn_refract_down.is_clicked((mx, my)):
                    level_config.decrease(); continue

                if btn_emitter.is_clicked((mx, my)):   object_mode = 'emitter';   continue
                if btn_target.is_clicked((mx, my)):    object_mode = 'target';    continue
                if btn_mirror.is_clicked((mx, my)):    object_mode = 'mirror';    continue
                if btn_lens.is_clicked((mx, my)):      object_mode = 'lens';      continue
                if btn_prism.is_clicked((mx, my)):     object_mode = 'prism';     continue
                if btn_blackhole.is_clicked((mx, my)): object_mode = 'blackhole'; continue
                if btn_eraser.is_clicked((mx, my)):    object_mode = 'eraser';    continue
                
                # RGB 목표지점 버튼
                if btn_red_target.is_clicked((mx, my)):   object_mode = 'red_target';   continue
                if btn_green_target.is_clicked((mx, my)): object_mode = 'green_target'; continue
                if btn_blue_target.is_clicked((mx, my)):  object_mode = 'blue_target';  continue

                # 배치/삭제
                if object_mode == 'emitter':
                    # 발사 장치는 1개만 허용
                    if len(emitters) >= 1:
                        print("발사 장치는 1개만 배치할 수 있습니다. 기존 발사 장치를 먼저 삭제하세요.")
                    else:
                        obj = Emitter(mx, my, 'white', 0); emitters.append(obj); last_selected = obj
                elif object_mode == 'target':
                    # 목표 지점은 1개만 허용
                    if len(targets) >= 1:
                        print("목표 지점은 1개만 배치할 수 있습니다. 기존 목표 지점을 먼저 삭제하세요.")
                    else:
                        obj = Target(mx, my, 'white'); targets.append(obj); last_selected = obj
                elif object_mode == 'mirror':
                    obj = Mirror(mx, my, 0); mirrors.append(obj); last_selected = obj
                elif object_mode == 'lens':
                    # 렌즈는 맵 굴절률 사용 (refract_index=None)
                    obj = Lens(mx, my, 0, None); lenses.append(obj); last_selected = obj
                elif object_mode == 'prism':
                    obj = Prism(mx, my, 0); prisms.append(obj); last_selected = obj
                elif object_mode == 'blackhole':
                    obj = Blackhole(mx, my); blackholes.append(obj); last_selected = obj
                elif object_mode == 'red_target':
                    obj = ColorTarget(mx, my, 'red'); color_targets.append(obj); last_selected = obj
                elif object_mode == 'green_target':
                    obj = ColorTarget(mx, my, 'green'); color_targets.append(obj); last_selected = obj
                elif object_mode == 'blue_target':
                    obj = ColorTarget(mx, my, 'blue'); color_targets.append(obj); last_selected = obj
                elif object_mode == 'eraser':
                    for lst in [emitters, color_targets, targets, mirrors, lenses, prisms, blackholes]:
                        for obj in lst[:]:
                            if hasattr(obj, 'x') and hasattr(obj, 'y') and near(mx, my, obj.x, obj.y):
                                lst.remove(obj); break

            elif event.type == pygame.MOUSEWHEEL and last_selected is not None:
                if isinstance(last_selected, (Emitter, Mirror, Prism, Lens)):
                    last_selected.angle = angle_wrap(last_selected.angle + event.y * 5)

        # 그리기
        screen.fill((30, 30, 30))

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

        # 상태 표시 (굴절률 포함)
        mode_text = f"모드: {object_mode if object_mode else '없음'}  |  상태: {'실행중' if game_started else '대기'}  |  굴절률(n): {level_config.refract_index:.2f}"
        screen.blit(FONT.render(mode_text, True, (230,230,230)), (20, 170))

        # 안내 메시지
        info[2] = f"굴절률(n): {level_config.refract_index:.2f} | 스넬의 법칙: n1*sin(θ1) = n2*sin(θ2)"
        for i, line in enumerate(info):
            screen.blit(FONT.render(line, True, (180,180,180)), (20, 200 + i*22))

        for e in emitters:   e.draw(screen)
        for t in color_targets: t.draw(screen)
        for t in targets:    t.draw(screen)
        for m in mirrors:    m.draw(screen)
        for l in lenses:     l.draw(screen)
        for p in prisms:     p.draw(screen)
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
