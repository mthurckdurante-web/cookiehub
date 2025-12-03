import subprocess
import sys

subprocess.check_call([sys.executable, "-m", "pip", "install", "matplotlib"])
import matplotlib.pyplot as plt





"""
CookieHub - Aplicação Streamlit completa (arquivo único)
Salve como: app.py
Rode: streamlit run app.py

Dependências:
- streamlit
- pandas
- matplotlib
- pillow

Instale com: pip install streamlit pandas matplotlib pillow

Descrição:
- App com navegação via sidebar
- CRUD para receitas (com upload de imagem)
- Registro de vendas
- Edição e exclusão
- Banco de dados SQLite (arquivo cookiehub.db)
- Estilos CSS e animações
- Relatórios e gráficos

Observação: imagens são salvas na pasta ./uploads e o caminho salvo no DB.
"""

import streamlit as st
import sqlite3
import os
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
import io
import uuid

# ---------------------- CONFIG ----------------------
st.set_page_config(page_title="CookieHub", page_icon="🍪", layout="wide")
DB_PATH = "cookiehub.db"
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ---------------------- CSS / STYLES ----------------------
CUSTOM_CSS = """
<style>
body { background: linear-gradient(180deg,#fff5f5 0%, #fff1f0 100%); }
.header {
  text-align: center;
  padding: 10px 0 0 0;
}
.title {
  font-size: 40px;
  color: #b22222;
  font-weight: 800;
  letter-spacing: 1px;
  animation: popIn 0.9s ease-in-out;
}
.subtitle {
  font-size: 16px;
  color: #6b0b0b;
}
.card {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 6px 18px rgba(171, 66, 66, 0.08);
}
.recipe-img { border-radius: 12px; }
@keyframes popIn {
  from { transform: translateY(-10px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}
.fade-in { animation: fade 1.2s ease-in; }
@keyframes fade { from {opacity:0} to{opacity:1} }
.small { font-size: 12px; color: #4b2a2a }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ---------------------- DATABASE ----------------------
def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    return conn

conn = get_connection()
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS receitas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    ingredientes TEXT,
    preparo TEXT,
    imagem_path TEXT,
    preco REAL DEFAULT 0
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS vendas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    receita_id INTEGER,
    quantidade INTEGER,
    preco_unitario REAL,
    data TEXT,
    total REAL,
    FOREIGN KEY(receita_id) REFERENCES receitas(id)
)
""")
conn.commit()

# ---------------------- HELPERS ----------------------

