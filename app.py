import os
from pathlib import Path
import streamlit as st

from ingest import DATA_DIR, CHROMA_DIR, ingest_documents
from rag import answer, LLM_MODEL, EMBEDDING_MODEL

st.set_page_config(
    page_title="Asistente de Contratos",
    layout="centered",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
#MainMenu, footer {visibility: hidden;}
.block-container {padding-top: 2rem; max-width: 780px;}
div.stButton > button {border-radius: 10px; min-height: 3.2rem; text-align: left;}
</style>
""", unsafe_allow_html=True)


def sanitize_and_save_pdf(uploaded_file, target_dir: Path) -> tuple[bool, str]:
    """Guarda un PDF validando extensión, tamaño, cabecera y ruta."""
    MAX_FILE_SIZE = 15 * 1024 * 1024  # 15 MB

    safe_name = os.path.basename(uploaded_file.name)
    if not safe_name.lower().endswith(".pdf"):
        return False, f"'{safe_name}' no tiene extensión .pdf."

    content = uploaded_file.getvalue()
    if len(content) > MAX_FILE_SIZE:
        return False, f"'{safe_name}' supera el límite de 15 MB."

    if not content.startswith(b"%PDF-"):
        return False, f"'{safe_name}' no es un PDF válido."

    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = (target_dir / safe_name).resolve()
    if target_dir.resolve() not in target_path.parents:
        return False, "Ruta de archivo no permitida."

    with open(target_path, "wb") as f:
        f.write(content)

    return True, f"Guardado: {safe_name}"


EJEMPLOS = {
    "Periodo de prueba vs. norma": "¿El periodo de prueba de 3 meses de Ana Torres cumple con la normativa laboral de SUNAFIL y el D.S. 003-97-TR?",
    "Sueldo y gratificaciones": "¿Cuál es la remuneración de Ana Torres y cómo se pagan sus gratificaciones?",
    "Desconexión digital": "¿Qué establece la Ley N° 31572 sobre la desconexión digital y qué sanciones impone SUNAFIL?",
    "Prácticas vs. Ley 28518": "¿La subvención de Lucía Robles cumple con la Ley N° 28518 de Modalidades Formativas?",
}

if "messages" not in st.session_state:
    st.session_state.messages = []


def set_pending(q: str):
    st.session_state.pending = q


def render_sources(fuentes):
    if not fuentes:
        return
    unicas = sorted({(s["archivo"], s["pagina"]) for s in fuentes})
    with st.expander(f"Fuentes ({len(unicas)})"):
        for archivo, pagina in unicas:
            st.markdown(f"**{archivo}** · pág. {pagina}")


DATA_DIR.mkdir(parents=True, exist_ok=True)
pdf_list = sorted(DATA_DIR.glob("*.pdf"))

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.header("Documentos")
    files = st.file_uploader(
        "Sube contratos en PDF", type=["pdf"], accept_multiple_files=True
    )

    if st.button(
        "Guardar e indexar",
        type="primary",
        use_container_width=True,
        disabled=not files,
    ):
        with st.spinner("Procesando documentos..."):
            for f in files:
                ok, msg = sanitize_and_save_pdf(f, DATA_DIR)
                if not ok:
                    st.error(msg)
            try:
                stats = ingest_documents(data_dir=DATA_DIR, chroma_dir=CHROMA_DIR)
                st.toast(f"Listo: {stats.get('total_in_db', 0)} fragmentos indexados")
            except Exception as e:
                st.error(f"Error al indexar: {e}")

    st.caption(f"{len(pdf_list)} documento(s) cargado(s)")
    with st.expander("Ver documentos"):
        for p in pdf_list:
            st.caption(f"• {p.name}")

    st.divider()
    if st.button("Nueva conversación", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    with st.expander("Acerca de"):
        st.caption(
            f"100% local y privado\n\nLLM: {LLM_MODEL}\n\nEmbeddings: {EMBEDDING_MODEL}\n\nVector store: ChromaDB"
        )

# ---------------- ENTRADA ----------------
prompt = st.chat_input("Pregunta sobre tus contratos...")
if not prompt and "pending" in st.session_state:
    prompt = st.session_state.pop("pending")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})

# ---------------- PANTALLA INICIAL ----------------
if not st.session_state.messages:
    st.title("Asistente de Contratos")
    st.write(
        "Pregunta en español y recibe la respuesta con el documento y la página de donde sale."
    )
    if not pdf_list:
        st.info("Empieza subiendo tus contratos en la barra lateral.")
    else:
        st.markdown("**Prueba con una pregunta:**")
        cols = st.columns(2)
        for i, (label, q) in enumerate(EJEMPLOS.items()):
            cols[i % 2].button(
                label, on_click=set_pending, args=(q,), use_container_width=True
            )

# ---------------- HISTORIAL ----------------
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        render_sources(m.get("sources"))

# ---------------- RESPUESTA ----------------
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    with st.chat_message("assistant"):
        with st.spinner("Buscando en los contratos..."):
            try:
                texto, fuentes = answer(st.session_state.messages[-1]["content"])
            except Exception as err:
                texto, fuentes = f"Error al procesar la consulta: {err}", []
        st.markdown(texto)
        render_sources(fuentes)
    st.session_state.messages.append(
        {"role": "assistant", "content": texto, "sources": fuentes}
    )

if st.session_state.messages:
    st.caption("Herramienta de apoyo. No sustituye asesoría legal.")