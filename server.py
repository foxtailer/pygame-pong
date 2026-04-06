import socket
import json
import threading
import time
import random

WIDTH, HEIGHT = 750, 800
BALL_SPEED = 5
PADDLE_SPEED = 10
COUNTDOWN_START = 3

class GameServer:
    def __init__(self, host='localhost', port=8080):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))
        self.server.listen(2)
        print("🎮 Server started")

        self.clients = {0: None, 1: None}
        self.connected = {0: False, 1: False}
        self.lock = threading.Lock()
        self.reset_game_state()
        self.sound_event = None

    def reset_game_state(self):
        self.paddles = {0: 250, 1: 250}  # Paddles to mid
        self.scores = [0, 0]
        self.ball = {
            "x": WIDTH // 2,
            "y": HEIGHT // 2,
            "vx": 0,  # BALL_SPEED * random.choice([-1, 1]),
            "vy": BALL_SPEED * random.choice([-1, 1])
        }
        self.countdown = COUNTDOWN_START
        self.game_over = False
        self.winner = None

    def handle_client(self, pid):  # pid 1|0 player_id
        conn = self.clients[pid]
        try:
            while True:
                data = conn.recv(64).decode()
                with self.lock:
                    if data == "LEFT":
                        self.paddles[pid] = max(0, self.paddles[pid] - PADDLE_SPEED)
                    elif data == "RIGHT":
                        self.paddles[pid] = min(WIDTH - 100, self.paddles[pid] + PADDLE_SPEED)
        except:
            with self.lock:
                self.connected[pid] = False
                self.game_over = True
                self.winner = 1 - pid  # інший гравець автоматично виграє
                print(f"Гравець {pid} відключився. Переміг гравець {1 - pid}.")

    def broadcast_state(self):
        state = json.dumps({
            "paddles": self.paddles,
            "ball": self.ball,
            "scores": self.scores,
            "countdown": max(self.countdown, 0),
            "winner": self.winner if self.game_over else None,
            "sound_event": self.sound_event,
        }) + "\n"
        for pid, conn in self.clients.items():
            if conn:
                try:
                    conn.sendall(state.encode())
                except:
                    self.connected[pid] = False

    def ball_logic(self):
        while self.countdown > 0:
            time.sleep(1)
            with self.lock:
                self.countdown -= 1
                self.broadcast_state()

        while not self.game_over:
            with self.lock:
                # Ball fly
                self.ball['x'] += self.ball['vx']
                self.ball['y'] += self.ball['vy']
                
                # Walls hit
                if self.ball['x'] + 5 <= 0 or self.ball['x'] + 5 >= WIDTH:
                    self.ball['vx'] *= -1
                    self.sound_event = "wall_hit"

                # Platform hit
                if self.ball['vy'] < 0:  # Up
                    if self.ball['x'] >= 750 - 100 - self.paddles[0] and self.ball['x'] <= 750 - self.paddles[0]:
                        if self.ball['y'] <= 30:
                            self.ball['vy'] *= -1

                            middle_x = self.paddles[0] + 100 / 2
                            mirror_middle_x = 750 - middle_x
                            difference_in_x = mirror_middle_x - self.ball['x']
                            reduction_factor = (100 / 2) / BALL_SPEED
                            x_vel = difference_in_x / reduction_factor
                            self.ball['vx'] = -1 * x_vel

                    self.sound_event = 'platform_hit'
                        
                else:
                    if self.ball['x'] >= self.paddles[1] and self.ball['x'] <= self.paddles[1] + 100:
                        if self.ball['y'] >= HEIGHT - 30:
                            self.ball['vy'] *= -1

                            middle_x = self.paddles[1] + 100 / 2
                            difference_in_x = middle_x - self.ball['x']
                            reduction_factor = (100 / 2) / BALL_SPEED
                            x_vel = difference_in_x / reduction_factor
                            self.ball['vx'] = -1 * x_vel

                    self.sound_event = 'platform_hit'

                # Goall
                if self.ball['y'] < 0:
                    self.scores[1] += 1
                    self.reset_ball()
                elif self.ball['y'] > HEIGHT:
                    self.scores[0] += 1
                    self.reset_ball()

                if self.scores[0] >= 10:
                    self.game_over = True
                    self.winner = 0
                elif self.scores[1] >= 10:
                    self.game_over = True
                    self.winner = 1

                self.broadcast_state()
                self.sound_event = None
            time.sleep(0.016)

    def reset_ball(self):
        self.ball = {
            "x": WIDTH // 2,
            "y": HEIGHT // 2,
            "vx": 0, # BALL_SPEED * random.choice([-1, 1]),
            "vy": self.ball["vy"] * -1  # BALL_SPEED * random.choice([-1, 1])
        }

    def accept_players(self):
        for pid in [0, 1]:
            print(f"Очікуємо гравця {pid}...")
            conn, _ = self.server.accept()
            self.clients[pid] = conn
            conn.sendall((str(pid) + "\n").encode())
            self.connected[pid] = True
            print(f"Гравець {pid} приєднався")
            threading.Thread(target=self.handle_client, args=(pid,), daemon=True).start()

    def run(self):
        while True:
            self.accept_players()
            self.reset_game_state()
            threading.Thread(target=self.ball_logic, daemon=True).start()

            while not self.game_over and all(self.connected.values()):
                time.sleep(0.1)

            print(f"Гравець {self.winner} переміг!")
            time.sleep(5)

            # Закриваємо старі з'єднання
            for pid in [0, 1]:
                try:
                    self.clients[pid].close()
                except:
                    pass
                self.clients[pid] = None
                self.connected[pid] = False

GameServer().run()