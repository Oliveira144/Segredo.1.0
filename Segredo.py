import streamlit as st
from collections import deque

# =====================================================
# CONFIG
# =====================================================
st.set_page_config(
    page_title="Football Studio PRO ULTIMATE",
    layout="centered"
)

MAX_HISTORY = 120

# =====================================================
# STATE
# =====================================================
if "history" not in st.session_state:
    st.session_state.history = deque(maxlen=MAX_HISTORY)

if "cycle_memory" not in st.session_state:
    st.session_state.cycle_memory = []

if "bank" not in st.session_state:
    st.session_state.bank = 1000.0

if "profit" not in st.session_state:
    st.session_state.profit = 0.0

if "rounds_without_draw" not in st.session_state:
    st.session_state.rounds_without_draw = 0

# =====================================================
# UI
# =====================================================
st.title("⚽ Football Studio – PRO ULTIMATE")

c1, c2, c3 = st.columns(3)
if c1.button("🔴 Home"):
    st.session_state.history.appendleft("R")
if c2.button("🔵 Away"):
    st.session_state.history.appendleft("B")
if c3.button("🟡 Draw"):
    st.session_state.history.appendleft("D")

st.markdown(f"### 💰 Banca: R$ {st.session_state.bank:.2f}")
st.markdown(f"### 📈 Lucro: R$ {st.session_state.profit:.2f}")

# =====================================================
# DRAW COUNTER
# =====================================================
if st.session_state.history:
    if st.session_state.history[0] == "D":
        st.session_state.rounds_without_draw = 0
    else:
        st.session_state.rounds_without_draw += 1

# =====================================================
# HISTÓRICO
# =====================================================
st.markdown("## 📊 Histórico (Recente → Antigo)")

def icon(x):
    return "🔴" if x == "R" else "🔵" if x == "B" else "🟡"

st.write(" ".join(icon(x) for x in list(st.session_state.history)[:30]))

# =====================================================
# CORE ANALYSIS
# =====================================================
def extract_blocks(hist):
    hist = list(hist)
    if not hist:
        return []

    blocks = []
    current = hist[0]
    size = 1

    for i in range(1, len(hist)):
        if hist[i] == current:
            size += 1
        else:
            blocks.append({"color": current, "size": size})
            current = hist[i]
            size = 1

    blocks.append({"color": current, "size": size})
    return blocks

# -----------------------------------------------------
# ALTERNÂNCIA REAL (RAW)
# -----------------------------------------------------
def detect_alternation_raw(hist, window=8):
    seq = [x for x in hist if x != "D"][:window]
    if len(seq) < window:
        return False, 0.0

    changes = sum(seq[i] != seq[i+1] for i in range(len(seq)-1))
    ratio = changes / (len(seq)-1)
    return ratio >= 0.75, round(ratio, 2)

# -----------------------------------------------------
# REGIME DE MERCADO
# -----------------------------------------------------
def market_regime(hist):
    blocks = extract_blocks(hist)
    sizes = [b["size"] for b in blocks if b["color"] != "D"][:6]

    if len(sizes) >= 4 and all(s == 1 for s in sizes):
        return "CHOPPY PURO"

    if sizes and max(sizes) >= 5:
        return "DIRECIONAL FORTE"

    if len(sizes) >= 3 and sizes[0] > sizes[1] < sizes[2]:
        return "FALSA QUEBRA"

    return "MISTO"

# -----------------------------------------------------
# MEMÓRIA DE CICLOS
# -----------------------------------------------------
def update_cycle_memory(regime):
    mem = st.session_state.cycle_memory
    if not mem or mem[-1] != regime:
        mem.append(regime)
    if len(mem) > 3:
        mem[:] = mem[-3:]

# -----------------------------------------------------
# PADRÕES ESTRUTURAIS
# -----------------------------------------------------
def detect_patterns(hist):
    blocks = extract_blocks(hist)
    patterns = []

    if not blocks:
        return patterns

    colors = [b["color"] for b in blocks]
    sizes = [b["size"] for b in blocks]

    # Streak curta
    if sizes[0] == 2:
        patterns.append((colors[0], 55, "DUPLO"))

    # Streak média
    if sizes[0] in [3, 4]:
        patterns.append((colors[0], 58, "STREAK MÉDIA"))

    # Streak forte
    if sizes[0] >= 5:
        patterns.append((colors[0], 62, "STREAK FORTE"))

    # Falsa quebra
    if len(sizes) >= 3 and sizes[1] == 1 and sizes[0] >= 3:
        patterns.append((colors[0], 60, "FALSA QUEBRA"))

    # Saturação choppy
    if len(sizes) >= 5 and all(s == 1 for s in sizes[:5]):
        patterns.append((colors[0], 59, "SATURAÇÃO"))

    # Pressão de empate
    if st.session_state.rounds_without_draw >= 28:
        patterns.append(("D", 65, "PRESSÃO DE EMPATE"))

    return patterns

# =====================================================
# IA FINAL
# =====================================================
def ia_decision(hist):
    if not hist:
        return "⏳ AGUARDAR", 0, "SEM DADOS"

    regime = market_regime(hist)
    update_cycle_memory(regime)

    alt, alt_ratio = detect_alternation_raw(hist)
    patterns = detect_patterns(hist)

    # 1️⃣ PRIORIDADE: ALTERNÂNCIA REAL
    if alt and regime != "DIRECIONAL FORTE":
        next_color = "R" if hist[0] == "B" else "B"
        score = int(60 + alt_ratio * 10)
        return (
            f"🎯 APOSTAR {'🔴 HOME' if next_color=='R' else '🔵 AWAY'}",
            score,
            f"ALTERNÂNCIA REAL ({alt_ratio})"
        )

    # 2️⃣ STREAK FORTE CONFIRMADA
    for c, s, p in patterns:
        if p == "STREAK FORTE" and regime == "DIRECIONAL FORTE":
            return (
                f"🎯 APOSTAR {'🔴 HOME' if c=='R' else '🔵 AWAY'}",
                s + 4,
                p
            )

    # 3️⃣ DRAW POR CONTEXTO
    if st.session_state.rounds_without_draw >= 30 and regime != "CHOPPY PURO":
        return "🎯 APOSTAR 🟡 DRAW", 66, "DRAW POR PRESSÃO + CONTEXTO"

    # 4️⃣ MELHOR PADRÃO RESTANTE
    if patterns:
        color, score, pattern = max(patterns, key=lambda x: x[1])
        if score >= 55:
            if color == "R":
                return "🎯 APOSTAR 🔴 HOME", score, pattern
            if color == "B":
                return "🎯 APOSTAR 🔵 AWAY", score, pattern
            return "🎯 APOSTAR 🟡 DRAW", score, pattern

    return "⏳ AGUARDAR", 0, "SEM CONFLUÊNCIA"

# =====================================================
# OUTPUT
# =====================================================
decision, score, context = ia_decision(st.session_state.history)

st.markdown("## 🎯 DECISÃO DA IA")
st.success(f"{decision}\n\nScore: {score}\n\n{context}")

with st.expander("🧠 Regime & Ciclos"):
    st.write("Regime atual:", market_regime(st.session_state.history))
    st.write("Memória:", st.session_state.cycle_memory)

with st.expander("🟡 Estatística de Empate"):
    st.write(f"Rodadas sem Draw: {st.session_state.rounds_without_draw}")
