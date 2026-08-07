const sendBtn = document.getElementById("sendBtn");
const userInput = document.getElementById("userInput");
const chatBox = document.getElementById("chatBox");
const heroSection = document.getElementById("heroSection");
const chatContainer = document.getElementById("chatContainer");
const btnSpinner = document.getElementById("btnSpinner");
const sendIcon = document.querySelector(".send-icon");

let isGenerating = false;

// Configure Marked to use Highlight.js for Code Highlighting
marked.setOptions({
  highlight: function (code, lang) {
    const language = hljs.getLanguage(lang) ? lang : 'plaintext';
    return hljs.highlight(code, { language }).value;
  },
  langPrefix: 'hljs language-'
});

// Auto-resize textarea dynamically
userInput.addEventListener("input", () => {
  userInput.style.height = "auto";
  userInput.style.height = `${Math.min(userInput.scrollHeight, 120)}px`;
});

// Key listener (Enter sends message, Shift+Enter adds newline)
userInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

sendBtn.addEventListener("click", () => sendMessage());

function sendSuggestedQuery(text) {
  userInput.value = text;
  sendMessage();
}

async function sendMessage() {
  const query = userInput.value.trim();
  if (!query || isGenerating) return;

  // Switch UI from Hero Center state to Active Chat state
  if (!heroSection.classList.contains("hidden")) {
    heroSection.classList.add("hidden");
    chatContainer.classList.remove("hidden");
  }

  // Render User Message with User Avatar
  appendMessage(query, "user");
  
  // Reset Input Field
  userInput.value = "";
  userInput.style.height = "auto";

  // Set Loading State
  setLoadingState(true);

  // Prepare Bot Message Div with Bot Logo Avatar
  const botMessageElement = appendMessage("", "bot");
  let rawResponseText = "";

  try {
    const response = await fetch("http://localhost:8000/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ q: query, thread_id: "default_user_thread" }),
    });

    if (!response.ok) throw new Error("Server error");

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    // Streaming text rendering with real-time Markdown Parsing
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      rawResponseText += decoder.decode(value, { stream: true });
      botMessageElement.innerHTML = marked.parse(rawResponseText);
      formatCodeBlocks(botMessageElement);
      chatBox.scrollTop = chatBox.scrollHeight;
    }

  } catch (error) {
    botMessageElement.textContent = "Error: Could not fetch response from server.";
  } finally {
    setLoadingState(false);
  }
}

// Render Message Rows along with Custom Avatars
function appendMessage(text, type) {
  const rowDiv = document.createElement("div");
  rowDiv.className = `chat-row ${type}-row`;

  const avatarDiv = document.createElement("div");
  avatarDiv.className = `avatar ${type}-avatar`;

  if (type === "bot") {
    // App Logo for Chatbot Avatar
    avatarDiv.innerHTML = `<img src="logo.png" alt="Pydocs AI">`;
  } else {
    // User SVG Icon for User Avatar
    avatarDiv.innerHTML = `
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
        <circle cx="12" cy="7" r="4"/>
      </svg>`;
  }

  const msgDiv = document.createElement("div");
  msgDiv.className = `message ${type}-message`;
  if (type === "user") {
    msgDiv.textContent = text;
  }

  rowDiv.appendChild(avatarDiv);
  rowDiv.appendChild(msgDiv);
  chatBox.appendChild(rowDiv);
  chatBox.scrollTop = chatBox.scrollHeight;

  return msgDiv;
}

function formatCodeBlocks(container) {
  const preElements = container.querySelectorAll("pre");
  preElements.forEach((pre) => {
    if (pre.parentElement.classList.contains("code-wrapper")) return;

    const wrapper = document.createElement("div");
    wrapper.className = "code-wrapper";

    const code = pre.querySelector("code");
    const lang = code ? (code.className.match(/language-(\w+)/) || [])[1] || "code" : "code";

    const header = document.createElement("div");
    header.className = "code-header";
    header.innerHTML = `<span>${lang}</span><button class="copy-btn">Copy</button>`;

    const copyBtn = header.querySelector(".copy-btn");
    copyBtn.addEventListener("click", () => {
      navigator.clipboard.writeText(code.innerText);
      copyBtn.textContent = "Copied!";
      setTimeout(() => (copyBtn.textContent = "Copy"), 2000);
    });

    pre.parentNode.insertBefore(wrapper, pre);
    wrapper.appendChild(header);
    wrapper.appendChild(pre);
  });
}

function setLoadingState(loading) {
  isGenerating = loading;
  sendBtn.disabled = loading;
  if (loading) {
    sendIcon.classList.add("hidden");
    btnSpinner.classList.remove("hidden");
  } else {
    sendIcon.classList.remove("hidden");
    btnSpinner.classList.add("hidden");
  }
}