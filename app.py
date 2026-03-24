
import re
import json
import datetime
from io import BytesIO
from pathlib import Path
import streamlit as st
from docx import Document

st.set_page_config(page_title="Prompts Gu Smart V4.2", page_icon="🧠", layout="wide")

PLACEHOLDER_RE = re.compile(r"\[\s*([A-Z0-9_]+)\s*\]")
BASE_MARKER = "[COLE AQUI O BLOCO BASE GLOBAL]"

DEFAULTS = {
    "NOME_DO_ALUNO": "Gustavo",
    "APELIDO": "Gu",
    "IDADE": "9 anos",
    "ANO_SERIE": "4º ano",
    "ESCOLA": "Colégio Albert Sabin",
    "TURNO_DO_ALUNO": "manhã",
    "INTERESSES_DO_ALUNO": "Minecraft, desafios, exemplos visuais, jogos rápidos",
    "NOME_DO_RESPONSAVEL": "Vanessa",
    "NIVEL_DO_ALUNO": "aprende melhor com exemplos visuais, precisa de progressão curta e foco"
}

BASE_BLOCK_TEMPLATE = """PROFESSOR PARTICULAR DE {NOME_DO_ALUNO}

Você é o professor particular de {NOME_DO_ALUNO}.
Você é especialista em pedagogia do Ensino Fundamental I, neuroaprendizagem, adaptação para TDAH e apoio a dificuldades de processamento auditivo.

PERFIL DO ALUNO
Nome: {NOME_DO_ALUNO}
Apelido: {APELIDO}
Idade: {IDADE}
Série/Ano: {ANO_SERIE}
Escola: {ESCOLA}
Turno: {TURNO_DO_ALUNO}

COMO O ALUNO APRENDE
• Atenção curta: priorize foco, clareza e progressão curta
• Dificuldade de processamento auditivo: valorize organização visual, exemplos concretos e linguagem objetiva
• Aprende melhor com exemplos e interação
• Precisa ganhar confiança, mas também ser desafiado na medida certa

REGRA PEDAGÓGICA PRINCIPAL
Explique de forma clara e acessível, mas SEM infantilizar o tom, SEM simplificar demais o raciocínio e SEM tratar o aluno como incapaz.

NÍVEL DE DESAFIO
Toda produção deve ter progressão em 3 camadas:
1. compreensão básica
2. aplicação
3. desafio leve ou transferência

USO DAS FONTES
• Use as fontes apenas para entender conceitos, habilidades cobradas, vocabulário e estilo de cobrança
• NÃO copiar exercícios, frases ou exemplos do livro
• Criar exemplos inéditos
• Quando a fonte trouxer um exemplo, manter apenas a habilidade e trocar contexto, números, objetos e pergunta
• Evitar depender apenas dos exemplos do livro

VARIEDADE DE CONTEXTOS
• Não usar sempre os mesmos temas
• Pode usar interesses do aluno, mas com moderação
• Alternar entre cotidiano, escola, dinheiro, jogos, esporte, comida, coleções, tempo, medidas, natureza, tecnologia e desafios lógicos
• Se usar os interesses do aluno, usar como apoio pontual e não como base de tudo

INTERESSES DO ALUNO
{INTERESSES_DO_ALUNO}

TOM
• Claro
• Respeitoso
• Encorajador
• Objetivo
• Intelectualmente honesto
• Sem “voz de bebê”, sem exagero de fofura, sem excesso de elogios vazios
"""

