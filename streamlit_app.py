import streamlit as st
import requests
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="🎲 Jogos Caixa – Mega-Sena", layout="centered")

# =====================================================
# API RESULTADO ATUAL
# =====================================================


@st.cache_data(ttl=600)
def fetch_megasena_results():
    url = "https://servicebus2.caixa.gov.br/portaldeloterias/api/megasena"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()


# =====================================================
# HISTÓRICO XLSX
# =====================================================
@st.cache_data(ttl=3600)
def fetch_megasena_historico():
    url = (
        "https://servicebus2.caixa.gov.br/"
        "portaldeloterias/api/resultados/download?modalidade=Mega-Sena"
    )
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    df = pd.read_excel(BytesIO(response.content), engine="openpyxl")

    df.columns = df.columns.str.strip()
    return df


# =====================================================
# ESTADO
# =====================================================
if "jogos" not in st.session_state:
    st.session_state.jogos = []


# =====================================================
# RESULTADO OFICIAL
# =====================================================
dados = fetch_megasena_results()

st.title("🎲 Jogos da Caixa – Mega-Sena")

if dados:
    dezenas_sorteadas = set(int(n) for n in dados["listaDezenas"])

    st.subheader(f"📢 Concurso {dados['numero']} – {dados['dataApuracao']}")
    st.markdown(
        "🎯 **Números sorteados:** "
        + " - ".join(f"**{n}**" for n in dados["listaDezenas"])
    )

    st.caption(
        f"💰 Estimativa próximo concurso: "
        f"R$ {dados['valorEstimadoProximoConcurso']:,.2f}"
        .replace(",", "X").replace(".", ",").replace("X", ".")
    )

st.divider()

# =====================================================
# INPUT DO JOGO
# =====================================================
st.subheader("✍️ Digite seu jogo")

cols = st.columns(6)
numeros = []

for i in range(6):
    with cols[i]:
        valor = st.text_input(
            f"N{i+1}",
            max_chars=2,
            key=f"num_{i}",
            placeholder="00"
        )
        numeros.append(int(valor) if valor.isdigit() else 0)

if st.button("Adicionar jogo"):
    if 0 in numeros:
        st.error("❌ Preencha todos os números.")
    elif any(n < 1 or n > 60 for n in numeros):
        st.error("❌ Números devem estar entre 1 e 60.")
    elif len(set(numeros)) < 6:
        st.error("❌ Não pode repetir números.")
    else:
        jogo = "-".join(f"{n:02d}" for n in sorted(numeros))
        st.session_state.jogos.append(jogo)
        st.success(f"🎟️ Jogo adicionado: {jogo}")

# =====================================================
# FUNÇÕES AUXILIARES
# =====================================================


def jogo_para_set(jogo):
    return set(int(n) for n in jogo.split("-"))


# =====================================================
# LISTA DE JOGOS + ACERTOS
# =====================================================
st.divider()
st.subheader("📋 Jogos cadastrados")

if not st.session_state.jogos:
    st.info("Nenhum jogo cadastrado.")
else:
    for i, jogo in enumerate(st.session_state.jogos, start=1):
        jogo_set = jogo_para_set(jogo)
        acertos = len(jogo_set & dezenas_sorteadas)

        if acertos == 6:
            st.markdown(
                f"**{i}. 🟢 {jogo} — {acertos} acertos 🎉**"
            )
        else:
            st.write(f"{i}. {jogo} — {acertos} acertos")


# =====================================================
# HISTÓRICO (ÚLTIMOS 20)
# =====================================================
st.divider()
st.subheader("📚 Últimos concursos")

df_hist = fetch_megasena_historico()

cols_dezenas = ["Bola1", "Bola2", "Bola3", "Bola4", "Bola5", "Bola6"]

df_view = df_hist[
    ["Concurso", "Data do Sorteio"] + cols_dezenas
].tail(20).iloc[::-1]


def highlight_row(row):
    bolas = set(int(row[c]) for c in cols_dezenas)
    if bolas == dezenas_sorteadas:
        return ["background-color: #2ecc71"] * len(row)
    return [""] * len(row)


st.dataframe(
    df_view.style.apply(highlight_row, axis=1),
    width='stretch'
)
