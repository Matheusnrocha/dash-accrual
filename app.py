import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import plotly.graph_objects as go

hoje = datetime.today().strftime("%d_%m_%y")

hoje_frontend = datetime.today().strftime("%d/%m/%y")


data_atual = pd.to_datetime(datetime.now().date())

sistema = ["GAR-PRESTADA", "IMP-CREDOC"]
encargo = ["COMISSAOP"]

tabela = pd.read_excel("data/ACCRUAL AG033 NOVO TRADE.xlsx")

tabela = tabela[tabela["Sistema"].isin(sistema)]
tabela = tabela[tabela["Encargo"].isin(encargo)]
tabela = tabela[tabela["Dt,Fim"].dt.year.isin([2022, 2023, 2024])]


tabela["Vl,Apropriado-MN"] = tabela["Vl,Apropriado-MN"] * -1


colunas_desejadas = ["Sistema", "Encargo", "Numero", "Operacao", "Boleto",
                      "Titular", "Moeda", "Valor-Base", "Vl,Apropriado-MN", "Dt,Inicio",
                     "Dt,Fim", "Dias-Total", "Taxa-Encargo", "Justificativa", "GNI", "Segmento"]


tabela = tabela[colunas_desejadas]

tabela["Dt,Fim"] = pd.to_datetime(tabela["Dt,Fim"])


atrasados = tabela["Dt,Fim"] < data_atual

df_atrasados = tabela[atrasados]

em_dia = tabela["Dt,Fim"] == data_atual

df_em_dia = tabela[em_dia]


bdd = pd.read_excel("data/bdd.xlsx")

bdd = bdd[bdd["Sistema"].isin(sistema)]
bdd = bdd[bdd["Encargo"].isin(encargo)]
bdd = bdd[bdd["Dt,Fim"].dt.year.isin([2022, 2023])]

bdd["Vl,Apropriado-MN"] = bdd["Vl,Apropriado-MN"] * -1

colunas_desejadas_bdd = ["Sistema", "Encargo","Titular", 
                         "Valor-Base", "Vl,Apropriado-MN",
                         "Dt,Inicio","Dt,Fim", "Data-base"]

bdd = bdd[colunas_desejadas_bdd]

bdd["Dt,Fim"] = pd.to_datetime(bdd["Dt,Fim"])
bdd["Data-base"] = pd.to_datetime(bdd["Data-base"])


# bdd_atrasados = bdd["Dt,Fim"] < data_atual

# bdd_atrasados = bdd[bdd_atrasados]

# bdd.to_excel("data/bdds.xlsx", index=False)

# bdd_atrasados.to_excel("data/bddatra.xlsx", index=False)


## ------------------------------------------------------------- INICIO DO APP ---------------------------------------------------------------------------------------


st.sidebar.header("Controle de Accrual")
st.sidebar.subheader("Manutenção Off Shore")

menu = st.sidebar.selectbox("Menu",["Analytics", "Vencidos", "Em dia"])


if menu == "Analytics":
    
    st.header("Analytics - Manutenção de Accrual")
    
    menuAnalytics = st.sidebar.selectbox("Casos",["DashBoard", "Cálculo de Valores"])
    
    if "DashBoard" in menuAnalytics:
        
        df_soma_por_cliente = df_atrasados.groupby("Titular")["Vl,Apropriado-MN"].sum().reset_index()
        df_soma_por_cliente = df_soma_por_cliente.sort_values(by="Vl,Apropriado-MN", ascending=False)
        
        top_5_titulares = df_soma_por_cliente.head(5)
        
        total_valor = df_soma_por_cliente["Vl,Apropriado-MN"].sum()
        top_5_titulares["Porcentagem"] = (top_5_titulares["Vl,Apropriado-MN"] / total_valor * 100)
        
        
        top_5_titulares=top_5_titulares[::-1]
        
        fig_pie = px.pie(top_5_titulares, values="Vl,Apropriado-MN", names="Titular", 
                         title = "Porcentagem de Valor Devido por Cliente em Relação ao Total")
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=top_5_titulares["Titular"], 
            x=top_5_titulares["Vl,Apropriado-MN"], 
            orientation="h",
            text=top_5_titulares["Vl,Apropriado-MN"].apply(lambda x: f'RS{abs(x):,.2f}'),
            textposition='outside',
            name="Valor Devido"
        ))
        fig.update_layout(
            title="Top 5 clientes com Maior Valor Devido",
            yaxis_title="Titular",
            xaxis_title = "Valor devido",
            width=500,
            height=500
        )
        
        bdd_agrupado = bdd.groupby('Data-base')['Vl,Apropriado-MN'].sum().reset_index()
        
        fig_linha = px.line(bdd_agrupado, x='Data-base', y='Vl,Apropriado-MN', title="Evolução de Valores Devidos")
        fig_linha.update_layout(
            xaxis_title="Data-base",
            yaxis_title="Soma dos valores"
        )
        
        
        col1, col2 = st.columns(2)
        col3, col4, col5 = st.columns(3)
    
        col1.plotly_chart(fig, use_container_width=True)
        col2.plotly_chart(fig_pie, use_container_width=True)
        col5.plotly_chart(fig_linha, use_container_width=True)       
        
        sistemas = df_atrasados["Sistema"].unique()
        
        for sistema in sistemas:
            valor_sistema=df_atrasados[df_atrasados["Sistema"] == sistema]["Vl,Apropriado-MN"].sum()
            quantidade = df_atrasados[df_atrasados["Sistema"] == sistema].shape[0]
            col3.info(f"**{sistema}**\n\nValor Devido Atrasado: R${abs(valor_sistema): ,.2f}\n\nQuantidade de casos Atrasados: {quantidade}")
        
    else:
        st.subheader("Cálculo de Valores em relação a Pagamento de Clientes")
        
        cliente_escolhido = st.selectbox("Escolha o cliente", df_atrasados["Titular"].unique())
        
        saldo_devedor_total = df_atrasados["Vl,Apropriado-MN"].sum()
        
        saldo_devedor_cliente = df_atrasados[df_atrasados["Titular"] == cliente_escolhido]["Vl,Apropriado-MN"].sum()
        
        novo_saldo_devedor = saldo_devedor_total - saldo_devedor_cliente
        
        st.markdown(f"O Saldo atual de valores Devidos é: **R${abs(saldo_devedor_total):,.2f}**\n\n Enquanto o saldo da empresa {cliente_escolhido} é de **R${abs(saldo_devedor_cliente):,.2f}**\n\nPortanto, se o cliente **{cliente_escolhido}** pagasse o valor que ele nos deve, nosso saldo devedor cairia para **R${abs(novo_saldo_devedor):,.2f}**.") 


