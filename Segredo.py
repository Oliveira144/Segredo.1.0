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

if "cycle_memory" not in st.session_state:
    st.session_state.cycle_memory = []

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

    if len(sizes) >= 4 and all(s == 1 for s in sizes[:4]):
        return "CHOPPY PURO"
    if sizes and max(sizes) >= 6:
        return "DIRECIONAL FORTE"
    if len(sizes) >= 3 and sizes[0] > sizes[1] < sizes[2]:
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
        return 2, "ALTERNÂNCIA SIMPLES"

    if len(sizes) >= 7 and all(s == 1 for s in sizes[:7]):
        return 3, "ALTERNÂNCIA ESTENDIDA"

    if max(sizes) in [2, 3]:
        return 4, "DIRECIONAL CURTO"

    if max(sizes) in [4, 5]:
        return 5, "DIRECIONAL MÉDIO"

    if max(sizes) >= 6:
        return 6, "DIRECIONAL FORTE"

    if len(sizes) >= 3 and sizes[1] == 1 and sizes[0] >= 3:
        return 7, "FALSA QUEBRA"

    if len(sizes) >= 6 and all(s >= 3 for s in sizes[:6]):
        return 8, "SATURAÇÃO"

    if st.session_state.rounds_without_draw >= 30:
        return 9, "MANIPULAÇÃO ATIVA (DRAW)"

    return 3, "NEUTRO"

# -----------------------------------------------------
# PROBABILIDADES MULTICENÁRIO
# -----------------------------------------------------
def probability_engine(hist):
    base = {"R": 33.0, "B": 33.0, "D": 34.0}
    blocks = extract_blocks(hist)
    last = hist[0]

    alt, ratio = detect_alternation_raw(hist)

    if alt:
        opp = "R" if last == "B" else "B"
        base[opp] += 18 * ratio
        base[last] -= 10

    if blocks and blocks[0]["size"] >= 4:
        base[blocks[0]["color"]] += 15

    if st.session_state.rounds_without_draw >= 28:
        base["D"] += 20

    total = sum(base.values())
    for k in base:
        base[k] = round((base[k] / total) * 100, 1)

    return base

# -----------------------------------------------------
# CASSINO vs JOGADOR
# -----------------------------------------------------
def casino_reading(level, regime):
    if level >= 7:
        return "🎰 Cassino criando armadilha psicológica"
    if regime == "DIRECIONAL FORTE":
        return "🎰 Cassino empurrando continuidade"
    if regime == "CHOPPY PURO":
        return "🎰 Cassino neutralizando padrões"
    return "🎰 Fluxo neutro"

def player_reading(level, alt):
    if alt and level <= 3:
        return "🧠 Explorar alternância"
    if level >= 7:
        return "🧠 Aguardar quebra real"
    if level >= 5:
        return "🧠 Seguir direção com cautela"
    return "🧠 Aguardar melhor contexto"

# =====================================================
# IA FINAL
# =====================================================
def ia_decision(hist):
    if not hist:
        return "⏳ AGUARDAR", 0, "SEM DADOS"

    regime = market_regime(hist)
    level, level_desc = manipulation_level(hist)
    alt, alt_ratio = detect_alternation_raw(hist)
    probs = probability_engine(hist)

    # PRIORIDADE 1 — MANIPULAÇÃO ATIVA
    if level >= 8:
        return "⛔ NÃO OPERAR", 0, level_desc

    # PRIORIDADE 2 — ALTERNÂNCIA REAL
    if alt and regime != "DIRECIONAL FORTE":
        next_color = "R" if hist[0] == "B" else "B"
        score = int(60 + alt_ratio * 10)
        return (
            f"🎯 APOSTAR {'🔴 HOME' if next_color=='R' else '🔵 AWAY'}",
            score,
            f"ALTERNÂNCIA REAL ({alt_ratio})"
        )

    # PRIORIDADE 3 — DIREÇÃO
    if regime == "DIRECIONAL FORTE":
        color = extract_blocks(hist)[0]["color"]
        return (
            f"🎯 APOSTAR {'🔴 HOME' if color=='R' else '🔵 AWAY'}",
            62,
            "DIRECIONAL FORTE"
        )

    # PRIORIDADE 4 — DRAW
    if st.session_state.rounds_without_draw >= 30:
        return "🎯 APOSTAR 🟡 DRAW", 66, "PRESSÃO DE EMPATE"

    return "⏳ AGUARDAR", 0, "SEM CONFLUÊNCIA"

# =====================================================
# OUTPUT
# =====================================================
decision, score, context = ia_decision(st.session_state.history)
level, level_desc = manipulation_level(st.session_state.history)
probs = probability_engine(st.session_state.history)
alt, _ = detect_alternation_raw(st.session_state.history)
regime = market_regime(st.session_state.history)

st.markdown("## 🎯 DECISÃO DA IA")
st.success(f"{decision}\n\nScore: {score}\n\n{context}")

st.markdown("## 🧬 MAPA DE MANIPULAÇÃO")
st.info(f"Nível {level} — {level_desc}")

st.markdown("## 📊 PROBABILIDADES")
st.write(f"🔴 Home: {probs['R']}%")
st.write(f"🔵 Away: {probs['B']}%")
st.write(f"🟡 Draw: {probs['D']}%")

st.markdown("## 🎰 vs 🧠 LEITURA ESTRATÉGICA")
st.warning(casino_reading(level, regime))
st.success(player_reading(level, alt))

with st.expander("🧠 Regime Atual"):
    st.write(regime)

with st.expander("🟡 Estatística de Empate"):
    st.write(f"Rodadas sem Draw: {st.session_state.rounds_without_draw}")
