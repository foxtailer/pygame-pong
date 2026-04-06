import pygame

from tools import show_ingame_menu


pygame.init()


# ---------------- SCREEN ----------------
info = pygame.display.Info()

SCREEN_WIDTH =  info.current_w
SCREEN_HEIGHT = info.current_h
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
MID = SCREEN_WIDTH // 2
FPS = 60


# ---------------- COLORS ----------------
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)


# ---------------- SETTINGS ----------------
PADDLE_WIDTH, PADDLE_HEIGHT = 120, 12
BALL_RADIUS = 8
WINNING_SCORE = 10
SCORE_FONT = pygame.font.SysFont("comicsans", 50)


# ---------------- PADDLE ----------------
class Paddle:
    COLOR = WHITE
    VEL = 7

    def __init__(self, x, y):
        self.x = self.original_x = x
        self.y = self.original_y = y
        self.width = PADDLE_WIDTH
        self.height = PADDLE_HEIGHT

    def draw(self, win1, win2):
        # original
        pygame.draw.rect(win1, self.COLOR, (self.x, self.y, self.width, self.height))

        # mirrored
        mirror_y = SCREEN_HEIGHT - self.y - self.height
        mirror_x = MID - self.x - self.width
        pygame.draw.rect(win2, self.COLOR, (mirror_x, mirror_y, self.width, self.height))

    def move(self, left=True):
        if left:
            self.x -= self.VEL
        else:
            self.x += self.VEL

    def reset(self):
        self.x = self.original_x
        self.y = self.original_y


# ---------------- BALL ----------------
class Ball:
    COLOR = WHITE
    MAX_VEL = 6

    def __init__(self, x, y):
        self.x = self.original_x = x
        self.y = self.original_y = y
        self.radius = BALL_RADIUS
        self.x_vel = 0
        self.y_vel = self.MAX_VEL

    def draw(self, win1, win2):
        pygame.draw.circle(win1, self.COLOR, (self.x, self.y), self.radius)

        mirror_y = SCREEN_HEIGHT - self.y - self.radius
        mirror_x = MID - self.x - self.radius
        pygame.draw.circle(win2, self.COLOR, (mirror_x, mirror_y), self.radius)

    def move(self):
        self.x += self.x_vel
        self.y += self.y_vel

    def reset(self):
        direction = 1 if self.y_vel >= 0 else -1
        self.x = self.original_x
        self.y = self.original_y
        # Drop speed to default
        self.y_vel = self.MAX_VEL * direction
        self.y_vel *= -1
        self.x_vel = 0


