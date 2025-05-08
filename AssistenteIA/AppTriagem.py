from typing import List # Importa o tipo de dado List usado para anotar funções
import warnings
warnings.filterwarnings("ignore", category=UserWarning) # Ignora mensagens de alerta do tipo UserWarning (apenas para deixar a interface limpa)
import streamlit as st # Importa a biblioteca de interface web Streamlit
from llama_index.core.llms import ChatMessage # Importa classes do LlamaIndex para usar um modelo de linguagem (LLM)
from llama_index.llms.ollama import Ollama
from llama_index.core import Settings
# Permite usar asyncio dentro do Streamlit sem conflito. Asyncio permite que múltiplas tarefas rodem ao mesmo tempo, sem travar.
import nest_asyncio
nest_asyncio.apply()
# Importa o ChromaDB, um banco de dados vetorial para armazenar e buscar embeddings
import chromadb
# Importa sqlite3 para armazenar as respostas para validação
import sqlite3
# Importa datetime para registrar a data e hora da triagem
from datetime import datetime
# Importa uuid para gerar identificadores únicos
import uuid

# Função para inicializar o banco de dados de validação
def init_validation_db():
    conn = sqlite3.connect('./validacao_triagem.db')
    cursor = conn.cursor()
    # Cria a tabela de validação se não existir
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS validacao_triagem (
        id TEXT PRIMARY KEY,
        sintomas TEXT NOT NULL,
        resposta TEXT NOT NULL,
        data_hora TEXT NOT NULL,
        validado INTEGER DEFAULT 0,
        feedback TEXT,
        validado_por TEXT,
        data_validacao TEXT
    )
    ''')
    conn.commit()
    conn.close()

# Função para salvar a resposta no banco de dados de validação
def salvar_para_validacao(sintomas, resposta):
    conn = sqlite3.connect('./validacao_triagem.db')
    cursor = conn.cursor()
    
    # Gera um ID único para a triagem
    triagem_id = str(uuid.uuid4())
    
    # Obtém a data e hora atual
    data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Insere os dados na tabela
    cursor.execute(
        "INSERT INTO validacao_triagem (id, sintomas, resposta, data_hora) VALUES (?, ?, ?, ?)",
        (triagem_id, sintomas, str(resposta), data_hora)
    )
    
    conn.commit()
    conn.close()
    
    return triagem_id

# Inicializa o banco de dados de validação
init_validation_db()

# Inicializa o modelo de linguagem da Ollama com o modelo Mistral
llm = Ollama(model="mistral", request_timeout=420.0)
Settings.llm = llm

# Cria o cliente do banco de dados vetorial ChromaDB com persistência (armazenamento local no diretório chroma_db)
chroma_client = chromadb.PersistentClient(path="./chroma_db")

# Define o nome da coleção (como uma "tabela") onde os dados serão armazenados
collection_name = "triagem_hci"

# Lista as coleções existentes no banco de dados (SELECT * FROM collections)
collections = chroma_client.list_collections()

# Verifica se a coleção já existe. Se sim, obtém ela. Caso contrário, cria uma nova.
if collection_name in [col.name for col in collections]:
    collection = chroma_client.get_collection(collection_name)
else:
    collection = chroma_client.create_collection(name=collection_name)

# Inicializa variáveis de estado da sessão
if 'resposta_atual' not in st.session_state:
    st.session_state.resposta_atual = None
if 'sintomas_atuais' not in st.session_state:
    st.session_state.sintomas_atuais = None
if 'enviado_para_validacao' not in st.session_state:
    st.session_state.enviado_para_validacao = False
if 'triagem_id' not in st.session_state:
    st.session_state.triagem_id = None

# Mostra o título da interface da aplicação no navegador
st.title("Agente IA de Classificação de Diagnósticos com base no CID 10")

# Cria um campo de texto onde enfermeiro(a) (ou outro profissional de saúde) pode informar os sintomas do paciente
new_case = st.text_area("Descreva os sintomas do paciente na triagem")

# Quando o botão é clicado, o sistema começa a análise
if st.button("Diagnosticar"):
    # Reseta o estado de envio para validação
    st.session_state.enviado_para_validacao = False
    
    # Verifica se o campo de texto com os sintomas foi preenchido
    if new_case:
        # Mostra um spinner (indicador visual) enquanto o processamento ocorre
        with st.spinner("Diagnosticando..."):

            # Importa e carrega o modelo de embeddings (vetorização) 
            from sentence_transformers import SentenceTransformer
            # Carrega um modelo pré-treinado de embeddings semânticos chamado all-MiniLM-L6-v2, 
            # disponibilizado pela Sentence Transformers, uma biblioteca baseada no Hugging Face e no PyTorch
            model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

            # Função que converte um texto em vetor numérico (embedding)
            def embed_text(text: str) -> List[float]:
                # Aplica o modelo para transformar o texto em vetor (tensor)
                embeddings = model.encode([text], convert_to_tensor=True)
                # Converte o tensor para lista de floats e retorna
                return embeddings.cpu().numpy()[0].tolist()

            # Função para ler os casos de triagem simulados a partir do arquivo "casos.txt"
            def load_triagem_cases(filepath: str) -> List[str]:
                # Abre o arquivo e retorna apenas linhas não vazias
                with open(filepath, "r", encoding="utf-8") as file:
                    return [line.strip() for line in file if line.strip()]

            # Carrega os casos simulados do arquivo
            triagem_cases = load_triagem_cases("casos.txt")

            # Recupera os IDs já existentes no banco vetorial para evitar duplicação
            existing_ids = set(collection.get()["ids"])

            # Para cada caso do arquivo
            for i, case in enumerate(triagem_cases):
                # Cria um ID único com base no índice
                case_id = f"case_{i}"
                # Adiciona o caso no banco apenas se ainda não existir
                if case_id not in existing_ids:
                    # Converte o caso em embedding
                    embedding = embed_text(case)
                    # Adiciona o vetor ao banco com o ID e metadado de conteúdo textual
                    collection.add(
                        embeddings=[embedding],
                        ids=[case_id],
                        metadatas=[{"content": case}]  # Armazena o texto original como metadado
                    )

            # Converte os sintomas informados pelo usuário em vetor (embedding)
            query_embedding = embed_text(new_case)

            # Consulta no banco vetorial os 3 casos mais semelhantes ao novo caso informado.
            # O ChromaDB utiliza o vetor de embedding gerado para o novo caso (query_embedding)
            # e compara esse vetor com todos os vetores previamente armazenados na coleção.
            # Essa comparação é feita usando uma métrica de similaridade (como produto interno ou cosseno),
            # retornando os 'n_results' casos com maior similaridade semântica.
            # O resultado inclui os metadados dos casos mais parecidos, que serão usados para orientar a resposta do LLM.
            results = collection.query(query_embeddings=[query_embedding], n_results=3)

            # Extrai os conteúdos (textos) dos casos similares retornados
            similar_cases = [metadata["content"] for metadata in results['metadatas'][0]]

            # Monta o prompt com os sintomas e os casos similares
            input_text = f"Sintomas do novo caso: {new_case}\n\nCasos Similares: {' '.join(similar_cases)}"

            # Cria a sequência de mensagens para enviar ao modelo de linguagem
            messages = [
                # Mensagem inicial: define o comportamento do assistente como um profissional da saúde
                ChatMessage(
                    role="system",
                    content="Você é um profissional de saúde responsável por analisar sintomas clínicos no Hospital de Clínicas de Ijuí. Seu objetivo é classificar o diagnóstico mais provável com base na CID-10, informando o código correspondente e sugerindo condutas clínicas iniciais apropriadas ao caso. Não inclua informações irrelevantes ou fora do contexto clínico."
                ),
                # Mensagem com os sintomas e os casos similares
                ChatMessage(role="user", content=input_text),
                # Solicita resposta estruturada com classificação, justificativa e conduta
                ChatMessage(
                    role="user",
                    content=(
                        "Com base nos sintomas descritos e nos casos similares fornecidos, elabore uma resposta estruturada contendo as seguintes seções:\n\n"
                        "Diagnóstico\n"
                        "Nome (CID-10: [CÓDIGO]): [Nome da condição diagnosticada]\n\n"
                        "Classificação de Risco\n"
                        "Cor: [Vermelha | Laranja | Amarela | Verde | Azul]\n"
                        "Justificativa: [Explique clinicamente os motivos da classificação com base nos sintomas, sinais vitais e idade do paciente]\n\n"
                        "Conduta Clínica Inicial\n"
                        "Encaminhamento: [Para onde o paciente deve ser encaminhado]\n"
                        "Objetivo: [O que deve ser feito inicialmente com o paciente: exames, estabilização, etc.]\n\n"
                        "Responda de forma objetiva, clara, curta e seguindo linguagem médica. Evite informações desnecessárias ou fora do contexto clínico."
)
                ),
            ]

            # Tenta executar a consulta ao modelo (via Ollama)
            try:
                resposta = llm.chat(messages)  # Envia as mensagens para o modelo e recebe resposta
                
                # Armazena a resposta e os sintomas na sessão para uso posterior
                st.session_state.resposta_atual = resposta
                st.session_state.sintomas_atuais = new_case
                
                # Exibe o resultado na interface web
                st.markdown("""
                    <h3 style='color:#2E8B57;font-weight:bold;margin:12px 0 4px 0;'>✅ Diagnóstico</h3>
                """, unsafe_allow_html=True)

                if resposta:
                    resposta_texto = str(resposta)

                    def extrair_bloco(texto, inicio, fim=None):
                        try:
                            start = texto.index(inicio)
                            end = texto.index(fim) if fim else len(texto)
                            return texto[start + len(inicio):end].strip()
                        except ValueError:
                            return "Informação não disponível."

                    bloco_diagnostico = extrair_bloco(resposta_texto, "Diagnóstico", "Classificação de Risco")
                    st.markdown(f"<div style='margin:0;'>{bloco_diagnostico}</div>", unsafe_allow_html=True)

                    bloco_classificacao = extrair_bloco(resposta_texto, "Classificação de Risco", "Conduta Clínica Inicial")
                    def detectar_cor_classificacao(texto):
                        cores = {
                            "vermelha": ("#B22222", "🟥"),
                            "laranja": ("#FFA500", "🟧"),
                            "amarela": ("#FFD700", "🟨"),
                            "verde": ("#32CD32", "🟩"),
                            "azul": ("#1E90FF", "🟦")
                        }
                        for cor, (hex_cor, emoji) in cores.items():
                            if f"Cor: {cor.capitalize()}" in texto:
                                return hex_cor, emoji
                        return "#DAA520", "🟡"  # padrão dourado

                    def formatar_classificacao(texto):
                        import re
                        cores = {
                            "vermelha": "#B22222",
                            "laranja": "#FFA500",
                            "amarela": "#FFD700",
                            "verde": "#32CD32",
                            "azul": "#1E90FF"
                        }
                        for cor, hex_cor in cores.items():
                            padrao = f"Cor: {cor.capitalize()}"
                            if padrao in texto:
                                texto = texto.replace(padrao, f"<span style='color:{hex_cor}; font-weight:bold;'>{padrao}</span><br>")
                        texto = re.sub(r"Justificativa:(.*?)", r"<br><strong>Justificativa:</strong>\1", texto)
                        return texto
                    cor_hex, emoji = detectar_cor_classificacao(bloco_classificacao)
                    st.markdown(f"<h3 style='color:#D3D3D3;font-weight:bold;margin:12px 0 4px 0;'>🔘 Classificação de Risco</h3>", unsafe_allow_html=True)
                    st.markdown(f"<div style='margin:0;'>{formatar_classificacao(bloco_classificacao)}</div>", unsafe_allow_html=True)
                    st.markdown("""
                        <h3 style='color:#D3D3D3;font-weight:bold;margin:12px 0 4px 0;'>🚨 Conduta Clínica Inicial</h3>
                    """, unsafe_allow_html=True)

                    def formatar_conduta(texto):
                        import re
                        texto = re.sub(r"Encaminhamento:(.*?)", r"<strong>Encaminhamento:</strong>\1", texto)
                        texto = re.sub(r"Objetivo:(.*?)", r"<br><strong>Objetivo:</strong>\1", texto)
                        return texto

                    bloco_conduta = extrair_bloco(resposta_texto, "Conduta Clínica Inicial")
                    st.markdown(f"<div style='margin-bottom:30px ;'>{formatar_conduta(bloco_conduta)}</div>", unsafe_allow_html=True)
                                
            except Exception as e:
                # Em caso de erro, mostra uma mensagem de erro na interface
                st.error(f"Ocorreu um erro ao consultar o modelo: {e}")
    else:
        # Caso o usuário não preencha os sintomas, exibe aviso
        st.warning("Por favor, insira os sintomas do paciente.")

# Botão para enviar para validação (aparece apenas se houver uma resposta)
if st.session_state.resposta_atual is not None and not st.session_state.enviado_para_validacao:
    if st.button("Enviar para validação por especialistas"):
        # Salva a resposta no banco de dados de validação
        triagem_id = salvar_para_validacao(
            st.session_state.sintomas_atuais, 
            st.session_state.resposta_atual
        )
        
        # Atualiza o estado da sessão
        st.session_state.enviado_para_validacao = True
        st.session_state.triagem_id = triagem_id
        
        # Exibe mensagem de sucesso
        st.success(f"Triagem enviada para validação com sucesso! ID: {triagem_id}")
        
        # Adiciona informações sobre o processo de validação
        st.info("A triagem será revisada por especialistas clínicos para garantir a precisão da classificação e das condutas sugeridas.")

# Exibe mensagem se já foi enviado para validação
if st.session_state.enviado_para_validacao:
    st.success(f"Esta triagem já foi enviada para validação. ID: {st.session_state.triagem_id}")

# Adiciona uma seção de informações sobre o sistema de validação
with st.expander("Sobre o sistema de validação"):
    st.markdown("""
    ### Sistema de Validação de Triagens
    
    As triagens enviadas para validação são armazenadas em um banco de dados seguro e revisadas por profissionais de saúde especializados.
    
    **Processo de validação:**
    1. A triagem é enviada e recebe um ID único
    2. Especialistas clínicos revisam a classificação e as condutas sugeridas
    3. Feedback é registrado para melhorar o sistema
    4. Casos validados são incorporados à base de conhecimento
    
    **Benefícios:**
    - Garantia de qualidade nas classificações
    - Melhoria contínua do sistema de IA
    - Segurança para os pacientes
    - Conformidade com protocolos clínicos
    """)

# Adiciona uma seção para administradores (apenas para demonstração)
with st.expander("Área de Administração (acesso restrito)"):
    st.markdown("""
    ### Painel de Administração
    
    Esta área é restrita a administradores do sistema e profissionais autorizados.
    
    Para acessar o painel completo de validação, utilize o aplicativo de administração separado.
    
    **Funcionalidades do painel administrativo:**
    - Visualização de todas as triagens pendentes de validação
    - Interface para revisão e feedback
    - Estatísticas de precisão do sistema
    - Gerenciamento de usuários e permissões
    """)