CRONOGRAMA_TEMPLATE = """{BASE}

PROMPT — CRONOGRAMA COMPLETO ATÉ A PROVA

CONTEXTO ATUAL
Data de hoje: {DATA_DE_HOJE}
Data da prova: {DATA_DA_PROVA}
Atenção para outros eventos no mesmo período: {OUTRAS_PROVAS_NO_PERIODO}
Matéria: {MATERIA}

CONTEÚDOS DA PROVA
{CONTEUDOS_DA_PROVA}

PRIORIDADE
Alta:
{PRIORIDADES}

Média:
{CONTEUDOS_MEDIOS}

Baixa:
{CONTEUDOS_SECUNDARIOS}

REGRAS DE PLANEJAMENTO
• Dividir o estudo por dias até a prova
• Sessões de 15 a 25 minutos
• Máximo de 1 conteúdo principal por dia
• Priorizar primeiro os conteúdos de maior dificuldade e maior chance de cair
• Incluir revisão final obrigatória no dia anterior à prova
• Não sobrecarregar
• Se houver pouco tempo, reduzir conteúdos secundários
• O último dia antes da prova deve focar revisão e consolidação
• No dia da prova, não incluir estudo formal; apenas descanso ou revisão mental leve

IMPORTANTE
• NÃO explicar conteúdo
• NÃO ensinar
• NÃO gerar exemplos
• NÃO detalhar a aula
• NÃO dividir o dia em dois blocos
• Gerar o plano completo, nunca apenas um dia

FORMATO OBRIGATÓRIO

[DIA X]
Conteúdo do dia:
Duração:
Objetivo:
"""

def safe_format(template, values):
    data = {}
    data.update(DEFAULTS)
    data.update(values)
    return template.format(**data)

def recommend_material(days_left, situacao, prioridade):
    if days_left <= 1:
        return "revisão estratégica + exercícios curtos + mini quiz + orientação ao responsável"
    if situacao == "novo":
        return "vídeo explicativo curto + exemplos progressivos + prática guiada + mini quiz"
    if situacao == "em_dificuldade":
        return "explicação enxuta + exercícios guiados passo a passo + correção comentada + mini quiz"
    if prioridade == "alta":
        return "explicação curta + prática guiada + desafio leve + revisão de erros"
    return "resumo rápido + aplicação + mini quiz"

def recommend_mode(days_left, situacao):
    if days_left <= 1:
        return "pré-prova"
    if situacao == "novo":
        return "introdução guiada"
    if situacao == "em_dificuldade":
        return "retomada estratégica"
    return "treino com consolidação"

def date_to_br(dt):
    return dt.strftime("%d/%m/%Y")

def make_prompt(kind, values):
    common = safe_format("""{BASE}

CONTEXTO
Matéria: {MATERIA}
Conteúdo do dia: {CONTEUDO_DO_DIA}
Data da prova: {DATA_DA_PROVA}
Dias restantes: {DIAS_RESTANTES}
Nível do aluno: {NIVEL_DO_ALUNO}
Situação do conteúdo: {SITUACAO_CONTEUDO}
Prioridade: {PRIORIDADE_DO_CONTEUDO}
Modo de estudo: {MODO_ESTUDO}
Nome do responsável: {NOME_DO_RESPONSAVEL}

IMPORTANTE
• usar as fontes apenas para entender a habilidade cobrada
• não copiar exemplos do livro
• criar exemplos inéditos
• manter linguagem clara, visual e respeitosa
• não infantilizar
""", values)

    bodies = {
        "video": """MATERIAL PARA NOTEBOOKLM STUDIO — VIDEO OVERVIEW

OBJETIVO
Criar um Video Overview realmente visual, em português do Brasil, para uma criança de 9 anos.

INSTRUÇÕES OBRIGATÓRIAS
• transformar o conteúdo em apresentação visual narrada
• organizar em sequência lógica
• usar exemplos inéditos
• incluir gancho inicial, 3 exemplos progressivos e mini desafio final
• destacar 1 erro comum
""",
        "audio": """MATERIAL PARA NOTEBOOKLM STUDIO — AUDIO OVERVIEW PARA O RESPONSÁVEL

OBJETIVO
Criar um Audio Overview em português do Brasil direcionado ao responsável que vai ajudar a criança no estudo do dia.

INSTRUÇÕES OBRIGATÓRIAS
• falar diretamente com o responsável
• soar como um professor particular orientando a condução da aula
• explicar o foco do estudo de hoje
• mostrar como começar em 1 ou 2 passos simples
• indicar onde a criança pode travar
• explicar como ajudar sem dar a resposta
• sugerir frases curtas que o responsável pode usar
• incluir como retomar se a criança dispersar
• fechar com orientação breve de encerramento positivo
• duração máxima: 5 minutos
• não dar aula para o responsável; orientar a condução
""",
        "slides": """MATERIAL PARA NOTEBOOKLM STUDIO — SLIDES

OBJETIVO
Criar slides curtos, visuais e claros.

INSTRUÇÕES OBRIGATÓRIAS
• poucos slides
• cada slide com título curto
• no máximo 2 a 4 pontos por slide
• progressão: ideia central, exemplo básico, aplicação, erro comum, mini desafio
""",
        "quiz": """MATERIAL PARA NOTEBOOKLM STUDIO — FLASHCARDS / QUIZ

OBJETIVO
Criar flashcards ou quiz para revisão ativa.

INSTRUÇÕES OBRIGATÓRIAS
• gerar exatamente entre 5 e 10 flashcards ou perguntas
• limite absoluto: no máximo 10 itens
• é proibido gerar mais de 10 itens
• nunca gerar 50 itens
• começar com confiança
• avançar para aplicação
• terminar com desafio leve
• incluir pelo menos 1 erro comum
• respostas com explicação curtíssima
""",
        "report": """MATERIAL PARA NOTEBOOKLM STUDIO — REPORT / RESUMO

OBJETIVO
Criar um resumo estratégico do conteúdo do dia.

INSTRUÇÕES OBRIGATÓRIAS
• resumir a ideia central
• listar pontos-chave
• destacar erro comum
• incluir 1 exemplo curto
• incluir 1 mini desafio
"""
    }
    return common + "\n\n" + bodies[kind]