# ---------------- DRAW ----------------
def draw(screen, win, left_paddle, right_paddle, ball, left_score, right_score):
    screen.fill(BLACK)
    l_win, r_win = win
    l_win.fill(BLACK)
    r_win.fill(BLACK)

    # paddles
    left_paddle.draw(l_win, r_win)
    right_paddle.draw(r_win, l_win)

    # ball
    ball.draw(l_win, r_win)

    # windows
    screen.blit(l_win, (0, 0))
    screen.blit(r_win, (MID, 0))

    # middle divider
    pygame.draw.line(screen, WHITE, (MID, 0), (MID, SCREEN_HEIGHT), 2)

    # score
    left_text = SCORE_FONT.render(str(left_score), True, WHITE)
    right_text = SCORE_FONT.render(str(right_score), True, WHITE)

    screen.blit(left_text, (MID - left_text.get_width() - 5, SCREEN_HEIGHT // 2))
    screen.blit(right_text, (MID + right_text.get_width() - 10, SCREEN_HEIGHT // 2))

    pygame.display.flip()


# ---------------- COLLISION ----------------
def handle_collision(ball, left_paddle, right_paddle):
    # walls
    if ball.x - ball.radius <= 0 or ball.x + ball.radius >= MID:
        ball.x_vel *= -1

    # left paddle
    if ball.y_vel < 0:  # Fly up.
        mirror_y = 20 + right_paddle.height  # 40 is a padding from screen border to paddle
        mirror_x = MID - right_paddle.x - right_paddle.width
        if ball.x >= mirror_x and ball.x <= mirror_x + right_paddle.width:  # Ball in coredor against paddle
            if ball.y - ball.radius <= mirror_y:  # Collision
                ball.y_vel *= -1  # Revers(bounce)
                ball.y_vel *= 1.05  # Axelerator

                # Reflection angle
                middle_x = mirror_x + right_paddle.width / 2
                difference_in_x = middle_x - ball.x
                reduction_factor = (right_paddle.width / 2) / ball.MAX_VEL
                y_vel = difference_in_x / reduction_factor
                ball.x_vel = -1 * y_vel
    # right paddle
    else:  # Fly down
        if ball.x >= left_paddle.x and ball.x <= left_paddle.x + left_paddle.width:  # Ball in coredor against paddle
            if ball.y + ball.radius >= left_paddle.y:  # Collision
                ball.y_vel *= -1  # Revers(bounce)
                ball.y_vel *= 1.05  # Axelerator

                # Reflection angle
                middle_x = left_paddle.x + left_paddle.width / 2
                difference_in_x = middle_x - ball.x
                reduction_factor = (left_paddle.width / 2) / ball.MAX_VEL
                y_vel = difference_in_x / reduction_factor
                ball.x_vel = -1 * y_vel

# ---------------- MOVEMENT ----------------
def handle_paddle_movement(keys, left_paddle, right_paddle):
    # LEFT PLAYER (A / D)
    if keys[pygame.K_a] and left_paddle.x > 0:
        left_paddle.move(left=True)
    if keys[pygame.K_d] and left_paddle.x + left_paddle.width < MID:
        left_paddle.move(left=False)

    # RIGHT PLAYER (LEFT / RIGHT)
    if keys[pygame.K_LEFT] and right_paddle.x > 0:
        right_paddle.move(left=True)
    if keys[pygame.K_RIGHT] and right_paddle.x + right_paddle.width < MID:
        right_paddle.move(left=False)


# ---------------- MAIN ----------------
def main():
    run = True
    paused = False
    clock = pygame.time.Clock()

    left_paddle = Paddle(MID // 2 - 60, SCREEN_HEIGHT - 40)
    right_paddle = Paddle(MID // 2 - 60, SCREEN_HEIGHT - 40)

    ball = Ball(MID // 2, MID // 2)

    left_window = pygame.Surface((MID, SCREEN_HEIGHT))
    right_window = pygame.Surface((MID, SCREEN_HEIGHT))

    left_score = 0
    right_score = 0

    while run:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                        run = show_ingame_menu(SCREEN)

        if paused:
            continue

        # input
        keys = pygame.key.get_pressed()
        handle_paddle_movement(keys, left_paddle, right_paddle)

        # update
        ball.move()
        handle_collision(ball, left_paddle, right_paddle)

        # scoring
        if ball.y < 0:
            right_score += 1
            ball.reset()
        elif ball.y > SCREEN_HEIGHT:
            left_score += 1
            ball.reset()

        # win condition
        if left_score >= WINNING_SCORE or right_score >= WINNING_SCORE:
            win_text = "Left Wins!" if left_score > right_score else "Right Wins!"
            text = SCORE_FONT.render(win_text, True, WHITE)
            SCREEN.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2,
                            SCREEN_HEIGHT // 2 - text.get_height() // 2))
            pygame.display.update()
            pygame.time.delay(3000)

            left_score = 0
            right_score = 0
            ball.reset()
            left_paddle.reset()
            right_paddle.reset()

        # render
        draw(SCREEN, (left_window, right_window), left_paddle, right_paddle, ball, left_score, right_score)

    pygame.quit()


if __name__ == "__main__":
    main()
