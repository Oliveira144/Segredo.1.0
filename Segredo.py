import streamlit as st
from collections import deque

# =====================================================
# CONFIG
# =====================================================
st.set_page_config(page_title="Football Studio PRO ULTIMATE", layout="centered")
MAX_HISTORY = 120

# =====================================================
# STATE
# =====================================================
if "history" not in st.session_state:
    st.session_state.history = deque(maxlen=MAX_HISTORY)

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
def icon(x):
    return "🔴" if x == "R" else "🔵" if x == "B" else "🟡"

st.markdown("## 📊 Histórico (Recente → Antigo)")
st.write(" ".join(icon(x) for x in list(st.session_state.history)[:30]))

# =====================================================
# CORE ENGINE
# =====================================================
def extract_blocks(hist):
    hist = list(hist)
    if not hist:
        return []
    blocks, current, size = [], hist[0], 1
    for i in range(1, len(hist)):
        if hist[i] == current:
            size += 1
        else:
            blocks.append({"color": current, "size": size})
            current, size = hist[i], 1
    blocks.append({"color": current, "size": size})
    return blocks

# -----------------------------------------------------
# ALTERNÂNCIA REAL
# -----------------------------------------------------
def detect_alternation_raw(hist, window=8):
    seq = [x for x in hist if x != "D"][:window]
    if len(seq) < window:
        return False, 0.0
    changes = sum(seq[i] != seq[i+1] for i in range(len(seq)-1))
    ratio = changes / (len(seq)-1)
    return ratio >= 0.65, round(ratio, 2)

# -----------------------------------------------------
# REGIME
# -----------------------------------------------------
def market_regime(hist):
    blocks = extract_blocks(hist)
    sizes = [b["size"] for b in blocks if b["color"] != "D"][:6]

    if len(sizes) >= 4 and all(s == 1 for s in sizes[:4]):
        return "CHOPPY"
    if sizes and max(sizes) >= 6:
        return "DIRECIONAL FORTE"
    if len(sizes) >= 3 and sizes[1] == 1 and sizes[0] >= 3:
        return "FALSA QUEBRA"
    return "MISTO"

# -----------------------------------------------------
# MAPA DE MANIPULAÇÃO (1–9)
# -----------------------------------------------------
def manipulation_level(hist):
    blocks = extract_blocks(hist)
    sizes = [b["size"] for b in blocks if b["color"] != "D"][:6]

    if not sizes:
        return 1, "SEM DADOS"
    if len(sizes) >= 5 and all(s == 1 for s in sizes[:5]):
        return 3, "ALTERNÂNCIA CONTROLADA"
    if max(sizes) in [2, 3]:
        return 4, "DIRECIONAL CURTO"
    if max(sizes) in [4, 5]:
        return 5, "DIRECIONAL MÉDIO"
    if max(sizes) >= 6:
        return 6, "DIRECIONAL FORTE"
    if len(sizes) >= 3 and sizes[1] == 1 and sizes[0] >= 3:
        return 7, "FALSA QUEBRA"
    if st.session_state.rounds_without_draw >= 30:
        return 9, "MANIPULAÇÃO ATIVA (DRAW)"
    return 3, "NEUTRO"

# -----------------------------------------------------
# VIÉS DIRECIONAL CURTO (🔥 DESBLOQUEIA ENTRADAS)
# -----------------------------------------------------
def short_term_bias(hist, window=5):
    seq = [x for x in hist if x != "D"][:window]
    if len(seq) < window:
        return None
    if seq.count("R") >= window - 1:
        return "R"
    if seq.count("B") >= window - 1:
        return "B"
    return None

# -----------------------------------------------------
# PROBABILIDADES
# -----------------------------------------------------
def probability_engine(hist):
    base = {"R": 33.0, "B": 33.0, "D": 34.0}
    last = hist[0]

    alt, ratio = detect_alternation_raw(hist)
    if alt:
        opp = "R" if last == "B" else "B"
        base[opp] += 15
        base[last] -= 8

    if st.session_state.rounds_without_draw >= 28:
        base["D"] += 15

    total = sum(base.values())
    for k in base:
        base[k] = round((base[k] / total) * 100, 1)

    return base

# =====================================================
# IA FINAL (CORRIGIDA)
# =====================================================
def ia_decision(hist):
    regime = market_regime(hist)
    level, level_desc = manipulation_level(hist)
    alt, alt_ratio = detect_alternation_raw(hist)
    bias = short_term_bias(hist)

    # ⛔ ARMADILHA
    if level >= 8:
        return "⛔ NÃO OPERAR", 0, level_desc

    # 🔁 ALTERNÂNCIA
    if alt and regime != "DIRECIONAL FORTE":
        next_color = "R" if hist[0] == "B" else "B"
        return f"🎯 APOSTAR {'🔴 HOME' if next_color=='R' else '🔵 AWAY'}", 60, "ALTERNÂNCIA REAL"

    # 🔥 DIRECIONAL FORTE
    if regime == "DIRECIONAL FORTE":
        color = extract_blocks(hist)[0]["color"]
        return f"🎯 APOSTAR {'🔴 HOME' if color=='R' else '🔵 AWAY'}", 62, "DIRECIONAL FORTE"

    # 🔥🔥 DIRECIONAL CURTO (NÍVEL 3–5)
    if level in [3, 4, 5] and bias:
        return f"🎯 APOSTAR {'🔴 HOME' if bias=='R' else '🔵 AWAY'}", 56, f"DIRECIONAL CURTO (NÍVEL {level})"

    # 🟡 DRAW
    if st.session_state.rounds_without_draw >= 30:
        return "🎯 APOSTAR 🟡 DRAW", 65, "PRESSÃO DE EMPATE"

    return "⏳ AGUARDAR", 0, "SEM VANTAGEM"

# =====================================================
# OUTPUT
# =====================================================
decision, score, context = ia_decision(st.session_state.history)
level, level_desc = manipulation_level(st.session_state.history)
probs = probability_engine(st.session_state.history)
regime = market_regime(st.session_state.history)

st.markdown("## 🎯 DECISÃO DA IA")
st.success(f"{decision}\n\nScore: {score}\n\n{context}")

st.markdown("## 🧬 MAPA DE MANIPULAÇÃO")
st.info(f"Nível {level} — {level_desc}")

st.markdown("## 📊 PROBABILIDADES")
st.write(f"🔴 Home: {probs['R']}%")
st.write(f"🔵 Away: {probs['B']}%")
st.write(f"🟡 Draw: {probs['D']}%")

st.markdown("## 🎰 vs 🧠 LEITURA")
st.warning(f"🎰 Cassino: {regime}")
st.success("🧠 Jogador: Explorar vantagem estrutural")
