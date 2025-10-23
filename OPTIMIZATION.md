# 🚀 최적화 제안사항

## 📌 현재 코드의 최적화 가능 영역

### 1. **빛 시뮬레이션 성능 최적화**
```python
# 현재: 매 프레임마다 모든 오브젝트와 충돌 체크 (O(n*m))
for _ in range(1000):
    for mirror in mirrors:  # 반복
        if near(x, y, mirror.x, mirror.y):
            ...
```

**개선 방안:**
- **공간 분할 (Spatial Partitioning)**: 그리드 기반 충돌 감지
  - 맵을 그리드로 나누고 각 셀에 오브젝트 저장
  - 충돌 체크 시 현재 위치의 셀만 검사 → O(1) 수준으로 개선
- **quadtree** 자료구조 사용 (큰 맵에서 효과적)

---

### 2. **렌즈/프리즘 충돌 감지 최적화**
```python
# 현재: 원의 거리 계산을 매번 수행
inside_now = ((x - lz.x)**2 + (y - lz.y)**2) <= (RADIUS*RADIUS)
```

**개선 방안:**
- 경계 상자(AABB) 사전 체크 후 정밀 검사
```python
if abs(x - lz.x) <= RADIUS and abs(y - lz.y) <= RADIUS:
    # 그 다음 정확한 원 충돌 검사
    if (x - lz.x)**2 + (y - lz.y)**2 <= RADIUS*RADIUS:
        ...
```

---

### 3. **오브젝트 그리기 최적화**
```python
# 현재: 매 프레임 모든 오브젝트 재그리기
for e in emitters:   e.draw(screen)
for t in targets:    t.draw(screen)
...
```

**개선 방안:**
- **레이어 분리**: 정적 오브젝트는 별도 Surface에 미리 그려두고 재사용
```python
static_layer = pygame.Surface((WIDTH, HEIGHT))
# 오브젝트 배치/삭제 시에만 재그리기
def redraw_static():
    static_layer.fill((30, 30, 30))
    for m in mirrors: m.draw(static_layer)
    ...
# 메인 루프
screen.blit(static_layer, (0, 0))  # 빠른 복사
```

---

### 4. **빛 경로 캐싱**
```python
# 현재: 게임 시작 버튼 누르면 매 프레임 재계산
if game_started:
    simulate_light(screen)
```

**개선 방안:**
- 오브젝트 변경이 없으면 빛 경로를 Surface에 캐싱
- 오브젝트 추가/삭제/이동 시에만 재계산

---

### 5. **삼각함수 계산 최적화**
```python
# 현재: 매 픽셀마다 삼각함수 계산
x += math.cos(math.radians(angle))
y += math.sin(math.radians(angle))
```

**개선 방안:**
- 각도가 바뀔 때만 계산하고 결과 저장
```python
dx = math.cos(math.radians(angle))
dy = math.sin(math.radians(angle))
for _ in range(distance):
    x += dx
    y += dy
```

---

### 6. **렌즈 굴절 중복 계산 제거**
```python
# 현재: 진입/이탈 시마다 법선 계산
normal_deg = math.degrees(math.atan2(y - lz.y, x - lz.x))
```

**개선 방안:**
- 법선은 렌즈 중심에서 점까지의 방향이므로, 벡터 정규화만 수행
- 또는 근사법 사용 (작은 렌즈는 평면 근사)

---

### 7. **메모리 최적화**
```python
# 현재: 광선 큐에서 set를 복사
ray_queue.append( (..., set(inside_lenses), set(list(inside_prisms) + [pid]), ...) )
```

**개선 방안:**
- frozenset 사용하거나 비트마스크로 상태 관리
- 광선이 많을 때 메모리 사용량 감소

---

### 8. **Button 클래스 이벤트 처리 개선**
```python
# 현재: 버튼마다 개별 if 체크
if btn_start.is_clicked((mx, my)): ...
elif btn_stop.is_clicked((mx, my)): ...
```

**개선 방안:**
- 버튼 매니저 클래스로 통합 관리
```python
class ButtonManager:
    def __init__(self):
        self.buttons = {}
    def add(self, name, button, callback):
        self.buttons[name] = (button, callback)
    def handle_click(self, pos):
        for btn, callback in self.buttons.values():
            if btn.is_clicked(pos):
                callback()
                return True
```

---

## 📊 예상 성능 향상

| 최적화 항목 | 예상 FPS 향상 | 난이도 |
|------------|--------------|--------|
| 공간 분할 | 2~5배 | 중 |
| 레이어 분리 | 1.5~2배 | 하 |
| 빛 경로 캐싱 | 3~10배 | 중 |
| 삼각함수 최적화 | 1.2~1.5배 | 하 |

---

## ⚠️ 주의사항

1. **조기 최적화 금지**: 기능 구현 완료 후 병목 지점 프로파일링
2. **가독성 유지**: 최적화로 코드가 복잡해지면 주석 필수
3. **테스트**: 최적화 후 동작 정확성 검증

---

## 🛠️ 프로파일링 방법
```python
import cProfile
cProfile.run('main()', sort='cumtime')
```

또는 pygame에서 FPS 측정:
```python
print(f"FPS: {clock.get_fps():.1f}")
```