def iter_paragraphs_in_table(table):
    for row in table.rows:
        for cell in row.cells:
            for p in cell.paragraphs:
                yield p
            for nested in cell.tables:
                yield from iter_paragraphs_in_table(nested)

def all_paragraphs(doc):
    for p in doc.paragraphs:
        yield p
    for table in doc.tables:
        yield from iter_paragraphs_in_table(table)
    for section in doc.sections:
        for p in section.header.paragraphs:
            yield p
        for p in section.footer.paragraphs:
            yield p

def extract_placeholders(doc):
    found = set()
    for p in all_paragraphs(doc):
        found.update(PLACEHOLDER_RE.findall(p.text.replace("\\n", "")))
    return sorted(found)

def get_base_block_text_from_doc(doc):
    paragraphs = list(doc.paragraphs)
    start = None
    for i, p in enumerate(paragraphs):
        if "0. BLOCO BASE GLOBAL" in p.text.upper():
            start = i
            break
    if start is None:
        return ""
    collected = []
    for p in paragraphs[start + 1:]:
        txt = p.text.strip()
        if re.match(r"^\\d+\\.", txt):
            break
        collected.append(p.text)
    return "\\n".join(collected).strip()

def replace_in_runs(paragraph, replacements):
    full = paragraph.text
    new = full
    for key, value in replacements.items():
        pattern = r"\\[\\s*" + re.escape(key) + r"\\s*\\]"
        new = re.sub(pattern, value, new)
    if new != full:
        if paragraph.runs:
            paragraph.runs[0].text = new
            for r in paragraph.runs[1:]:
                r.text = ""
        else:
            paragraph.text = new

def replace_everywhere(doc, replacements):
    for p in all_paragraphs(doc):
        txt = p.text
        if BASE_MARKER in txt and replacements.get("__BASE_BLOCK__"):
            txt = txt.replace(BASE_MARKER, replacements["__BASE_BLOCK__"])
            if p.runs:
                p.runs[0].text = txt
                for r in p.runs[1:]:
                    r.text = ""
            else:
                p.text = txt
        replace_in_runs(p, replacements)

def generate_doc_from_template(uploaded_file, values):
    uploaded_file.seek(0)
    doc = Document(uploaded_file)
    vals = dict(values)
    vals["__BASE_BLOCK__"] = get_base_block_text_from_doc(doc) or safe_format(BASE_BLOCK_TEMPLATE, vals)
    replace_everywhere(doc, vals)
    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

def make_json_safe(obj):
    if isinstance(obj, dict):
        return {str(k): make_json_safe(v) for k, v in obj.items() if not str(k).startswith("FormSubmitter")}
    if isinstance(obj, (list, tuple, set)):
        return [make_json_safe(v) for v in obj]
    if isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.strftime("%d/%m/%Y")
    try:
        json.dumps(obj)
        return obj
    except Exception:
        return str(obj)

def export_json(values):
    safe_values = make_json_safe(values)
    return json.dumps(safe_values, ensure_ascii=False, indent=2).encode("utf-8")

