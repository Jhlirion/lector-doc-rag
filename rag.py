"""
rag.py
------
Módulo de recuperación y generación aumentada (RAG) 100% local.

Flujo:
1. retrieve(pregunta, k=4): Genera embedding de la consulta con bge-m3 y busca
   los k fragmentos más relevantes en ChromaDB (colección 'contratos').
2. answer(pregunta): Ensambla el contexto extraído, aplica un prompt de sistema
   estricto y consulta al modelo qwen2.5:7b a través de Ollama.
3. Devuelve una tupla (respuesta, fuentes) con los archivos y números de página consultados.
"""

import json
import os
from pathlib import Path
import sys
import urllib.error
import urllib.request

try:
    import chromadb
except ImportError:
    chromadb = None

try:
    import ollama
except ImportError:
    ollama = None

# Configuración predeterminada
CHROMA_DIR = Path("./chroma_db")
COLLECTION_NAME = "contratos"
EMBEDDING_MODEL = "bge-m3"
LLM_MODEL = "qwen2.5:7b"
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# Prompt del sistema con restricciones estrictas contra alucinaciones y soporte de auditoría laboral
SYSTEM_PROMPT = """Eres un asistente de inteligencia artificial especializado en responder preguntas sobre contratos de trabajadores y normativa laboral oficial (SUNAFIL / MTPE / Políticas corporativas).
Tu única fuente de información es el CONTEXTO que se te proporciona, el cual está estrictamente organizado en dos secciones: CONTRATOS y NORMATIVA.

Reglas estrictas de comportamiento:
1. Responde en español usando SOLO el contexto. El contexto tiene dos secciones: CONTRATOS y NORMATIVA. Si la pregunta pide comparar, extrae el dato del contrato, extrae la regla de la normativa y concluye si cumple. Solo responde 'No encontré esa información en los documentos' si ninguna sección contiene datos relacionados con la pregunta, responde SIEMPRE en español de forma clara, directa, fundamentada y profesional.
2. Utiliza ÚNICA Y EXCLUSIVAMENTE la información que aparece de manera explícita en el CONTEXTO. No inventes datos, no asumas hechos que no estén escritos ni utilices conocimientos previos ajenos al texto suministrado.
3. Si la pregunta requiere evaluar, contrastar o verificar si una cláusula o condición de un CONTRATO cumple con la NORMATIVA (SUNAFIL / MTPE / Leyes):
   - Analiza en conjunto la sección CONTRATOS y la sección NORMATIVA.
   - Compara explícitamente los datos del contrato con los artículos y directivas legales del contexto.
   - Concluye de forma fundamentada si la condición contractual cumple, excede o vulnera la norma legal.
4. Si la respuesta a la pregunta no se encuentra de forma explícita en el contexto, o si la información no es suficiente para responder con certeza, responde EXACTAMENTE:
"No encontré esa información en los contratos."
5. Cita con precisión las cifras, montos en Soles (S/.), fechas, puestos, normativas y artículos tal como aparecen en los documentos.
6. Cada fragmento del contexto debe ir con su encabezado: [Archivo, pág. X].
7. Usa temperature=0 y num_ctx=8192 en las opciones de Ollama.
8. Imprime en consola el contexto enviado al LLM cuando DEBUG=1."""


