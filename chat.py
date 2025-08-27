# pygame을 이용한 간단한 대화창 예제
import pygame
import sys

pygame.init()

# 화면 크기
WIDTH, HEIGHT = 1280, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('별무리')

# 폰트 설정
FONT = pygame.font.SysFont('malgungothic', 24)

# 색상
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)


# NPC 대사 리스트
npc_dialogues = [
	"안녕하세요, 모험가님!",
	"이 마을에 온 것을 환영합니다.",
	"여기서 여러가지 퀘스트를 받을 수 있어요.",
	"궁금한 점이 있으면 언제든 물어보세요!",
	"행운을 빕니다!",
	"이건 32자 이상에 대한 테스트 문장입니다. 자동 줄바꿈이 잘 되는지 확인하기 위한 문장입니다. 길게 작성해 보았습니다."
]
current_idx = 0

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
		msg_surface = FONT.render("대화가 끝났습니다. ESC로 종료하세요.", True, BLACK)
		screen.blit(msg_surface, (70, HEIGHT - 140))
	pygame.display.flip()

while True:
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			pygame.quit()
			sys.exit()
		elif event.type == pygame.KEYDOWN:
			# 오른쪽 화살표 또는 스페이스: 다음 대사
			if event.key == pygame.K_RIGHT or event.key == pygame.K_SPACE:
				if current_idx < len(npc_dialogues):
					current_idx += 1
			# 왼쪽 화살표: 이전 대사
			elif event.key == pygame.K_LEFT:
				if current_idx > 0:
					current_idx -= 1
			# ESC: 종료
			elif event.key == pygame.K_ESCAPE:
				pygame.quit()
				sys.exit()
	draw_npc_dialogue()
	clock.tick(30)