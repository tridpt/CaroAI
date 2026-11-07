import pygame
import sys
import time
import math

# --- CONFIG ---
BOARD_SIZE = 15
CELL_SIZE = 40
MARGIN = 40
WINDOW_SIZE = BOARD_SIZE * CELL_SIZE + MARGIN * 2

WHITE = (245, 245, 245)
BLACK = (50, 50, 50)
RED = (230, 50, 50)
BLUE = (50, 50, 230)
BOARD_COLOR = (220, 180, 140)

EMPTY = 0
PLAYER = 1
AI = 2

class GomokuAI:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
        pygame.display.set_caption("Gomoku - Ultimate Minimax")
        self.font = pygame.font.SysFont("arial", 40, bold=True)
        self.small_font = pygame.font.SysFont("arial", 25, bold=True)
        self.reset_game()

    def reset_game(self):
        self.board = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.turn = PLAYER
        self.game_over = False
        self.winner = None
        self.last_move = None
        self.draw_board()
        print("\n===============================")
        print("🎮 NEW GAME STARTED!")
        print("===============================")

    def draw_board(self):
        self.screen.fill(BOARD_COLOR)
        for i in range(BOARD_SIZE):
            pygame.draw.line(self.screen, BLACK, (MARGIN + i*CELL_SIZE, MARGIN), (MARGIN + i*CELL_SIZE, WINDOW_SIZE-MARGIN), 2)
            pygame.draw.line(self.screen, BLACK, (MARGIN, MARGIN + i*CELL_SIZE), (WINDOW_SIZE-MARGIN, MARGIN + i*CELL_SIZE), 2)
        
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if self.board[r][c] == PLAYER:
                    self.draw_x(r, c)
                elif self.board[r][c] == AI:
                    self.draw_o(r, c)
                    
        # Nổi bật ô vừa đánh (Last Move Highlight)
        if self.last_move:
            lr, lc = self.last_move
            x = MARGIN + lc * CELL_SIZE
            y = MARGIN + lr * CELL_SIZE
            pygame.draw.rect(self.screen, (0, 220, 0), (x - 18, y - 18, 36, 36), 3)
        
        if self.game_over:
            s = pygame.Surface((WINDOW_SIZE, WINDOW_SIZE))
            s.set_alpha(220)
            s.fill(WHITE)
            self.screen.blit(s, (0, 0))
            
            if self.winner == AI:
                msg = "YOU HAVE BEEN CRUSHED BY AI!"
                color = RED
            elif self.winner == PLAYER:
                msg = "YOU ARE A GOMOKU GENIUS!"
                color = BLUE
            else:
                msg = "IT'S A DRAW!"
                color = BLACK
            
            text = self.font.render(msg, True, color)
            self.screen.blit(text, (WINDOW_SIZE//2 - text.get_width()//2, WINDOW_SIZE//2 - 50))
            
            btn_text = self.small_font.render("Click mouse or press 'R' to Play Again", True, BLACK)
            self.screen.blit(btn_text, (WINDOW_SIZE//2 - btn_text.get_width()//2, WINDOW_SIZE//2 + 30))

        pygame.display.update()

    def draw_x(self, r, c):
        x = MARGIN + c * CELL_SIZE
        y = MARGIN + r * CELL_SIZE
        pygame.draw.line(self.screen, RED, (x - 10, y - 10), (x + 10, y + 10), 4)
        pygame.draw.line(self.screen, RED, (x + 10, y - 10), (x - 10, y + 10), 4)

    def draw_o(self, r, c):
        x = MARGIN + c * CELL_SIZE
        y = MARGIN + r * CELL_SIZE
        pygame.draw.circle(self.screen, BLUE, (x, y), 12, 4)

    def check_win(self, player):
        dirs = [(0, 1), (1, 0), (1, 1), (1, -1)]
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if self.board[r][c] == player:
                    for dr, dc in dirs:
                        if 0 <= r+4*dr < BOARD_SIZE and 0 <= c+4*dc < BOARD_SIZE:
                            if all(self.board[r+i*dr][c+i*dc] == player for i in range(5)):
                                return True
        return False

    def evaluate_cell(self, r, c, player):
        """Siêu tối ưu hoá cho Phân loại Lưới: Chỉ kiểm tra 4 giao điểm đi qua ô cờ (r, c) thay vì đọc toàn bàn cờ."""
        score = 0
        p = str(player)
        e = str(EMPTY)
        o = str(AI if player == PLAYER else PLAYER)
        
        dirs = [(0, 1), (1, 0), (1, 1), (1, -1)]
        for dr, dc in dirs:
            line = []
            for i in range(-4, 5):
                nr, nc = r + i*dr, c + i*dc
                if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                    line.append(str(self.board[nr][nc]))
                else:
                    line.append(o) # Đổi 'X' thành 'o' để AI hiểu Vách Tường (Biên ranh giới) cũng chính là một cục cờ chặn!
            
            s = "".join(line)
            
            # --- ĐẾM SỐ LƯỢNG MỐI ĐE DỌA CỐT LÕI ---
            open_4 = s.count(e+p*4+e)
            blocked_4 = s.count(o+p*4+e) + s.count(e+p*4+o) + s.count(p+e+p*3) + s.count(p*3+e+p) + s.count(p*2+e+p*2)
            open_3 = s.count(e+p*3+e) + s.count(e+p+e+p*2+e) + s.count(e+p*2+e+p+e)
            
            # --- CÔNG THỨC RỦI RO KÉP (FORK DETECTION) ---
            if open_4 > 0: score += 1000000
            if open_3 >= 2 or (open_3 >= 1 and blocked_4 >= 1): 
                score += 500000 # GÀI CỜ ĐÔI (FORK) -> Rủi ro chí tử ngang ngửa Tứ tử hở 2 đầu!
            
            if p*5 in s: score += 100000000
            score += blocked_4 * 10000
            score += open_3 * 50000
            score += s.count(o+p*3+e+e) * 1000
            score += s.count(e+e+p*3+o) * 1000
            score += s.count(o+p+e+p*2+e) * 1000
            score += s.count(e+p*2+e+p+o) * 1000
            score += s.count(e+e+p*2+e+e) * 500
            score += s.count(e+p+e+p+e) * 450
        return score

    def evaluate_board(self, player):
        board_str = []
        for r in range(BOARD_SIZE):
            board_str.append("".join(str(self.board[r][c]) for c in range(BOARD_SIZE)))
        for c in range(BOARD_SIZE):
            board_str.append("".join(str(self.board[r][c]) for r in range(BOARD_SIZE)))
            
        for d in range(-BOARD_SIZE + 1, BOARD_SIZE):
            board_str.append("".join(str(self.board[i][i - d]) for i in range(max(0, d), min(BOARD_SIZE, BOARD_SIZE + d))))
            
        for d in range(2 * BOARD_SIZE - 1):
            board_str.append("".join(str(self.board[i][d - i]) for i in range(max(0, d - BOARD_SIZE + 1), min(BOARD_SIZE, d + 1))))

        full_str = "x".join(board_str)
        
        p = str(player)
        e = str(EMPTY)
        o = str(AI if player == PLAYER else PLAYER)
        
        score = 0
        if p*5 in full_str: score += 100000000
        
        # Nhận diện Fork trên toàn bàn cờ
        open_4 = full_str.count(e+p*4+e)
        blocked_4 = full_str.count(o+p*4+e) + full_str.count(e+p*4+o) + full_str.count(p+e+p*3) + full_str.count(p*3+e+p) + full_str.count(p*2+e+p*2)
        open_3 = full_str.count(e+p*3+e) + full_str.count(e+p+e+p*2+e) + full_str.count(e+p*2+e+p+e)
        
        if open_4 > 0: score += 1000000
        if open_3 >= 2 or (open_3 >= 1 and blocked_4 >= 1):
            score += 500000 # Báo rúp khẩn cấp cho "Nhãn quan" về mối hiểm họa kép!
            
        score += blocked_4 * 10000
        score += open_3 * 50000
        score += full_str.count(o+p*3+e+e) * 1000
        score += full_str.count(e+e+p*3+o) * 1000
        score += full_str.count(o+p+e+p*2+e) * 1000
        score += full_str.count(e+p*2+e+p+o) * 1000
        score += full_str.count(e+e+p*2+e+e) * 500
        score += full_str.count(e+p+e+p+e) * 450
        return score

    def evaluate(self):
        ai_score = self.evaluate_board(AI)
        pl_score = self.evaluate_board(PLAYER)
        return ai_score * 1.1 - pl_score * 1.5 

    def get_top_moves(self, limit=12):
        moves = []
        has_piece = False
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if self.board[r][c] != EMPTY:
                    has_piece = True
                    for dr in range(-2, 3):
                        for dc in range(-2, 3):
                            if dr == 0 and dc == 0: continue
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and self.board[nr][nc] == EMPTY:
                                if (nr, nc) not in moves:
                                    moves.append((nr, nc))
        if not has_piece:
            return [(BOARD_SIZE//2, BOARD_SIZE//2)]
            
        move_scores = []
        for r, c in moves:
            self.board[r][c] = AI
            s_ai = self.evaluate_cell(r, c, AI)
            self.board[r][c] = PLAYER
            s_pl = self.evaluate_cell(r, c, PLAYER)
            self.board[r][c] = EMPTY
            move_scores.append((max(s_ai, s_pl), (r, c)))
            
        move_scores.sort(reverse=True)
        return [m[1] for m in move_scores[:limit]]

    def minimax(self, depth, alpha, beta, is_maximizing):
        if self.check_win(AI): return 100000000
        if self.check_win(PLAYER): return -100000000
        if depth == 0: return self.evaluate()

        moves = self.get_top_moves(6)
        if not moves: return 0

        if is_maximizing:
            max_eval = -math.inf
            for r, c in moves:
                self.board[r][c] = AI
                eval = self.minimax(depth - 1, alpha, beta, False)
                self.board[r][c] = EMPTY
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha: break
            return max_eval
        else:
            min_eval = math.inf
            for r, c in moves:
                self.board[r][c] = PLAYER
                eval = self.minimax(depth - 1, alpha, beta, True)
                self.board[r][c] = EMPTY
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha: break
            return min_eval

    def ai_move(self):
        print("\n🤔 [TERMINATOR] Scanning matrix futures...")
        start_t = time.time()
        best_score = -math.inf
        best_move = None
        
        moves = self.get_top_moves(12) 
        
        # Tiêu diệt ngay nếu ván cờ tới hồi kết (Ưu tiên SỐ 1)
        for r, c in moves:
            self.board[r][c] = AI
            if self.check_win(AI): 
                self.place(r, c, AI)
                print(f"👉 Finishing move at ({r}, {c})")
                return
            self.board[r][c] = EMPTY

        # Chặn họng ngay nếu phát hiện đối thủ sắp Win (Ưu tiên SỐ 2)
        for r, c in moves:
            self.board[r][c] = PLAYER
            if self.check_win(PLAYER):
                self.board[r][c] = EMPTY
                self.place(r, c, AI)
                print(f"👉 Emergency Block at ({r}, {c})")
                return 
            self.board[r][c] = EMPTY

        # Tính toán Minimax độ sâu 3 với Alpha-Beta Pruning
        for r, c in moves:
            self.board[r][c] = AI
            score = self.minimax(3, -math.inf, math.inf, False) 
            self.board[r][c] = EMPTY
            
            if score > best_score:
                best_score = score
                best_move = (r, c)
                
        if not best_move and moves:
            best_move = moves[0]

        print(f"👉 Decisive move at {best_move} in {round(time.time()-start_t, 2)}s!")
        if best_move:
            self.place(best_move[0], best_move[1], AI)
            
    def is_board_full(self):
        return all(self.board[r][c] != EMPTY for r in range(BOARD_SIZE) for c in range(BOARD_SIZE))

    def place(self, r, c, player):
        self.board[r][c] = player
        self.last_move = (r, c)
        if self.check_win(player):
            self.game_over = True
            self.winner = player
            if player == AI:
                print("❌ YOU HAVE BEEN CRUSHED BY AI! ❌")
            else:
                print("🎉 INCREDIBLE! YOU DEFEATED THE TERMINATOR! 🎉")
        elif self.is_board_full():
            self.game_over = True
            self.winner = None
            print("🤝 DRAW! THE BOARD IS FULL! 🤝")
        else:
            self.turn = AI if player == PLAYER else PLAYER
            
        self.draw_board()
            
    def run(self):
        clock = pygame.time.Clock()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.game_over:
                        self.reset_game()
                    elif self.turn == PLAYER:
                        mouse_x, mouse_y = event.pos
                        col = round((mouse_x - MARGIN) / CELL_SIZE)
                        row = round((mouse_y - MARGIN) / CELL_SIZE)
                        
                        if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE and self.board[row][col] == EMPTY:
                            self.place(row, col, PLAYER)
                            
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r and self.game_over:
                        self.reset_game()
                        
            if self.turn == AI and not self.game_over:
                self.ai_move()
            clock.tick(60)

if __name__ == "__main__":
    game = GomokuAI()
    game.run()
