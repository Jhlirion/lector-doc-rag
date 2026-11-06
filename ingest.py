"""
ingest.py
---------
Módulo de ingesta y procesamiento de documentos para el sistema RAG local.

Flujo de ejecución:
1. Lee todos los contratos en formato PDF del directorio ./data
2. Extrae el texto página por página utilizando PyMuPDF (fitz)
3. Divide el contenido en fragmentos (chunks) con RecursiveCharacterTextSplitter
   (chunk_size=800, chunk_overlap=100) y preserva metadatos (archivo, página)
4. Genera embeddings vectoriales locales mediante Ollama (modelo: bge-m3)
5. Almacena los vectores en ChromaDB persistente en ./chroma_db (colección 'contratos')
6. Implementa control de duplicados mediante identificadores deterministas (hash)
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import urllib.error
import urllib.request

# Verificación de dependencias clave
try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    RecursiveCharacterTextSplitter = None

try:
    import chromadb
except ImportError:
    chromadb = None

try:
    import ollama
except ImportError:
    ollama = None

# Configuración predeterminada
DATA_DIR = Path("./data")
CHROMA_DIR = Path("./chroma_db")
COLLECTION_NAME = "contratos"
EMBEDDING_MODEL = "bge-m3"
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

CHUNK_SIZE = 800
CHUNK_OVERLAP = 100


def get_ollama_embedding(text: str, model: str = EMBEDDING_MODEL, host: str = OLLAMA_HOST) -> list[float]:
    """
    Genera el vector de embedding para un fragmento de texto usando Ollama local.
    Intenta primero la librería oficial 'ollama' y, como respaldo, la API REST nativa HTTP.
    """
    # 1. Intentar con la biblioteca de Python 'ollama'
    if ollama is not None:
        try:
            client = ollama.Client(host=host)
            # Compatibilidad con API nueva (embed) y API clásica (embeddings)
            if hasattr(client, "embed"):
                res = client.embed(model=model, input=text)
                if "embeddings" in res and res["embeddings"]:
                    return res["embeddings"][0]
            res = client.embeddings(model=model, prompt=text)
            return res["embedding"]
        except Exception:
            pass  # Fallback a llamada HTTP directa

    # 2. Respaldo HTTP directo a la API local de Ollama (sin dependencias adicionales)
    url_embed = f"{host.rstrip('/')}/api/embed"
    payload_embed = json.dumps({"model": model, "input": text}).encode("utf-8")
    req_embed = urllib.request.Request(
        url_embed,
        data=payload_embed,
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req_embed, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
            if "embeddings" in data and data["embeddings"]:
                return data["embeddings"][0]
    except Exception:
        # Reintentar con el endpoint clásico /api/embeddings
        url_embeddings = f"{host.rstrip('/')}/api/embeddings"
        payload_embeddings = json.dumps({"model": model, "prompt": text}).encode("utf-8")
        req_embeddings = urllib.request.Request(
            url_embeddings,
            data=payload_embeddings,
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req_embeddings, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))
                return data["embedding"]
        except urllib.error.URLError as err:
            raise ConnectionError(
                f"No se pudo conectar con Ollama en {host}. "
                f"Verifica que el servicio esté activo ('ollama serve') y el modelo '{model}' descargado "
                f"('ollama pull {model}'). Detalle: {err}"
            ) from err


def extract_pages_from_pdf(pdf_path: Path) -> list[dict]:
    """
    Extrae el texto de un archivo PDF página por página usando PyMuPDF (fitz).
    Retorna una lista de diccionarios con el número de página y su contenido de texto.
    """
    if fitz is None:
        raise ImportError(
            "La librería 'PyMuPDF' no está instalada. Ejecuta: pip install pymupdf"
        )

    pages = []
    doc = fitz.open(str(pdf_path))
    try:
        for page_idx in range(len(doc)):
            page = doc[page_idx]
            page_text = page.get_text("text").strip()
            # Conservamos solo páginas que contengan texto legible
            if page_text:
                pages.append({
                    "pagina": page_idx + 1,  # Indexado humano (comenzando en 1)
                    "texto": page_text
                })
    finally:
        doc.close()

    return pages


def split_text_into_chunks(pages: list[dict], filename: str) -> list[dict]:
    """
    Divide el texto de cada página en fragmentos (chunks) usando RecursiveCharacterTextSplitter.
    Antepone el encabezado 'Documento: {archivo} | Página: {pagina}\n' a cada fragmento y
    asigna metadatos que incluyen el tipo ('contrato' o 'normativa').
    """
    if RecursiveCharacterTextSplitter is None:
        raise ImportError(
            "La librería 'langchain-text-splitters' no está instalada. "
            "Ejecuta: pip install langchain-text-splitters"
        )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", ". ", "; ", " ", ""]
    )

    # Determinar tipo: 'normativa' si el archivo empieza por 'guia_', 'compendio_' o 'manual_', de lo contrario 'contrato'
    filename_lower = filename.lower()
    if filename_lower.startswith(("guia_", "compendio_", "manual_")):
        tipo = "normativa"
    else:
        tipo = "contrato"

    chunks = []
    for p in pages:
        page_num = p["pagina"]
        page_text = p["texto"]

        split_texts = splitter.split_text(page_text)
        for idx, chunk_text in enumerate(split_texts):
            clean_chunk = chunk_text.strip()
            if not clean_chunk:
                continue

            # Anteponer encabezado contextual a cada fragmento antes de vectorizar
            texto_con_encabezado = f"Documento: {filename} | Página: {page_num}\n{clean_chunk}"

            # Generar un hash determinista para identificar de forma única el chunk
            content_hash = hashlib.sha256(
                f"{filename}_{page_num}_{texto_con_encabezado}".encode("utf-8")
            ).hexdigest()[:12]

            chunk_id = f"{filename}_p{page_num}_c{idx}_{content_hash}"

            chunks.append({
                "id": chunk_id,
                "texto": texto_con_encabezado,
                "metadata": {
                    "archivo": filename,
                    "pagina": page_num,
                    "chunk_index": idx,
                    "tipo": tipo
                }
            })

    return chunks


def ingest_documents(
    data_dir: Path | str = DATA_DIR,
    chroma_dir: Path | str = CHROMA_DIR,
    collection_name: str = COLLECTION_NAME,
    force_reset: bool = False
) -> dict:
    """
    Función principal de ingesta: procesa los PDFs de data_dir, genera embeddings
    y los almacena en ChromaDB sin duplicados.
    
    Retorna un diccionario con estadísticas del proceso.
    """
    data_path = Path(data_dir)
    chroma_path = Path(chroma_dir)

    if not data_path.exists():
        data_path.mkdir(parents=True, exist_ok=True)

    # 1. Buscar archivos PDF en la carpeta
    pdf_files = sorted(
        list(data_path.glob("*.pdf")) + list(data_path.glob("*.PDF"))
    )

    print("=" * 70)
    print(" INICIO DE INGESTA RAG - CONTRATOS LABORALES")
    print("=" * 70)
    print(f"Directorio de datos: {data_path.resolve()}")
    print(f"Base de datos Chroma: {chroma_path.resolve()}")
    print(f"Colección destino:   {collection_name}")
    print(f"Modelo embeddings:   {EMBEDDING_MODEL} (Ollama)")
    print(f"Configuración chunk: size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP}")
    print("-" * 70)

    if not pdf_files:
        print("[AVISO] No se encontraron archivos PDF en ./data.")
        print("        Coloca archivos PDF en la carpeta o ejecuta 'python generate_sample_contracts.py'.")
        return {
            "status": "warning",
            "message": "No se encontraron archivos PDF para procesar.",
            "total_files": 0,
            "new_chunks": 0,
            "existing_chunks": 0
        }

    print(f"Se encontraron {len(pdf_files)} contrato(s) PDF para procesar:\n")
    for f in pdf_files:
        print(f"  • {f.name} ({f.stat().st_size / 1024:.1f} KB)")
    print("-" * 70)

    # 2. Inicializar cliente persistente de ChromaDB
    if chromadb is None:
        raise ImportError(
            "La librería 'chromadb' no está instalada. Ejecuta: pip install chromadb"
        )

    chroma_client = chromadb.PersistentClient(path=str(chroma_path))

    if force_reset:
        try:
            chroma_client.delete_collection(name=collection_name)
            print(f"[RESET] Colección '{collection_name}' eliminada para reindexación completa.")
        except Exception:
            pass

    collection = chroma_client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )

    # Obtener IDs existentes para evitar procesar y calcular duplicados
    existing_data = collection.get()
    existing_ids = set(existing_data.get("ids", []))
    print(f"[ESTADO] Chunks previamente almacenados en ChromaDB: {len(existing_ids)}\n")

    total_new_chunks = 0
    total_skipped_chunks = 0
    total_pages_extracted = 0

    # 3. Procesar cada archivo PDF
    for i, pdf_path in enumerate(pdf_files, start=1):
        filename = pdf_path.name
        print(f"[{i}/{len(pdf_files)}] Procesando: {filename}...")

        try:
            pages = extract_pages_from_pdf(pdf_path)
            total_pages_extracted += len(pages)
            print(f"   -> {len(pages)} página(s) con texto extraídas.")
        except Exception as e:
            print(f"   [ERROR] Falló la lectura de {filename}: {e}")
            continue

        if not pages:
            print("   [AVISO] Archivo sin texto legible (podría ser un escaneo de imagen).")
            continue

        chunks = split_text_into_chunks(pages, filename)
        tipo_doc = chunks[0]["metadata"]["tipo"] if chunks else "desconocido"
        print(f"   -> Generados {len(chunks)} fragmentos (chunks) [Tipo: {tipo_doc.upper()}].")

        # Filtrar chunks que ya existen en la base de datos
        chunks_to_add = []
        for chk in chunks:
            if chk["id"] in existing_ids:
                total_skipped_chunks += 1
            else:
                chunks_to_add.append(chk)

        if not chunks_to_add:
            print("   -> Todos los fragmentos ya se encuentran indexados. (Sin cambios)")
            continue

        print(f"   -> Calculando embeddings para {len(chunks_to_add)} fragmento(s) nuevo(s)...")

        ids_batch = []
        docs_batch = []
        metas_batch = []
        embeddings_batch = []

        for chk_idx, chk in enumerate(chunks_to_add, start=1):
            sys.stdout.write(
                f"\r      Generando embedding [{chk_idx}/{len(chunks_to_add)}] "
                f"(Pág {chk['metadata']['pagina']})..."
            )
            sys.stdout.flush()

            try:
                emb = get_ollama_embedding(chk["texto"], model=EMBEDDING_MODEL)
            except Exception as e:
                print(f"\n   [ERROR] No se pudo generar embedding con Ollama: {e}")
                raise e

            ids_batch.append(chk["id"])
            docs_batch.append(chk["texto"])
            metas_batch.append(chk["metadata"])
            embeddings_batch.append(emb)

        print("\r      Embeddings generados con éxito. Guardando en ChromaDB...   ")

        # Guardar en ChromaDB usando upsert (garantiza unicidad e idempotencia)
        collection.upsert(
            ids=ids_batch,
            embeddings=embeddings_batch,
            documents=docs_batch,
            metadatas=metas_batch
        )

        # Actualizar conjunto de IDs en memoria
        existing_ids.update(ids_batch)
        total_new_chunks += len(ids_batch)
        print(f"   [OK] {len(ids_batch)} fragmento(s) agregados exitosamente.\n")

    final_count = collection.count()

    print("=" * 70)
    print(" RESUMEN DE INGESTA")
    print("=" * 70)
    print(f"Archivos procesados:       {len(pdf_files)}")
    print(f"Páginas totales leídas:    {total_pages_extracted}")
    print(f"Nuevos chunks indexados:   {total_new_chunks}")
    print(f"Chunks existentes omitidos: {total_skipped_chunks}")
    print(f"Total en ChromaDB:         {final_count} vectores")
    print(f"Ubicación de base de datos: {chroma_path.resolve()}")
    print("=" * 70)

    return {
        "status": "success",
        "total_files": len(pdf_files),
        "pages_read": total_pages_extracted,
        "new_chunks": total_new_chunks,
        "skipped_chunks": total_skipped_chunks,
        "total_in_db": final_count
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Ingesta y procesamiento de contratos PDF para RAG local."
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Elimina la colección anterior y reindexa desde cero."
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default=str(DATA_DIR),
        help="Ruta al directorio de contratos PDF (por defecto ./data)."
    )
    args = parser.parse_args()

    try:
        ingest_documents(data_dir=args.data_dir, force_reset=args.reset)
    except KeyboardInterrupt:
        print("\n[INFO] Ingesta cancelada por el usuario.")
    except Exception as err:
        print(f"\n[ERROR CRÍTICO] Ocurrió un error durante la ingesta: {err}")
        sys.exit(1)

