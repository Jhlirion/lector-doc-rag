"""
generate_sample_contracts.py
----------------------------
Script auxiliar para generar contratos laborales y documentos normativos del gobierno en PDF (100% Python estándar).
Genera documentos sintéticos detallados en Soles (S/.), contratos laborales de trabajadores,
políticas corporativas internas y guías oficiales de SUNAFIL / MTPE sobre derechos laborales mínimos,
periodos de prueba, teletrabajo y modalidades formativas.
"""

from pathlib import Path


def _build_pdf_bytes(pages: list[list[str]]) -> bytes:
    """
    Construye un documento PDF 1.4 válido con múltiples páginas usando exclusivamente
    la biblioteca estándar de Python (sin dependencias externas).
    """
    catalog_id = 1
    pages_id = 2
    font_id = 3

    # Fuente estándar Helvetica
    font_obj = f"{font_id} 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>\nendobj"

    cur_id = 4
    content_and_page_ids = []

    for lines in pages:
        content_id = cur_id
        cur_id += 1
        page_id = cur_id
        cur_id += 1

        # Construir stream de texto con posicionamiento y salto de línea
        stream_ops = ["BT", "/F1 9 Tf", "45 790 Td", "13 TL"]
        for line in lines:
            if not line.strip():
                stream_ops.append("T*")
                continue
            # Escapar caracteres reservados de PDF
            escaped = (
                line.replace("\\", "\\\\")
                .replace("(", "\\(")
                .replace(")", "\\)")
            )
            stream_ops.append(f"({escaped}) '")
        stream_ops.append("ET")

        stream_body = "\n".join(stream_ops)
        stream_bytes = stream_body.encode("latin1", errors="replace")

        content_obj = (
            f"{content_id} 0 obj\n"
            f"<< /Length {len(stream_bytes)} >>\n"
            f"stream\n{stream_body}\nendstream\nendobj"
        )
        page_obj = (
            f"{page_id} 0 obj\n"
            f"<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 595 842] "
            f"/Contents {content_id} 0 R /Resources << /Font << /F1 {font_id} 0 R >> >> >>\nendobj"
        )
        content_and_page_ids.append((content_obj, page_obj, page_id))

    kids_str = " ".join(f"{pid} 0 R" for _, _, pid in content_and_page_ids)
    pages_obj = (
        f"{pages_id} 0 obj\n"
        f"<< /Type /Pages /Kids [{kids_str}] /Count {len(content_and_page_ids)} >>\nendobj"
    )
    catalog_obj = (
        f"{catalog_id} 0 obj\n<< /Type /Catalog /Pages {pages_id} 0 R >>\nendobj"
    )

    all_objs = [catalog_obj, pages_obj, font_obj]
    for c_obj, p_obj, _ in content_and_page_ids:
        all_objs.append(c_obj)
        all_objs.append(p_obj)

    # Serialización de offsets
    out = bytearray()
    out.extend(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]

    for obj in all_objs:
        offsets.append(len(out))
        out.extend(obj.encode("latin1", errors="replace") + b"\n")

    xref_offset = len(out)
    out.extend(f"xref\n0 {len(all_objs) + 1}\n0000000000 65535 f \n".encode("latin1"))
    for off in offsets[1:]:
        out.extend(f"{off:010d} 00000 n \n".encode("latin1"))

    trailer = (
        f"trailer\n<< /Size {len(all_objs) + 1} /Root {catalog_id} 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n"
    )
    out.extend(trailer.encode("latin1"))
    return bytes(out)