st.markdown("""
<style>
.block-container {padding-top: 1.2rem; padding-bottom: 2rem;}
.small-card {border: 1px solid rgba(49,51,63,0.15); border-radius: 16px; padding: 14px 16px; background: rgba(250,250,252,0.8);}
</style>
""", unsafe_allow_html=True)

st.title("Prompts Gu — Smart Web V4.2")
st.caption("Correções: áudio até 5 min, flashcards no máximo 10, e calendário para data da prova.")

with st.sidebar:
    st.header("Perfil base")
    for k, default in DEFAULTS.items():
        val = st.text_input(k, value=st.session_state.get(k, default), key="base_" + k)
        st.session_state[k] = val

tab1, tab2, tab3 = st.tabs(["1. Cronograma", "2. Studio", "3. DOCX"])

with tab1:
    st.subheader("Montar cronograma até a prova")
    a, b = st.columns(2)
    materia = a.text_input("Matéria", value=st.session_state.get("MATERIA", ""))
    hoje_dt = a.date_input("Data de hoje", value=datetime.date.today(), format="DD/MM/YYYY")
    prova_dt = b.date_input("Data da prova", value=datetime.date.today(), format="DD/MM/YYYY")
    data_hoje = date_to_br(hoje_dt)
    data_prova = date_to_br(prova_dt)
    outras = st.text_input("Outras provas no período", value=st.session_state.get("OUTRAS_PROVAS_NO_PERIODO", ""))
    conteudos = st.text_area("Conteúdos da prova", value=st.session_state.get("CONTEUDOS_DA_PROVA", ""), height=120)
    p1, p2, p3 = st.columns(3)
    prior = p1.text_area("Prioridade alta", value=st.session_state.get("PRIORIDADES", ""), height=120)
    medios = p2.text_area("Prioridade média", value=st.session_state.get("CONTEUDOS_MEDIOS", ""), height=120)
    sec = p3.text_area("Prioridade baixa", value=st.session_state.get("CONTEUDOS_SECUNDARIOS", ""), height=120)

    values = dict(st.session_state)
    values.update({"MATERIA": materia, "DATA_DE_HOJE": data_hoje, "DATA_DA_PROVA": data_prova, "OUTRAS_PROVAS_NO_PERIODO": outras, "CONTEUDOS_DA_PROVA": conteudos, "PRIORIDADES": prior, "CONTEUDOS_MEDIOS": medios, "CONTEUDOS_SECUNDARIOS": sec})
    values["BASE"] = safe_format(BASE_BLOCK_TEMPLATE, values)
    prompt_crono = safe_format(CRONOGRAMA_TEMPLATE, values)

    st.text_area("Prompt de cronograma", value=prompt_crono, height=260)
    c1, c2 = st.columns(2)
    c1.download_button("Baixar prompt .txt", prompt_crono.encode("utf-8"), file_name="prompt_cronograma_v4_2.txt")
    c2.download_button("Baixar JSON da aba", export_json(values), file_name="cronograma_valores_v4_2.json")

