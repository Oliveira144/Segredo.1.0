import streamlit as st
from collections import deque, Counter

# ======================================================
# CONFIG
# ======================================================
st.set_page_config("Football Studio – Manipulation AI", layout="centered")
MAX_HISTORY = 120

# ======================================================
# STATE
# ======================================================
if "history" not in st.session_state:
    st.session_state.history = deque(maxlen=MAX_HISTORY)

if "rounds_without_draw" not in st.session_state:
    st.session_state.rounds_without_draw = 0

# ======================================================
# UI INPUT
# ======================================================
st.title("⚽ Football Studio – Manipulation AI")

c1, c2, c3 = st.columns(3)
if c1.button("🔴 HOME"):
    st.session_state.history.appendleft("R")
if c2.button("🔵 AWAY"):
    st.session_state.history.appendleft("B")
if c3.button("🟡 DRAW"):
    st.session_state.history.appendleft("D")

# ======================================================
# DRAW CONTROL
# ======================================================
if st.session_state.history:
    if st.session_state.history[0] == "D":
        st.session_state.rounds_without_draw = 0
    else:
        st.session_state.rounds_without_draw += 1

# ======================================================
# HELPERS
# ======================================================
def icon(x):
    return {"R":"🔴","B":"🔵","D":"🟡"}[x]

def blocks(hist):
    hist = list(hist)
    if not hist:
        return []
    out, cur, size = [], hist[0], 1
    for x in hist[1:]:
        if x == cur:
            size += 1
        else:
            out.append((cur, size))
            cur, size = x, 1
    out.append((cur, size))
    return out

# ======================================================
# HISTÓRICO
# ======================================================
st.markdown("## 📊 Histórico (Recente → Antigo)")
st.write(" ".join(icon(x) for x in list(st.session_state.history)[:30]))

# ======================================================
# MANIPULATION MAP (1–9)
# ======================================================
def manipulation_level(hist):
    if len(hist) < 6:
        return 1, "Ruído"

    bl = blocks(hist)
    sizes = [s for c,s in bl if c != "D"][:6]

    if st.session_state.rounds_without_draw >= 30:
        return 9, "Pressão extrema (empate)"

    if len(sizes) >= 5 and all(s == 1 for s in sizes[:5]):
        return 3, "Alternância simples"

    if max(sizes) == 2:
        return 4, "Direcional curto"

    if max(sizes) in [3,4]:
        return 5, "Direcional médio"

    if max(sizes) >= 5:
        return 6, "Direcional forte"

    if sizes[0] >= 4 and sizes[1] == 1:
        return 7, "Falsa quebra"

    return 2, "Padrão fraco"

# ======================================================
# PROBABILITIES (MULTI-CENÁRIO)
# ======================================================
def probability_engine(hist):
    if not hist:
        return {"R":33,"B":33,"D":34}

    base = Counter(hist)
    total = sum(base.values())

    structural = {
        "R": base["R"]/total,
        "B": base["B"]/total,
        "D": base["D"]/total
    }

    alt_bias = {"R":0,"B":0,"D":0}
    if len(hist) >= 4 and hist[0] != hist[1]:
        alt_bias["R" if hist[0]=="B" else "B"] += 0.15

    draw_bias = {"R":0,"B":0,"D":0}
    if st.session_state.rounds_without_draw >= 28:
        draw_bias["D"] += 0.25

    final = {}
    for k in ["R","B","D"]:
        final[k] = round((structural[k] + alt_bias[k] + draw_bias[k]) * 100,1)

    return final

# ======================================================
# CASINO VS PLAYER
# ======================================================
def casino_reading(hist):
    if len(hist) < 5:
        return "Induzindo overleitura"
    if hist[0] == hist[1]:
        return "Forçando continuidade"
    return "Forçando alternância"

def player_reading(hist, level):
    if level >= 7:
        return "Evitar armadilha"
    if level in [4,5]:
        return "Explorar direção"
    if level == 9:
        return "Empate com valor"
    return "Aguardar"

# ======================================================
# IA DECISION (NUNCA FICA MUDA)
# ======================================================
def ia_decision(hist):
    level, desc = manipulation_level(hist)
    probs = probability_engine(hist)

    best = max(probs, key=probs.get)
    conf = probs[best]

    if level >= 8:
        return "⛔ NÃO OPERAR", conf, desc

    if conf >= 55:
        label = "🔴 HOME" if best=="R" else "🔵 AWAY" if best=="B" else "🟡 DRAW"
        return f"🎯 ENTRAR {label}", conf, desc

    return "⏳ AGUARDAR", conf, desc

# ======================================================
# OUTPUT
# ======================================================
decision, confidence, context = ia_decision(st.session_state.history)
level, level_desc = manipulation_level(st.session_state.history)
probs = probability_engine(st.session_state.history)

st.markdown("## 🎯 DECISÃO DA IA")
st.success(f"{decision}\n\nConfiança: {confidence}%\n\n{context}")

st.markdown("## 🧬 MAPA DE MANIPULAÇÃO")
st.info(f"Nível {level} — {level_desc}")

st.markdown("## 📊 PROBABILIDADES FINAIS")
st.write(f"🔴 Home: {probs['R']}%")
st.write(f"🔵 Away: {probs['B']}%")
st.write(f"🟡 Draw: {probs['D']}%")

st.markdown("## 🎰 Cassino vs 🧠 Jogador")
st.warning(f"🎰 Cassino: {casino_reading(st.session_state.history)}")
st.success(f"🧠 Jogador: {player_reading(st.session_state.history, level)}")
