"use strict";

const chat = document.querySelector("#chat");
const messagesEl = document.querySelector("#messages");
const welcome = document.querySelector("#welcome");
const form = document.querySelector("#composer");
const textarea = document.querySelector("#message");
const sendButton = document.querySelector("#send");
const listEl = document.querySelector("#conversation-list");
const activeKey = "cendrix-active-conversation";
let conversationId = localStorage.getItem(activeKey) || crypto.randomUUID();
localStorage.setItem(activeKey, conversationId);

function renderMessage(role, text, isError = false) {
  welcome.hidden = true;
  const row = document.createElement("article");
  row.className = `message ${role}${isError ? " error" : ""}`;
  const avatar = document.createElement("span");
  avatar.className = "message-avatar";
  avatar.textContent = role === "user" ? "Y" : "C";
  const content = document.createElement("div");
  content.className = "message-content";
  content.textContent = text;
  row.append(avatar, content);
  messagesEl.append(row);
  chat.scrollTop = chat.scrollHeight;
}

async function loadConversations() {
  try {
    const response = await fetch("/api/conversations");
    const data = await response.json();
    listEl.replaceChildren();
    for (const item of data.conversations) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = `conversation-item${item.id === conversationId ? " active" : ""}`;
      button.textContent = item.preview || "New conversation";
      button.title = button.textContent;
      button.addEventListener("click", () => openConversation(item.id));
      listEl.append(button);
    }
  } catch {
    // Chat itself remains available; recent history is a convenience.
  }
}

async function openConversation(id) {
  conversationId = id;
  localStorage.setItem(activeKey, id);
  messagesEl.replaceChildren();
  try {
    const response = await fetch(`/api/conversations/${encodeURIComponent(id)}/messages`);
    const data = await response.json();
    if (data.messages.length) {
      welcome.hidden = true;
      data.messages.forEach((item) => renderMessage(item.role, item.content));
    } else {
      welcome.hidden = false;
    }
  } catch {
    renderMessage("assistant", "I could not load that conversation. Please try again.", true);
  }
  loadConversations();
}

function startNewConversation() {
  conversationId = crypto.randomUUID();
  localStorage.setItem(activeKey, conversationId);
  messagesEl.replaceChildren();
  welcome.hidden = false;
  loadConversations();
  textarea.focus();
}

async function sendMessage(text) {
  renderMessage("user", text);
  textarea.value = "";
  textarea.style.height = "auto";
  sendButton.disabled = true;
  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ conversation_id: conversationId, message: text }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Cendrix could not answer.");
    renderMessage("assistant", data.answer);
    loadConversations();
  } catch (error) {
    renderMessage("assistant", error.message || "A local connection error occurred.", true);
  } finally {
    sendButton.disabled = false;
    textarea.focus();
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const text = textarea.value.trim();
  if (text && !sendButton.disabled) sendMessage(text);
});

textarea.addEventListener("input", () => {
  textarea.style.height = "auto";
  textarea.style.height = `${Math.min(textarea.scrollHeight, 180)}px`;
});

document.querySelector("#new-chat").addEventListener("click", startNewConversation);
document.querySelector("#mobile-new-chat").addEventListener("click", startNewConversation);
document.querySelectorAll("[data-prompt]").forEach((button) => {
  button.addEventListener("click", () => {
    textarea.value = button.dataset.prompt;
    textarea.focus();
    textarea.dispatchEvent(new Event("input"));
  });
});

loadConversations();
if ("serviceWorker" in navigator) navigator.serviceWorker.register("/sw.js").catch(() => {});