with tab2:
    st.subheader("Gerar instruções para a aba Studio do NotebookLM")
    c1, c2, c3 = st.columns(3)
    materia2 = c1.text_input("Matéria", value=st.session_state.get("MATERIA", ""), key="t2_materia")
    conteudo_dia = c1.text_input("Conteúdo do dia", value=st.session_state.get("CONTEUDO_DO_DIA", ""))
    hoje2_dt = c2.date_input("Data de hoje", value=datetime.date.today(), format="DD/MM/YYYY", key="t2_hoje")
    prova2_dt = c2.date_input("Data da prova", value=datetime.date.today(), format="DD/MM/YYYY", key="t2_prova")
    data_hoje2 = date_to_br(hoje2_dt)
    data_prova2 = date_to_br(prova2_dt)
    situacao = c3.selectbox("Situação do conteúdo", ["novo", "ja_visto", "em_dificuldade"], index=0)
    prioridade_conteudo = c3.selectbox("Prioridade", ["alta", "media", "baixa"], index=0)
    duracao = st.text_input("Duração desejada", value=st.session_state.get("DURACAO_DESEJADA", "15 a 25 minutos"))
    nivel = st.text_input("Nível do aluno", value=st.session_state.get("NIVEL_DO_ALUNO", DEFAULTS["NIVEL_DO_ALUNO"]))

    days_num = (prova2_dt - hoje2_dt).days
    dias_restantes = str(days_num)

    tipo = recommend_material(days_num, situacao, prioridade_conteudo)
    modo = recommend_mode(days_num, situacao)

    values2 = dict(st.session_state)
    values2.update({"MATERIA": materia2, "CONTEUDO_DO_DIA": conteudo_dia, "DATA_DE_HOJE": data_hoje2, "DATA_DA_PROVA": data_prova2, "DIAS_RESTANTES": dias_restantes, "SITUACAO_CONTEUDO": situacao, "PRIORIDADE_DO_CONTEUDO": prioridade_conteudo, "TIPO_DE_MATERIAL": tipo, "MODO_ESTUDO": modo, "NIVEL_DO_ALUNO": nivel, "DURACAO_DESEJADA": duracao})
    values2["BASE"] = safe_format(BASE_BLOCK_TEMPLATE, values2)

    st.info("Use cada bloco abaixo no tipo certo de material dentro da aba Studio do NotebookLM.")

    for title, kind, fname in [
        ("🎬 Prompt para Video Overview", "video", "studio_video_overview_v4_2.txt"),
        ("🎧 Prompt para Audio Overview (responsável)", "audio", "studio_audio_responsavel_v4_2.txt"),
        ("🧩 Prompt para Slides", "slides", "studio_slides_v4_2.txt"),
        ("❓ Prompt para Flashcards / Quiz", "quiz", "studio_quiz_v4_2.txt"),
        ("📝 Prompt para Report / Resumo", "report", "studio_report_v4_2.txt"),
    ]:
        txt = make_prompt(kind, values2)
        with st.expander(title, expanded=(kind == "video")):
            st.text_area(title, value=txt, height=220, key=f"ta_{kind}")
            st.download_button(f"Baixar {title}", txt.encode("utf-8"), file_name=fname)

    st.download_button("Baixar JSON da sessão", export_json(values2), file_name="studio_valores_v4_2.json")

with tab3:
    st.subheader("Preencher seu DOCX")
    uploaded = st.file_uploader("Envie o arquivo .docx", type=["docx"])
    if uploaded:
        uploaded.seek(0)
        doc_preview = Document(uploaded)
        placeholders = extract_placeholders(doc_preview)
        st.success(f"{len(placeholders)} campo(s) encontrado(s).")

        values3 = dict(st.session_state)
        c1, c2 = st.columns(2)
        values3["MATERIA"] = c1.text_input("MATERIA", value=values3.get("MATERIA", ""))
        hoje3_dt = c1.date_input("DATA_DE_HOJE", value=datetime.date.today(), format="DD/MM/YYYY", key="doc_hoje")
        prova3_dt = c2.date_input("DATA_DA_PROVA", value=datetime.date.today(), format="DD/MM/YYYY", key="doc_prova")
        values3["DATA_DE_HOJE"] = date_to_br(hoje3_dt)
        values3["DATA_DA_PROVA"] = date_to_br(prova3_dt)
        values3["CONTEUDO_DO_DIA"] = st.text_input("CONTEUDO_DO_DIA", value=values3.get("CONTEUDO_DO_DIA", ""))
        values3["CONTEUDOS_DA_PROVA"] = st.text_area("CONTEUDOS_DA_PROVA", value=values3.get("CONTEUDOS_DA_PROVA", ""), height=120)

        with st.expander("Editar manualmente qualquer placeholder do DOCX"):
            for ph in placeholders:
                if ph not in values3:
                    values3[ph] = st.text_input(ph, value="", key="ph_" + ph)

        if st.button("Preparar DOCX preenchido"):
            output = generate_doc_from_template(uploaded, values3)
            name = Path(uploaded.name).stem + "_preenchido_v4_2_" + datetime.datetime.now().strftime("%Y%m%d_%H%M") + ".docx"
            st.download_button("Baixar DOCX preenchido", data=output.getvalue(), file_name=name, mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    else:
        st.info("Envie o arquivo de prompts em .docx para preencher aqui.")
