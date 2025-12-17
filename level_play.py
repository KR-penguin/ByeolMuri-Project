import pygame
import math
import json
import sys
import os
import wave
import struct

# 모듈 임포트 (objects.py, utils.py 필요)
from objects import (Button, Emitter, Target, Mirror, Lens, Blackhole, Portal,
                     COLORS, RADIUS)
from utils import near, angle_wrap, vec_from_angle, advance, refract_angle, N_AIR

# --- 기본 설정 ---
WIDTH, HEIGHT = 1280, 720
FPS = 60

# 그리드 설정
GRID_SIZE = 41  # 가로 30칸 기준 (1230 / 30 = 41)
GRID_OFFSET_X = 50
GRID_OFFSET_Y = 300

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("광학 퍼즐 게임 - 레벨 플레이")
clock = pygame.time.Clock()
FONT = pygame.font.SysFont("Malgun Gothic", 20)
FONT_BIG = pygame.font.SysFont("Malgun Gothic", 24)

# BGM 설정
BGM_DIR = os.path.join(os.path.dirname(__file__), "assets", "bgm")
# 단일 BGM 파일명 (한글 파일명도 지원) - WAV로 자동생성
BGM_FILE = '경쾌한 BGM.mp3'  # 레벨 입장 시 단일 BGM을 반복 재생


# 오디오 초기화 및 재생 함수
def init_audio():
    """사운드 시스템 초기화."""
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        print("🔊 오디오 시스템 초기화 완료")
    except Exception as e:
        print(f"오디오 초기화 실패: {e}")


def play_bgm_for_map(map_index):
    """맵을 로드할 때 단일 BGM을 무한 반복 재생.
    map_index가 None이면 BGM을 중지한다."""
    # 맵 인덱스가 없더라도 기본 BGM 파일이 있으면 재생하도록 변경
    if map_index is None:
        print("BGM: 맵 정보 없음, 기본 BGM 재생 시도")

    if not pygame.mixer.get_init():
        try:
            pygame.mixer.init()
        except Exception as e:
            print(f"오디오 초기화 실패: {e}")
            return

    path = os.path.join(BGM_DIR, BGM_FILE)
    if not os.path.isfile(path):
        # BGM 파일이 없으면 재생을 시도하지 않고 조용히 종료
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass
        print(f"BGM 파일 없음: {path} -- 재생하지 않습니다.")
        return

    try:
        pygame.mixer.music.load(path)
        pygame.mixer.music.set_volume(0.6)
        pygame.mixer.music.play(-1)  # 무한 반복
        print(f"♬ BGM 재생: {BGM_FILE} (맵 인덱스: {map_index})")
    except Exception as e:
        print(f"BGM 재생 실패: {e}")

# --- 그리드 함수 ---
def snap_to_grid(x, y):
    """마우스 좌표를 가장 가까운 그리드 중심으로 스냅"""
    grid_x = round((x - GRID_OFFSET_X) / GRID_SIZE) * GRID_SIZE + GRID_OFFSET_X
    grid_y = round((y - GRID_OFFSET_Y) / GRID_SIZE) * GRID_SIZE + GRID_OFFSET_Y
    return grid_x, grid_y

def draw_grid(surface):
    """그리드 그리기"""
    grid_color = (60, 60, 60)
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
portals_a, portals_b = [], []
player_objects = []  # 플레이어가 배치한 오브젝트

# --- 모드/상태 ---
object_mode = None  # 'mirror'|'lens'|'blackhole'|'portal_a'|'portal_b'|'eraser'
game_started = False

# --- 버튼들 ---
btn_start = Button(20, 20, 120, 40, "게임 시작")
btn_stop = Button(160, 20, 120, 40, "중단")
btn_clear = Button(300, 20, 120, 40, "초기화")
btn_back = Button(440, 20, 120, 40, "메뉴로")

# 도구 버튼 (2번째 줄)
btn_mirror = Button(20, 70, 100, 40, "거울")
btn_lens = Button(140, 70, 100, 40, "렌즈")
btn_blackhole = Button(260, 70, 100, 40, "블랙홀")
btn_portal_a = Button(380, 70, 100, 40, "포탈 A")
btn_portal_b = Button(500, 70, 100, 40, "포탈 B")
btn_eraser = Button(620, 70, 100, 40, "지우개")

