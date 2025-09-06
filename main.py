
# pygame을 이용한 간단한 대화창 예제 (dialogs.json에서 대사 불러오기)
import pygame
import sys
import json
import os

pygame.init()

# 화면 크기
WIDTH, HEIGHT = 1280, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('별무리')

# 폰트 설정(맑은 고딕, 글자 크기 24)
FONT = pygame.font.SysFont('malgungothic', 24)

# 색상(색상 정의)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)

# 대화창 상태
dialog_open = False  # 대화창 열림 여부
current_idx = 0  # 현재 대사 인덱스

# 대사 파일 경로
DIALOG_PATH = os.path.join(os.path.dirname(__file__), "dialogs.json") 

# 대사 불러오기
def load_dialogs():
	if not os.path.exists(DIALOG_PATH):
		return ["대사 파일이 없습니다."]
	with open(DIALOG_PATH, 'r', encoding='utf-8') as f:
		return json.load(f)

npc_dialogues = load_dialogs()

clock = pygame.time.Clock()



def draw_npc_dialogue():
	screen.fill(WHITE)
	# NPC 대화창 배경
	dialogue_box = pygame.Rect(50, HEIGHT - 180, WIDTH - 100, 120)
	pygame.draw.rect(screen, GRAY, dialogue_box, border_radius=10)
	pygame.draw.rect(screen, BLACK, dialogue_box, 3, border_radius=10)
	# NPC 대사 출력
	if current_idx < len(npc_dialogues):
		lines = []
		text = npc_dialogues[current_idx]
		# 긴 문장은 자동 줄바꿈
		while len(text) > 0:
			line = text[:50]
			lines.append(line)
			text = text[50:]
		y = HEIGHT - 160
		for line in lines:
			msg_surface = FONT.render(line, True, BLACK)
			screen.blit(msg_surface, (70, y))
			y += 36
	else:
		msg_surface = FONT.render("대화가 끝났습니다. ESC로 창이 닫힙니다.", True, BLACK)
		screen.blit(msg_surface, (70, HEIGHT - 140))
	pygame.display.flip()


while True:
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			pygame.quit()
			sys.exit()
		elif event.type == pygame.KEYDOWN:
			# 스페이스바로 대화창 열기/닫기
			if event.key == pygame.K_SPACE:
				if not dialog_open:
					dialog_open = True
					current_idx = 0
				elif dialog_open:
					# 대화 중이면 다음 대사
					if current_idx < len(npc_dialogues):
						current_idx += 1
					# 마지막 대사 이후에는 창 닫기
					if current_idx >= len(npc_dialogues):
						dialog_open = False
			# ESC로 프로그램 종료
			elif event.key == pygame.K_ESCAPE:
				pygame.quit()
				sys.exit()
			# 왼쪽/오른쪽 화살표로 대사 이동 (대화창이 열려 있을 때만)
			elif dialog_open and event.key == pygame.K_RIGHT:
				if current_idx < len(npc_dialogues) - 1:
					current_idx += 1
			elif dialog_open and event.key == pygame.K_LEFT:
				if current_idx > 0:
					current_idx -= 1
	if dialog_open:
		draw_npc_dialogue()
	else:
		screen.fill(WHITE)
		msg_surface = FONT.render("스페이스바를 눌러 대화창을 여세요.", True, BLACK)
		screen.blit(msg_surface, (WIDTH//2 - 200, HEIGHT//2))
		pygame.display.flip()
	clock.tick(30)