def get_query_embedding(text: str, model: str = EMBEDDING_MODEL, host: str = OLLAMA_HOST) -> list[float]:
    """
    Genera el vector de embedding para una consulta de usuario usando Ollama (bge-m3).
    """
    # 1. Intentar con librería de Python 'ollama'
    if ollama is not None:
        try:
            client = ollama.Client(host=host)
            if hasattr(client, "embed"):
                res = client.embed(model=model, input=text)
                if "embeddings" in res and res["embeddings"]:
                    return res["embeddings"][0]
            res = client.embeddings(model=model, prompt=text)
            return res["embedding"]
        except Exception:
            pass

    # 2. Respaldo HTTP directo
    url_embed = f"{host.rstrip('/')}/api/embed"
    payload_embed = json.dumps({"model": model, "input": text}).encode("utf-8")
    req_embed = urllib.request.Request(
        url_embed,
        data=payload_embed,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req_embed, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if "embeddings" in data and data["embeddings"]:
                return data["embeddings"][0]
    except Exception:
        url_embeddings = f"{host.rstrip('/')}/api/embeddings"
        payload_embeddings = json.dumps({"model": model, "prompt": text}).encode("utf-8")
        req_embeddings = urllib.request.Request(
            url_embeddings,
            data=payload_embeddings,
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req_embeddings, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["embedding"]
        except urllib.error.URLError as err:
            raise ConnectionError(
                f"No se pudo conectar con Ollama en {host}. "
                f"Asegúrate de ejecutar 'ollama serve' y tener el modelo '{model}' disponible. Error: {err}"
            ) from err


def call_ollama_llm(
    prompt: str,
    system_prompt: str = SYSTEM_PROMPT,
    model: str = LLM_MODEL,
    host: str = OLLAMA_HOST,
    temperature: float = 0.1
) -> str:
    """
    Envía el prompt al modelo LLM local (qwen2.5:7b) mediante Ollama.
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]

    # 1. Intentar con librería de Python 'ollama'
    if ollama is not None:
        try:
            client = ollama.Client(host=host)
            response = client.chat(
                model=model,
                messages=messages,
                options={"temperature": temperature}
            )
            return response["message"]["content"]
        except Exception:
            pass

    # 2. Respaldo HTTP directo
    url = f"{host.rstrip('/')}/api/chat"
    payload = json.dumps({
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": temperature}
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["message"]["content"]
    except urllib.error.URLError as err:
        raise ConnectionError(
            f"No se pudo conectar con el modelo '{model}' en Ollama ({host}). "
            f"Verifica que Ollama esté iniciado y que hayas ejecutado 'ollama pull {model}'. Detalle: {err}"
        ) from err


def _query_collection_by_type(collection, query_vector: list[float], tipo: str, k_sub: int) -> list[dict]:
    """Realiza una búsqueda vectorial en ChromaDB filtrando por el metadato 'tipo'."""
    if k_sub <= 0:
        return []

    try:
        matching_data = collection.get(where={"tipo": tipo})
        matching_ids = matching_data.get("ids", [])
        if not matching_ids:
            return []

        actual_k = min(k_sub, len(matching_ids))
        results = collection.query(
            query_embeddings=[query_vector],
            n_results=actual_k,
            where={"tipo": tipo},
            include=["documents", "metadatas", "distances"]
        )
    except Exception:
        return []

    chunks = []
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    for doc, meta, dist in zip(documents, metadatas, distances):
        chunks.append({
            "texto": doc,
            "archivo": meta.get("archivo", "Desconocido"),
            "pagina": meta.get("pagina", 1),
            "chunk_index": meta.get("chunk_index", 0),
            "tipo": meta.get("tipo", tipo),
            "distancia": dist
        })

    return chunks


def retrieve(
    pregunta: str,
    k: int = 8,
    chroma_dir: Path | str = CHROMA_DIR,
    collection_name: str = COLLECTION_NAME
) -> list[dict]:
    """
    Busca fragmentos relevantes para la pregunta en ChromaDB realizando dos búsquedas
    separadas con filtro 'where':
    - k=4 con tipo='contrato'
    - k=4 con tipo='normativa'
    Une los resultados (hasta k=8 en total) y elimina duplicados.
    """
    chroma_path = Path(chroma_dir)
    if not chroma_path.exists():
        print(f"[AVISO] Directorio ChromaDB no encontrado en {chroma_path.resolve()}.")
        return []

    if chromadb is None:
        raise ImportError(
            "La librería 'chromadb' no está instalada. Ejecuta: pip install chromadb"
        )

    chroma_client = chromadb.PersistentClient(path=str(chroma_path))
    try:
        collection = chroma_client.get_collection(name=collection_name)
    except Exception:
        # La colección aún no existe o no tiene datos
        return []

    if collection.count() == 0:
        return []

    # Generar vector para la pregunta
    query_vector = get_query_embedding(pregunta, model=EMBEDDING_MODEL)

    # 1. Dos búsquedas separadas por tipo (4 contratos + 4 normativas por defecto para k=8)
    k_contratos = k // 2
    k_normativas = k - k_contratos

    chunks_contratos = _query_collection_by_type(collection, query_vector, "contrato", k_contratos)
    chunks_normativas = _query_collection_by_type(collection, query_vector, "normativa", k_normativas)

    # 2. Unir y quitar duplicados
    vistos = set()
    chunks_unidos = []

    for c in chunks_contratos + chunks_normativas:
        clave = (c["archivo"], c["pagina"], c.get("chunk_index", 0), c["texto"][:120])
        if clave not in vistos:
            vistos.add(clave)
            chunks_unidos.append(c)

    # Respaldo de seguridad si la colección no tenía metadato 'tipo' previo a la reindexación
    if not chunks_unidos and collection.count() > 0:
        results = collection.query(
            query_embeddings=[query_vector],
            n_results=min(k, collection.count()),
            include=["documents", "metadatas", "distances"]
        )
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        for doc, meta, dist in zip(documents, metadatas, distances):
            arch = meta.get("archivo", "Desconocido")
            tipo_inf = "normativa" if arch.lower().startswith(("guia_", "compendio_", "manual_")) else "contrato"
            clave = (arch, meta.get("pagina", 1), meta.get("chunk_index", 0), doc[:120])
            if clave not in vistos:
                vistos.add(clave)
                chunks_unidos.append({
                    "texto": doc,
                    "archivo": arch,
                    "pagina": meta.get("pagina", 1),
                    "chunk_index": meta.get("chunk_index", 0),
                    "tipo": meta.get("tipo", tipo_inf),
                    "distancia": dist
                })

    return chunks_unidos


def answer(pregunta: str, k: int = 8) -> tuple[str, list[dict]]:
    """
    Función principal de RAG:
    1. Recupera los fragmentos con retrieve(k=8): 4 de contratos y 4 de normativa sin duplicados.
    2. Si no hay contexto o la base de datos está vacía, devuelve el mensaje estándar.
    3. Construye el prompt separando el contexto en CONTRATOS y NORMATIVA, pidiendo comparar si aplica.
    4. Consulta al LLM local (qwen2.5:7b) y devuelve la respuesta + lista de fuentes.
    """
    pregunta_limpia = pregunta.strip()
    if not pregunta_limpia:
        return ("Por favor, escribe una pregunta válida sobre los contratos.", [])

    # 1. Recuperar fragmentos relevantes de ChromaDB (k=8 total: 4 contratos + 4 normativas)
    try:
        chunks = retrieve(pregunta_limpia, k=k)
    except Exception as err:
        return (f"Error durante la búsqueda de fragmentos en la base vectorial: {err}", [])

    # Si no se recuperó ningún fragmento o la base de datos está vacía
    if not chunks:
        return ("No encontré esa información en los contratos.", [])

    # 2. Separar fragmentos en CONTRATOS y NORMATIVA
    chunks_contrato = [c for c in chunks if c.get("tipo") == "contrato"]
    chunks_normativa = [c for c in chunks if c.get("tipo") == "normativa"]

    # Clasificación por nombre si algún fragmento no trajo metadato tipo
    for c in chunks:
        if c not in chunks_contrato and c not in chunks_normativa:
            arch = c.get("archivo", "").lower()
            if arch.startswith(("guia_", "compendio_", "manual_")):
                chunks_normativa.append(c)
            else:
                chunks_contrato.append(c)

    # Formatear sección CONTRATOS
    fragmentos_contrato = []
    for idx, c in enumerate(chunks_contrato, start=1):
        archivo = c.get("archivo", "Desconocido")
        pagina = c.get("pagina", 1)
        texto = c.get("texto", "").strip()
        fragmentos_contrato.append(
            f"[Contrato #{idx} | Documento: {archivo} | Página: {pagina}]\n{texto}"
        )

    # Formatear sección NORMATIVA
    fragmentos_normativa = []
    for idx, c in enumerate(chunks_normativa, start=1):
        archivo = c.get("archivo", "Desconocido")
        pagina = c.get("pagina", 1)
        texto = c.get("texto", "").strip()
        fragmentos_normativa.append(
            f"[Normativa #{idx} | Documento: {archivo} | Página: {pagina}]\n{texto}"
        )

    bloque_contratos = (
        "\n\n".join(fragmentos_contrato)
        if fragmentos_contrato
        else "No se encontraron fragmentos de contratos específicos para esta consulta."
    )
    bloque_normativa = (
        "\n\n".join(fragmentos_normativa)
        if fragmentos_normativa
        else "No se encontraron fragmentos de normativa o políticas aplicables para esta consulta."
    )

    user_prompt = f"""CONTEXTO RECUPERADO:

======================================================================
1. CONTRATOS (Información contractual de los trabajadores):
======================================================================
{bloque_contratos}

======================================================================
2. NORMATIVA (Leyes laborales, directivas de SUNAFIL/MTPE y políticas):
======================================================================
{bloque_normativa}
======================================================================

PREGUNTA DEL USUARIO:
{pregunta_limpia}

INSTRUCCIONES DE RESPUESTA:
1. Responde basándote estrictamente en el contexto provisto anteriormente.
2. Si la pregunta requiere comparar o verificar si una condición del CONTRATO cumple con la ley o directivas de SUNAFIL/MTPE (ej. periodo de prueba, jornada, horas extras, teletrabajo, remuneración o beneficios):
   - Contrasta explícitamente lo estipulado en la sección CONTRATOS frente a lo establecido en la sección NORMATIVA.
   - Cita las cláusulas, montos, fechas y artículos aplicables de ambas partes.
   - Emite una conclusión clara sobre si la condición contractual cumple o vulnera la norma legal.
3. Si la pregunta es únicamente sobre un contrato o únicamente sobre una norma, responde detalladamente con la sección correspondiente.
4. Si la información solicitada no se encuentra en el contexto, responde exactamente:
   "No encontré esa información en los contratos."

RESPUESTA:"""

    # 3. Invocar al modelo LLM local (qwen2.5:7b)
    try:
        respuesta_texto = call_ollama_llm(
            prompt=user_prompt,
            system_prompt=SYSTEM_PROMPT,
            model=LLM_MODEL
        )
    except Exception as err:
        return (f"Error al generar respuesta con el modelo LLM ({LLM_MODEL}): {err}", [])

    # 4. Formatear y desduplicar la lista de fuentes (archivo, página)
    fuentes = []
    vistos_fuentes = set()
    for c in chunks:
        item = {
            "archivo": c.get("archivo", "Desconocido"),
            "pagina": c.get("pagina", 1)
        }
        clave = (item["archivo"], item["pagina"])
        if clave not in vistos_fuentes:
            vistos_fuentes.add(clave)
            fuentes.append(item)

    return (respuesta_texto.strip(), fuentes)


if __name__ == "__main__":
    print("=" * 70)
    print(f" SISTEMA RAG LOCAL - CONSULTA DE CONTRATOS (LLM: {LLM_MODEL})")
    print("=" * 70)

    # Si se pasa una pregunta por línea de comandos
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        print(f"\nPregunta: {query}\n")
        print("Consultando base vectorial y generando respuesta con Qwen2.5...\n")
        resp, sources = answer(query)
        print("RESPUESTA:")
        print("-" * 50)
        print(resp)
        print("-" * 50)
        print("\nFUENTES CONSULTADAS:")
        for s in sources:
            print(f"  • Archivo: {s['archivo']} | Página: {s['pagina']}")
        print()
    else:
        # Modo interactivo en terminal
        print("Modo interactivo activo. Escribe tu pregunta o escribe 'salir' para terminar.\n")
        while True:
            try:
                user_q = input("\nPregunta > ").strip()
                if not user_q:
                    continue
                if user_q.lower() in ("salir", "exit", "quit", "q"):
                    print("Hasta luego.")
                    break

                resp, sources = answer(user_q)
                print("\n[RESPUESTA]:")
                print(resp)
                if sources:
                    print("\n[FUENTES]:")
                    for s in sources:
                        print(f"  • {s['archivo']} (Pág. {s['pagina']})")
            except (KeyboardInterrupt, EOFError):
                print("\nSesión finalizada.")
                break

