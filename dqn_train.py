import time
import random
import os
import numpy as np
from collections import deque

# Bắt buộc cài PyTorch nếu chạy trên Colab (Có sẵn trên Colab rồi)
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    import torch.nn.functional as F
except ImportError:
    print("Vui lòng chạy lệnh: !pip install torch torchvision torchaudio")
    exit()

# Cấu hình Mạng & Bàn cờ
BOARD_SIZE = 15
BATCH_SIZE = 128
GAMMA = 0.99
LR = 0.001
MEMORY_SIZE = 100000
TARGET_UPDATE = 100
UPDATE_FREQ = 16 # BÍ QUYẾT TĂNG TỐC GẤP 16 LẦN: Học theo Batch sau mỗi 16 nước đi thay vì từng bước 1

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"🔥 SẴN SÀNG HUẤN LUYỆN BẰNG: {device.type.upper()} 🔥")

class ConvDQN(nn.Module):
    """
    Mạng Nơ-ron Tích Chập (CNN) mô phỏng nhãn quan của con người.
    Nhìn vào bàn cờ dưới dạng "Kênh Hình Ảnh" để suy luận điểm yếu.
    """
    def __init__(self):
        super(ConvDQN, self).__init__()
        # Kênh 0: Quân của mình, Kênh 1: Quân đối thủ
        self.conv1 = nn.Conv2d(2, 64, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(64, 128, kernel_size=3, padding=1)
        self.conv3 = nn.Conv2d(128, 128, kernel_size=3, padding=1)
        
        # Mạng tuyến tính quyết định
        self.fc1 = nn.Linear(128 * BOARD_SIZE * BOARD_SIZE, 512)
        self.fc2 = nn.Linear(512, BOARD_SIZE * BOARD_SIZE) # 225 ô cờ = 225 giá trị Q (nước đi)

    def forward(self, x):
        x = F.relu(self.conv1(x))
        x = F.relu(self.conv2(x))
        x = F.relu(self.conv3(x))
        x = x.view(x.size(0), -1) # Ép phẳng về 1D
        x = F.relu(self.fc1(x))
        return self.fc2(x)

class GomokuFastEnv:
    def __init__(self):
        self.board = np.zeros((BOARD_SIZE, BOARD_SIZE), dtype=int)
        
    def reset(self):
        self.board = np.zeros((BOARD_SIZE, BOARD_SIZE), dtype=int)
        return self.get_state(2) # 2 là AI
        
    def get_state(self, player):
        """ Chuyển bàn cờ thành Ma trận Tensor đưa vào GPU """
        opponent = 1 if player == 2 else 2
        
        my_stones = (self.board == player).astype(np.float32)
        enemy_stones = (self.board == opponent).astype(np.float32)
        
        # Shape: (2, 15, 15)
        state = np.stack([my_stones, enemy_stones], axis=0)
        return state

    def check_win(self, player):
        # [NGHIỀN NÁT NÚT THẮT CỔ CHAI]: Dùng Numpy Slicing thay vòng lặp For 
        # Tốc độ kiểm tra thắng cực nhanh (O(1) Python calls)
        b = self.board == player
        # Quét 1 phát toàn bộ hàng ngang
        if np.any(b[:, :-4] & b[:, 1:-3] & b[:, 2:-2] & b[:, 3:-1] & b[:, 4:]): return True
        # Quét 1 phát toàn bộ hàng dọc
        if np.any(b[:-4, :] & b[1:-3, :] & b[2:-2, :] & b[3:-1, :] & b[4:, :]): return True
        # Quét 1 phát toàn bộ chéo chính
        if np.any(b[:-4, :-4] & b[1:-3, 1:-3] & b[2:-2, 2:-2] & b[3:-1, 3:-1] & b[4:, 4:]): return True
        # Quét 1 phát toàn bộ chéo phụ
        b_rev = b[:, ::-1]
        if np.any(b_rev[:-4, :-4] & b_rev[1:-3, 1:-3] & b_rev[2:-2, 2:-2] & b_rev[3:-1, 3:-1] & b_rev[4:, 4:]): return True
        return False
        
    def step(self, action, player):
        r, c = action // BOARD_SIZE, action % BOARD_SIZE
        if self.board[r, c] != 0:
            return self.get_state(player), -10, True # Lỗi đi vào ổ cờ có sẵn -> Phạt nặng và thua
            
        self.board[r, c] = player
        if self.check_win(player):
            return self.get_state(player), 1.0, True # Thắng vinh quang
            
        if np.all(self.board != 0):
            return self.get_state(player), 0.0, True # Hòa
            
        return self.get_state(player), 0.0, False # Tiếp tục

def dqn_train():
    env = GomokuFastEnv()
    policy_net = ConvDQN().to(device)
    target_net = ConvDQN().to(device)
    target_net.load_state_dict(policy_net.state_dict())
    
    optimizer = optim.Adam(policy_net.parameters(), lr=LR)
    memory = deque(maxlen=MEMORY_SIZE)
    loss_fn = nn.MSELoss()
    
    epsilon = 1.0
    epsilon_min = 0.1
    epsilon_decay = 0.999
    
    epochs = 5000 # Số trận giả lập (Colab GPU quẩy 5000 trận cực nhanh)
    print("🚀 ĐẨY DỮ LIỆU LÊN CARD ĐỒ HOẠ...")
    
    for epoch in range(1, epochs + 1):
        state = env.reset()
        done = False
        moves_played = 0
        total_loss = 0
        
        while not done:
            # Chọn nước đi (Epsilon-Greedy kết hợp phán đoán GPU)
            valid_moves = np.where(env.board.flatten() == 0)[0]
            if random.random() < epsilon:
                action = random.choice(valid_moves)
            else:
                # Ép dữ liệu lên GPU chỉ khi thực sự cần thiết để né độ trễ đường truyền
                state_tensor = torch.FloatTensor(state).unsqueeze(0).to(device)
                with torch.no_grad():
                    q_values = policy_net(state_tensor).squeeze()
                    q_values[env.board.flatten() != 0] = -1e9
                    action = q_values.argmax().item()
                    
            next_state, reward, done = env.step(action, 2)
            memory.append((state, action, reward, next_state, done))
            state = next_state
            
            # [BÍ QUYẾT TỐI THƯỢNG]: SELF-PLAY (Tự diễn biến, tự phân thân chiến đấu)
            # Kẻ địch không còn bốc đại cờ nữa. Nó sẽ dùng chung BỘ NÃO policy_net để học cách bóp nghẹt AI!
            if not done:
                enemy_moves = np.where(env.board.flatten() == 0)[0]
                if random.random() < epsilon:
                    enemy_action = random.choice(enemy_moves)
                else:
                    # Rất quan trọng: Phải đưa state dưới góc nhìn của Kẻ địch (Player 1)
                    state_enemy_view = env.get_state(1)
                    enemy_tensor = torch.FloatTensor(state_enemy_view).unsqueeze(0).to(device)
                    with torch.no_grad():
                        eq_values = policy_net(enemy_tensor).squeeze()
                        eq_values[env.board.flatten() != 0] = -1e9
                        enemy_action = eq_values.argmax().item()

                next_state_enemy, en_reward, en_done = env.step(enemy_action, 1)
                
                if en_done and en_reward > 0: # Địch (Phân thân) thắng -> AI gốc bị trừ 1 điểm cực đậm
                    memory.append((state, action, -1.0, next_state_enemy, True))
                    done = True
                else:
                    state = env.get_state(2)
            
            # Huấn luyện trên Mini-batch từ Replay Buffer (NHƯNG CHỈ SAU MỖI 16 BƯỚC THAY VÌ MỖI BƯỚC)
            if len(memory) > BATCH_SIZE and moves_played % UPDATE_FREQ == 0:
                mini_batch = random.sample(memory, BATCH_SIZE)
                
                # Biến nguyên mảng Numpy lớn rồi mới đưa lên GPU -> Tiết kiệm băng thông PCI-e
                b_states = torch.FloatTensor(np.array([m[0] for m in mini_batch])).to(device)
                b_actions = torch.LongTensor(np.array([m[1] for m in mini_batch])).to(device).unsqueeze(1)
                b_rewards = torch.FloatTensor(np.array([m[2] for m in mini_batch])).to(device)
                b_next_states = torch.FloatTensor(np.array([m[3] for m in mini_batch])).to(device)
                b_dones = torch.FloatTensor(np.array([float(m[4]) for m in mini_batch])).to(device)

                curr_Q = policy_net(b_states).gather(1, b_actions).squeeze(1)
                
                with torch.no_grad():
                    max_next_Q = target_net(b_next_states).max(1)[0]
                    target_Q = b_rewards + (GAMMA * max_next_Q * (1 - b_dones))
                    
                loss = loss_fn(curr_Q, target_Q)
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                total_loss += loss.item()

            moves_played += 1
            if moves_played > env.board.size: break
            
        epsilon = max(epsilon_min, epsilon * epsilon_decay)
        
        if epoch % TARGET_UPDATE == 0:
            target_net.load_state_dict(policy_net.state_dict())
            
        if epoch % 50 == 0:
            print(f"💻 Epoch {epoch}/{epochs} | Epsilon: {epsilon:.2f} | Loss: {total_loss:.4f} | Số nước: {moves_played}")
            
    print("✅ HUẤN LUYỆN XONG! LƯU NÃO DEEP LEARNING...")
    torch.save(policy_net.state_dict(), "deep_brain.pth")
    print("📁 File não đã được lưu thành xuất: deep_brain.pth")
    print("Bạn có thể tải file deep_brain.pth này về máy và dùng nó để tàn sát!")

if __name__ == "__main__":
    dqn_train()
