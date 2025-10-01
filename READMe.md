# 📧 Analisador de E-mails com IA (Gemini)

Uma aplicação web inteligente construída com **Flask** e **Google Gemini** para classificar e-mails, extrair insights e sugerir respostas automaticamente, otimizando a triagem e a produtividade de equipes.

**🔗 Link para a aplicação:** [**Acesse a demonstração aqui!**](https://email-classifier-git-main-vinicius-dillers-projects.vercel.app/)

![Demonstração da Interface](./assets/demo.gif)
*(Dica: Grave um GIF curto da tela e adicione aqui. Ferramentas como ScreenToGif são ótimas para isso)*

---

## ✨ Funcionalidades Principais

| Funcionalidade | Descrição |
| :--- | :--- |
| **🤖 Classificação Inteligente** | Utiliza o modelo `gemini-pro` do Google para classificar e-mails como **"Produtivo"** ou **"Improdutivo"** com alta precisão. |
| **📝 Análise Completa** | Além da classificação, a IA extrai o **tópico principal**, o **sentimento** (Positivo, Negativo, Neutro) e sugere uma **resposta automática**. |
| **📂 Múltiplos Formatos** | Analise e-mails colando o texto diretamente ou fazendo o upload de múltiplos arquivos `.txt` e `.pdf` de uma só vez. |
| **🗂️ Histórico de Análises** | Todas as análises são salvas em um banco de dados SQLite e exibidas em um histórico interativo na interface. |
| **📊 Exportação para CSV** | Exporte o histórico completo de análises para um arquivo `.csv`, pronto para ser aberto no Excel ou em outras ferramentas. |
| **☁️ Pronto para a Nuvem** | O projeto está configurado para deploy *serverless* na **Vercel**, garantindo escalabilidade e facilidade de manutenção. |

---

## 🛠️ Tecnologias Utilizadas

* **Backend:** Python, Flask
* **Inteligência Artificial:** Google Gemini API
* **Frontend:** HTML5, CSS3, JavaScript
* **Banco de Dados:** SQLite
* **Processamento de Arquivos:** PyPDF
* **Deploy:** Vercel

---

## 🚀 Como Executar o Projeto Localmente

Siga os passos abaixo para ter o projeto rodando na sua máquina.

#### **Pré-requisitos**

* Python 3.8+
* pip (gerenciador de pacotes)
* Uma **chave de API do Google Gemini**. Você pode obter uma gratuitamente no [Google AI Studio](https://aistudio.google.com/).

#### **Passos para Instalação**

1.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/viniciusdiller/Email-Classifier.git](https://github.com/viniciusdiller/Email-Classifier.git)
    cd Email-Classifier
    ```

2.  **Crie e ative um ambiente virtual:**
    ```bash
    # Para Windows
    python -m venv venv
    .\venv\Scripts\activate

    # Para macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure a sua chave de API:**
    Crie um arquivo chamado `.env` na raiz do projeto (no mesmo nível do `requirements.txt`) e adicione sua chave de API:
    ```.env
    GEMINI_API_KEY="SUA_CHAVE_DE_API_AQUI"
    ```
    O arquivo `.env` já está no `.gitignore` para garantir que sua chave não seja enviada para o repositório.

5.  **Execute a aplicação:**
    ```bash
    # Navegue até a pasta do código-fonte
    cd src/

    # Inicie o servidor Flask
    flask run
    ```

6.  **Acesse no navegador:**
    Abra seu navegador e acesse `http://127.0.0.1:5000`.

---




