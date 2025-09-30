document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("email-form");
  const fileUploadArea = document.querySelector(".file-upload-area");
  const fileInput = document.getElementById("file-upload");
  const emailTextInput = document.getElementById("email-text");

  const fileUploadP = document.querySelector(".file-upload-area p");
  const originalFileUploadHTML = fileUploadP.innerHTML;

  // Carrega o histórico
  loadHistory();

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    handleFormSubmit();
  });

  // Lógica para arrastar arquivo
  fileUploadArea.addEventListener("dragover", (event) => {
    event.preventDefault();
    fileUploadArea.classList.add("dragover");
  });
  fileUploadArea.addEventListener("dragleave", () => {
    fileUploadArea.classList.remove("dragover");
  });
  fileUploadArea.addEventListener("drop", (event) => {
    event.preventDefault();
    fileUploadArea.classList.remove("dragover");
    const files = event.dataTransfer.files;
    if (files.length > 0) {
      fileInput.files = files;
      updateFileName(files[0].name);
      emailTextInput.value = "";
    }
  });

  //  Lógica deselecionar arquivo
  fileInput.addEventListener("change", () => {
    if (fileInput.files && fileInput.files.length > 0) {
      updateFileName(fileInput.files[0].name);
      emailTextInput.value = "";
    }
  });

  fileUploadArea.addEventListener("click", (event) => {
    if (event.target.closest("#remove-file-btn")) {
      event.preventDefault();
      event.stopPropagation();
      restoreFileUploadArea();
    }
  });

  // Função para mostrar o nome do arquivo e o botão de remover
  function updateFileName(name) {
    fileUploadArea.classList.add("file-selected");

    fileUploadP.innerHTML = `
            <div class="file-selected-container">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
                <span class="file-name">${name}</span>
                <button type="button" id="remove-file-btn" title="Remover arquivo">&times;</button>
            </div>
        `;
  }

  // Função para limpar o input e restaurar a área de upload
  function restoreFileUploadArea() {
    fileInput.value = "";
    fileUploadP.innerHTML = originalFileUploadHTML;
    fileUploadArea.classList.remove("file-selected");
  }
  const historyContainer = document.getElementById("history");
  if (historyContainer) {
    historyContainer.addEventListener("click", (event) => {
      const header = event.target.closest(".history-header");
      if (header) {
        const item = header.closest(".history-item");
        item.classList.toggle("expanded");
      }
    });
  }
});

// Funções de formulário e resultados
async function handleFormSubmit() {
  const emailText = document.getElementById("email-text").value;
  const file = document.getElementById("file-upload").files[0];
  const resultsArea = document.getElementById("results-area");
  const loadingIndicator = document.getElementById("loading-indicator");
  const formData = new FormData();

  if (emailText) {
    formData.append("email_text", emailText);
  } else if (file) {
    formData.append("file", file);
  } else {
    displayError("Por favor, insira um texto ou faça o upload de um arquivo.");
    return;
  }

  resultsArea.classList.add("hidden");
  resultsArea.innerHTML = "";
  clearError();
  loadingIndicator.classList.remove("hidden");

  try {
    const response = await fetch("/classify", {
      method: "POST",
      body: formData,
    });
    const responseData = await response.json();
    if (!response.ok) {
      throw new Error(responseData.error || "Ocorreu um erro no servidor.");
    }
    displayResults(responseData);
    loadHistory();
  } catch (error) {
    console.error("Erro:", error);
    displayError(error.message);
  } finally {
    loadingIndicator.classList.add("hidden");
  }
}

function displayResults(data) {
  const resultsArea = document.getElementById("results-area");
  if (!data || !data.classification) {
    displayError("A IA retornou uma resposta em um formato inesperado.");
    return;
  }
  const translationMap = {
    classification: "Classificação",
    confidence_score: "Nível de Confiança",
    key_topic: "Tópico Principal", // CORRIGIDO
    sentiment: "Sentimento",
  };
  const suggestedResponse =
    data.suggested_response || "Nenhuma resposta necessária.";
  let resultsGridHTML = "";
  for (const key of Object.keys(data)) {
    if (key === "suggested_response") continue;
    const label =
      translationMap[key] || key.charAt(0).toUpperCase() + key.slice(1);
    let displayValue = data[key];
    if (key === "confidence_score") {
      displayValue = `${(data[key] * 100).toFixed(0)}%`;
    }
    resultsGridHTML += `<div class="result-item"><strong>${label}</strong><span>${displayValue}</span></div>`;
  }
  resultsArea.innerHTML = `<h2>Resultados da Análise</h2><div class="results-grid">${resultsGridHTML}</div><div class="result-item-response"><div class="response-header"><strong>Resposta Sugerida:</strong><button id="copy-btn" title="Copiar resposta">Copiar</button></div><p id="suggested-text">${suggestedResponse.replace(
    /\n/g,
    "<br>"
  )}</p></div>`;
  resultsArea.classList.remove("hidden");
  const copyBtn = document.getElementById("copy-btn");
  if (copyBtn) {
    copyBtn.addEventListener("click", () => {
      navigator.clipboard
        .writeText(suggestedResponse)
        .then(() => {
          copyBtn.textContent = "Copiado!";
          setTimeout(() => {
            copyBtn.textContent = "Copiar";
          }, 2000);
        })
        .catch((err) => console.error("Erro ao copiar texto: ", err));
    });
  }
}

// FUNÇÕES PARA O HISTÓRICO
async function loadHistory() {
  try {
    const response = await fetch("/history");
    if (!response.ok) {
      throw new Error("Não foi possível carregar o histórico.");
    }
    const historyData = await response.json();
    displayHistory(historyData);
  } catch (error) {
    console.error("Erro ao carregar histórico:", error);
  }
}

function displayHistory(history) {
  const historyList = document.getElementById("history-list");
  if (history.length === 0) {
    historyList.innerHTML = "<p>Nenhuma análise foi feita ainda.</p>";
    return;
  }

  historyList.innerHTML = history
    .map(
      (item) => `
        <div class="history-item">
            <div class="history-header">
                <div class="history-header-left">
                    <!-- CORRIGIDO: Usando 'classification' (do DB) em vez de 'category' (antigo) -->
                    <span class="history-category category-${item.classification.toLowerCase()}">${
        item.classification
      }</span>
                    <span class="history-date">${new Date(
                      item.created_at
                    ).toLocaleString("pt-BR")}</span>
                </div>
                <div class="history-header-right">
                    <svg class="expand-arrow" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>
                </div>
            </div>
            <div class="history-content-wrapper">
                <!-- Conteúdo Original do E-mail (CORRIGIDO: usando 'email_content') -->
                <p class="history-content">
                    <strong>E-mail Analisado:</strong><br>
                    ${item.email_content.replace(/\n/g, "<br>")}
                </p>
                <!-- Resposta Sugerida da IA (CORRIGIDO: usando 'suggested_response') -->
                <p class="history-content" style="margin-top: 1rem;">
                    <strong>Resposta Sugerida:</strong><br>
                    ${item.suggested_response.replace(/\n/g, "<br>")}
                </p>
            </div>
        </div>
    `
    )
    .join("");
}

function displayError(message) {
  const errorContainer = document.getElementById("error-message-container");
  errorContainer.innerHTML = `<div id="error-message">${message}</div>`;
}

function clearError() {
  const errorContainer = document.getElementById("error-message-container");
  errorContainer.innerHTML = "";
}
