/* ============================================================
   LocalRAG 前端逻辑
   ============================================================ */

const API = "/api";

const $messages = document.getElementById("messages");
const $input = document.getElementById("input");
const $sendBtn = document.getElementById("sendBtn");
const $fileInput = document.getElementById("fileInput");
const $docList = document.getElementById("docList");
const $docCount = document.getElementById("docCount");
const $status = document.getElementById("status");

let isGenerating = false;

/* ---------------- 初始化 ---------------- */
window.addEventListener("DOMContentLoaded", () => {
  loadDocuments();
  checkHealth();
});

/* ---------------- 健康检查 ---------------- */
async function checkHealth() {
  try {
    const r = await fetch(`${API}/health`);
    const d = await r.json();
    const ok = d.qdrant === "ok" && d.ollama === "ok";
    $status.innerHTML = ok
      ? `✅ 服务正常<br>模型: ${d.llm_model}`
      : `⚠️ Qdrant: ${d.qdrant} / Ollama: ${d.ollama}`;
  } catch (e) {
    $status.textContent = "⚠️ 无法连接后端";
  }
}

/* ---------------- 文档管理 ---------------- */
$fileInput.addEventListener("change", async (e) => {
  const file = e.target.files[0];
  if (!file) return;

  appendMessage("bot", `正在索引「${file.name}」…`);
  const form = new FormData();
  form.append("file", file);

  try {
    const r = await fetch(`${API}/documents/upload`, { method: "POST", body: form });
    const d = await r.json();
    if (!r.ok) throw new Error(d.detail || "上传失败");
    appendMessage("bot", `✅ 「${d.filename}」已索引，共 ${d.chunks} 个文本块。`);
    loadDocuments();
  } catch (err) {
    appendMessage("bot", `❌ 上传失败：${err.message}`);
  } finally {
    $fileInput.value = "";
  }
});

async function loadDocuments() {
  try {
    const r = await fetch(`${API}/documents`);
    const d = await r.json();
    const docs = d.documents || [];
    $docCount.textContent = docs.length;

    if (!docs.length) {
      $docList.innerHTML = `<li style="border:none;color:#9ca3af;font-size:12px;padding-left:0">
        还没有文档，先上传一个吧</li>`;
      return;
    }

    $docList.innerHTML = docs.map((doc) => `
      <li>
        <div>
          <div class="name">${escapeHtml(doc.filename)}</div>
          <div class="meta">${doc.chunks} 个文本块</div>
        </div>
        <button class="del" onclick="deleteDoc('${doc.document_id}')">删除</button>
      </li>
    `).join("");
  } catch (e) {
    console.error(e);
  }
}

async function deleteDoc(id) {
  if (!confirm("确定删除这个文档及其索引？")) return;
  await fetch(`${API}/documents/${id}`, { method: "DELETE" });
  loadDocuments();
}

/* ---------------- 对话 ---------------- */
$sendBtn.addEventListener("click", sendQuestion);

$input.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendQuestion();
  }
});

$input.addEventListener("input", () => {
  $input.style.height = "auto";
  $input.style.height = Math.min($input.scrollHeight, 140) + "px";
});

async function sendQuestion() {
  const question = $input.value.trim();
  if (!question || isGenerating) return;

  isGenerating = true;
  $sendBtn.disabled = true;
  $input.value = "";
  $input.style.height = "auto";

  clearEmptyState();
  appendMessage("user", question);

  const botEl = appendMessage("bot", "…");
  const bubble = botEl.querySelector(".bubble");

  try {
    const r = await fetch(`${API}/chat/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });

    if (!r.ok) throw new Error(`HTTP ${r.status}`);

    const sources = decodeSourcesHeader(r.headers.get("X-LocalRAG-Sources"));

    const reader = r.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let text = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      text += decoder.decode(value, { stream: true });
      bubble.textContent = text;
      $messages.scrollTop = $messages.scrollHeight;
    }

    if (!text.trim()) bubble.textContent = "（没有返回内容）";
    renderSources(botEl, sources);
  } catch (err) {
    bubble.textContent = `❌ 出错了：${err.message}`;
  } finally {
    isGenerating = false;
    $sendBtn.disabled = false;
    $input.focus();
  }
}

/* ---------------- 来源展示 ---------------- */
function decodeSourcesHeader(value) {
  if (!value) return [];
  try {
    const normalized = value.replace(/-/g, "+").replace(/_/g, "/");
    const padded = normalized.padEnd(Math.ceil(normalized.length / 4) * 4, "=");
    const bytes = Uint8Array.from(atob(padded), (c) => c.charCodeAt(0));
    return JSON.parse(new TextDecoder("utf-8").decode(bytes));
  } catch (e) {
    console.warn("无法解析来源信息", e);
    return [];
  }
}

function renderSources(messageEl, sources) {
  if (!sources || !sources.length) return;

  const box = document.createElement("div");
  box.className = "sources";
  box.innerHTML = `<div class="sources-title">参考来源</div>${sources.map((s) => `
    <div class="src">
      ${escapeHtml(s.file || "未知文档")} · 块 ${Number(s.chunk_index || 0) + 1}
      · 相似度 ${Number(s.score || 0).toFixed(4)}
    </div>`).join("")}`;
  messageEl.appendChild(box);
}
/* ---------------- UI 工具 ---------------- */
function appendMessage(role, text) {
  const wrap = document.createElement("div");
  wrap.className = `msg ${role}`;
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;
  wrap.appendChild(bubble);
  $messages.appendChild(wrap);
  $messages.scrollTop = $messages.scrollHeight;
  return wrap;
}

function clearEmptyState() {
  const empty = $messages.querySelector(".empty-state");
  if (empty) empty.remove();
}

function escapeHtml(s) {
  const div = document.createElement("div");
  div.textContent = s;
  return div.innerHTML;
}