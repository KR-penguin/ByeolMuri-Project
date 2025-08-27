import pygame
import math
import json

# --- 기본 설정 ---
WIDTH, HEIGHT = 1000, 700
FPS = 60
COLORS = {
    "white": (255,255,255),
    "red":   (255,0,0),
    "green": (0,255,0),
    "blue":  (0,0,255),
}

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Light Puzzle (Lens/Prism/Load Fixed)")
clock = pygame.time.Clock()
FONT = pygame.font.SysFont("Malgun Gothic", 22)
FONT_BIG = pygame.font.SysFont("Malgun Gothic", 28)

# --- 버튼 클래스 ---
class Button:
    def __init__(self, x, y, w, h, text):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color_idle = (70, 70, 160)
        self.color_hover = (90, 90, 200)
    def draw(self, surface):
        color = self.color_hover if self.rect.collidepoint(pygame.mouse.get_pos()) else self.color_idle
        pygame.draw.rect(surface, color, self.rect, border_radius=6)
        txt = FONT_BIG.render(self.text, True, (255,255,255))
        surface.blit(txt, (self.rect.x+10, self.rect.y+6))
    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

# --- 오브젝트 클래스 ---
RADIUS = 18  # 공통 반경(충돌/선택)
N_AIR = 1.0  # 공기 굴절률

class Emitter:
    def __init__(self, x, y, color='red', angle=0):
        self.x, self.y, self.color, self.angle = x, y, color, angle
    def draw(self, surf):
        pygame.draw.circle(surf, COLORS[self.color], (int(self.x), int(self.y)), RADIUS, 2)
        dx = math.cos(math.radians(self.angle)) * 24
        dy = math.sin(math.radians(self.angle)) * 24
        pygame.draw.line(surf, COLORS[self.color], (self.x, self.y), (self.x+dx, self.y+dy), 2)

class Target:
    def __init__(self, x, y, color='red'):
        self.x, self.y, self.color = x, y, color
    def draw(self, surf):
        pygame.draw.circle(surf, COLORS[self.color], (int(self.x), int(self.y)), RADIUS, 3)

class Mirror:
    def __init__(self, x, y, angle=0):  # ✅ 기본 각도 0°
        self.x, self.y, self.angle = x, y, angle
    def draw(self, surf):
        length = 36
        dx = math.cos(math.radians(self.angle)) * length
        dy = math.sin(math.radians(self.angle)) * length
        pygame.draw.line(surf, (200,200,200), (self.x-dx, self.y-dy), (self.x+dx, self.y+dy), 3)
        pygame.draw.circle(surf, (200,200,200), (int(self.x), int(self.y)), 4)

class Lens:
    def __init__(self, x, y, angle=0, refract_index=1.5):
        self.x, self.y, self.angle, self.refract_index = x, y, angle, refract_index
    def draw(self, surf):
        pygame.draw.circle(surf, (100,180,255), (int(self.x), int(self.y)), RADIUS, 0)
        pygame.draw.circle(surf, (20,60,120), (int(self.x), int(self.y)), RADIUS, 2)

class Prism:
    def __init__(self, x, y, angle=0):
        self.x, self.y, self.angle = x, y, angle
    def draw(self, surf):
        pygame.draw.polygon(surf, (180,120,80), [
            (self.x-RADIUS, self.y+RADIUS),
            (self.x, self.y-RADIUS),
            (self.x+RADIUS, self.y+RADIUS),
        ], 0)
        pygame.draw.polygon(surf, (80,50,30), [
            (self.x-RADIUS, self.y+RADIUS),
            (self.x, self.y-RADIUS),
            (self.x+RADIUS, self.y+RADIUS),
        ], 2)

class Blackhole:
    def __init__(self, x, y):
        self.x, self.y = x, y
    def draw(self, surf):
        pygame.draw.circle(surf, (0,0,0), (int(self.x), int(self.y)), RADIUS, 0)
        pygame.draw.circle(surf, (90,90,90), (int(self.x), int(self.y)), RADIUS, 2)

