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
            "vx": 0,
            "vy": BALL_SPEED * random.choice([-1, 1])
        }
        self.countdown = COUNTDOWN_START
        self.game_over = False
        self.winner = None
        self.pause = False

    def handle_client(self, player_id):
        conn = self.clients[player_id]
        try:
            while True:
                data = conn.recv(64).decode()

                with self.lock:
                    if data == "LEFT":
                        self.paddles[player_id] = max(0, self.paddles[player_id] - PADDLE_SPEED)
                    elif data == "RIGHT":
                        self.paddles[player_id] = min(WIDTH - 100, self.paddles[player_id] + PADDLE_SPEED)
                    elif data == "PAUSE":
                        self.pause = not self.pause
        except:
            with self.lock:
                self.connected[player_id] = False
                self.game_over = True
                self.winner = 1 - player_id  # Oposite player wins
                print(f"Player {player_id} left the game. Player {1 - player_id} wins.")

    def broadcast_state(self):
        state = json.dumps({
            "paddles": self.paddles,
            "ball": self.ball,
            "scores": self.scores,
            "countdown": max(self.countdown, 0),
            "winner": self.winner if self.game_over else None,
            "sound_event": self.sound_event,
            "pause": self.pause
        }) + "\n"

        for player_id, conn in self.clients.items():
            if conn:
                try:
                    conn.sendall(state.encode())
                except:
                    self.connected[player_id] = False

    def ball_logic(self):
        while self.countdown > 0:
            time.sleep(1)
            with self.lock:
                self.countdown -= 1
                self.broadcast_state()

        while not self.game_over:
            if self.pause:
                    time.sleep(0.1)
                    continue
            
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
            "vx": 0,
            "vy": self.ball["vy"] * -1  # Oposite direction after goal
        }

    def accept_players(self):
        for player_id in [0, 1]:
            print(f"Wait for player {player_id}...")
            conn, _ = self.server.accept() # Wait for player to connect
            self.clients[player_id] = conn
            self.connected[player_id] = True
            conn.sendall((str(player_id) + "\n").encode())
            print(f"Player {player_id} joined the game.")
            threading.Thread(target=self.handle_client, args=(player_id,), daemon=True).start()

    def run(self):
        while True:
            self.accept_players()
            self.reset_game_state()
            threading.Thread(target=self.ball_logic, daemon=True).start()

            while not self.game_over and all(self.connected.values()):
                time.sleep(0.1)

            print(f"Player {self.winner} won!")
            time.sleep(1)

            # Closing old connections
            for player_id in [0, 1]:
                try:
                    self.clients[player_id].close()
                except:
                    pass
                self.clients[player_id] = None
                self.connected[player_id] = False

GameServer().run()