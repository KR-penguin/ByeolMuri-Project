"""
유틸리티 함수 모음
- 수학 계산 (각도, 벡터)
- 물리 시뮬레이션 (스넬의 법칙, 굴절)
- 충돌 감지
"""

import math

# 상수
RADIUS = 18
N_AIR = 1.0  # 공기 굴절률


def near(p1x, p1y, p2x, p2y, r=RADIUS):
    """두 점이 반경 r 안에 있는지 확인"""
    return (abs(p1x - p2x) <= r) and (abs(p1y - p2y) <= r)


def angle_wrap(deg):
    """각도를 0~360 범위로 정규화"""
    return deg % 360


def vec_from_angle(deg, length=1.0):
    """각도에서 벡터 생성 (dx, dy)"""
    rad = math.radians(deg)
    return math.cos(rad) * length, math.sin(rad) * length


def advance(x, y, angle, step=2.0):
    """주어진 각도로 step만큼 전진한 좌표 반환"""
    dx, dy = vec_from_angle(angle, step)
    return x + dx, y + dy


def refract_angle(inc_angle_deg, normal_deg, n1, n2):
    """
    스넬의 법칙을 이용한 굴절각 계산
    
    Parameters:
        inc_angle_deg: 입사광선의 진행 방향 (절대각, degree)
        normal_deg: 경계면의 법선 방향 (외향, degree)
        n1: 입사 매질의 굴절률
        n2: 굴절 매질의 굴절률
    
    Returns:
        (new_angle, is_total_reflection): 
            - new_angle: 굴절(또는 반사) 후 진행 방향 (degree)
            - is_total_reflection: 전반사 발생 여부 (bool)
    
    수학 공식:
        n1 * sin(θ1) = n2 * sin(θ2)  (스넬의 법칙)
        
        전반사 조건: |sin(θ2)| = |n1/n2 * sin(θ1)| > 1
    """
    # 입사각 계산 (법선 기준 상대 각도, -180 ~ 180)
    relative_angle = inc_angle_deg - normal_deg
    
    # -180 ~ 180 범위로 정규화
    while relative_angle > 180:
        relative_angle -= 360
    while relative_angle < -180:
        relative_angle += 360
    
    theta1_rad = math.radians(relative_angle)
    
    # 입사각: 법선과 입사광선 사이의 각도 (0 ~ 90도)
    # cos(theta1) > 0이면 법선 방향으로 진입, < 0이면 반대편에서 진입
    cos_theta1 = math.cos(theta1_rad)
    sin_theta1 = math.sin(theta1_rad)
    
    # 법선 반대쪽에서 오는 경우 처리
    if cos_theta1 < 0:
        # 180도 회전
        theta1_rad = math.pi - theta1_rad
        normal_deg = angle_wrap(normal_deg + 180)
        cos_theta1 = -cos_theta1
        sin_theta1 = -sin_theta1
    
    # 스넬의 법칙: sin(θ2) = (n1/n2) * sin(θ1)
    sin_theta2 = (n1 / n2) * abs(sin_theta1)
    
    # 전반사 확인
    if sin_theta2 > 1.0:
        # 전반사: 반사각 = 입사각 (법선 기준 반대편)
        reflected_angle = normal_deg - relative_angle
        return angle_wrap(reflected_angle), True
    
    # 정상 굴절
    theta2_rad = math.asin(sin_theta2)
    
    # 굴절각의 부호는 입사각과 같은 쪽
    if sin_theta1 < 0:
        theta2_rad = -theta2_rad
    
    refracted_angle = normal_deg + math.degrees(theta2_rad)
    return angle_wrap(refracted_angle), False