elif menu == "Vencidos":
    
    st.header("Casos Vencidos")
    
    produto = st.sidebar.multiselect("Produto", ["Selecionar Todos"] + list(df_atrasados["Sistema"].unique()))
    
    if "Selecionar Todos" in produto:
        produto = list(df_atrasados["Sistema"].unique())
    
    nomes_disponiveis = df_atrasados[df_atrasados["Sistema"].isin(produto)]["Titular"].unique()
    
    cliente = st.sidebar.multiselect("Cliente", ["Selecionar Todos"] + list(nomes_disponiveis if nomes_disponiveis.any() else df_atrasados["Titular"].unique()))
    
    if "Selecionar Todos" in cliente:
        cliente = list(df_atrasados["Titular"].unique())
    
    if st.sidebar.button("Filtrar"): 
        df_atrasados_filtrado = df_atrasados[df_atrasados["Sistema"].isin(produto) & df_atrasados["Titular"].isin(cliente)]
        st.success(f"Filtro {produto} aplicado")
    else:
        df_atrasados_filtrado = df_atrasados
        
    st.dataframe(df_atrasados_filtrado, height=800)
    
    if st.button("Exportar"):
        
        nome_arquivo=f"Vencidos_{hoje}"
        
        if produto:
            
            nome_arquivo += f"_{'+'.join(produto)}"
        
        nome_arquivo += ".xlsx"
        df_atrasados_filtrado.to_excel(nome_arquivo, index=False, engine="openpyxl")
        st.success(f"Tabela Exportada com sucesso")
    
    
else:
    
    st.header(f"Casos do dia - {hoje_frontend} ")
    
    produto_em_dia = st.sidebar.multiselect("Produto", ["Selecionar Todos"] + list(df_em_dia["Sistema"].unique()))
    
    if "Selecionar Todos" in produto_em_dia:
        produto_em_dia = list(df_em_dia["Sistema"].unique())
    
    nomes_disponiveis_em_dia = df_em_dia[df_em_dia["Sistema"].isin(produto_em_dia)]["Titular"].unique()
    
    
    cliente_em_dia = st.sidebar.multiselect("Cliente", ["Selecionar Todos"] + list(nomes_disponiveis_em_dia if nomes_disponiveis_em_dia.any() else df_em_dia["Titular"].unique()))
    
    if "Selecionar Todos" in cliente_em_dia:
        cliente_em_dia = list(df_em_dia["Titular"].unique())
    
    if st.sidebar.button("Filtrar"): 
        df_em_dia_filtrado = df_em_dia[df_em_dia["Sistema"].isin(produto_em_dia) & df_em_dia["Titular"].isin(cliente_em_dia)]
        st.success(f"Filtro {produto_em_dia} aplicado")
    else:
        df_em_dia_filtrado = df_em_dia
        
    st.dataframe(df_em_dia, height=800)
    
    if st.button("Exportar"):
        
        nome_arquivo_em_dia=f"Em_dia_{hoje}"
        
        if produto_em_dia:
            
            nome_arquivo_em_dia += f"_{'+'.join(produto_em_dia)}"
        
        nome_arquivo_em_dia += ".xlsx"
        df_em_dia_filtrado.to_excel(nome_arquivo_em_dia, index=False, engine="openpyxl")
        st.success(f"Tabela Exportada com sucesso")
    
    
    
    
    
    
  