buttons = [btn_start, btn_stop, btn_clear, btn_back,
           btn_mirror, btn_lens, btn_blackhole, btn_portal_a, btn_portal_b, btn_eraser]

# --- 레벨 로드 ---
def load_level(filename):
    """JSON 파일에서 레벨 불러오기"""
    global emitters, targets, mirrors, lenses, portals_a, portals_b, blackholes, player_objects
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # 고정 오브젝트만 로드 (발사장치, 목표지점)
        emitters.clear()
        targets.clear()
        mirrors.clear()
        lenses.clear()
        portals_a.clear()
        portals_b.clear()
        blackholes.clear()
        player_objects.clear()

        # 발사장치와 목표지점만 로드 (플레이어가 배치할 수 없음)
        for e in data.get("emitters", []):
            emitters.append(Emitter(e["x"], e["y"], e.get("color","white"), e.get("angle",0)))
        for t in data.get("targets", []):
            targets.append(Target(t["x"], t["y"], t.get("color","white")))
        
        # 맵 인덱스 기반으로 BGM 재생 (없으면 중지)
        map_idx = data.get("map_index")
        play_bgm_for_map(map_idx)
        
        # 나머지는 힌트로만 표시 (선택사항)
#        for m in data.get("mirrors", []):
#            mirrors.append(Mirror(m["x"], m["y"], m.get("angle",0)))
#        for l in data.get("lenses", []):
#            lenses.append(Lens(l["x"], l["y"], l.get("angle",0)))
#        for p in data.get("portals_a", []):
#            portals_a.append(Portal(p["x"], p["y"], 'A'))
#        for p in data.get("portals_b", []):
#            portals_b.append(Portal(p["x"], p["y"], 'B'))
#        for b in data.get("blackholes", []):
#            blackholes.append(Blackhole(b["x"], b["y"]))
        
        print(f"레벨 로드 완료: {filename}")
        print(f"발사장치: {len(emitters)}개, 목표지점: {len(targets)}개")
    except Exception as e:
        print(f"레벨 로드 실패: {e}")

