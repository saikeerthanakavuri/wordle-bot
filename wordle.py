"""
Wordle Bot — A feature-rich terminal Wordle game.

Word sources:
  • Stanford GraphBase (sgb-words.txt)  — 5,757 curated common words
  • SOWPODS Scrabble dictionary         — 12,478 valid Scrabble 5-letter words
UI:        Rich library for colorful terminal output
Features:  6 tries, color feedback, letter tracker, win streak, play again
"""

import contextlib
import pathlib
import random
import sys
from string import ascii_letters, ascii_uppercase

import requests
from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.rule import Rule
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

# ── Constants ──────────────────────────────────────────────────────────────────
NUM_LETTERS = 5
NUM_GUESSES = 6

# Stanford GraphBase
STANFORD_CACHE = pathlib.Path(__file__).parent / "sgb-words.txt"
STANFORD_URL   = "https://www-cs-faculty.stanford.edu/~knuth/sgb-words.txt"

# SOWPODS (Collins Scrabble Words — international Scrabble dictionary)
SOWPODS_CACHE  = pathlib.Path(__file__).parent / "sowpods-5.txt"
SOWPODS_URL    = "https://raw.githubusercontent.com/MReeveCO/sowpods/main/sowpods.txt"

# ── Rich Console ───────────────────────────────────────────────────────────────
THEME = Theme({
    "correct":   "bold white on green",
    "misplaced": "bold white on dark_goldenrod",
    "wrong":     "white on grey35",
    "empty":     "dim white on grey23",
    "warning":   "bold red on yellow",
    "info":      "bold cyan",
    "title":     "bold magenta",
    "win":       "bold white on green",
    "lose":      "bold white on red",
    "streak":    "bold yellow",
})
console = Console(theme=THEME)


# ── Word Lists ─────────────────────────────────────────────────────────────────

def _load_from_file(path: pathlib.Path) -> list[str]:
    """Read cached word file and return filtered uppercase 5-letter words."""
    raw = path.read_text(encoding="utf-8")
    return [
        w.upper()
        for w in raw.splitlines()
        if len(w.strip()) == NUM_LETTERS and all(c in ascii_letters for c in w.strip())
    ]


def fetch_stanford_words() -> list[str]:
    """
    Load the Stanford GraphBase 5-letter word list (5,757 common words).
    Downloads once and caches locally as sgb-words.txt.
    """
    if not STANFORD_CACHE.exists():
        console.print("[info]Downloading Stanford word list (one-time)…[/]")
        try:
            r = requests.get(STANFORD_URL, timeout=10)
            r.raise_for_status()
            STANFORD_CACHE.write_text(r.text, encoding="utf-8")
            console.print("[info]Saved to sgb-words.txt ✓[/]")
        except requests.RequestException as exc:
            console.print(f"[warning]Could not download Stanford list: {exc}[/]")
            return FALLBACK_WORDS

    words = _load_from_file(STANFORD_CACHE)
    return words if words else FALLBACK_WORDS


def fetch_sowpods_words() -> list[str]:
    """
    Load the SOWPODS (Collins Scrabble Words) 5-letter word list (12,478 words).
    Downloads the full SOWPODS list once, filters to 5-letter words, and caches
    locally as sowpods-5.txt.
    """
    if not SOWPODS_CACHE.exists():
        console.print("[info]Downloading SOWPODS word list (one-time)…[/]")
        try:
            r = requests.get(SOWPODS_URL, timeout=15)
            r.raise_for_status()
            # Filter to 5-letter words while saving
            five_letter = [
                w.strip().lower()
                for w in r.text.splitlines()
                if len(w.strip()) == NUM_LETTERS and all(c in ascii_letters for c in w.strip())
            ]
            SOWPODS_CACHE.write_text("\n".join(five_letter), encoding="utf-8")
            console.print(f"[info]Saved {len(five_letter):,} SOWPODS words to sowpods-5.txt ✓[/]")
        except requests.RequestException as exc:
            console.print(f"[warning]Could not download SOWPODS list: {exc}[/]")
            console.print("[warning]Falling back to Stanford word list.[/]")
            return fetch_stanford_words()

    words = _load_from_file(SOWPODS_CACHE)
    return words if words else fetch_stanford_words()


