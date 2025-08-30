import './index.css';

const backButton = document.getElementById("back-button");
const forwardButton = document.getElementById("forward-button");
const reloadButton = document.getElementById("reload-button");
const newWindowButton = document.getElementById("new-window-button");
const newTabButton = document.getElementById("new-tab-button");
const goButton = document.getElementById("go");
const urlInputField = document.getElementById("url-input");
const webview = document.getElementById("webview");
const tabsContainer = document.getElementById("tabs-container");

let tabs = [];
let currentTabIndex = 0;

function handleUrl() {
  let url = "";
  const inputUrl = urlInputField.value.trim();
  
  if (!inputUrl) return;
  
  if (inputUrl.startsWith("http://") || inputUrl.startsWith("https://")) {
    url = inputUrl;
  } else if (inputUrl.includes(".") && !inputUrl.includes(" ")) {
    url = "https://" + inputUrl;
  } else {
    url = "https://www.google.com/search?q=" + encodeURIComponent(inputUrl);
  }
  
  webview.src = url;
  if (tabs[currentTabIndex]) {
    tabs[currentTabIndex].url = url;
    tabs[currentTabIndex].title = getTabTitle(url);
    renderTabs();
  }
}

function getTabTitle(url) {
  if (!url || url === "about:blank") return "Nova aba";
  try {
    const domain = new URL(url).hostname;
    return domain.replace('www.', '') || "Nova aba";
  } catch {
    return "Nova aba";
  }
}

// Event Listeners
urlInputField.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    handleUrl();
  }
});

goButton.addEventListener("click", (event) => {
  event.preventDefault();
  handleUrl();
});

backButton.addEventListener("click", () => {
  if (webview.canGoBack()) {
    webview.goBack();
  }
});

forwardButton.addEventListener("click", () => {
  if (webview.canGoForward()) {
    webview.goForward();
  }
});

reloadButton.addEventListener("click", () => {
  webview.reload();
});

// Atualizar estado dos botões de navegação
function updateNavigationButtons() {
  backButton.disabled = !webview.canGoBack();
  forwardButton.disabled = !webview.canGoForward();
}

webview.addEventListener("did-navigate", (event) => {
  const url = event.url;
  urlInputField.value = url;
  if (tabs[currentTabIndex]) {
    tabs[currentTabIndex].url = url;
    tabs[currentTabIndex].title = getTabTitle(url);
    renderTabs();
  }
  updateNavigationButtons();
});

webview.addEventListener("did-navigate-in-page", () => {
  updateNavigationButtons();
});

// Funcionalidade de abas
newTabButton.addEventListener("click", () => {
  const tab = {
    title: "Nova aba",
    url: "about:blank",
  };
  tabs.push(tab);
  renderTabs();
  switchToTab(tabs.length - 1);
});

newWindowButton.addEventListener("click", () => {
  if (typeof api !== 'undefined' && api.newWindow) {
    api.newWindow();
  }
});

// Renderizar abas
function renderTabs() {
  tabsContainer.innerHTML = "";
  tabs.forEach((tab, index) => {
    const tabElement = document.createElement("div");
    tabElement.className = `tab ${index === currentTabIndex ? "active" : ""}`;
    
    const tabTitle = document.createElement("span");
    tabTitle.textContent = tab.title;
    tabTitle.style.overflow = "hidden";
    tabTitle.style.textOverflow = "ellipsis";
    tabTitle.style.whiteSpace = "nowrap";
    
    const closeButton = document.createElement("button");
    closeButton.innerHTML = "×";
    closeButton.style.background = "none";
    closeButton.style.border = "none";
    closeButton.style.cursor = "pointer";
    closeButton.style.padding = "2px 6px";
    closeButton.style.borderRadius = "4px";
    closeButton.style.fontSize = "16px";
    closeButton.style.color = "#64748b";
    closeButton.style.transition = "all 0.2s ease";
    
    closeButton.addEventListener("mouseenter", () => {
      closeButton.style.background = "#ef4444";
      closeButton.style.color = "#ffffff";
    });
    
    closeButton.addEventListener("mouseleave", () => {
      closeButton.style.background = "none";
      closeButton.style.color = "#64748b";
    });
    
    closeButton.addEventListener("click", (e) => {
      e.stopPropagation();
      closeTab(index);
    });
    
    tabElement.appendChild(tabTitle);
    if (tabs.length > 1) {
      tabElement.appendChild(closeButton);
    }
    
    tabElement.addEventListener("click", () => switchToTab(index));
    tabsContainer.appendChild(tabElement);
  });
}

// Trocar de aba
function switchToTab(index) {
  if (index < 0 || index >= tabs.length) return;
  
  currentTabIndex = index;
  const tab = tabs[index];
  urlInputField.value = tab.url === "about:blank" ? "" : tab.url;
  webview.src = tab.url;
  renderTabs();
  updateNavigationButtons();
}

// Fechar aba
function closeTab(index) {
  if (tabs.length <= 1) return;
  
  tabs.splice(index, 1);
  
  if (currentTabIndex >= tabs.length) {
    currentTabIndex = tabs.length - 1;
  } else if (currentTabIndex > index) {
    currentTabIndex--;
  }
  
  renderTabs();
  switchToTab(currentTabIndex);
}

// Inicializar com a primeira aba
tabs.push({ title: "Nova aba", url: "about:blank" });
renderTabs();
updateNavigationButtons();

// Atalhos de teclado
document.addEventListener("keydown", (event) => {
  if (event.ctrlKey || event.metaKey) {
    switch (event.key) {
      case "t":
        event.preventDefault();
        newTabButton.click();
        break;
      case "w":
        event.preventDefault();
        if (tabs.length > 1) {
          closeTab(currentTabIndex);
        }
        break;
      case "r":
        event.preventDefault();
        reloadButton.click();
        break;
      case "l":
        event.preventDefault();
        urlInputField.focus();
        urlInputField.select();
        break;
    }
  }
});

window.addEventListener("load", () => {
  urlInputField.focus();
});