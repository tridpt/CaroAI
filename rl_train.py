import random
import json
import os
import time
import math

BOARD_SIZE = 15
EMPTY = 0
AI = 2
OPPONENT = 1

class GomokuEnv:
    def __init__(self):
        self.board = [[EMPTY]*BOARD_SIZE for _ in range(BOARD_SIZE)]
        
    def reset(self):
        self.board = [[EMPTY]*BOARD_SIZE for _ in range(BOARD_SIZE)]
        return self.board
        
    def check_win(self, player):
        dirs = [(0, 1), (1, 0), (1, 1), (1, -1)]
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if self.board[r][c] == player:
                    for dr, dc in dirs:
                        count = 0
                        for i in range(5):
                            nr, nc = r + dr*i, c + dc*i
                            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and self.board[nr][nc] == player:
                                count += 1
                            else:
                                break
                        if count == 5:
                            return True
        return False
        
    def get_valid_moves(self):
        moves = set()
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if self.board[r][c] != EMPTY:
                    for i in range(-1, 2):
                        for j in range(-1, 2):
                            nr, nc = r + i, c + j
                            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and self.board[nr][nc] == EMPTY:
                                moves.add((nr, nc))
        if not moves:
            return [(BOARD_SIZE//2, BOARD_SIZE//2)]
        return list(moves)

    def extract_features(self, player, opponent):
        """
        f[0], f[1], f[2], f[3], f[4] -> Tương ứng với chuỗi 1..5 của MÌNH
        f[5], f[6], f[7], f[8], f[9] -> Tương ứng với chuỗi 1..5 của KẺ ĐỊCH
        """
        features = [0.0]*10
        dirs = [(0, 1), (1, 0), (1, 1), (1, -1)]
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if self.board[r][c] == EMPTY: continue
                for dr, dc in dirs:
                    p1_c = 0
                    p2_c = 0
                    for i in range(5):
                        nr, nc = r + dr*i, c + dc*i
                        if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                            if self.board[nr][nc] == player:
                                p1_c += 1
                            elif self.board[nr][nc] == opponent:
                                p2_c += 1
                        else:
                            p1_c = p2_c = 0
                            break
                    
                    if p1_c > 0 and p2_c == 0:
                        features[p1_c - 1] += 1
                    elif p2_c > 0 and p1_c == 0:
                        features[5 + p2_c - 1] += 1
        return features

class QLearningAgent:
    def __init__(self):
        # Bộ Trọng Số Ban Đầu: Mù tịt, chả biết gì về thế giới
        self.weights = [0.0] * 10
        self.load_weights()
        self.alpha = 0.05   # Tốc độ học (Learning Rate)
        self.gamma = 0.9    # Độ ưu tiên tầm nhìn xa (Discount Factor)
        self.epsilon = 0.3  # 30% đánh bừa để khám phá chiến thuật, 70% đánh khôn
        
    def get_value(self, features):
        return sum(w*f for w, f in zip(self.weights, features))

    def choose_action(self, env, player, opponent):
        moves = env.get_valid_moves()
        # Exploration: Đánh bừa để vấp ngã rồi rút kinh nghiệm
        if random.random() < self.epsilon:
            return random.choice(moves)
            
        # Exploitation: Dùng cái não của mình để đánh
        best_val = -float('inf')
        best_move = random.choice(moves)
        for r, c in moves:
            env.board[r][c] = player
            features = env.extract_features(player, opponent)
            val = self.get_value(features)
            env.board[r][c] = EMPTY
            
            if val > best_val:
                best_val = val
                best_move = (r, c)
        return best_move

    def update(self, old_features, reward, new_features):
        old_val = self.get_value(old_features)
        new_val = self.get_value(new_features) if new_features else 0
        delta = reward + self.gamma * new_val - old_val
        delta = max(-1000.0, min(1000.0, delta)) # Cắt tỉa chống bùng nổ Gradient
        for i in range(10):
            # Gradient Ascent cập nhật trọng số
            self.weights[i] += self.alpha * delta * old_features[i]
            # Giới hạn cực độ trọng số từ -1 triêu đển 1 triêu để không ra NaN
            if math.isnan(self.weights[i]):
                self.weights[i] = 0.0
            self.weights[i] = max(-1000000.0, min(1000000.0, self.weights[i]))

    def load_weights(self):
        if os.path.exists("brain.json"):
            with open("brain.json", "r") as f:
                self.weights = json.load(f)
                
    def save_weights(self):
        with open("brain.json", "w") as f:
            json.dump(self.weights, f)

def train(epochs=200):
    env = GomokuEnv()
    agent = QLearningAgent()
    
    print("[BAT DAU] HUAN LUYEN AI TU HOC TU SAI LAM BANG Q-LEARNING...")
    print("[TRANG THAI] Nao khi ban dau:", [round(x, 2) for x in agent.weights])
    
    for epoch in range(1, epochs + 1):
        env.reset()
        
        # Self-Play: AI lấy tay trái (AI_1) đánh AI tay phải (AI_2)
        turn = OPPONENT # opponent đi trước
        last_features = {OPPONENT: env.extract_features(OPPONENT, AI), AI: env.extract_features(AI, OPPONENT)}
        
        moves_played = 0
        while True:
            other = AI if turn == OPPONENT else OPPONENT
            
            action = agent.choose_action(env, turn, other)
            env.board[action[0]][action[1]] = turn
            moves_played += 1
            
            new_features = env.extract_features(turn, other)
            
            # Nếu Thắng: AI được CỘNG 100đ, kẻ thua bị TRỪ 100đ
            if env.check_win(turn):
                agent.update(last_features[turn], 100, None)
                # Kẻ thua cũng cần học bài học là mình vừa chết
                agent.update(last_features[other], -100, None)
                break
                
            if moves_played > BOARD_SIZE * BOARD_SIZE: # Hòa
                break
                
            # Học kinh nghiệm dọc đường: 
            # Đánh xong chưa chết, nhưng tự nhận thức xem bàn cờ đang ngon hay dở 
            agent.update(last_features[turn], 0, new_features)
            
            last_features[turn] = new_features
            turn = other # Đổi lượt

        # AI khôn dần lên qua từng ván, cứ mỗi 10 ván in ra 1 lần
        if epoch % 10 == 0:
            print(f"[TIEN DO] Van {epoch}/{epochs} | So nuoc danh: {moves_played}")
            print(f"    Trong so Nao da tu: {[round(w, 2) for w in agent.weights]}")
            agent.save_weights()

if __name__ == "__main__":
    train(10000) # Chỉ train thử 100 ván để trải nghiệm thực tế, có thể nâng lên 10,000 ván 