def choose_word_source() -> tuple[list[str], str]:
    """
    Show a word-source selection menu and return (word_list, source_name).
    """
    console.print()
    console.print(Rule("[bold cyan]Choose Word Source[/]", style="cyan"))
    console.print()

    table = Table(show_header=True, header_style="bold cyan", box=None, padding=(0, 2))
    table.add_column("Option", justify="center", style="bold yellow", min_width=6)
    table.add_column("Source", style="bold white")
    table.add_column("Words", justify="right", style="green")
    table.add_column("Description", style="dim")

    table.add_row("1", "Stanford GraphBase (sgb-words)", "5,757",
                  "Curated common English words — same list as the original Wordle")
    table.add_row("2", "SOWPODS Scrabble Dictionary",    "12,478",
                  "Full international Scrabble dictionary — harder, more obscure words")

    console.print(Align.center(table))
    console.print()

    choice = Prompt.ask(
        "[bold cyan]Pick a source[/]",
        choices=["1", "2"],
        default="1",
        console=console,
    )

    if choice == "2":
        words = fetch_sowpods_words()
        return words, "SOWPODS"
    else:
        words = fetch_stanford_words()
        return words, "Stanford"


# Legacy alias (used if called without the menu)
def fetch_word_list() -> list[str]:
    return fetch_stanford_words()


# Small fallback in case the network is unavailable and cache doesn't exist
FALLBACK_WORDS = [
    "CRANE", "SLATE", "AUDIO", "STARE", "RAISE", "AROSE",
    "TRACE", "CRATE", "SANER", "LEAST", "LEARN", "EARTH",
    "HEART", "REACT", "TEARS", "RATES", "STERN", "TIERS",
    "TRIED", "TIRED", "RIDER", "RIDER", "TIGER", "LIGHT",
    "SIGHT", "MIGHT", "NIGHT", "FIGHT", "RIGHT", "BIGHT",
]


# ── Display Helpers ────────────────────────────────────────────────────────────

def clear_screen() -> None:
    console.clear()


def show_banner(headline: str) -> None:
    """Print the game banner / rule with a headline."""
    console.print()
    console.print(Rule(f"[title]🟩 WORDLE  ·  {headline}[/]", style="magenta"))
    console.print()


def show_welcome() -> None:
    """Show a styled welcome / instructions panel."""
    clear_screen()
    welcome_text = Text.assemble(
        ("Welcome to ", "bold white"),
        ("WORDLE", "bold green"),
        ("!\n\n", "bold white"),
        ("How to play:\n", "bold cyan"),
        ("  • Guess the secret 5-letter word in 6 tries.\n", "white"),
        ("  • After each guess the letters are coloured:\n\n", "white"),
        ("    🟩  GREEN   ", "bold white on green"),
        (" — correct letter, correct spot\n", "white"),
        ("    🟨  YELLOW  ", "bold white on dark_goldenrod"),
        (" — correct letter, wrong spot\n", "white"),
        ("    ⬛  GREY    ", "white on grey35"),
        (" — letter not in the word\n\n", "white"),
        ("Word sources available:\n", "bold cyan"),
        ("  • Stanford GraphBase — ", "white"),
        ("5,757", "bold green"),
        (" curated common words\n", "white"),
        ("  • SOWPODS Scrabble   — ", "white"),
        ("12,478", "bold green"),
        (" international Scrabble words\n\n", "white"),
        ("Type ", "white"),
        ("QUIT", "bold red"),
        (" at any time to exit.", "white"),
    )
    panel = Panel(
        Align.center(welcome_text),
        title="[bold magenta]🟩 W O R D L E[/]",
        border_style="magenta",
        padding=(1, 4),
    )
    console.print(panel)
    console.print()


def letter_style(letter: str, word: str, position: int) -> str:
    """Return the Rich style for a guessed letter."""
    if letter == "_":
        return "empty"
    if letter == word[position]:
        return "correct"
    if letter in word:
        return "misplaced"
    if letter in ascii_letters:
        return "wrong"
    return "dim"


def render_board(guesses: list[str], word: str) -> None:
    """Print the 6-row guess board with coloured letters."""
    table = Table.grid(padding=(0, 1))
    for _ in range(NUM_LETTERS):
        table.add_column(justify="center", min_width=3)

    for guess in guesses:
        row_cells = []
        for pos, letter in enumerate(guess):
            style = letter_style(letter, word, pos)
            cell = Text(f" {letter} ", style=style, justify="center")
            row_cells.append(cell)
        table.add_row(*row_cells)

    console.print(Align.center(table))


def render_keyboard(guesses: list[str], word: str) -> None:
    """Show the A-Z keyboard with per-letter colour status."""
    # Priority: correct > misplaced > wrong > unseen
    STATUS_PRIORITY = {"correct": 3, "misplaced": 2, "wrong": 1, "": 0}
    status: dict[str, str] = {ch: "" for ch in ascii_uppercase}

    for guess in guesses:
        for pos, letter in enumerate(guess):
            if letter == "_":
                continue
            new_style = letter_style(letter, word, pos)
            # Only upgrade, never downgrade
            if STATUS_PRIORITY.get(new_style, 0) > STATUS_PRIORITY.get(status[letter], 0):
                status[letter] = new_style

    rows = ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"]
    console.print()
    for row in rows:
        line = Text()
        for ch in row:
            s = status[ch]
            if s:
                line.append(f" {ch} ", style=s)
            else:
                line.append(f" {ch} ", style="dim white")
        console.print(Align.center(line))
    console.print()


def render_game(guesses: list[str], word: str, headline: str) -> None:
    """Full refresh: banner + board + keyboard."""
    clear_screen()
    show_banner(headline)
    render_board(guesses, word)
    render_keyboard(guesses, word)


# ── Input Validation ──────────────────────────────────────────────────────────

def get_guess(previous_guesses: list[str], all_words: list[str]) -> str:
    """
    Prompt the user for a valid 5-letter guess.
    Loops until valid input is provided (or user types QUIT).
    """
    while True:
        raw = console.input("[bold cyan]Guess >[/] ").strip().upper()

        if raw == "QUIT":
            console.print("\n[bold red]Thanks for playing! Goodbye. 👋[/]\n")
            sys.exit(0)

        if len(raw) != NUM_LETTERS:
            console.print(
                f"[warning] ⚠  Your guess must be exactly {NUM_LETTERS} letters.[/]"
            )
            continue

        if not all(c in ascii_uppercase for c in raw):
            console.print("[warning] ⚠  Only English letters are allowed.[/]")
            continue

        if raw in previous_guesses:
            console.print(f"[warning] ⚠  You already guessed [bold]{raw}[/bold]. Try a different word.[/]")
            continue

        # Optional: validate against word list (commented out — avoids frustrating
        # players with a limited list; uncomment to enforce dictionary words only)
        # if raw not in all_words:
        #     console.print("[warning] ⚠  Not in word list. Try again.[/]")
        #     continue

        return raw


# ── Game Over Screen ──────────────────────────────────────────────────────────

def show_game_over(
    guesses: list[str],
    word: str,
    won: bool,
    streak: int,
    num_guesses_used: int,
) -> None:
    """Display the final board and result message."""
    render_game(guesses, word, "Game Over")

    if won:
        msg_style = "win"
        messages = {
            1: "🌟 Genius!",
            2: "🔥 Magnificent!",
            3: "🎉 Impressive!",
            4: "👏 Splendid!",
            5: "😌 Great!",
            6: "😅 Phew!",
        }
        msg = messages.get(num_guesses_used, "🎉 Nice!")
        console.print(
            Align.center(
                Text(f" {msg}  The word was  {word} ", style=msg_style)
            )
        )
        console.print(
            Align.center(
                Text(f" 🔥 Win Streak: {streak} ", style="streak")
            )
        )
    else:
        console.print(
            Align.center(
                Text(f" 😞  The word was  {word} ", style="lose")
            )
        )
        console.print(
            Align.center(
                Text(" Streak reset to 0. ", style="dim")
            )
        )
    console.print()


# ── Core Game Loop ────────────────────────────────────────────────────────────

def play_round(words: list[str], streak: int) -> tuple[bool, int]:
    """
    Play a single round of Wordle.
    Returns (won: bool, updated_streak: int).
    """
    word = random.choice(words)
    guesses = ["_" * NUM_LETTERS] * NUM_GUESSES
    won = False
    num_guesses_used = 0

    with contextlib.suppress(KeyboardInterrupt):
        for idx in range(NUM_GUESSES):
            render_game(guesses, word, f"Guess {idx + 1} / {NUM_GUESSES}")

            guess = get_guess(previous_guesses=guesses[:idx], all_words=words)
            guesses[idx] = guess
            num_guesses_used = idx + 1

            if guess == word:
                won = True
                break

    updated_streak = streak + 1 if won else 0
    show_game_over(guesses, word, won, updated_streak, num_guesses_used)
    return won, updated_streak


def ask_play_again() -> bool:
    """Ask the user if they want to play another round."""
    answer = Prompt.ask(
        "[bold cyan]Play again?[/]",
        choices=["y", "n"],
        default="y",
        console=console,
    )
    return answer.lower() == "y"


# ── Entry Point ───────────────────────────────────────────────────────────────

def main() -> None:
    show_welcome()
    words, source_name = choose_word_source()
    console.print(f"[info]Loaded {len(words):,} words from {source_name}.[/]")
    console.input("\n[bold]Press Enter to start…[/] ")

    streak = 0
    while True:
        _won, streak = play_round(words, streak)
        if not ask_play_again():
            break

    console.print()
    console.print(
        Panel(
            Align.center(
                Text.assemble(
                    ("Thanks for playing ", "bold white"),
                    ("WORDLE", "bold green"),
                    ("!\n", "bold white"),
                    (f"Final streak: {streak} 🔥", "bold yellow"),
                )
            ),
            border_style="magenta",
            padding=(1, 4),
        )
    )
    console.print()


if __name__ == "__main__":
    main()
