"""
게임 오브젝트 클래스 정의
- Emitter: 빛 발사 장치
- Target: 목표 지점
- Mirror: 거울 (반사)
- Lens: 렌즈 (굴절)
- Prism: 프리즘 (분광)
- Blackhole: 블랙홀 (흡수)
- Button: UI 버튼
"""

import pygame
import math

# 상수
RADIUS = 18  # 공통 반경(충돌/선택)

COLORS = {
    "white": (255, 255, 255),
    "red":   (255, 0, 0),
    "green": (0, 255, 0),
    "blue":  (0, 0, 255),
}


class Button:
    """UI 버튼 클래스"""
    def __init__(self, x, y, w, h, text):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color_idle = (70, 70, 160)
        self.color_hover = (90, 90, 200)
    
    def draw(self, surface, font):
        color = self.color_hover if self.rect.collidepoint(pygame.mouse.get_pos()) else self.color_idle
        pygame.draw.rect(surface, color, self.rect, border_radius=6)
        txt = font.render(self.text, True, (255, 255, 255))
        surface.blit(txt, (self.rect.x + 10, self.rect.y + 6))
    
    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)


class Emitter:
    """빛 발사 장치 (흰색 빛)"""
    def __init__(self, x, y, color='white', angle=0):
        self.x, self.y, self.color, self.angle = x, y, color, angle
    
    def draw(self, surf):
        pygame.draw.circle(surf, COLORS[self.color], (int(self.x), int(self.y)), RADIUS, 2)
        dx = math.cos(math.radians(self.angle)) * 24
        dy = math.sin(math.radians(self.angle)) * 24
        pygame.draw.line(surf, COLORS[self.color], (self.x, self.y), (self.x + dx, self.y + dy), 2)


class Target:
    """목표 지점 (흰색)"""
    def __init__(self, x, y, color='white'):
        self.x, self.y, self.color = x, y, color
        self.hit = False  # 빛을 받았는지 여부
    
    def draw(self, surf):
        # 빛을 받았으면 채워진 원, 안 받았으면 테두리만
        if self.hit:
            pygame.draw.circle(surf, COLORS[self.color], (int(self.x), int(self.y)), RADIUS, 0)
        else:
            pygame.draw.circle(surf, COLORS[self.color], (int(self.x), int(self.y)), RADIUS, 3)


class ColorTarget:
    """색상 목표 지점 (R, G, B 중 하나)"""
    def __init__(self, x, y, color):
        self.x, self.y, self.color = x, y, color
        self.hit = False  # 빛을 받았는지 여부
    
    def draw(self, surf):
        # 빛을 받았으면 밝게 채워진 원, 안 받았으면 어둡게
        if self.hit:
            pygame.draw.circle(surf, COLORS[self.color], (int(self.x), int(self.y)), RADIUS, 0)
        else:
            # 어두운 색상으로 표시
            dark_color = tuple(c // 3 for c in COLORS[self.color])
            pygame.draw.circle(surf, dark_color, (int(self.x), int(self.y)), RADIUS, 3)
            pygame.draw.circle(surf, dark_color, (int(self.x), int(self.y)), RADIUS - 5, 0)


class Mirror:
    """거울 (반사)"""
    def __init__(self, x, y, angle=0):
        self.x, self.y, self.angle = x, y, angle
    
    def draw(self, surf):
        length = 36
        dx = math.cos(math.radians(self.angle)) * length
        dy = math.sin(math.radians(self.angle)) * length
        pygame.draw.line(surf, (200, 200, 200), (self.x - dx, self.y - dy), (self.x + dx, self.y + dy), 3)
        pygame.draw.circle(surf, (200, 200, 200), (int(self.x), int(self.y)), 4)


class Lens:
    """렌즈 (굴절) - 맵의 굴절률 설정을 따름"""
    def __init__(self, x, y, angle=0, refract_index=None):
        self.x, self.y, self.angle = x, y, angle
        # refract_index가 None이면 맵 설정을 따르도록 함
        self.refract_index = refract_index
    
    def get_refract_index(self, map_refract_index):
        """렌즈의 굴절률 반환 (None이면 맵 설정 사용)"""
        return self.refract_index if self.refract_index is not None else map_refract_index
    
    def draw(self, surf):
        pygame.draw.circle(surf, (100, 180, 255), (int(self.x), int(self.y)), RADIUS, 0)
        pygame.draw.circle(surf, (20, 60, 120), (int(self.x), int(self.y)), RADIUS, 2)


class Prism:
    """프리즘 (분광)"""
    def __init__(self, x, y, angle=0):
        self.x, self.y, self.angle = x, y, angle
    
    def draw(self, surf):
        pygame.draw.polygon(surf, (180, 120, 80), [
            (self.x - RADIUS, self.y + RADIUS),
            (self.x, self.y - RADIUS),
            (self.x + RADIUS, self.y + RADIUS),
        ], 0)
        pygame.draw.polygon(surf, (80, 50, 30), [
            (self.x - RADIUS, self.y + RADIUS),
            (self.x, self.y - RADIUS),
            (self.x + RADIUS, self.y + RADIUS),
        ], 2)


class Blackhole:
    """블랙홀 (흡수)"""
    def __init__(self, x, y):
        self.x, self.y = x, y
    
    def draw(self, surf):
        pygame.draw.circle(surf, (0, 0, 0), (int(self.x), int(self.y)), RADIUS, 0)
        pygame.draw.circle(surf, (90, 90, 90), (int(self.x), int(self.y)), RADIUS, 2)
