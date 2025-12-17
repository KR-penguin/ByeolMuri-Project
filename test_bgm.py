import os
import time
import pygame

BGM = os.path.join(os.path.dirname(__file__), 'assets', 'bgm', '경쾌한 BGM.mp3')
print('테스트 BGM 경로:', BGM)
if not os.path.isfile(BGM):
    print('파일이 존재하지 않습니다. 경로를 확인하고 assets/bgm/경쾌한 BGM.mp3을 추가하세요.')
    raise SystemExit(1)

try:
    pygame.mixer.init()
    print('pygame.mixer 초기화 성공')
except Exception as e:
    print('pygame.mixer 초기화 실패:', e)
    raise

try:
    pygame.mixer.music.load(BGM)
    pygame.mixer.music.set_volume(0.8)
    pygame.mixer.music.play(-1)
    print('재생 시작: 10초간 재생 후 정지합니다...')
    time.sleep(10)
    pygame.mixer.music.stop()
    pygame.mixer.quit()
    print('재생 완료, 종료')
except Exception as e:
    print('재생 실패:', e)
    raise