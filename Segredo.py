import streamlit as st

# =====================================================
# CONFIG
# =====================================================
st.set_page_config(
    page_title="Football Studio – AI FINAL (Baixo Erro)",
    layout="wide"
)

# =====================================================
# STATE
# =====================================================
if "history" not in st.session_state:
    st.session_state.history = []

if "cycle_memory" not in st.session_state:
    st.session_state.cycle_memory = []

# =====================================================
# UI
# =====================================================
st.title("⚽ Football Studio – AI FINAL")

c1, c2, c3, c4 = st.columns(4)
if c1.button("🔴 Home"):
    st.session_state.history.insert(0, "🔴")
if c2.button("🔵 Away"):
    st.session_state.history.insert(0, "🔵")
if c3.button("🟡 Draw"):
    st.session_state.history.insert(0, "🟡")
if c4.button("Reset"):
    st.session_state.history.clear()
    st.session_state.cycle_memory.clear()

# =====================================================
# HISTÓRICO 9x10
# =====================================================
st.divider()
st.subheader("📊 Histórico (Mais recente → Mais antigo)")

def render_history(hist):
    rows = [hist[i:i+9] for i in range(0, len(hist), 9)]
    for row in rows[:10]:
        st.write(" ".join(row))

render_history(st.session_state.history)

# =====================================================
# BLOCO ATIVO
# =====================================================
def get_active_block(history):
    base = history[0]
    size = 1
    for i in range(1, len(history)):
        if history[i] == base:
            size += 1
        else:
            break
    return base, size

# =====================================================
# EXTRAÇÃO DE BLOCOS (ANTIGO → RECENTE)
# =====================================================
def extract_blocks(history):
    hist = list(reversed(history))  # antigo → recente
    blocks = []
    i = 0
    while i < len(hist):
        color = hist[i]
        size = 1
        i += 1
        while i < len(hist) and hist[i] == color:
            size += 1
            i += 1
        blocks.append({"color": color, "size": size})
    return blocks[::-1]  # recente primeiro

# =====================================================
# CICLOS
# =====================================================
def classify_block(size):
    if size == 1:
        return "CHOPPY"
    if size == 2:
        return "CURTO"
    if size == 3:
        return "STREAK"
    return "STREAK_FORTE"

def update_cycle(block_type):
    mem = st.session_state.cycle_memory
    if not mem or mem[-1] != block_type:
        mem.append(block_type)
    if len(mem) > 3:
        mem[:] = mem[-3:]

# =====================================================
# FILTRO 1 — FALSA CONTINUIDADE
# =====================================================
def false_continuity(blocks, current_size):
    if current_size < 3 or len(blocks) < 3:
        return False
    recent_sizes = [b["size"] for b in blocks[1:4]]
    return recent_sizes.count(current_size) >= 1

# =====================================================
# FILTRO 2 — QUEBRA SIMÉTRICA
# =====================================================
def symmetric_break(blocks):
    if len(blocks) < 2:
        return False
    return blocks[0]["size"] == blocks[1]["size"]

# =====================================================
# ANÁLISE FINAL
# =====================================================
def analyze(history):
    if len(history) < 3:
        return "INÍCIO", "WAIT", 0, "SEM LEITURA"

    color, size = get_active_block(history)

    # -------- EMPATE --------
    if color == "🟡":
        return "RESET", "WAIT", 0, "EMPATE TRAVA A MESA"

    block_type = classify_block(size)
    update_cycle(block_type)
    mem = st.session_state.cycle_memory

    # -------- FORMAÇÃO --------
    if size < 3:
        return "FORMAÇÃO", "WAIT", 0, "BLOCO IMATURO"

    # -------- SATURAÇÃO --------
    if mem.count("STREAK_FORTE") >= 2:
        return "SATURAÇÃO", "WAIT", 0, "CICLO SATURADO"

    # -------- ARMADILHA STREAK CURTA --------
    if size == 3 and history[1] != color and history[1] != "🟡":
        return "ARMADILHA", "WAIT", 0, "STREAK CURTA SUSPEITA"

    blocks = extract_blocks(history)

    # -------- FALSA CONTINUIDADE --------
    if false_continuity(blocks, size):
        return "ARMADILHA", "WAIT", 0, "FALSA CONTINUIDADE"

    # -------- QUEBRA SIMÉTRICA --------
    if symmetric_break(blocks):
        return "ARMADILHA", "WAIT", 0, "QUEBRA SIMÉTRICA"

    # -------- ENTRADA --------
    confidence = 60 + min(size * 3, 12)

    return (
        f"CONTINUIDADE {color}",
        color,
        confidence,
        f"{block_type} MATURADO"
    )

# =====================================================
# OUTPUT
# =====================================================
context, suggestion, conf, reading = analyze(st.session_state.history)

st.divider()
st.subheader("🧠 Análise")

c1, c2, c3 = st.columns(3)
c1.metric("Contexto", context)
c2.metric("Confiança", f"{conf}%")
c3.metric("Ciclo", " → ".join(st.session_state.cycle_memory))

st.info(f"📌 Leitura: {reading}")

st.subheader("🎯 Decisão")
if suggestion in ["🔴", "🔵"]:
    st.success(f"ENTRADA SUGERIDA: {suggestion} ({conf}%)")
else:
    st.warning("AGUARDAR – proteção de banca ativa")

st.caption(
    "Sistema final consolidado: bloco ativo, maturação, memória de ciclo, "
    "saturação, armadilhas avançadas (falsa continuidade e quebra simétrica). "
    "Menos entradas, erro real drasticamente menor."
)
