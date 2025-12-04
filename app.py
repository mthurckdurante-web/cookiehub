# app.py - CookieHub Streamlit App
# Dependências: streamlit, pandas, matplotlib, pillow

import streamlit as st
import sqlite3
import os
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
import uuid

# ------------------ CONFIG ------------------
st.set_page_config(page_title="CookieHub", page_icon="🍪", layout="wide")
DB_PATH = "cookiehub.db"
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ------------------ CSS ------------------
CUSTOM_CSS = """
<style>
body { background: linear-gradient(180deg,#fff5f5 0%, #fff1f0 100%); }
.header { text-align: center; padding: 10px 0 0 0; }
.title { font-size: 40px; color: #b22222; font-weight: 800; letter-spacing: 1px; animation: popIn 0.9s ease-in-out; }
.subtitle { font-size: 16px; color: #6b0b0b; }
.card { background: #fff; border-radius: 12px; padding: 16px; box-shadow: 0 6px 18px rgba(171, 66, 66, 0.08); }
.recipe-img { border-radius: 12px; }
@keyframes popIn { from { transform: translateY(-10px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
.fade-in { animation: fade 1.2s ease-in; }
@keyframes fade { from {opacity:0} to{opacity:1} }
.small { font-size: 12px; color: #4b2a2a }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ------------------ DATABASE ------------------
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

# ------------------ HELPERS ------------------
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
    return pd.read_sql_query("SELECT * FROM receitas", conn)

def get_sales_df():
    return pd.read_sql_query("""