# --- 빛 시뮬레이션 ---
def simulate_light(surface):
    """빛의 경로를 시뮬레이션"""
    MAX_STEPS = 20000
    MAX_BOUNCES = 64
    NUDGE = 2.0

    for t in targets:
        t.hit = False

    # 플레이어가 배치한 오브젝트로 임시 리스트 생성
    temp_mirrors = list(mirrors) + [obj for obj in player_objects if isinstance(obj, Mirror)]
    temp_lenses = list(lenses) + [obj for obj in player_objects if isinstance(obj, Lens)]
    temp_portals_a = list(portals_a) + [obj for obj in player_objects if isinstance(obj, Portal) and obj.portal_type == 'A']
    temp_portals_b = list(portals_b) + [obj for obj in player_objects if isinstance(obj, Portal) and obj.portal_type == 'B']
    temp_blackholes = list(blackholes) + [obj for obj in player_objects if isinstance(obj, Blackhole)]

    for emitter in emitters:
        ray_queue = [(emitter.x, emitter.y, emitter.angle, emitter.color, set(), 0)]

        while ray_queue:
            x, y, angle, color_name, inside_lenses, bounces = ray_queue.pop(0)
            steps = 0

            while steps < MAX_STEPS:
                steps += 1
                x += math.cos(math.radians(angle))
                y += math.sin(math.radians(angle))

                if not (0 <= x < WIDTH and 0 <= y < HEIGHT):
                    break

                # 거울 반사
                reflected = False
                for m in temp_mirrors:
                    if near(x, y, m.x, m.y):
                        angle = angle_wrap(2 * m.angle - angle)
                        x, y = advance(x, y, angle, NUDGE)
                        bounces += 1
                        reflected = True
                        break
                if reflected:
                    if bounces > MAX_BOUNCES: break
                    pygame.draw.circle(surface, COLORS[color_name], (int(x), int(y)), 2)

                if not (0 <= x < WIDTH and 0 <= y < HEIGHT):
                    break

                # 렌즈: 45도 꺾기
                bent = False
                for lz in temp_lenses:
                    lid = id(lz)
                    dist = math.sqrt((x - lz.x)**2 + (y - lz.y)**2)
                    if dist < 3 and lid not in inside_lenses:
                        angle = angle_wrap(angle + 45)
                        inside_lenses.add(lid)
                        x, y = advance(x, y, angle, NUDGE)
                        bounces += 1
                        bent = True
                        break
                if bent:
                    if bounces > MAX_BOUNCES: break
                    pygame.draw.circle(surface, COLORS[color_name], (int(x), int(y)), 2)

                for lz in temp_lenses:
                    lid = id(lz)
                    if lid in inside_lenses:
                        dist = math.sqrt((x - lz.x)**2 + (y - lz.y)**2)
                        if dist > RADIUS * 2:
                            inside_lenses.remove(lid)

                # 포탈
                teleported = False
                for pa in temp_portals_a:
                    if near(x, y, pa.x, pa.y):
                        if len(temp_portals_b) > 0:
                            pb = temp_portals_b[0]
                            x, y = pb.x, pb.y
                            x, y = advance(x, y, angle, NUDGE * 2)
                            teleported = True
                            break
                if teleported:
                    pygame.draw.circle(surface, COLORS[color_name], (int(x), int(y)), 2)
                    continue

                # 블랙홀
                absorbed = False
                for bh in temp_blackholes:
                    if near(x, y, bh.x, bh.y):
                        absorbed = True
                        break
                if absorbed:
                    break

                # 목표 체크
                for tg in targets:
                    if near(x, y, tg.x, tg.y):
                        if color_name == 'white':
                            tg.hit = True
                            pygame.draw.circle(surface, (255, 255, 0), (int(tg.x), int(tg.y)), RADIUS+6, 3)
                            break
                else:
                    pygame.draw.circle(surface, COLORS[color_name], (int(x), int(y)), 2)
                    if bounces > MAX_BOUNCES:
                        break
                    continue
                break

def check_game_complete():
    """게임 완료 조건 체크"""
    if len(targets) == 0:
        return False
    for t in targets:
        if not t.hit:
            return False
    return True

