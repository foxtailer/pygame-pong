import pygame


WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (180, 180, 180)


class Button:
    def __init__(self, x, y, width, height, text, font, bg_color=GRAY, text_color=BLACK):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.bg_color = bg_color
        self.text_color = text_color
        self.hover_color = (min(bg_color[0] + 30, 255), 
                            min(bg_color[1] + 30, 255),
                            min(bg_color[2] + 30, 255))

    def draw(self, screen):
        """Draw the button on the screen with hover effect"""
        mouse_pos = pygame.mouse.get_pos()
        color = self.hover_color if self.rect.collidepoint(mouse_pos) else self.bg_color
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, BLACK, self.rect, 2)  # border

        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def is_clicked(self, event):
        """Return True if button was clicked"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False



def show_ingame_menu(screen):
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 40)

    cx = screen.get_width() // 2
    cy = screen.get_height() // 2

    quit_btn = Button(cx - 100, cy, 200, 50, "Quit", font,
                      bg_color=(220, 20, 60), text_color=WHITE)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return True

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if quit_btn.is_clicked(event):
                    return False

        # --- DRAW BUTTONS ---
        quit_btn.draw(screen)

        pygame.display.flip()
        clock.tick(60)