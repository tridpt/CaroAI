# CaroAI (Gomoku Terminator)

A highly optimized Gomoku (Caro/Five-in-a-Row) game against an unbeatable AI, developed in Python using Pygame. The AI utilizes the **Minimax Algorithm with Alpha-Beta Pruning** and an advanced heuristic evaluation function to detect complex tactical threats like double-forks.

## 🌟 Key Features

* **Advanced AI Opponent:** The AI ("Terminator") thinks ahead using Minimax and Alpha-Beta pruning, aggressively blocking your moves and seizing victory.
* **Super-Optimized Evaluation:** Evaluates cells and lines dynamically. Recognizes critical Gomoku patterns like "Open 4," "Blocked 4," "Open 3," and devastating double-threats (Forks).
* **Smooth UI:** A clean and interactive graphical user interface built with Pygame. Features board highlighting, winning animations, and move tracking.
* **Lightning Fast:** Achieves depth 3 calculations near-instantaneously thanks to localized cell evaluation updates and dynamic move sorting heuristics (`get_top_moves`).
* **Visual Helpers:** Highlights the last played move to easily keep track of the board state.

## 🚀 Installation & Requirements

Ensure you have **Python 3.8+** installed along with **Pygame**. 

1. **Clone the repository:**
   ```bash
   git clone https://github.com/tridpt/CaroAI.git
   cd CaroAI
   ```

2. **Install dependency:**
   ```bash
   pip install pygame
   ```

3. **Run the Game:**
   ```bash
   python main.py
   ```

## 🎮 How to Play

* Click on an empty intersection on the board to place your piece (Red 'X').
* The AI (Blue 'O') will immediately calculate and make its move.
* Get 5 pieces in a row (horizontally, vertically, or diagonally) to win.
* At the end of the game, click the mouse or press the `R` key to instantly restart and play again.

## 👨‍💻 Developer Notes

Developed by **Trần Đức Trí**. 
This project was conceptualized to eliminate performance bottlenecks in traditional Gomoku AI, balancing the strategic depth of the Minimax algorithm with real-time responsiveness.