# --- 오브젝트 리스트 ---
emitters, targets, mirrors, lenses, prisms, blackholes = [], [], [], [], [], []

# --- 모드/상태 ---
object_mode = None  # 'emitter'|'target'|'mirror'|'lens'|'prism'|'blackhole'|'eraser'
game_started = False

# --- 버튼들 ---
btn_start     = Button( 20, 20, 120, 40, "게임 시작")
btn_emitter   = Button(160, 20, 120, 40, "발사장치")
btn_target    = Button(300, 20, 120, 40, "목표지점")
btn_mirror    = Button(440, 20, 120, 40, "거울")
btn_lens      = Button(580, 20, 120, 40, "렌즈")
btn_prism     = Button(720, 20, 120, 40, "프리즘")
btn_blackhole = Button(860, 20, 120, 40, "블랙홀")

btn_eraser = Button( 20, 70, 120, 40, "지우개")
btn_stop   = Button(160, 70, 120, 40, "중단")
btn_clear  = Button(300, 70, 120, 40, "클리어")
btn_save   = Button(440, 70, 120, 40, "맵 저장")
btn_load   = Button(580, 70, 120, 40, "맵 불러오기")

buttons = [btn_start, btn_emitter, btn_target, btn_mirror, btn_lens, btn_prism, btn_blackhole,
           btn_eraser, btn_stop, btn_clear, btn_save, btn_load]

def near(p1x, p1y, p2x, p2y, r=RADIUS):
    return (abs(p1x - p2x) <= r) and (abs(p1y - p2y) <= r)

def angle_wrap(deg):
    return deg % 360

def vec_from_angle(deg, length=1.0):
    rad = math.radians(deg)
    return math.cos(rad)*length, math.sin(rad)*length

def advance(x, y, angle, step=2.0):
    dx, dy = vec_from_angle(angle, step)
    return x+dx, y+dy

# --- 굴절 보조(Snell 근사) ---
def refract_angle(inc_angle_deg, normal_deg, n1, n2):
    """
    inc_angle_deg: 진행 방향(절대각)
    normal_deg   : 면의 법선(절대각, 진행 방향이 법선에서 시계방향 양수)
    n1->n2 굴절. 반환: (새 진행각, total_internal_reflection_flag)
    """
    theta1 = math.radians(angle_wrap(inc_angle_deg - normal_deg))
    theta1 = math.atan2(math.sin(theta1), math.cos(theta1))

    s = (n1 / n2) * math.sin(theta1)
    if abs(s) > 1.0:
        theta_r = -theta1
        new_abs = angle_wrap(math.degrees(theta_r) + normal_deg)
        return new_abs, True

    theta2 = math.asin(s)
    new_abs = angle_wrap(math.degrees(theta2) + normal_deg)
    return new_abs, False

# --- 저장/불러오기 ---
def save_map():
    level_data = {
        "emitters":   [{"x":e.x, "y":e.y, "color":e.color, "angle":e.angle} for e in emitters],
        "targets":    [{"x":t.x, "y":t.y, "color":t.color} for t in targets],
        "mirrors":    [{"x":m.x, "y":m.y, "angle":m.angle} for m in mirrors],
        "lenses":     [{"x":l.x, "y":l.y, "angle":l.angle, "refract_index":l.refract_index} for l in lenses],
        "prisms":     [{"x":p.x, "y":p.y, "angle":p.angle} for p in prisms],
        "blackholes": [{"x":b.x, "y":b.y} for b in blackholes],
    }
    with open("saved_map.json", "w", encoding="utf-8") as f:
        json.dump(level_data, f, ensure_ascii=False, indent=2)
    print("맵 저장 완료: saved_map.json")

