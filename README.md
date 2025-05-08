
# Assistente de IA para Triagem Clínica com Validação Profissional

Este projeto implementa um assistente de IA com interface web para triagem clínica automatizada, utilizando **embeddings semânticos**, **modelo local via Ollama (Mistral)**, **banco vetorial (ChromaDB)** e um sistema de **validação por especialistas clínicos**.

---

## 🔍 Visão Geral

O assistente:

- Recebe **sintomas clínicos** como entrada
- Busca **casos semelhantes** em um banco vetorial
- Classifica o paciente com base na **CID-10** e no **Protocolo de Manchester**
- Sugere **condutas clínicas iniciais**
- Permite envio da triagem para **validação por especialistas**
- Incorpora **casos validados** ao banco de conhecimento, otimizando classificações futuras

---

## 📌 Funcionalidades Principais

- Interface amigável para **entrada de sintomas**
- Classificação estruturada: **Diagnóstico (CID-10), Risco, Justificativa e Conduta**
- Banco de conhecimento com aprendizado contínuo
- Sistema de **validação com feedback especializado**
- Painel administrativo com estatísticas e exportação

---

## 🖥️ Requisitos do Sistema

- **Sistema Operacional:** Windows 10 ou superior  
- **Python:** 3.10.x  
- **RAM:** 8 GB ou mais  
- **Disco:** 10 GB livres  
- **Suporte a virtualização** (para usar o Ollama)

---

## ⚙️ Instalação

### 1. Instalar o Ollama

Baixe: [https://ollama.com/download](https://ollama.com/download)

Teste no terminal:

```bash
ollama list
```

### 2. Baixar o Modelo

```bash
ollama pull mistral
```

### 3. Instalar Python

Baixe: [Python 3.10.11](https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe)

### 4. Criar ambiente virtual

```powershell
python -m venv venv310
.env310\Scripts\Activate.ps1
```

### 5. Instalar dependências

```bash
pip install --upgrade pip
pip install streamlit llama-index llama-index-llms-ollama "llama-index[llms]"
pip install chromadb sentence-transformers nest_asyncio pandas
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

---

## 🚀 Executar o Aplicativo Principal

```bash
streamlit run AppTriagem.py
```

Acesse: [http://localhost:8501](http://localhost:8501)

---

## 🩺 Interface do Usuário

- Campo para **sintomas do paciente**
- Botão **"Diagnosticar"**
- Resultado com:
  - **Diagnóstico (CID-10)**
  - **Classificação de Risco** (colorida e com emoji)
  - **Justificativa Clínica**
  - **Conduta Clínica Inicial**
- Botão **"Enviar para validação por especialistas"**
- Seção informativa sobre o processo de validação

---

## 📊 Painel de Administração

```bash
streamlit run AppAdminMedico.py
```

- Dashboard com estatísticas
- Validação e exclusão de triagens
- Feedback médico incorporado ao banco vetorial
- Exportação de triagens em CSV
- Credenciais de demonstração:

  - **Admin:** admin / admin123  
  - **Médico:** medico / medico123  
  - **Enfermeiro:** enfermeiro / enfermeiro123

---

## 🧠 Aprendizado Contínuo

1. IA gera resposta baseada em casos similares (vetorial)
2. Profissionais validam e dão feedback
3. Casos validados são **adicionados ao banco vetorial**
4. IA melhora progressivamente suas respostas

---

## 📁 Estrutura de Arquivos

- `AppTriagem.py`: Aplicativo principal de triagem
- `AppAdminMedico.py`: Painel de validação
- `casos.txt`: Casos clínicos simulados para classificação
- `validacao_triagem.db`: Banco SQLite com triagens
- `chroma_db/`: Banco vetorial persistente

---

## 🧪 Exemplo de Entrada e Saída

### Entrada:
> "Paciente de 72 anos, com dor torácica súbita, irradiação para braço esquerdo, PA 180/110"

### Saída:
- Diagnóstico: **Infarto Agudo do Miocárdio (CID-10: I21)**
- Risco: **🔴 Vermelha**
- Justificativa: Idade elevada, dor típica, PA elevada
- Conduta: Atendimento imediato na emergência

---

## 🔗 Links Úteis

- [LlamaIndex](https://docs.llamaindex.ai/)
- [ChromaDB](https://docs.trychroma.com/)
- [Ollama](https://ollama.com/)
- [Streamlit](https://streamlit.io/)
- [CID-10](https://www.cid10.com.br/)

---

> Projeto desenvolvido para fins educacionais com foco em sistemas de apoio à decisão clínica.