# --- 메인 ---
def main():
    global object_mode, game_started, player_objects
    
    # 레벨 파일 로드
    if len(sys.argv) > 1:
        level_file = sys.argv[1]
    else:
        level_file = "level_0.json"
    print(f"📂 레벨 파일 로드 시도: {level_file}")

    # 오디오 초기화
    init_audio()

    load_level(level_file)
    
    print(f"✅ 발사장치: {len(emitters)}개")
    print(f"✅ 목표지점: {len(targets)}개")
    print(f"✅ 거울: {len(mirrors)}개")
    print(f"✅ 렌즈: {len(lenses)}개")

    if len(emitters) > 0:
        print(f"   발사장치 위치: ({emitters[0].x}, {emitters[0].y})")
    if len(targets) > 0:
        print(f"   목표지점 위치: ({targets[0].x}, {targets[0].y})")

    running = True
    last_selected = None

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos

                # 버튼 처리
                if btn_start.is_clicked((mx, my)):
                    game_started = True
                    continue
                if btn_stop.is_clicked((mx, my)):
                    game_started = False
                    continue
                if btn_clear.is_clicked((mx, my)):
                    player_objects.clear()
                    game_started = False
                    object_mode = None
                    continue
                if btn_back.is_clicked((mx, my)):
                    running = False
                    continue

                if btn_mirror.is_clicked((mx, my)):
                    object_mode = 'mirror'
                    continue
                if btn_lens.is_clicked((mx, my)):
                    object_mode = 'lens'
                    continue
                if btn_blackhole.is_clicked((mx, my)):
                    object_mode = 'blackhole'
                    continue
                if btn_portal_a.is_clicked((mx, my)):
                    object_mode = 'portal_a'
                    continue
                if btn_portal_b.is_clicked((mx, my)):
                    object_mode = 'portal_b'
                    continue
                if btn_eraser.is_clicked((mx, my)):
                    object_mode = 'eraser'
                    continue

                # 오브젝트 배치/삭제
                gx, gy = snap_to_grid(mx, my)
                
                if object_mode == 'mirror':
                    obj = Mirror(gx, gy, 45)
                    player_objects.append(obj)
                    last_selected = obj
                elif object_mode == 'lens':
                    obj = Lens(gx, gy, 0)
                    player_objects.append(obj)
                    last_selected = obj
                elif object_mode == 'blackhole':
                    obj = Blackhole(gx, gy)
                    player_objects.append(obj)
                    last_selected = obj
                elif object_mode == 'portal_a':
                    obj = Portal(gx, gy, 'A')
                    player_objects.append(obj)
                    last_selected = obj
                elif object_mode == 'portal_b':
                    obj = Portal(gx, gy, 'B')
                    player_objects.append(obj)
                    last_selected = obj
                elif object_mode == 'eraser':
                    for obj in player_objects[:]:
                        if hasattr(obj, 'x') and hasattr(obj, 'y') and near(mx, my, obj.x, obj.y):
                            player_objects.remove(obj)
                            break

            elif event.type == pygame.MOUSEWHEEL and last_selected is not None:
                if isinstance(last_selected, (Mirror, Emitter)):
                    last_selected.rotate()
                elif isinstance(last_selected, Lens):
                    last_selected.angle = angle_wrap(last_selected.angle + event.y * 5)

        # 그리기
        screen.fill((30, 30, 30))
        
        # 그리드 그리기
        draw_grid(screen)

        # 버튼 그리기
        for b in buttons:
            b.draw(screen, FONT)

        # 상태 표시
        mode_text = f"선택 도구: {object_mode if object_mode else '없음'}  |  상태: {'실행중' if game_started else '대기'}"
        screen.blit(FONT.render(mode_text, True, (230,230,230)), (20, 130))

        # 안내 메시지
        info = [
            "좌클릭: 도구 배치 | 마우스 휠: 회전 | 지우개: 도구 삭제",
            "목표: 발사장치에서 나온 빛이 목표지점에 도달하도록 도구 배치"
        ]
        for i, line in enumerate(info):
            screen.blit(FONT.render(line, True, (180,180,180)), (20, 160 + i*22))

        # 고정 오브젝트 그리기 (반투명)
#        for m in mirrors:
#            m.draw(screen)
#            # 힌트 표시 (반투명)
#            s = pygame.Surface((RADIUS*4, RADIUS*4), pygame.SRCALPHA)
#            pygame.draw.circle(s, (255, 255, 0, 80), (RADIUS*2, RADIUS*2), RADIUS*2, 2)
#            screen.blit(s, (m.x - RADIUS*2, m.y - RADIUS*2))
#        for l in lenses:
#            l.draw(screen)
#            s = pygame.Surface((RADIUS*4, RADIUS*4), pygame.SRCALPHA)
#            pygame.draw.circle(s, (255, 255, 0, 80), (RADIUS*2, RADIUS*2), RADIUS*2, 2)
#            screen.blit(s, (l.x - RADIUS*2, l.y - RADIUS*2))

        # 발사장치와 목표지점 (고정)
        for e in emitters:
            e.draw(screen)
        for t in targets:
            t.draw(screen)

        # 플레이어가 배치한 오브젝트
        for obj in player_objects:
            obj.draw(screen)

        # 게임 시작 시 빛 시뮬레이션
        if game_started:
            simulate_light(screen)
            
            if check_game_complete():
                complete_text = FONT_BIG.render("★ 퍼즐 완료! ★", True, (255, 255, 0))
                complete_rect = complete_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
                bg_rect = complete_rect.inflate(40, 20)
                pygame.draw.rect(screen, (0, 100, 0), bg_rect, border_radius=10)
                pygame.draw.rect(screen, (255, 255, 0), bg_rect, 3, border_radius=10)
                screen.blit(complete_text, complete_rect)

        pygame.display.flip()
        clock.tick(FPS)

    # 종료 시 BGM 정지
    try:
        pygame.mixer.music.stop()
        pygame.mixer.quit()
    except Exception:
        pass

    pygame.quit()

if __name__ == "__main__":
    main()