SELECT v.id, v.receita_id, r.nome as receita, v.quantidade, v.preco_unitario, v.total, v.data 
FROM vendas v LEFT JOIN receitas r ON v.receita_id = r.id 
ORDER BY v.data DESC
""", conn)

# ------------------ CRUD ------------------
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
    cur.execute("SELECT imagem_path FROM receitas WHERE id=?", (id_,))
    row = cur.fetchone()
    if row and row[0] and os.path.exists(row[0]):
        os.remove(row[0])
    cur.execute("DELETE FROM receitas WHERE id=?", (id_,))
    conn.commit()

def add_sale(receita_id, quantidade, preco_unitario, data):
    total = quantidade * preco_unitario
    cur.execute("INSERT INTO vendas (receita_id, quantidade, preco_unitario, data, total) VALUES (?, ?, ?, ?, ?)",
                (receita_id, quantidade, preco_unitario, data, total))
    conn.commit()

# ------------------ SIDEBAR ------------------
st.sidebar.image("fotos/cookie.jfif", width=140)
st.sidebar.markdown("---")
page = st.sidebar.selectbox("Navegação", ["Home", "Receitas", "Nova Receita", "Registrar Venda", "Relatórios / Consultas", "Exportar / Backup"]) 

# ------------------ HOME ------------------
if page == "Home":
    st.markdown("<div class='header'><div class='title'>🍪 CookieHub</div><div class='subtitle'>Gerencie receitas, vendas e relatórios</div></div>", unsafe_allow_html=True)
    st.image(
    "data:image/jpeg;base64,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",   # coloque aqui sua URL
    use_column_width=True
)
    col1, col2 = st.columns([2,1])
    with col1:
        st.markdown("<div class='card fade-in'> <h3>O que você pode fazer</h3><ul><li>Cadastrar receitas</li><li>Registrar vendas</li><li>Editar/excluir receitas</li><li>Visualizar relatórios</li></ul></div>", unsafe_allow_html=True)
    with col2:
        df_rec = get_recipes_df()
        df_sales = get_sales_df()
        st.markdown(f"<div class='card'><h4>Estatísticas rápidas</h4>Receitas: {len(df_rec)}<br>Vendas: {len(df_sales)}</div>", unsafe_allow_html=True)

# ------------------ RECEITAS ------------------
elif page == "Receitas":
    st.header("🍪 Receitas Cadastradas")

    # JANELA DE CONFIRMAÇÃO DE EXCLUSÃO (se houver algo pendente)
    if 'delete_id' in st.session_state:
        st.warning(
            f"Tem certeza que deseja excluir a receita *{st.session_state['delete_nome']}*?"
        )
        colc1, colc2 = st.columns(2)

        with colc1:
            if st.button("✅ Sim, excluir"):
                delete_recipe(st.session_state['delete_id'])
                del st.session_state['delete_id']
                del st.session_state['delete_nome']
                st.success("Receita excluída com sucesso!")
                st.rerun()

        with colc2:
            if st.button("❌ Cancelar"):
                del st.session_state['delete_id']
                del st.session_state['delete_nome']
                st.info("Exclusão cancelada.")
                st.rerun()

    # CARREGAR RECEITAS DO BANCO
    df = get_recipes_df()

    if df.empty:
        st.info("Nenhuma receita cadastrada ainda. Vá em 'Nova Receita' para adicionar.")
    else:
        for _, row in df.sort_values('id', ascending=False).iterrows():
            cols = st.columns([1, 2, 1])

            # Coluna da imagem
            with cols[0]:
                if row['imagem_path'] and os.path.exists(row['imagem_path']):
                    st.image(row['imagem_path'], use_column_width=True, caption=row['nome'])
                else:
                    # imagem padrão se não houver
                    st.image("https://mojo.generalmills.com/api/public/content/_pLFRXFETcuXWg_Z0MhZPw_webp_base.webp?v=1c273e93&t=191ddcab8d1c415fa10fa00a14351227", use_column_width=True)

            # Coluna do texto
            with cols[1]:
                st.markdown(
                    f"<div class='card'><h3>{row['nome']}  "
                    f"<span class='small'>R$ {row['preco']:.2f}</span></h3>",
                    unsafe_allow_html=True
                )
                st.markdown(
                    f"<p><strong>Ingredientes:</strong><br>{row['ingredientes']}</p>",
                    unsafe_allow_html=True
                )
                st.markdown(
                    f"<p><strong>Modo de preparo:</strong><br>{row['preparo']}</p></div>",
                    unsafe_allow_html=True
                )

            # Coluna dos botões
            with cols[2]:
                if st.button(f"Editar ✏️", key=f"edit_{row['id']}"):
                    st.session_state['edit_id'] = int(row['id'])
                    st.rerun()

                if st.button(f"Excluir 🗑️", key=f"del_{row['id']}"):
                    st.session_state['delete_id'] = int(row['id'])
                    st.session_state['delete_nome'] = row['nome']
                    st.rerun()
# ------------------ NOVA RECEITA ------------------
elif page == "Nova Receita":
    st.header("➕ Adicionar / Editar Receita")
    edit_mode = False
    edit_id = st.session_state.get('edit_id', None)
    edit_row = None
    if edit_id:
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
            path = save_image(imagem) if imagem else (edit_row[4] if edit_mode else None)
            if not nome.strip():
                st.error("Nome obrigatório")
            else:
                if edit_mode:
                    update_recipe(edit_id, nome, ingredientes, preparo, path, preco)
                    st.success("Receita atualizada com sucesso!")
                    del st.session_state['edit_id']
                else:
                    add_recipe(nome, ingredientes, preparo, path, preco)
                    st.success("Receita adicionada com sucesso!")
                st.rerun()

# ------------------ REGISTRAR VENDA ------------------
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
            receita_id = receita_map[escolha]
            preco_default = float(cur.execute("SELECT preco FROM receitas WHERE id=?", (receita_id,)).fetchone()[0] or 0)
            preco_unitario = st.number_input("Preço unitário (R$)", min_value=0.0, value=preco_default, step=0.5)
            data_venda = st.date_input("Data da venda", value=datetime.today())
            submitted = st.form_submit_button("Registrar Venda")
            if submitted:
                add_sale(receita_id, int(quantidade), float(preco_unitario), str(data_venda))
                st.success("Venda registrada com sucesso!")
                st.rerun()

# ------------------ RELATÓRIOS ------------------
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
            if st.button("Exportar receitas como CSV"):
                csv = rec_df.to_csv(index=False).encode('utf-8')
                st.download_button("Clique para baixar CSV", data=csv, file_name='receitas.csv', mime='text/csv')

# ------------------ EXPORTAR / BACKUP ------------------
elif page == "Exportar / Backup":
    st.header("💾 Exportar / Backup")
    if st.button("Baixar arquivo SQLite (.db)"):
        with open(DB_PATH, 'rb') as f:
            data = f.read()
        st.download_button("Download do DB", data=data, file_name='cookiehub.db', mime='application/octet-stream')
    st.markdown("---")
    if st.button("Resetar aplicação (apagar receitas e vendas)"):
        if st.confirm("Tem certeza? Esta ação apagará todas as receitas e vendas e removerá imagens salvas."):
            df = get_recipes_df()
            for p in df['imagem_path'].dropna().tolist():
                if p and os.path.exists(p):
                    os.remove(p)
            cur.execute("DELETE FROM vendas")
            cur.execute("DELETE FROM receitas")
            conn.commit()
            st.success("Aplicação resetada. Recarregue a página.")
            st.rerun()

# ------------------ FOOTER ------------------
st.markdown("<div class='small' style='text-align:center;margin-top:30px'>Feito com ❤️ por você</div>", unsafe_allow_html=True)