def save_image(uploaded_file):
    if uploaded_file is None:
        return None
    try:
        ext = os.path.splitext(uploaded_file.name)[1]
        filename = f"{uuid.uuid4().hex}{ext}"
        path = os.path.join(UPLOAD_DIR, filename)
        with open(path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return path
    except Exception as e:
        st.error("Erro ao salvar imagem: " + str(e))
        return None


def get_recipes_df():
    df = pd.read_sql_query("SELECT * FROM receitas", conn)
    return df


def get_sales_df():
    df = pd.read_sql_query("SELECT v.id, v.receita_id, r.nome as receita, v.quantidade, v.preco_unitario, v.total, v.data FROM vendas v LEFT JOIN receitas r ON v.receita_id = r.id ORDER BY v.data DESC", conn)
    return df

# ---------------------- FUNÇÕES CRUD ----------------------

def add_recipe(nome, ingredientes, preparo, imagem_path, preco):
    cur.execute("INSERT INTO receitas (nome, ingredientes, preparo, imagem_path, preco) VALUES (?, ?, ?, ?, ?)",
                (nome, ingredientes, preparo, imagem_path, preco))
    conn.commit()


def update_recipe(id_, nome, ingredientes, preparo, imagem_path, preco):
    if imagem_path:
        cur.execute("UPDATE receitas SET nome=?, ingredientes=?, preparo=?, imagem_path=?, preco=? WHERE id=?",
                    (nome, ingredientes, preparo, imagem_path, preco, id_))
    else:
        cur.execute("UPDATE receitas SET nome=?, ingredientes=?, preparo=?, preco=? WHERE id=?",
                    (nome, ingredientes, preparo, preco, id_))
    conn.commit()


def delete_recipe(id_):
    # apagar imagem física
    cur.execute("SELECT imagem_path FROM receitas WHERE id=?", (id_,))
    row = cur.fetchone()
    if row and row[0]:
        try:
            if os.path.exists(row[0]):
                os.remove(row[0])
        except Exception:
            pass
    cur.execute("DELETE FROM receitas WHERE id=?", (id_,))
    conn.commit()


def add_sale(receita_id, quantidade, preco_unitario, data):
    total = quantidade * preco_unitario
    cur.execute("INSERT INTO vendas (receita_id, quantidade, preco_unitario, data, total) VALUES (?, ?, ?, ?, ?)",
                (receita_id, quantidade, preco_unitario, data, total))
    conn.commit()

# ---------------------- UI: SIDEBAR NAV ----------------------
st.sidebar.image("https://i.imgur.com/zk2JQ.png", width=140)
st.sidebar.markdown("---")
page = st.sidebar.selectbox("Navegação", ["Home", "Receitas", "Nova Receita", "Registrar Venda", "Relatórios / Consultas", "Exportar / Backup"]) 

# ---------------------- HOME ----------------------
if page == "Home":
    st.markdown("<div class='header'><div class='title'>🍪 CookieHub</div><div class='subtitle'>Gerencie receitas, vendas e relatórios de forma simples e bonita</div></div>", unsafe_allow_html=True)
    col1, col2 = st.columns([2,1])
    with col1:
        st.markdown("<div class='card fade-in'> <h3>O que você pode fazer</h3> <ul><li>Cadastrar receitas com imagem e preço</li><li>Registrar vendas e calcular totais</li><li>Editar e excluir receitas</li><li>Visualizar relatórios e gráficos</li></ul></div>", unsafe_allow_html=True)
        st.markdown("<div class='card small'><strong>Dica:</strong> use imagens em boa resolução (até ~5MB) para melhor visualização.</div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='card'><h4>Estatísticas rápidas</h4>", unsafe_allow_html=True)
        try:
            df_rec = get_recipes_df()
            df_sales = get_sales_df()
            st.write(f"Receitas cadastradas: {len(df_rec)}")
            st.write(f"Vendas registradas: {len(df_sales)}")
        except Exception:
            st.write("Carregando...")
        st.markdown("</div>", unsafe_allow_html=True)

# ---------------------- RECEITAS (LIST / EDIT / DELETE) ----------------------
elif page == "Receitas":
    st.header("🍪 Receitas Cadastradas")
    df = get_recipes_df()
    if df.empty:
        st.info("Nenhuma receita cadastrada ainda. Vá em 'Nova Receita' para adicionar uma.")
    else:
        for _, row in df.sort_values('id', ascending=False).iterrows():
            with st.container():
                cols = st.columns([1,2,1])
                with cols[0]:
                    if row['imagem_path'] and os.path.exists(row['imagem_path']):
                        try:
                            st.image(row['imagem_path'], use_column_width=True, caption=row['nome'])
                        except Exception:
                            st.write("Imagem inválida")
                    else:
                        st.image("https://via.placeholder.com/300x200.png?text=Sem+imagem", use_column_width=True)
                with cols[1]:
                    st.markdown(f"<div class='card'><h3>{row['nome']}  <span class='small'>R$ {row['preco']:.2f}</span></h3>", unsafe_allow_html=True)
                    st.markdown(f"<p><strong>Ingredientes:</strong><br>{row['ingredientes']}</p>", unsafe_allow_html=True)
                    st.markdown(f"<p><strong>Modo de preparo:</strong><br>{row['preparo']}</p></div>", unsafe_allow_html=True)
                with cols[2]:
                    if st.button(f"Editar ✏️", key=f"edit_{row['id']}"):
                        st.session_state['edit_id'] = int(row['id'])
                        st.experimental_rerun()
                    if st.button(f"Excluir 🗑️", key=f"del_{row['id']}"):
                        if st.confirm(f"Tem certeza que quer excluir a receita '{row['nome']}'? Esta ação é irreversível."):
                            delete_recipe(row['id'])
                            st.success("Receita excluída")
                            st.experimental_rerun()

# ---------------------- NOVA RECEITA / EDIT ----------------------
elif page == "Nova Receita":
    st.header("➕ Adicionar / Editar Receita")
    edit_mode = False
    edit_id = st.session_state.get('edit_id', None)

    if edit_id:
        # carregar dados
        edit_row = cur.execute("SELECT id, nome, ingredientes, preparo, imagem_path, preco FROM receitas WHERE id=?", (edit_id,)).fetchone()
        if edit_row:
            edit_mode = True
            st.info(f"Editando receita: {edit_row[1]}")

    with st.form("recipe_form", clear_on_submit=False):
        nome = st.text_input("Nome", value=edit_row[1] if edit_mode else "")
        preco = st.number_input("Preço unitário (R$)", min_value=0.0, value=float(edit_row[5]) if edit_mode else 0.0, step=0.5)
        ingredientes = st.text_area("Ingredientes (separe por vírgula)", value=edit_row[2] if edit_mode else "")
        preparo = st.text_area("Modo de preparo", value=edit_row[3] if edit_mode else "")
        imagem = st.file_uploader("Imagem da receita (png/jpg)", type=["png","jpg","jpeg"], key="img_up")
        submitted = st.form_submit_button("Salvar")

        if submitted:
            path = None
            if imagem is not None:
                path = save_image(imagem)
            elif edit_mode:
                # manter imagem anterior
                path = edit_row[4]

            if not nome.strip():
                st.error("Nome obrigatório")
            else:
                if edit_mode:
                    update_recipe(edit_id, nome, ingredientes, preparo, path, preco)
                    st.success("Receita atualizada com sucesso!")
                    # limpar estado
                    if 'edit_id' in st.session_state:
                        del st.session_state['edit_id']
                    st.experimental_rerun()
                else:
                    add_recipe(nome, ingredientes, preparo, path, preco)
                    st.success("Receita adicionada com sucesso!")
                    st.experimental_rerun()

# ---------------------- REGISTRAR VENDA ----------------------
elif page == "Registrar Venda":
    st.header("📦 Registrar Venda")
    df = get_recipes_df()
    if df.empty:
        st.info("Cadastre uma receita antes de registrar vendas.")
    else:
        with st.form("sale_form"):
            receita_map = {f"{r['id']} - {r['nome']}": r['id'] for _, r in df.iterrows()}
            escolha = st.selectbox("Escolha a receita", list(receita_map.keys()))
            quantidade = st.number_input("Quantidade", min_value=1, value=1)
            # obter preco default da receita
            receita_id = receita_map[escolha]
            preco_default = float(cur.execute("SELECT preco FROM receitas WHERE id=?", (receita_id,)).fetchone()[0] or 0)
            preco_unitario = st.number_input("Preço unitário (R$)", min_value=0.0, value=preco_default, step=0.5)
            data_venda = st.date_input("Data da venda", value=datetime.today())
            submitted = st.form_submit_button("Registrar Venda")
            if submitted:
                add_sale(receita_id, int(quantidade), float(preco_unitario), str(data_venda))
                st.success("Venda registrada com sucesso!")
                st.experimental_rerun()

# ---------------------- RELATÓRIOS / CONSULTAS ----------------------
elif page == "Relatórios / Consultas":
    st.header("📊 Relatórios e Consultas")
    tab1, tab2 = st.tabs(["Vendas", "Receitas"])
    with tab1:
        sales_df = get_sales_df()
        if sales_df.empty:
            st.info("Nenhuma venda registrada ainda.")
        else:
            st.subheader("Vendas recentes")
            st.dataframe(sales_df)

            # Gráfico: vendas por receita
            resumo = sales_df.groupby('receita').agg({'quantidade':'sum','total':'sum'}).reset_index()
            st.subheader("Resumo por receita")
            st.dataframe(resumo)

            fig, ax = plt.subplots(figsize=(8,4))
            ax.bar(resumo['receita'], resumo['total'])
            ax.set_title('Receita total por receita (R$)')
            ax.set_ylabel('Total (R$)')
            ax.set_xticklabels(resumo['receita'], rotation=45, ha='right')
            st.pyplot(fig)

    with tab2:
        rec_df = get_recipes_df()
        if rec_df.empty:
            st.info("Nenhuma receita cadastrada.")
        else:
            st.subheader("Receitas")
            st.dataframe(rec_df)
            # opção de exportar tabela
            if st.button("Exportar receitas como CSV"):
                csv = rec_df.to_csv(index=False).encode('utf-8')
                st.download_button("Clique para baixar CSV", data=csv, file_name='receitas.csv', mime='text/csv')

# ---------------------- EXPORT / BACKUP ----------------------
elif page == "Exportar / Backup":
    st.header("💾 Exportar / Backup")
    st.write("Faça backup do banco de dados ou exporte tabelas.")
    if st.button("Baixar arquivo SQLite (.db)"):
        with open(DB_PATH, 'rb') as f:
            data = f.read()
        st.download_button("Download do DB", data=data, file_name='cookiehub.db', mime='application/octet-stream')

    # exportar imagens zip não implementado para manter simplicidade
    st.markdown("---")
    st.write("Apagar todos os dados (reset)")
    if st.button("Resetar aplicação (apagar receitas e vendas)"):
        if st.confirm("Tem certeza? Esta ação apagará todas as receitas e vendas e removerá imagens salvas."):
            # apagar imagens
            df = get_recipes_df()
            for p in df['imagem_path'].dropna().tolist():
                try:
                    if p and os.path.exists(p):
                        os.remove(p)
                except Exception:
                    pass
            cur.execute("DELETE FROM vendas")
            cur.execute("DELETE FROM receitas")
            conn.commit()
            st.success("Aplicação resetada. Recarregue a página.")
            st.experimental_rerun()

# ---------------------- FOOTER ----------------------
st.markdown("<div class='small' style='text-align:center;margin-top:30px'>Feito com ❤️ por sua dupla — personalize o tema, imagens e funcionalidades.</div>", unsafe_allow_html=True)