def load_map():
    global emitters, targets, mirrors, lenses, prisms, blackholes
    try:
        with open("saved_map.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        emitters.clear(); targets.clear(); mirrors.clear()
        lenses.clear(); prisms.clear(); blackholes.clear()

        for e in data.get("emitters", []):
            emitters.append(Emitter(e["x"], e["y"], e.get("color","red"), e.get("angle",0)))
        for t in data.get("targets", []):
            targets.append(Target(t["x"], t["y"], t.get("color","red")))
        for m in data.get("mirrors", []):
            mirrors.append(Mirror(m["x"], m["y"], m.get("angle",0)))  # ✅ 로드 시 기본값도 0
        for l in data.get("lenses", []):
            lenses.append(Lens(l["x"], l["y"], l.get("angle",0), l.get("refract_index",1.5)))
        for p in data.get("prisms", []):
            prisms.append(Prism(p["x"], p["y"], p.get("angle",0)))
        for b in data.get("blackholes", []):
            blackholes.append(Blackhole(b["x"], b["y"]))
        print("맵 불러오기 완료: saved_map.json")
    except Exception as e:
        print(f"[로드 실패] {e}")

# --- 빛 시뮬레이션 ---
def simulate_light(surface):
    """
    - 렌즈: 원 경계(거리<=RADIUS) 진입/이탈에서만 굴절 계산.
    - 프리즘: 진입 시 1회만 분광(±10도), 내부에선 재분광 금지.
    - 거울: 반사 후 살짝 전진하여 충돌 반경 탈출.
    - 무한 루프 방지: step/bounce 제한 및 NUDGE.
    """
    MAX_STEPS = 3000
    MAX_BOUNCES = 64
    NUDGE = 2.0

    for emitter in emitters:
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
                    continue

                # 2) 렌즈 굴절 (진입/이탈 시 1회)
                for lz in lenses:
                    lid = id(lz)
                    inside_now = ((x - lz.x)**2 + (y - lz.y)**2) <= (RADIUS*RADIUS)
                    if inside_now and lid not in inside_lenses:
                        normal_deg = math.degrees(math.atan2(x - lz.x, lz.y - y))  # 근사 법선 (외향)
                        normal_deg = math.degrees(math.atan2(y - lz.y, x - lz.x))  # 중심->점(외향)
                        new_angle, tir = refract_angle(angle, normal_deg, N_AIR, lz.refract_index)
                        if tir:
                            angle = angle_wrap(2*normal_deg - angle)
                            bounces += 1
                        else:
                            angle = new_angle
                        inside_lenses.add(lid)
                        x, y = advance(x, y, angle, NUDGE)
                    elif (lid in inside_lenses) and (not inside_now):
                        normal_deg = math.degrees(math.atan2(y - lz.y, x - lz.x))
                        new_angle, tir = refract_angle(angle, normal_deg, lz.refract_index, N_AIR)
                        if tir:
                            angle = angle_wrap(2*normal_deg - angle)
                            bounces += 1
                        else:
                            angle = new_angle
                            inside_lenses.remove(lid)
                        x, y = advance(x, y, angle, NUDGE)

                # 3) 프리즘 분광 (진입 1회)
                for pr in prisms:
                    pid = id(pr)
                    inside_now = ((x - pr.x)**2 + (y - pr.y)**2) <= (RADIUS*RADIUS)
                    if inside_now and pid not in inside_prisms:
                        if bounces <= MAX_BOUNCES - 2:
                            ray_queue.append( (x, y, angle_wrap(angle + 10), 'green',
                                               set(inside_lenses), set(list(inside_prisms) + [pid]), bounces+1) )
                            ray_queue.append( (x, y, angle_wrap(angle - 10), 'blue',
                                               set(inside_lenses), set(list(inside_prisms) + [pid]), bounces+1) )
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

                # 5) 타겟
                hit_target = False
                for tg in targets:
                    if near(x, y, tg.x, tg.y) and color_name == tg.color:
                        pygame.draw.circle(surface, (255, 255, 0), (int(tg.x), int(tg.y)), RADIUS+6, 3)
                        hit_target = True
                        break
                if hit_target:
                    return

                # 6) 그리기
                pygame.draw.circle(surface, COLORS[color_name], (int(x), int(y)), 2)

                if bounces > MAX_BOUNCES:
                    break

# --- 메인 루프 ---
def main():
    global object_mode, game_started
    running = True

    info = [
        "좌클릭: 현재 모드 오브젝트 배치 / 지우개는 근접 오브젝트 삭제",
        "마우스 휠: 마지막 배치한 Emitter/거울/렌즈/프리즘 각도 조절(360°)",
        "버튼: 게임 시작/중단/클리어/저장/불러오기",
    ]

    last_selected = None  # 각도 조절 대상

    while running:
        # 이벤트
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos

                # 버튼 처리
                if btn_start.is_clicked((mx, my)):
                    game_started = True;   continue
                if btn_stop.is_clicked((mx, my)):
                    game_started = False;  continue
                if btn_clear.is_clicked((mx, my)):
                    emitters.clear(); targets.clear(); mirrors.clear()
                    lenses.clear(); prisms.clear(); blackholes.clear()
                    game_started = False; object_mode = None; continue
                if btn_save.is_clicked((mx, my)):
                    save_map(); continue
                if btn_load.is_clicked((mx, my)):
                    load_map(); continue

                if btn_emitter.is_clicked((mx, my)):   object_mode = 'emitter';   continue
                if btn_target.is_clicked((mx, my)):    object_mode = 'target';    continue
                if btn_mirror.is_clicked((mx, my)):    object_mode = 'mirror';    continue
                if btn_lens.is_clicked((mx, my)):      object_mode = 'lens';      continue
                if btn_prism.is_clicked((mx, my)):     object_mode = 'prism';     continue
                if btn_blackhole.is_clicked((mx, my)): object_mode = 'blackhole'; continue
                if btn_eraser.is_clicked((mx, my)):    object_mode = 'eraser';    continue

                # 배치/삭제
                if object_mode == 'emitter':
                    obj = Emitter(mx, my, 'red', 0); emitters.append(obj); last_selected = obj
                elif object_mode == 'target':
                    obj = Target(mx, my, 'red'); targets.append(obj); last_selected = obj
                elif object_mode == 'mirror':
                    obj = Mirror(mx, my, 0); mirrors.append(obj); last_selected = obj   # ✅ 배치 각도 0°
                elif object_mode == 'lens':
                    obj = Lens(mx, my, 0, 1.5); lenses.append(obj); last_selected = obj
                elif object_mode == 'prism':
                    obj = Prism(mx, my, 0); prisms.append(obj); last_selected = obj
                elif object_mode == 'blackhole':
                    obj = Blackhole(mx, my); blackholes.append(obj); last_selected = obj
                elif object_mode == 'eraser':
                    for lst in [emitters, targets, mirrors, lenses, prisms, blackholes]:
                        for obj in lst[:]:
                            if hasattr(obj, 'x') and hasattr(obj, 'y') and near(mx, my, obj.x, obj.y):
                                lst.remove(obj); break

            elif event.type == pygame.MOUSEWHEEL and last_selected is not None:
                if isinstance(last_selected, (Emitter, Mirror, Prism, Lens)):
                    last_selected.angle = angle_wrap(last_selected.angle + event.y * 5)

        # 그리기
        screen.fill((30, 30, 30))

        for b in buttons:
            b.draw(screen)

        mode_text = f"모드: {object_mode if object_mode else '없음'}  |  상태: {'실행중' if game_started else '대기'}"
        screen.blit(FONT.render(mode_text, True, (230,230,230)), (20, 120))

        for i, line in enumerate(info):
            screen.blit(FONT.render(line, True, (180,180,180)), (20, 150 + i*22))

        for e in emitters:   e.draw(screen)
        for t in targets:    t.draw(screen)
        for m in mirrors:    m.draw(screen)
        for l in lenses:     l.draw(screen)
        for p in prisms:     p.draw(screen)
        for b in blackholes: b.draw(screen)

        if game_started:
            simulate_light(screen)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()
