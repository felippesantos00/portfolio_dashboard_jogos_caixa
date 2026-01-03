import streamlit as st
import pandas as pd
import requests
from io import BytesIO

st.set_page_config(
    page_title="Dashboard Mega-Sena",
    layout="wide"
)

st.title("📊 Evolução dos Prêmios Acumulados – Mega-Sena")

# =====================================
# DOWNLOAD + CACHE DO HISTÓRICO
# =====================================


@st.cache_data(ttl=86400)  # 1 dia
def fetch_megasena_historico():
    url = (
        "https://servicebus2.caixa.gov.br/"
        "portaldeloterias/api/resultados/download?modalidade=Mega-Sena"
    )
    response = requests.get(url, timeout=20)
    response.raise_for_status()
    df = pd.read_excel(BytesIO(response.content))
    return df


df = fetch_megasena_historico()

# =====================================
# LIMPEZA DE DADOS
# =====================================
df = df.rename(columns=lambda x: x.strip())

df["Data do Sorteio"] = pd.to_datetime(
    df["Data do Sorteio"], dayfirst=True, errors="coerce"
)


def moeda_para_float(valor):
    if isinstance(valor, str):
        return (
            valor.replace("R$", "")
            .replace(".", "")
            .replace(",", ".")
            .strip()
        )
    return valor


df["Estimativa prêmio"] = df["Estimativa prêmio"].apply(
    moeda_para_float).astype(float)
df["Acumulado 6 acertos"] = df["Acumulado 6 acertos"].apply(
    moeda_para_float).astype(float)

df = df.sort_values("Concurso")

# =====================================
# FILTROS
# =====================================
st.sidebar.header("🔎 Filtros")

min_concurso, max_concurso = int(
    df["Concurso"].min()), int(df["Concurso"].max())

concurso_range = st.sidebar.slider(
    "Intervalo de concursos",
    min_value=min_concurso,
    max_value=max_concurso,
    value=(min_concurso, max_concurso)
)

df_filtrado = df[
    (df["Concurso"] >= concurso_range[0]) &
    (df["Concurso"] <= concurso_range[1])
]

# =====================================
# MÉTRICAS
# =====================================
st.subheader("📌 Visão Geral")

col1, col2, col3 = st.columns(3)

col1.metric(
    "🏆 Maior prêmio estimado",
    f"R$ {df_filtrado['Estimativa prêmio'].max():,.2f}".replace(
        ",", "X").replace(".", ",").replace("X", ".")
)

col2.metric(
    "📈 Prêmio médio",
    f"R$ {df_filtrado['Estimativa prêmio'].mean():,.2f}".replace(
        ",", "X").replace(".", ",").replace("X", ".")
)

col3.metric(
    "🔁 Concursos acumulados",
    int((df_filtrado["Acumulado 6 acertos"] > 0).sum())
)

st.divider()

# =====================================
# GRÁFICO
# =====================================
st.subheader("📉 Evolução do prêmio estimado ao longo do tempo")

st.line_chart(
    df_filtrado.set_index("Concurso")["Estimativa prêmio"],
    height=450
)

# =====================================
# TABELA
# =====================================
st.subheader("📋 Histórico resumido")

df_view = df_filtrado[[
    "Concurso",
    "Data do Sorteio",
    "Estimativa prêmio",
    "Acumulado 6 acertos"
]].copy()

df_view["Estimativa prêmio"] = df_view["Estimativa prêmio"].apply(
    lambda x: f"R$ {x:,.2f}".replace(
        ",", "X").replace(".", ",").replace("X", ".")
)

df_view["Acumulado 6 acertos"] = df_view["Acumulado 6 acertos"].apply(
    lambda x: f"R$ {x:,.2f}".replace(
        ",", "X").replace(".", ",").replace("X", ".")
)

st.dataframe(df_view, use_container_width=True)
st.markdown("---")
st.markdown(
    """
    # 🙋 Sobre o Autor
    ## 📫 Contato

    - Email: felipperodrigues00@gmail.com
    - LinkedIn: https://www.linkedin.com/in/felippe-santos-54058111a/
    - Medium: https://medium.com/@felipperodrigues00
    """
)
