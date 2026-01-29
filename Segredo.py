import streamlit as st

# =====================================================
# CONFIG
# =====================================================
st.set_page_config(
    page_title="Football Studio – BASE ESTÁVEL",
    layout="centered"
)

# =====================================================
# STATE
# =====================================================
if "history" not in st.session_state:
    st.session_state.history = []

if "rounds_without_draw" not in st.session_state:
    st.session_state.rounds_without_draw = 0

# =====================================================
# UI
# =====================================================
st.title("⚽ Football Studio – BASE ESTÁVEL")

c1, c2, c3 = st.columns(3)
if c1.button("🔴 Home"):
    st.session_state.history.insert(0, "R")
if c2.button("🔵 Away"):
    st.session_state.history.insert(0, "B")
if c3.button("🟡 Draw"):
    st.session_state.history.insert(0, "D")

# =====================================================
# DRAW COUNTER
# =====================================================
if st.session_state.history:
    if st.session_state.history[0] == "D":
        st.session_state.rounds_without_draw = 0
    else:
        st.session_state.rounds_without_draw += 1

# =====================================================
# HELPERS
# =====================================================
def icon(x):
    return {"R": "🔴", "B": "🔵", "D": "🟡"}[x]

# =====================================================
# HISTÓRICO
# =====================================================
st.markdown("## 📊 Histórico (Recente → Antigo)")
st.write(" ".join(icon(x) for x in st.session_state.history[:30]))

# =====================================================
# CICLO DE 3 (BASE REAL)
# =====================================================
st.markdown("## 🔁 Ciclo Atual (3 Rodadas)")

def cycle_3(hist):
    if len(hist) < 3:
        return None
    return hist[:3]

def classify_cycle(c):
    a, b, c2 = c

    if a == b == c2:
        return "DIRECIONAL PURO"

    if a != b and b != c2 and a == c2:
        return "ALTERNÂNCIA CLÁSSICA"

    if a == b and b != c2:
        return "QUEBRA CURTA"

    if a != b and b == c2:
        return "REVERSÃO"

    if "D" in c:
        return "DRAW COMO ÂNCORA"

    return "MISTO"

cycle = cycle_3(st.session_state.history)

if cycle:
    st.write(" ".join(icon(x) for x in cycle))
    cycle_type = classify_cycle(cycle)
    st.info(f"Leitura do ciclo: **{cycle_type}**")
else:
    cycle_type = None
    st.write("Aguardando 3 rodadas...")

# =====================================================
# DECISÃO SIMPLES (SEM TRAVAR)
# =====================================================
st.markdown("## 🎯 Decisão")

decision = "⏳ AGUARDAR"
reason = "Histórico insuficiente"

if cycle_type == "ALTERNÂNCIA CLÁSSICA":
    next_color = "R" if cycle[0] == "B" else "B"
    decision = f"🎯 APOSTAR {'🔴 HOME' if next_color=='R' else '🔵 AWAY'}"
    reason = "Alternância detectada (ciclo 3)"

elif cycle_type == "DIRECIONAL PURO":
    decision = f"🎯 APOSTAR {icon(cycle[0])}"
    reason = "Direção contínua"

elif st.session_state.rounds_without_draw >= 30:
    decision = "🎯 APOSTAR 🟡 DRAW"
    reason = "Pressão de empate"

st.success(f"{decision}\n\nMotivo: {reason}")

# =====================================================
# DEBUG TRANSPARENTE
# =====================================================
with st.expander("🧪 Debug (transparente)"):
    st.write("Histórico bruto:", st.session_state.history[:10])
    st.write("Rodadas sem draw:", st.session_state.rounds_without_draw)
