import os
import sys
import json
import logging
import pygame

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def get_display_rect(img_w, img_h, win_w, win_h):
    if img_w == 0 or img_h == 0: return 0, 0, 0, 0, 1.0
    scale = min(win_w / img_w, win_h / img_h, 1.0)
    sw, sh = int(img_w * scale), int(img_h * scale)
    return sw, sh, (win_w - sw) // 2, (win_h - sh) // 2, scale

def screen_to_image(sx, sy, off_x, off_y, scale):
    if scale <= 0: return 0, 0
    return int((sx - off_x) / scale), int((sy - off_y) / scale)

def run_manual_cutter(image_path):
    pygame.init()
    win_w, win_h = 1024, 768
    screen = pygame.display.set_mode((win_w, win_h), pygame.RESIZABLE)
    pygame.display.set_caption("S: Save | Backspace: Undo | Q: Quit")

    try:
        surface = pygame.image.load(image_path).convert_alpha()
    except Exception as e:
        print(f"Ошибка загрузки картинки: {e}")
        pygame.quit()
        return

    img_w, img_h = surface.get_size()
    boxes = []
    drag_start = None
    clock = pygame.time.Clock()

    running = True
    while running:
        sw, sh, off_x, off_y, scale = get_display_rect(img_w, img_h, win_w, win_h)
        scaled = pygame.transform.scale(surface, (sw, sh)) if scale != 1.0 else surface

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                win_w, win_h = event.w, event.h
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                drag_start = event.pos
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and drag_start:
                x1, y1 = screen_to_image(*drag_start, off_x, off_y, scale)
                x2, y2 = screen_to_image(*event.pos, off_x, off_y, scale)
                x, y = max(0, min(x1, x2)), max(0, min(y1, y2))
                w, h = min(abs(x2-x1), img_w-x), min(abs(y2-y1), img_h-y)
                if w > 0 and h > 0: boxes.append([x, y, w, h])
                drag_start = None
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_s:
                    data = {"image": os.path.basename(image_path), "boxes": boxes}
                    logger.info("Результат разметки:\n%s", json.dumps(data, ensure_ascii=False, indent=2))
                    running = False # Выходим после логирования
                elif event.key == pygame.K_BACKSPACE and boxes:
                    boxes.pop()
                elif event.key in (pygame.K_q, pygame.K_ESCAPE):
                    running = False

        screen.fill((30, 30, 30))
        screen.blit(scaled, (off_x, off_y))
        for (ix, iy, iw, ih) in boxes:
            pygame.draw.rect(screen, (0, 255, 0), (off_x+ix*scale, off_y+iy*scale, iw*scale, ih*scale), 2)
        if drag_start:
            mx, my = pygame.mouse.get_pos()
            pygame.draw.rect(screen, (255, 255, 0), (min(drag_start[0], mx), min(drag_start[1], my), abs(mx-drag_start[0]), abs(my-drag_start[1])), 2)
        
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

def main():
    # Если запускаете через VS Code, убедитесь, что cloud_3.png лежит в той же папке
    img = "sheep_2-1.png"
    if len(sys.argv) >= 2: img = sys.argv[1]
    if not os.path.exists(img):
        print(f"Файл не найден: {img}")
        return
    run_manual_cutter(img)

if __name__ == "__main__":
    main()