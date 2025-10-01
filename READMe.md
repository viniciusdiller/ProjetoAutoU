# 📧 Analisador de E-mails com IA

Uma aplicação web em **Flask/Python** que utiliza o **Google Gemini** para classificar e-mails como "Produtivo" ou "Improdutivo" e sugerir respostas automaticamente.

---

## ✨ Funcionalidades em Destaque

| Funcionalidade            | Descrição                                                                                   |
| :------------------------ | :------------------------------------------------------------------------------------------ |
| **Classificação Gemini**  | Utiliza o modelo `gemini-2.5-flash-lite` para análise semântica e categorização.            |
| **Múltiplas Entradas**    | Analisa texto copiado e colado ou arquivos de upload (`.txt` e `.pdf`).                     |
| **Histórico Persistente** | Salva e exibe as últimas análises em tempo real, utilizando SQLite.                         |
| **Exportação Segura**     | Permite baixar todo o histórico de classificações em um arquivo CSV (otimizado para Excel). |
| **Deployment Serverless** | Configurado para fácil implementação em plataformas como o Vercel.                          |

---

## 🚀 Como Executar o Projeto

Este projeto pode ser executado tanto via link público (Vercel) quanto localmente.

### Opção 1: Acesso Online (Deployment)

O projeto está configurado para ser executado no Vercel.

🔗 **Link de Demonstração:** [https://email-classifier-git-main-vinicius-dillers-projects.vercel.app/](https://email-classifier-git-main-vinicius-dillers-projects.vercel.app/)

_(**Nota:** O histórico de dados é persistente apenas durante a sessão do servidor serverless, sendo reiniciado após um período de inatividade.)_

### Opção 2: Execução Local

#### Pré-requisitos

- Python 3.8+
- pip (gerenciador de pacotes do Python)
- **Chave de API do Google Gemini** (necessária para alimentar o modelo de IA).

#### Passos para Instalação

1. **Clone o repositório:**

   ```bash
   git clone [https://github.com/viniciusdiller/Email-Classifier](https://github.com/viniciusdiller/Email-Classifier)
   cd Email-Classifier
   ```

2. **Crie e ative o ambiente virtual:**

   ```bash
   #dentro do git bash
   python -m venv venv
   source venv/Scripts/activate

   ```

3. **Instale as dependências:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure suas credenciais:**
   **⚠️ Aviso Importante: Nunca exponha sua Chave de API!**

   A chave de API do Gemini é um segredo de acesso. Expor essa chave publicamente gera riscos de segurança e custos inesperados. Crie um arquivo na raiz do projeto chamado **`.env`** e insira sua chave:

   ```.env
   GEMINI_API_KEY="SUA_CHAVE_DE_API_AQUI"
   ```

5. **Vá para a pasta src**

   ```bash
   cd src/
   ```

5. **Execute a aplicação:**

   ```bash
   flask run
   ```

6. **Acesso:** Abra seu navegador e acesse `http://127.0.0.1:5000`.

---

## 🔒 Por Que a Chave da API deve ser Secreta?

É fundamental entender que a sua `GEMINI_API_KEY` é sua credencial de acesso aos serviços de Inteligência Artificial do Google e está diretamente ligada à sua conta de faturamento.

- **Risco Financeiro:** Ao expor a chave publicamente (por exemplo, no GitHub), qualquer pessoa mal-intencionada pode usá-la para fazer milhares de chamadas de API, **gerando custos inesperados e altos** na sua fatura.
- **Melhor Prática:** O uso de arquivos `.env` e a configuração de variáveis de ambiente em plataformas como o Vercel são a **prática padrão da indústria** para proteger credenciais, demonstrando maturidade em segurança.

---

## 🔑 Como Obter Sua Chave de API do Gemini

Para rodar o projeto localmente, você precisará gerar sua própria chave de API. É um processo rápido:

1. Acesse o **Google AI Studio** ou o **Google Cloud Console**.
2. Procure a opção para **"Criar chave de API"** (Create API Key).
3. Copie a chave gerada.
4. Cole-a no seu arquivo **`.env`** conforme o Passo 4 da seção de instalação.

---

## ⚙️ Estrutura do Projeto

A aplicação segue uma estrutura modular, com o código Python movido para a pasta `src/` para melhor organização:

