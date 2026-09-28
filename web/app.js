// ── Word list URLs ────────────────────────────────────────────────────────────
const SOURCES = {
  stanford: {
    url: "/words/stanford",
    label: "Stanford"
  },
  sowpods: {
    url: "/words/sowpods",
    label: "SOWPODS"
  }
};

// ── Game State ────────────────────────────────────────────────────────────────
let wordList    = [];
let secretWord  = "";
let currentRow  = 0;
let currentCol  = 0;
let currentGuess = [];
let gameOver    = false;
let streak      = 0;
let activeSource = "stanford";

// Priority for key colour: correct > misplaced > wrong
const KEY_PRIORITY = { correct: 3, misplaced: 2, wrong: 1, "": 0 };

// ── DOM helpers ───────────────────────────────────────────────────────────────
const tile     = (r, c)  => document.getElementById(`r${r}c${c}`);
const keyEl    = (letter) => document.querySelector(`.key[data-key="${letter}"]`);
const streakEl = ()       => document.getElementById("streak");

// ── Loading overlay ───────────────────────────────────────────────────────────
function showLoading(msg = "Loading word list…") {
  let ov = document.getElementById("loading-overlay");
  if (!ov) {
    ov = document.createElement("div");
    ov.id = "loading-overlay";
    ov.innerHTML = `<div class="spinner"></div><div>${msg}</div>`;
    document.body.appendChild(ov);
  } else {
    ov.querySelector("div:last-child").textContent = msg;
    ov.style.display = "flex";
  }
}

function hideLoading() {
  const ov = document.getElementById("loading-overlay");
  if (ov) ov.style.display = "none";
}

// ── Toast ─────────────────────────────────────────────────────────────────────
let toastTimer = null;
function showToast(msg, duration = 1800) {
  const t = document.getElementById("toast");
  t.textContent = msg;
  t.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.remove("show"), duration);
}

