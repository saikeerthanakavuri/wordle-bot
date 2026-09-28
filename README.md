# 🟩 Wordle Bot — Terminal Edition

A feature-rich, colourful Wordle clone for your terminal, built with Python and [Rich](https://github.com/Textualize/rich).

## Features

| Feature | Details |
|---|---|
| 🎯 Word source | **Stanford GraphBase** (5,757) or **SOWPODS Scrabble** (12,478) — pick at startup |
| 🎨 Colour feedback | Green (correct), Yellow (misplaced), Grey (wrong) |
| ⌨️ Letter tracker | On-screen QWERTY keyboard updates after every guess |
| 🔢 6 tries | Standard Wordle rules |
| 🔥 Win streak | Tracks consecutive wins across rounds |
| ♻️ Play again | Replay as many times as you like |
| ✅ Input validation | Rejects non-letters, wrong-length guesses, repeated guesses |
| 📥 Auto-download | Word lists fetched once and cached locally |

## Quick Start

```bash
# 1. Create a virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Play!
python wordle.py
```

## How to Play

1. The game picks a secret **5-letter word** at random.
2. Type your guess and press **Enter**.
3. Each letter gets coloured feedback:

   - 🟩 **Green** — right letter, right position  
   - 🟨 **Yellow** — right letter, wrong position  
   - ⬛ **Grey** — letter not in the word at all

4. You have **6 attempts** to find the word.
5. Type **QUIT** at any prompt to exit.

## Project Structure

```
wordle-bot/
├── wordle.py        # Main game
├── sgb-words.txt    # Stanford word list (auto-downloaded on first run)
├── sowpods-5.txt    # SOWPODS 5-letter words (auto-downloaded on first run)
├── requirements.txt # Dependencies
└── README.md        # This file
```

## Dependencies

- **rich** `13.7.1` — beautiful terminal UI (colours, panels, tables)
- **requests** `2.31.0` — downloads word lists on first run

## Word Lists

### Stanford GraphBase (default, easier)
Words from Donald Knuth's **Stanford GraphBase** project:  
`https://www-cs-faculty.stanford.edu/~knuth/sgb-words.txt`  
**5,757 common 5-letter English words** — the same list used by the original Wordle game.

### SOWPODS (harder mode)
The **SOWPODS** dictionary — the international Scrabble word list (Collins Scrabble Words):  
`https://github.com/MReeveCO/sowpods`  
**12,478 valid 5-letter Scrabble words** — includes many obscure and rare words for a tougher challenge.

| | Stanford | SOWPODS |
|---|---|---|
| Words | 5,757 | 12,478 |
| Difficulty | ⭐ Standard | ⭐⭐ Hard |
| Style | Common English words | Full Scrabble dictionary |