def create_all_documents(output_dir: str = "./data"):
    """Crea contratos de trabajadores y compendios normativos del gobierno en Soles (S/.)."""
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # =========================================================================
    # DOCUMENTOS DE EMPLEADOS Y POLÍTICAS INTERNAS
    # =========================================================================

    # 1. Contrato Indefinido - Ana Torres Mendoza (Tech Lead Cloud)
    pdf1_pages = [
        [
            "CONTRATO DE TRABAJO A PLAZO INDETERMINADO",
            "REGISTRO RRHH: CNT-IND-2026-0088",
            "================================================================================",
            "Conste por el presente documento el Contrato Individual de Trabajo a Plazo Indeterminado",
            "que celebran de una parte:",
            "",
            "EL EMPLEADOR: INKACLOUD SOLUTIONS S.A.C., con R.U.C. N 20601234567, con domicilio fiscal",
            "en Av. Canaval y Moreyra 450, Piso 12, San Isidro, Lima, debidamente representada por su",
            "Gerente General, D. Roberto Morales Chavez, identificado con D.N.I. N 10293847.",
            "",
            "EL TRABAJADOR: DÑA. ANA LUCIA TORRES MENDOZA, identificada con D.N.I. N 47.891.234,",
            "de profesion Ingeniera de Sistemas, domiciliada en Calle Los Sauces 280, Dpto. 402, Miraflores.",
            "",
            "CLAUSULA PRIMERA: PUESTO Y VINCULACION",
            "EL EMPLEADOR contrata a LA TRABAJADORA para desempenar el cargo de LIDER TECNICA DE",
            "ARQUITECTURA CLOUD (Tech Lead) en el area de Ingenieria. Fecha de ingreso: 01 de febrero de 2026.",
            "Sus funciones principales abarcan: diseno de infraestructura en AWS, coordinacion de equipos",
            "DevOps, auditorias de seguridad de datos y diseno de arquitecturas para soluciones de IA.",
            "",
            "CLAUSULA SEGUNDA: PERIODO DE PRUEBA",
            "De conformidad con la legislacion laboral, se fija un periodo de prueba de 3 MESES calendario,",
            "computado desde el 01 de febrero de 2026 hasta el 30 de abril de 2026.",
            "",
            "CLAUSULA TERCERA: JORNADA Y HORARIO DE TRABAJO",
            "La jornada laboral ordinaria sera de 40 HORAS SEMANALES, de lunes a viernes en horario",
            "flexible de 08:30 a 17:30 horas, con 60 minutos de refrigerio no computables como jornada.",
            "Modalidad: HIBRIDA (2 dias presenciales en sede San Isidro y 3 dias de teletrabajo).",
        ],
        [
            "CONTRATO DE TRABAJO A PLAZO INDETERMINADO (PAGINA 2)",
            "Codigo: CNT-IND-2026-0088 | Trabajadora: Ana Lucia Torres Mendoza",
            "================================================================================",
            "CLAUSULA CUARTA: REMUNERACION Y BENEFICIOS SOCIALES",
            "LA TRABAJADORA percibira una remuneracion mensual ordinaria de S/ 14,500.00 SOLES (Catorce",
            "mil quinientos y 00/100 Soles) brutos, abonados mediante deposito bancario el dia 27 de cada mes.",
            "",
            "Beneficios y Bonificaciones de Ley:",
            "- Gratificaciones Legales: Dos remuneraciones al ano (Julio - Fiestas Patrias y Diciembre - Navidad),",
            "  equivalentes a un sueldo completo cada una mas la bonificacion extraordinaria de ley (9% ESSALUD).",
            "- Compensacion por Tiempo de Servicios (CTS): Depositada semestralmente en Mayo y Noviembre en BBVA.",
            "- Asignacion Familiar mensual de acuerdo con la Ley N 25129.",
            "- Seguro de Salud EPS Pacifico (Plan Dorado) cubierto al 100% por la empresa para la titular.",
            "- Bono de conectividad y energia para teletrabajo: S/ 200.00 soles mensuales no remunerativos.",
            "",
            "CLAUSULA QUINTA: POLITICA DE TELETRABAJO Y DESCONEXION DIGITAL",
            "En concordancia con la Ley de Teletrabajo (Ley N 31572):",
            "1. La empresa garantiza el derecho irrestricto a la DESCONEXION DIGITAL durante un minimo de",
            "   12 HORAS CONTINUAS entre el fin de una jornada y el inicio de la siguiente, fines de semana,",
            "   feriados y descansos vacacionales.",
            "2. Queda prohibido el envio de solicitudes operativas por correo, Slack o WhatsApp fuera de horario.",
            "",
            "CLAUSULA SEXTA: POLITICA DE CIBERSEGURIDAD Y PROTECCION DE ACTIVOS",
            "LA TRABAJADORA se compromete a usar exclusivamente la laptop Apple MacBook Pro corporativa provista,",
            "mantener activo el software antivirus EDR corporativo, la VPN institucional y el doble factor de",
            "autenticacion (MFA). Se prohibe expresamente el uso de memorias USB personales no cifradas.",
            "",
            "Lima, 01 de febrero de 2026.",
            "Por InkaCloud Solutions S.A.C.                La Trabajadora: Ana Lucia Torres Mendoza",
        ],
    ]

    # 2. Contrato a Plazo Fijo - Miguel Quispe Huaman (Senior Data Engineer)
    pdf2_pages = [
        [
            "CONTRATO DE TRABAJO SUJETO A MODALIDAD POR INICIO O INCREMENTO DE ACTIVIDAD",
            "REGISTRO: MOD-2026-0312",
            "================================================================================",
            "EMPRESA: BANCO ANDINO DIGITAL S.A., con RUC N 20559876543, con domicilio en Av. Rivera",
            "Navarrete 501, San Isidro, Lima, representada por Dña. Gabriela Salas Renteria (Gerente de RRHH).",
            "",
            "TRABAJADOR: D. MIGUEL ANGEL QUISPE HUAMAN, con D.N.I. N 44.556.677, domiciliado en",
            "Av. Arequipa 2450, Dpto. 801, Lince, Lima.",
            "",
            "ESTIPULACION PRIMERA: CAUSA OBJETIVA Y OBJETO DEL CONTRATO",
            "El presente contrato se suscribe al amparo del Art. 57 del D.S. N 003-97-TR por motivo del incremento",
            "extraordinario en la operacion del nuevo Data Lake analitico en la nube. EL TRABAJADOR ocupara",
            "el cargo de INGENIERO DE DATOS SENIOR (Senior Data Engineer).",
            "",
            "ESTIPULACION SEGUNDA: PLAZO DE VIGENCIA Y FECHAS",
            "El plazo pactado es de 12 MESES: Fecha de inicio el 15 DE ENERO DE 2026 y fecha de vencimiento",
            "el 14 DE ENERO DE 2027. Periodo de prueba: 3 meses (vence el 14 de abril de 2026).",
            "",
            "ESTIPULACION TERCERA: JORNADA Y REGIMEN LABORAL",
            "Jornada de 48 HORAS SEMANALES distribuidas de lunes a viernes de 08:30 a 18:00 horas, con 90 minutos",
            "de refrigerio. Modalidad: 100% REMOTA con revisiones presenciales trimestrales en San Isidro.",
        ],
        [
            "CONTRATO SUJETO A MODALIDAD POR INCREMENTO DE ACTIVIDAD (PAGINA 2)",
            "Codigo: MOD-2026-0312 | Trabajador: Miguel Angel Quispe Huaman",
            "================================================================================",
            "ESTIPULACION CUARTA: REMUNERACION Y BENEFICIOS",
            "EL TRABAJADOR percibira un haber mensual de S/ 9,800.00 SOLES (Nueve mil ochocientos y 00/100",
            "Soles) brutos en 12 mensualidades ordinarias. Fecha de pago: dia 28 de cada mes en cuenta sueldo.",
            "",
            "Beneficios laborales completos:",
            "- Gratificaciones legales de Julio y Diciembre equivalentes a un sueldo completo cada una.",
            "- CTS depositada semestralmente conforme a ley en el banco de eleccion del trabajador (BCP).",
            "- 30 dias de descanso vacacional remunerado tras cumplir el record vacacional anual.",
            "- Asignacion por teletrabajo: S/ 150.00 soles mensuales por concepto de internet y energia.",
            "- Bono anual de desempeno de hasta S/ 12,000.00 soles condicionado a objetivos de disponibilidad de datos.",
            "",
            "ESTIPULACION QUINTA: POLITICA DE PROTECCION DE DATOS PERSONALES (LEY N 29733)",
            "Dado el caracter financiero de la entidad, EL TRABAJADOR asume la obligacion legal de estricta",
            "reserva y secreto bancario. Queda terminantemente prohibido extraer, copiar, divulgar o procesar",
            "datos financieros o de identificacion de clientes fuera del entorno bancario seguro.",
            "",
            "ESTIPULACION SEXTA: POLITICA DE PROPIEDAD INTELECTUAL Y NO CONCURRENCIA",
            "Todo algoritmo, pipeline ETL, codigo SQL/Python y modelo analitico producido pertenece de forma",
            "exclusiva al Banco Andino Digital S.A. Pacto de no concurrencia con entidades financieras",
            "competidoras durante la vigencia del contrato y por 12 meses posteriores.",
            "",
            "San Isidro, 15 de enero de 2026.",
            "Por Banco Andino Digital S.A.                 El Trabajador: Miguel Angel Quispe Huaman",
        ],
    ]

    # 3. Convenio de Prácticas Profesionales - Lucía Robles Castro
    pdf3_pages = [
        [
            "CONVENIO FORMATIVO DE PRACTICAS PROFESIONALES (LEY N 28518)",
            "REGISTRO INSTITUCIONAL: PRK-2026-0045",
            "================================================================================",
            "EMPRESA: SECURTECH PERU S.A.C., con RUC N 20771122334, sita en Av. Jose Pardo 620, Miraflores,",
            "Lima, representada por el Mag. Renzo Valdivia Calderon (Chief Information Security Officer).",
            "",
            "PRACTICANTE: DÑA. LUCIA BEATRIZ ROBLES CASTRO, con D.N.I. N 72.345.678, egresada de la carrera",
            "de Ingenieria de Ciberseguridad de la Universidad Nacional de Ingenieria (UNI), Promocion 2025.",
            "",
            "CLAUSULA 1: MODALIDAD Y OBJETIVOS FORMATIVOS",
            "Se suscribe el convenio para la capacitacion profesional en el puesto de ANALISTA JUNIOR DE",
            "SEGURIDAD DE LA INFORMACION (SOC). Plan de aprendizaje practico:",
            "1. Monitoreo de alertas SIEM y respuesta a incidentes de seguridad informatica.",
            "2. Analisis de vulnerabilidades web (OWASP Top 10) y revision de codigo seguro.",
            "3. Implementacion y gestion de modelos LLM locales para clasificacion de eventos.",
            "",
            "CLAUSULA 2: ASIGNACION DE TUTOR TECNICO",
            "La empresa designa expresamente al Ing. Carlos Benavides (Subdirector de SOC) como TUTOR",
            "ENCARGADO de la supervision, evaluacion mensual y direccion tecnica del plan formativo.",
            "",
            "CLAUSULA 3: VIGENCIA DEL CONVENIO Y HORARIO",
            "Duracion: 12 MESES, iniciando el 01 DE MARZO DE 2026 y culminando el 28 DE FEBRERO DE 2027.",
            "Jornada formativa: 30 HORAS SEMANALES, de lunes a viernes en horario de 08:00 a 14:00 horas.",
        ],
        [
            "CONVENIO FORMATIVO DE PRACTICAS PROFESIONALES (PAGINA 2)",
            "Codigo: PRK-2026-0045 | Practicante: Lucia Beatriz Robles Castro",
            "================================================================================",
            "CLAUSULA 4: SUBVENCION ECONOMICA Y DERECHOS",
            "LA PRACTICANTE percibira una subvencion economica mensual de S/ 2,400.00 SOLES (Dos mil cuatrocientos",
            "y 00/100 Soles) netos, depositados el dia 25 de cada mes.",
            "",
            "Derechos formativos contemplados:",
            "- Media subvencion economica adicional (S/ 1,200.00 soles) al cumplir cada periodo de 6 meses continuos.",
            "- Descanso vacacional pagado de 15 dias calendario anuales.",
            "- Seguro Medico contra Accidentes y Enfermedades (FOLA) cubierto al 100% por SecurTech Peru S.A.C.",
            "- Certificado oficial de practicas profesionales emitido al culminar satisfactoriamente el convenio.",
            "",
            "CLAUSULA 5: POLITICA DE PREVENCION DEL HOSTIGAMIENTO SEXUAL LABORAL (LEY N 27942)",
            "SecurTech mantiene una politica estricta de Cero Tolerancia frente al hostigamiento sexual y laboral.",
            "Se dispone del canal confidencial y anonimo: etica@securtech.com.pe y del Comite de Intervencion",
            "para garantizar medidas de proteccion inmediata y sancion ejemplar.",
            "",
            "Miraflores, 01 de marzo de 2026.",
            "Por SecurTech Peru S.A.C.                     La Practicante: Lucia Beatriz Robles Castro",
        ],
    ]

    # 4. Contrato Especialista AI - Carlos Mendoza Rivas
    pdf4_pages = [
        [
            "CONTRATO DE TRABAJO A PLAZO FIJO POR NECESIDADES DEL MERCADO",
            "CODIGO: CNT-ESP-2026-0155",
            "================================================================================",
            "EMPLEADOR: INNOVATECH LATAM S.A.C., con RUC N 20689944332, con domicilio en Av. El Derby 250,",
            "Torre 2, Piso 8, Santiago de Surco, Lima, representada por el Ing. David Hurtado Paz.",
            "",
            "TRABAJADOR: D. CARLOS DAVID MENDOZA RIVAS, identificado con D.N.I. N 41.223.344,",
            "con residencia en Av. Encalada 740, Surco, Lima.",
            "",
            "CLAUSULA PRIMERA: PUESTO Y VINCULACION",
            "EL TRABAJADOR desempenara las funciones de ESPECIALISTA EN MODELOS GENERATIVOS Y RAG",
            "(AI Solutions Engineer) para el desarrollo de productos inteligentes internos.",
            "",
            "CLAUSULA SEGUNDA: PLAZO DE EJECUCION Y FECHAS",
            "Inicio: 01 DE ABRIL DE 2026. Vencimiento: 30 DE NOVIEMBRE DE 2026 (Duracion: 8 MESES).",
            "Periodo de prueba estipulado: 2 meses (culmina el 31 de mayo de 2026).",
            "",
            "CLAUSULA TERCERA: REMUNERACION Y RETRIBUCION MENSUAL",
            "Haber mensual bruto de S/ 12,000.00 SOLES (Doce mil y 00/100 Soles) pagaderos el ultimo dia habil de cada mes.",
            "Compensacion de gastos por teletrabajo: S/ 180.00 soles mensuales por servicios de conexion y luz.",
            "Bono trimestral por cumplimiento de hitos de despliegue RAG: hasta S/ 4,000.00 soles adicionales.",
        ],
        [
            "CONTRATO A PLAZO FIJO POR NECESIDADES DEL MERCADO (PAGINA 2)",
            "Codigo: CNT-ESP-2026-0155 | Trabajador: Carlos David Mendoza Rivas",
            "================================================================================",
            "CLAUSULA CUARTA: POLITICA DE USO DE INTELIGENCIA ARTIFICIAL Y CONFIDENCIALIDAD",
            "EL TRABAJADOR asume la obligacion de cumplir las politicas de gobernanza de IA de la empresa:",
            "1. Queda TERMINANTEMENTE PROHIBIDO subir contratos, balances financieros, codigos fuente",
            "   o datos personales de empleados/clientes a servicios externos de IA pública (ChatGPT web,",
            "   Claude público u otros) sin aislamiento corporativo garantizado.",
            "2. Todos los experimentos de RAG deben ejecutarse obligatoriamente en entornos aislados o locales",
            "   utilizando modelos Open Source (como Ollama, Qwen, Llama o embeddings BGE).",
            "3. La violacion de esta politica constituye falta grave causal de despido inmediato y denuncia civil.",
            "",
            "CLAUSULA QUINTA: VACACIONES PROPORCIONALES",
            "Al término de su vigencia de 8 meses, el trabajador tendra derecho a 20 dias calendario de vacaciones",
            "truncas liquidadas en su liquidacion de beneficios sociales conforme a ley.",
            "",
            "Santiago de Surco, 01 de abril de 2026.",
            "Por InnovaTech Latam S.A.C.                   El Trabajador: Carlos David Mendoza Rivas",
        ],
    ]

    # 5. Documento Transversal de Políticas Corporativas de RRHH
    pdf5_pages = [
        [
            "MANUAL DE POLITICAS CORPORATIVAS DE RECURSOS HUMANOS - EDICION 2026",
            "CODIGO NORMATIVO INTERNO: POL-RRHH-2026-REV3",
            "EMPRESA: GRUPO EMPRESARIAL ANDINO (APLICABLE A TODAS LAS EMPRESAS DEL GRUPO)",
            "Fecha de emision y vigencia general: 01 de Enero de 2026",
            "================================================================================",
            "SECCION I: POLITICA GENERAL DE PERMISOS Y LICENCIAS LABORALES REMUNERADAS",
            "1. Licencia por Maternidad: 98 dias naturales subsidiados por ESSALUD.",
            "2. Licencia por Paternidad: 10 dias calendario continuos remunerados al 100% por la empresa.",
            "   En casos de partos prematuros o nacimientos multiples, se extiende a 20 dias calendario.",
            "3. Licencia por Fallecimiento de familiar directo (padres, conyuge, hijos, hermanos):",
            "   5 dias habiles remunerados en la misma provincia; 8 dias habiles si el deceso ocurre en otra provincia.",
            "4. Permiso por Matrimonio del colaborador: 3 dias laborables con goce de haber.",
            "",
            "SECCION II: POLITICA DE HORARIOS, TARDANZAS Y TRABAJO EN SOBRETIEMPO (HORAS EXTRAS)",
            "1. Tolerancia máxima de ingreso: 10 minutos diarios, con un tope acumulado de 30 minutos al mes.",
            "2. Horas Extras: Son de caracter voluntario tanto para el colaborador como para la empresa.",
            "   Deben contar con aprobacion previa escrita de la Gerencia de Area. Las primeras 2 horas se pagan",
            "   con una sobretasa del 25% y las siguientes horas con sobretasa del 35%.",
        ],
        [
            "MANUAL DE POLITICAS CORPORATIVAS DE RRHH 2026 (PAGINA 2)",
            "Codigo: POL-RRHH-2026-REV3 | Grupo Empresarial Andino",
            "================================================================================",
            "SECCION III: POLITICA DE VACACIONES Y REGIMEN DE DESCANSO",
            "1. Todo colaborador adquiere el derecho a 30 dias calendario de descanso vacacional tras 1 ano de labor.",
            "2. Fraccionamiento vacacional: A solicitud del colaborador, el descanso puede dividirse en periodos:",
            "   un bloque no menor de 7 dias calendario consecutivos y el resto en fracciones minimas de 1 dia.",
            "3. Venta de vacaciones: Se permite acordar por escrito la venta de hasta 15 dias de descanso anual.",
            "",
            "SECCION IV: POLITICA DE DESCONEXION DIGITAL Y SALUD MENTAL (LEY N 31572)",
            "1. Todo colaborador bajo regimen de teletrabajo o trabajo remoto tiene derecho a desconectarse de",
            "   los medios informaticos y de comunicacion durante minimo 12 horas continuas entre jornadas.",
            "2. En dias de descanso semanal obligatorio, feriados, descansos medicos y vacaciones, no se podra",
            "   exigir respuesta a correos electronicos, mensajeria o tareas operativas.",
            "",
            "SECCION V: CANAL ETICO Y TOLERANCIA CERO AL HOSTIGAMIENTO SEXUAL (LEY N 27942)",
            "Cualquier situacion de acoso o represalia puede ser denunciada directamente al Comité de Ética",
            "a traves de: canaletico@andino.com.pe. La investigacion se inicia en un plazo maximo de 24 horas,",
            "brindando proteccion y reserva absoluta a la persona denunciante.",
            "",
            "Aprobado por el Directorio en Lima, a 01 de Enero de 2026.",
        ],
    ]

    # =========================================================================
    # DOCUMENTOS OFICIALES DEL GOBIERNO (SUNAFIL / MTPE)
    # =========================================================================

    # 6. Guía Oficial de Derechos Laborales y Criterios Inspectivos - SUNAFIL / MTPE
    pdf6_pages = [
        [
            "GUIA OFICIAL DE DERECHOS LABORALES Y FISCALIZACION LABORAL",
            "SUPERINTENDENCIA NACIONAL DE FISCALIZACION LABORAL (SUNAFIL)",
            "MINISTERIO DE TRABAJO Y PROMOCION DEL EMPLEO (MTPE) - REPUBLICA DEL PERU",
            "Compendio Normativo de Derechos Minimos del Regimen Laboral de la Actividad Privada",
            "Base Legal: D.S. N 003-97-TR (TUO del D.Leg. 728), Ley N 27735, D.S. N 001-97-TR",
            "================================================================================",
            "TITULO I: PERIODO DE PRUEBA LEGAL Y EXCEPCIONES PERMITIDAS",
            "1. Regla General (Art. 10, D.S. 003-97-TR): El periodo de prueba legal ordinario es de 3 MESES.",
            "   Durante este plazo el trabajador no goza de proteccion contra el despido arbitrario.",
            "2. Ampliacion del Periodo de Prueba: Las partes pueden pactar por escrito un periodo mayor en los",
            "   siguientes supuestos expresamente tasados por ley:",
            "   - Personal calificado o de confianza: Hasta un maximo de 6 MESES.",
            "   - Personal de direccion: Hasta un maximo de 1 ANO (12 meses).",
            "3. Criterio de Fiscalizacion de SUNAFIL: Todo pacto que exceda los plazos legales o que imponga",
            "   periodos de prueba extendidos a trabajadores sin calificacion especial es NULO DE PLENO DERECHO.",
            "",
            "TITULO II: JORNADA MAXIMA DE TRABAJO Y REGIMEN DE HORAS EXTRAS",
            "1. Tope Constitucional: La jornada ordinaria maxima de trabajo es de 8 HORAS DIARIAS o 48 HORAS",
            "   SEMANALES. Es licito pactar jornadas menores (jornada a tiempo parcial o reducida).",
            "2. Horas Extras: Tienen caracter estrictamente voluntario en su otorgamiento y prestacion.",
            "   - Sobretasa legal minima: 25% por hora calculada sobre el valor ordinario para las primeras dos horas.",
            "   - Para las horas subsiguientes: Sobretasa no menor al 35% por hora.",
            "   - No compensar ni pagar el sobretiempo constituye infraccion grave en materia laboral sancionable.",
        ],
        [
            "GUIA OFICIAL DE DERECHOS LABORALES SUNAFIL (PAGINA 2)",
            "Superintendencia Nacional de Fiscalizacion Laboral - MTPE",
            "================================================================================",
            "TITULO III: BENEFICIOS SOCIALES LEGALES OBLIGATORIOS (REGIMEN GENERAL)",
            "1. Gratificaciones Legales (Ley N 27735):",
            "   - Dos gratificaciones al ano: una en Fiestas Patrias (Julio) y otra en Navidad (Diciembre).",
            "   - Monto: Una remuneracion mensual completa mas la Bonificacion Extraordinaria de Ley (9% ESSALUD",
            "     o 6.75% para afiliados a EPS privada).",
            "   - Plazo improrrogable de pago: Hasta el 15 de julio y 15 de diciembre de cada ano.",
            "",
            "2. Compensacion por Tiempo de Servicios - CTS (TUO D.S. N 001-97-TR):",
            "   - Beneficio social de prevision contra las contingencias que origine el cese en el trabajo.",
            "   - Oportunidad de deposito: Obligatorio dentro de los primeros 15 dias naturales de Mayo y Noviembre.",
            "   - El incumplimiento en el deposito de la CTS califica como infraccion grave ante SUNAFIL.",
            "",
            "3. Descanso Vacacional Remunerado (Decreto Legislativo N 713):",
            "   - 30 dias calendario continuos de descanso remunerado por cada ano completo de servicios.",
            "   - Requisitos: Cumplimiento del record vacacional anual de asistencia efectiva.",
            "   - Fraccionamiento: A solicitud escrita del trabajador, puede fraccionarse en un bloque minimo",
            "     de 7 dias continuos y los 23 dias restantes en periodos minimos de 1 dia habil.",
            "   - Venta de vacaciones: Se puede acordar la compensacion en dinero de hasta 15 dias vacacionales.",
            "",
            "TITULO IV: ASIGNACION FAMILIAR (LEY N 25129)",
            "Trabajadores de la actividad privada que tengan hijos menores de 18 anos o hijos mayores que sigan",
            "estudios superiores exitosos hasta los 24 anos perciben el 10% de la Remuneracion Minima Vital (RMV).",
            "",
            "Publicado por el Ministerio de Trabajo y Promocion del Empleo - SUNAFIL. Lima, Peru.",
        ],
    ]

    # 7. Compendio Oficial de la Ley de Teletrabajo - Ley N° 31572 y D.S. N° 002-2023-TR
    pdf7_pages = [
        [
            "COMPENDIO DE FISCALIZACION DEL TELETRABAJO (LEY N 31572)",
            "MINISTERIO DE TRABAJO Y PROMOCION DEL EMPLEO - DIRECTIVA MTPE / SUNAFIL",
            "Normas, Derechos, Obligaciones y Criterios Inspectivos para el Teletrabajo y Trabajo Hibrido",
            "Base Legal: Ley N 31572 y su Reglamento aprobado por Decreto Supremo N 002-2023-TR",
            "================================================================================",
            "CAPITULO I: DEFINICION, VOLUNTARIEDAD Y REVERSIBILIDAD",
            "1. El teletrabajo es una modalidad especial de prestacion de servicios subordinada caracterizada por",
            "   la utilizacion preponderante de tecnologias de la informacion y comunicacion (TIC) fuera del centro laboral.",
            "2. El acuerdo de teletrabajo es de caracter voluntario y puede ser total (100% remoto) o hibrido.",
            "3. El caracter de reversibilidad garantiza que tanto empleador como teletrabajador puedan solicitar",
            "   el retorno a la modalidad presencial formalizando un preaviso razonable.",
            "",
            "CAPITULO II: DERECHO FUNDAMENTAL A LA DESCONEXION DIGITAL",
            "1. Alcance Legal (Art. 9 de la Ley 31572): El teletrabajador tiene derecho a desconectarse de los medios",
            "   informaticos, de telecomunicaciones y redes durante las horas que no corresponden a su jornada.",
            "2. Garantia Temporal Minima: Se garantiza un descanso continuo no menor a 12 HORAS CONTINUAS en un",
            "   periodo de 24 horas, asi como durante los dias de descanso semanal, feriados, vacaciones y descansos medicos.",
            "3. Prohibicion Absoluta: Durante el periodo de desconexion digital, el empleador NO puede:",
            "   - Exigir al teletrabajador que atienda llamadas, responda correos o atienda mensajes de mensajeria.",
            "   - Asignar tareas, requerir elaboracion de informes ni condicionar evaluaciones al tiempo de respuesta.",
            "4. Tipificacion SUNAFIL: Disponer o solicitar tareas vulnerando la desconexion digital constituye una",
            "   INFRACCION MUY GRAVE en materia de relaciones laborales, sancionable con multas de hasta 52 UIT.",
        ],
        [
            "COMPENDIO DE FISCALIZACION DEL TELETRABAJO (PAGINA 2)",
            "Directiva SUNAFIL - Lineamientos de Inspeccion Laboral N 31572",
            "================================================================================",
            "CAPITULO III: PROVISION DE EQUIPOS Y COMPENSACION DE GASTOS",
            "1. Regla Principal: El empleador es responsable de proporcionar los equipos de trabajo (ordenador,",
            "   perifericos, software asegurado) y de compensar el consumo de acceso a internet y energia electrica.",
            "2. Pacto en Contrario Valido: Las partes pueden acordar por escrito que el teletrabajador aporte sus",
            "   propios equipos y medios de conectividad. En dicho caso, el empleador debe compensar mensualmente",
            "   los costos incurridos basandose en las formulas oficiales de consumo aprobadas por el MTPE.",
            "3. Caracter No Remunerativo: Los montos abonados por concepto de compensacion de internet y electricidad",
            "   tienen condicion de gasto operativo y no constituyen base de calculo para gratificaciones, CTS ni tributos.",
            "",
            "CAPITULO IV: SEGURIDAD, SALUD EN EL TRABAJO Y CONFIDENCIALIDAD",
            "1. Autoevaluacion Ergonomica: El empleador debe instruir al teletrabajador sobre las posturas y pausas",
            "   activas necesarias, proveyendo el formato oficial de autoevaluacion de riesgos en el hogar.",
            "2. Ciberseguridad: El teletrabajador debe observar diligentemente las politicas de confidencialidad,",
            "   uso de VPN corporativa y resguardo de datos personales establecidas por la empresa.",
            "",
            "Superintendencia Nacional de Fiscalizacion Laboral (SUNAFIL). Sede Central, Lima, Peru.",
        ],
    ]

    # 8. Guía Oficial de Modalidades Formativas Laborales - Ley N° 28518
    pdf8_pages = [
        [
            "GUIA OFICIAL DE MODALIDADES FORMATIVAS LABORALES (LEY N 28518)",
            "MINISTERIO DE TRABAJO Y PROMOCION DEL EMPLEO (MTPE)",
            "Manual Orientativo sobre Convenios de Practicas Preprofesionales y Profesionales en el Peru",
            "Base Legal: Ley N 28518 y su Reglamento aprobado por D.S. N 007-2005-TR",
            "================================================================================",
            "SECCION 1: PRACTICAS PROFESIONALES - NATURALEZA Y LIMITES",
            "1. Definicion: Mecanismo formativo que busca consolidar el aprendizaje practico de los egresados",
            "   de instituciones de educacion superior universitaria o tecnica antes de su obtencion del titulo.",
            "2. Plazo Maximo Improrrogable: El periodo maximo de duracion del convenio de practicas profesionales",
            "   es de 12 MESES continuos o acumulados en la misma o distintas empresas.",
            "3. Jornada Formativa Maxima: No puede exceder de 8 HORAS DIARIAS o 48 HORAS SEMANALES.",
            "   (Para practicas preprofesionales con estudiantes regulares, el limite maximo es de 30 horas semanales).",
            "",
            "SECCION 2: OBLIGACIONES ECONOMICAS DE LA EMPRESA CON EL PRACTICANTE",
            "1. Subvencion Economica Mensual Minima: No puede ser inferior a una Remuneracion Minima Vital (RMV)",
            "   completa cuando se cumpla la jornada formativa maxima.",
            "2. Media Subvencion Economica Adicional: Por cada 6 MESES de duracion continua de la modalidad formativa,",
            "   el beneficiario tiene derecho inalienable a percibir el pago de MEDIA SUBVENCION ECONOMICA ADICIONAL.",
            "3. Descanso Subvencionado Anual: 15 DIAS CALENDARIO de descanso retribuido tras acumular 12 meses continuos,",
            "   o la fraccion proporcional correspondiente al termino del convenio.",
            "4. Seguro de Salud Obligatorio: La empresa debe contratar y asumir al 100% una poliza de seguro de",
            "   salud para accidentes personales y atencion medica (FOLA) con una cobertura minima de 14 RMV.",
        ],
        [
            "GUIA DE MODALIDADES FORMATIVAS LEY 28518 (PAGINA 2)",
            "Ministerio de Trabajo y Promocion del Empleo - MTPE",
            "================================================================================",
            "SECCION 3: SUPERVISION Y ASIGNACION DE TUTOR",
            "1. Toda empresa formadora esta obligada a designar a un TUTOR o coordinador tecnico especializado",
            "   que guie y supervise de forma periodica el plan de aprendizaje formativo del practicante.",
            "2. Al culminar satisfactoriamente el convenio, la empresa debe otorgar al beneficiario un Certificado",
            "   Oficial de Practicas Profesionales donde consten las competencias y horas ejecutadas.",
            "",
            "SECCION 4: INFRACCIONES Y DESNATURALIZACION DEL CONVENIO FORMATIVO",
            "El convenio formativo se DESNATURALIZA considerandose una relacion laboral formal de plazo indeterminado si:",
            "- El practicante continua desempenando funciones tras vencer el plazo maximo de 12 meses.",
            "- Se le asignan tareas que no guardan relacion con su especialidad formativa.",
            "- Se le exige realizar horas extraordinarias (las horas extras estan expresamente prohibidas para practicantes).",
            "- No se suscribe el convenio formalmente dentro de los plazos legales.",
            "",
            "Direccion de Promocion del Empleo y Autoempleo. Ministerio de Trabajo (MTPE), Lima, Peru.",
        ],
    ]

    all_docs = [
        # Contratos de Trabajadores
        ("contrato_indefinido_ana_torres.pdf", pdf1_pages),
        ("contrato_plazo_fijo_miguel_quispe.pdf", pdf2_pages),
        ("contrato_formativo_lucia_robles.pdf", pdf3_pages),
        ("contrato_especialista_ai_carlos_mendoza.pdf", pdf4_pages),
        # Políticas Corporativas de la Empresa
        ("manual_politicas_rrhh_2026.pdf", pdf5_pages),
        # Normativa Oficial del Gobierno (SUNAFIL / MTPE)
        ("guia_oficial_derechos_laborales_sunafil_mtpe.pdf", pdf6_pages),
        ("compendio_normativo_ley_teletrabajo_31572_sunafil.pdf", pdf7_pages),
        ("guia_modalidades_formativas_practicas_ley_28518.pdf", pdf8_pages),
    ]

    print(f"Generando contratos y normativas gubernamentales (SUNAFIL/MTPE) en {out_path.resolve()}...")
    for filename, pages in all_docs:
        file_path = out_path / filename
        pdf_bytes = _build_pdf_bytes(pages)
        with open(file_path, "wb") as f:
            f.write(pdf_bytes)
        print(f"  [OK] Creado: {filename} ({len(pages)} páginas)")

    print(f"\nSe generaron exitosamente {len(all_docs)} documentos PDF en {out_path.resolve()}.\n")


if __name__ == "__main__":
    create_all_documents()
