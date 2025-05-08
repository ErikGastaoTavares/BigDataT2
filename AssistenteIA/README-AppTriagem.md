
# Aplicativo Principal de Triagem Clínica

Este aplicativo é uma interface web desenvolvida com **Streamlit** que utiliza um **modelo de linguagem local (Mistral via Ollama)** para auxiliar profissionais de saúde na **classificação clínica de diagnósticos com base na CID-10**. A aplicação faz uso de **embeddings semânticos**, **banco vetorial ChromaDB** e um **banco de dados relacional SQLite** para armazenamento e aprendizado contínuo.

---

## Funcionalidades

- Entrada de sintomas clínicos via interface
- Busca por casos similares em banco vetorial
- Geração de diagnóstico provável com código CID-10
- Classificação de risco segundo o Protocolo de Manchester (com cor e emoji)
- Sugestão de condutas clínicas iniciais
- Envio da triagem para validação por especialistas
- Armazenamento da triagem com ID único e data/hora
- Aprendizado contínuo a partir dos casos validados

---

## Tecnologias Utilizadas

- **Streamlit**
- **LlamaIndex** + **Ollama (modelo Mistral)**
- **ChromaDB**
- **SQLite**
- **Sentence Transformers**
- **Python 3.10**

---

## Fluxo do Sistema

```text
[Entrada de Sintomas]
        ↓
[Embeddings + ChromaDB]
        ↓
[Casos Similares] → [Modelo Mistral]
                            ↓
[Diagnóstico + Risco + Conduta]
                            ↓
[Validação por Especialistas]
        ↓                         ↓
[Base Vetorial]         [SQLite com histórico]
```

---

## Como Executar

### 1. Pré-requisitos

- Python 3.10
- Ollama instalado (`https://ollama.com/download`)
- Modelo Mistral baixado:  
  `ollama pull mistral`

### 2. Ambiente Virtual e Instalações

```bash
python -m venv venv310
.env310\Scriptsctivate

pip install --upgrade pip
pip install streamlit llama-index llama-index-llms-ollama "llama-index[llms]"
pip install chromadb sentence-transformers nest_asyncio pandas
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### 3. Executar o Aplicativo

```bash
streamlit run AppTriagem.py
```

Acesse [http://localhost:8501](http://localhost:8501)

---

## Interface do Usuário

- Campo de texto para sintomas
- Botão **“Diagnosticar”**
- Exibição:
  - Diagnóstico (CID-10)
  - Classificação de Risco (cor + emoji)
  - Justificativa clínica
  - Conduta clínica inicial
- Botão **“Enviar para validação por especialistas”**
- Informações sobre o sistema de validação

---

## Integração com Painel de Validação

As triagens são salvas no banco `validacao_triagem.db` com um identificador único. Profissionais autorizados acessam o painel (`AppAdminMedico.py`) para validar ou rejeitar os casos e fornecer feedback, que é incorporado ao banco de conhecimento vetorial.

---

## Observações

- O sistema não substitui o julgamento clínico.
- O modelo funciona localmente, mantendo a privacidade dos dados.
- Casos validados melhoram automaticamente a precisão do sistema.