// ── Fetch word list from server ───────────────────────────────────────────────
async function loadWords(source) {
  showLoading(`Loading ${SOURCES[source].label} word list…`);
  try {
    const res = await fetch(SOURCES[source].url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const text = await res.text();
    const words = text
      .split("\n")
      .map(w => w.trim().toUpperCase())
      .filter(w => w.length === 5 && /^[A-Z]+$/.test(w));
    if (words.length === 0) throw new Error("Empty word list");
    return words;
  } catch (err) {
    showToast(`⚠ Could not load ${SOURCES[source].label}: ${err.message}`);
    return null;
  } finally {
    hideLoading();
  }
}

// ── Board ─────────────────────────────────────────────────────────────────────
function resetBoard() {
  for (let r = 0; r < 6; r++) {
    for (let c = 0; c < 5; c++) {
      const t = tile(r, c);
      t.textContent = "";
      t.className = "tile";
    }
  }
}

function resetKeyboard() {
  document.querySelectorAll(".key").forEach(k => {
    k.classList.remove("correct", "misplaced", "wrong");
  });
}

// ── Type / Backspace ──────────────────────────────────────────────────────────
function typeLetter(letter) {
  if (gameOver || currentCol >= 5) return;
  currentGuess.push(letter);
  const t = tile(currentRow, currentCol);
  t.textContent = letter;
  t.classList.add("filled");
  // pop animation
  t.classList.remove("pop");
  void t.offsetWidth; // reflow
  t.classList.add("pop");
  currentCol++;
}

function deleteLetter() {
  if (gameOver || currentCol === 0) return;
  currentCol--;
  currentGuess.pop();
  const t = tile(currentRow, currentCol);
  t.textContent = "";
  t.classList.remove("filled");
}

// ── Evaluate a guess against the secret word ─────────────────────────────────
// Returns array of 5 states: "correct" | "misplaced" | "wrong"
function evaluate(guess, word) {
  const result = Array(5).fill("wrong");
  const wordArr = word.split("");
  const guessArr = guess.split("");
  const used = Array(5).fill(false);

  // Pass 1: find correct positions
  for (let i = 0; i < 5; i++) {
    if (guessArr[i] === wordArr[i]) {
      result[i] = "correct";
      used[i] = true;
    }
  }
  // Pass 2: find misplaced
  for (let i = 0; i < 5; i++) {
    if (result[i] === "correct") continue;
    for (let j = 0; j < 5; j++) {
      if (!used[j] && guessArr[i] === wordArr[j]) {
        result[i] = "misplaced";
        used[j] = true;
        break;
      }
    }
  }
  return result;
}

// ── Reveal a row with flip animation ─────────────────────────────────────────
function revealRow(row, states, onDone) {
  const FLIP_DELAY = 300; // ms between each tile flip
  states.forEach((state, col) => {
    setTimeout(() => {
      const t = tile(row, col);
      t.classList.add("flip");
      // apply colour at halfway point of the flip
      setTimeout(() => {
        t.classList.remove("filled");
        t.classList.add(state);
      }, 250);
      if (col === 4) {
        setTimeout(onDone, 250 + 50);
      }
    }, col * FLIP_DELAY);
  });
}

// ── Update keyboard colours ───────────────────────────────────────────────────
function updateKeyboard(guess, states) {
  for (let i = 0; i < 5; i++) {
    const letter = guess[i];
    const k = keyEl(letter);
    if (!k) continue;
    const current = [...k.classList].find(c => KEY_PRIORITY[c] !== undefined) || "";
    if ((KEY_PRIORITY[states[i]] || 0) > (KEY_PRIORITY[current] || 0)) {
      k.classList.remove("correct", "misplaced", "wrong");
      k.classList.add(states[i]);
    }
  }
}

// ── Bounce win animation ──────────────────────────────────────────────────────
function bounceRow(row) {
  for (let c = 0; c < 5; c++) {
    setTimeout(() => {
      const t = tile(row, c);
      t.classList.remove("bounce");
      void t.offsetWidth;
      t.classList.add("bounce");
    }, c * 100);
  }
}

// ── Submit guess ──────────────────────────────────────────────────────────────
function submitGuess() {
  if (gameOver) return;
  if (currentCol < 5) {
    shakeRow(currentRow);
    showToast("Not enough letters");
    return;
  }

  const guess = currentGuess.join("");
  const states = evaluate(guess, secretWord);
  const row = currentRow;

  revealRow(row, states, () => {
    updateKeyboard(guess, states);

    if (guess === secretWord) {
      streak++;
      streakEl().textContent = streak;
      bounceRow(row);
      const messages = ["🧠 Genius!", "🔥 Magnificent!", "🎉 Impressive!", "👏 Splendid!", "😌 Great!", "😅 Phew!"];
      showToast(messages[row] || "Nice!", 3000);
      gameOver = true;
      return;
    }

    currentRow++;
    currentCol = 0;
    currentGuess = [];

    if (currentRow === 6) {
      streak = 0;
      streakEl().textContent = 0;
      showToast(`The word was ${secretWord}`, 4000);
      gameOver = true;
    }
  });
}

// ── Shake for invalid ─────────────────────────────────────────────────────────
function shakeRow(row) {
  const r = document.getElementById(`row-${row}`);
  r.classList.remove("shake");
  void r.offsetWidth;
  r.classList.add("shake");
  setTimeout(() => r.classList.remove("shake"), 500);
}

// ── Start new game ────────────────────────────────────────────────────────────
function newGame() {
  if (wordList.length === 0) return;
  secretWord   = wordList[Math.floor(Math.random() * wordList.length)];
  currentRow   = 0;
  currentCol   = 0;
  currentGuess = [];
  gameOver     = false;
  resetBoard();
  resetKeyboard();
  console.log("Secret word (dev):", secretWord); // remove in production
}

// ── Keyboard input ────────────────────────────────────────────────────────────
document.addEventListener("keydown", (e) => {
  if (e.ctrlKey || e.altKey || e.metaKey) return;
  const key = e.key.toUpperCase();
  if (key === "ENTER") {
    submitGuess();
  } else if (key === "BACKSPACE") {
    deleteLetter();
  } else if (/^[A-Z]$/.test(key)) {
    typeLetter(key);
  }
});

// ── On-screen keyboard clicks ─────────────────────────────────────────────────
document.getElementById("keyboard").addEventListener("click", (e) => {
  const btn = e.target.closest(".key");
  if (!btn) return;
  const k = btn.dataset.key;
  if (k === "ENTER") submitGuess();
  else if (k === "BACKSPACE") deleteLetter();
  else typeLetter(k);
});

// ── New game button ───────────────────────────────────────────────────────────
document.getElementById("new-game-btn").addEventListener("click", newGame);

// ── Word source toggle ────────────────────────────────────────────────────────
document.querySelectorAll(".source-btn").forEach(btn => {
  btn.addEventListener("click", async () => {
    const src = btn.dataset.source;
    if (src === activeSource) return;

    document.querySelectorAll(".source-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    activeSource = src;

    const words = await loadWords(src);
    if (words) {
      wordList = words;
      newGame();
    }
  });
});

// ── Init ──────────────────────────────────────────────────────────────────────
(async () => {
  const words = await loadWords(activeSource);
  if (words) {
    wordList = words;
    newGame();
  }
})();
