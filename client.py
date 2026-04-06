import json
import socket
from threading import Thread

import pygame

from tools import show_ingame_menu


def connect_to_server():
    while True:
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(('localhost', 8080)) # ---- Підключення до сервера
            buffer = ""
            game_state = {}
            my_id = int(client.recv(24).decode())
            return my_id, game_state, buffer, client
        except:
            pass


def receive():
    global buffer, game_state, game_over, client
    while not game_over:
        try:
            data = client.recv(1024).decode()
            buffer += data
            while "\n" in buffer:
                packet, buffer = buffer.split("\n", 1)
                if packet.strip():
                    game_state = json.loads(packet)
        except:
            game_state["winner"] = -1
            break


pygame.init()

screen = pygame.display.set_mode((750, 800))
clock = pygame.time.Clock()
run = True
paused = False
font_win = pygame.font.Font(None, 72)
font_main = pygame.font.Font(None, 36)
game_over = False
winner = None
you_winner = None
my_id, game_state, buffer, client = connect_to_server()
Thread(target=receive, daemon=True).start()


while run:
    for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                        run = show_ingame_menu(screen)

    
    if "countdown" in game_state and game_state["countdown"] > 0:
        screen.fill((0, 0, 0))
        countdown_text = pygame.font.Font(None, 72).render(str(game_state["countdown"]), True, (255, 255, 255))
        screen.blit(countdown_text, (750 // 2 - 20, 800 // 2 - 30))
        pygame.display.update()
        continue  # Не малюємо гру до завершення відліку

    if "winner" in game_state and game_state["winner"] is not None:
        screen.fill((20, 20, 20))

        if you_winner is None:  # Встановлюємо тільки один раз
            if game_state["winner"] == my_id:
                you_winner = True
            else:
                you_winner = False

        if you_winner:
            text = "Ти переміг!"
        else:
            text = "Пощастить наступним разом!"

        win_text = font_win.render(text, True, (255, 215, 0))
        text_rect = win_text.get_rect(center=(750 // 2, 800 // 2))
        screen.blit(win_text, text_rect)

        text = font_win.render('К - рестарт', True, (255, 215, 0))
        text_rect = text.get_rect(center=(750 // 2, 800 // 2 + 120))
        screen.blit(text, text_rect)

        pygame.display.update()
        continue
        # my_id, game_state, buffer, client = connect_to_server()

    if game_state:
        screen.fill((30, 30, 30))

        if my_id == 1:
            pygame.draw.rect(screen, (255, 0, 255), (game_state['paddles']['1'], 800 - 40, 100, 20))
            pygame.draw.rect(screen, (0, 255, 0), (750 - 100 - game_state['paddles']['0'], 20, 100, 20))
            pygame.draw.circle(screen, (255, 255, 255), (game_state['ball']['x'], game_state['ball']['y']), 10)
        else:
            pygame.draw.rect(screen, (0, 255, 0), (game_state['paddles']['0'], 800 - 40, 100, 20))
            pygame.draw.rect(screen, (255, 0, 255), (750 - 100 - game_state['paddles']['1'], 20, 100, 20))
            bx = game_state['ball']['x']
            by = game_state['ball']['y']

            pygame.draw.circle(screen, (255, 255, 255),
                            (750 - bx, 800 - by), 10)

        score_text = font_main.render(f"{game_state['scores'][0]} : {game_state['scores'][1]}", True, (255, 255, 255))
        screen.blit(score_text, (750 // 2 -25, 20))

        if game_state['sound_event']:
            if game_state['sound_event'] == 'wall_hit':
                # звук відбиття м'ячика від стін
                pass
            if game_state['sound_event'] == 'platform_hit':
                # звук відбиття м'ячика від платформи
                pass

    else:
        wating_text = font_main.render(f"Очікування гравців...", True, (255, 255, 255))
        screen.blit(wating_text, (750 // 2 - 25, 20))

    pygame.display.update()
    clock.tick(60)

    keys = pygame.key.get_pressed()
    if keys[pygame.K_a]:
        client.send(b"LEFT")
    elif keys[pygame.K_d]:
        client.send(b"RIGHT")

pygame.quit()
