"use strict";

const qEl = document.getElementById("q");
const computeCard = document.getElementById("compute-card");
const explainCard = document.getElementById("explain-card");
const computeBody = document.getElementById("compute-body");
const explainBody = document.getElementById("explain-body");
const btnBoth = document.getElementById("btn-both");
const btnExplain = document.getElementById("btn-explain");

const EXAMPLES = [
  "解方程 x^2 - 5x + 6 = 0",
  "积分 exp(-x^2) from 0 to inf",
  "极限 sin(x)/x as x->0",
  "求导 x*sin(x)",
  "特征值 [[1,2],[3,4]]",
  "逆矩阵 [[1,2],[3,4]]",
  "行列式 [[1,2],[3,4]]",
  "factorint 2^67 - 1",
  "totient 100",
  "证明 √2 是无理数",
  "解释极限的 ε-δ 定义",
];

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function renderMath(tex) {
  try {
    return katex.renderToString(tex, { throwOnError: false });
  } catch (e) {
    return escapeHtml(tex);
  }
}

// 行内文本：转义 → 粗体 → 行内公式
function renderInline(t) {
  let html = escapeHtml(t);
  html = html.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  html = html.replace(/\$([^$\n]+?)\$|\\\(([^\\\n]+?)\\\)/g, (full, a, b) => {
    const src = (a || b || "").trim();
    try {
      return katex.renderToString(src, { throwOnError: false });
    } catch (e) {
      return full;
    }
  });
  html = html.replace(/\n/g, "<br>");
  return html;
}

// 整段讲解文本：先切 $$...$$ / \[...\] 独立公式，其余按行内处理
function renderRich(text) {
  const out = [];
  const re = /\$\$([\s\S]*?)\$\$|\\\[([\s\S]*?)\\\]/g;
  let last = 0, m;
  while ((m = re.exec(text))) {
    out.push(renderInline(text.slice(last, m.index)));
    const src = (m[1] || m[2] || "").trim();
    try {
      out.push(katex.renderToString(src, { displayMode: true, throwOnError: false }));
    } catch (e) {
      out.push(escapeHtml(m[0]));
    }
    last = m.index + m[0].length;
  }
  out.push(renderInline(text.slice(last)));
  return out.join("");
}

function renderChips() {
  const chips = document.getElementById("chips");
  EXAMPLES.forEach((e) => {
    const b = document.createElement("button");
    b.className = "chip";
    b.textContent = e;
    b.onclick = () => {
      qEl.value = e;
      qEl.focus();
    };
    chips.appendChild(b);
  });
}

function setLoading(busy) {
  btnBoth.disabled = busy;
  btnExplain.disabled = busy;
}

function renderCompute(c) {
  computeCard.hidden = false;
  if (!c || !c.ok) {
    const err = (c && c.error) || "";
    computeBody.innerHTML =
      '<div class="note">💬 未识别为可精确计算的式子（可能是概念/证明/文字题），已直接交给讲解引擎处理。</div>' +
      (err ? `<div class="muted">${escapeHtml(err)}</div>` : "");
    return;
  }
  let html = "";
  if (c.interpreted) {
    html += `<div class="row"><span class="label">输入理解</span><div class="math">${renderMath(c.interpreted)}</div></div>`;
  }
  if (c.factor) {
    html += `<div class="row"><span class="label">因式分解</span><div class="math">${renderMath(c.factor)}</div></div>`;
  }
  html += `<div class="row"><span class="label">精确结果</span><div class="math result">${renderMath(c.result)}</div></div>`;
  if (c.approx) {
    html += `<div class="row"><span class="label">数值近似</span><div class="math">≈ ${escapeHtml(c.approx)}</div></div>`;
  }
  if (c.note) {
    html += `<div class="row note">${escapeHtml(c.note)}</div>`;
  }
  computeBody.innerHTML = html;
}

async function doCompute(query) {
  const r = await fetch("/api/compute", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });
  return r.json();
}

async function streamExplain(query, computation) {
  explainCard.hidden = false;
  explainBody.innerHTML = '<div class="thinking">💭 正在思考并组织讲解…</div>';

  let resp;
  try {
    resp = await fetch("/api/explain", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, computation }),
    });
  } catch (e) {
    explainBody.innerHTML = `<div class="err">网络错误：${escapeHtml(String(e))}</div>`;
    return;
  }

  if (!resp.ok) {
    const j = await resp.json().catch(() => null);
    explainBody.innerHTML = `<div class="err">${escapeHtml((j && j.error) || "HTTP " + resp.status)}</div>`;
    return;
  }

  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
  let buf = "";
  let text = "";
  const raw = document.createElement("div");
  raw.className = "raw-stream";
  explainBody.innerHTML = "";
  explainBody.appendChild(raw);

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    let idx;
    while ((idx = buf.indexOf("\n\n")) !== -1) {
      const chunk = buf.slice(0, idx);
      buf = buf.slice(idx + 2);
      const line = chunk.trim();
      if (!line.startsWith("data:")) continue;
      const data = line.slice(5).trim();
      if (data === "[DONE]") continue;
      try {
        const o = JSON.parse(data);
        if (o.error) {
          raw.textContent = "⚠️ " + o.error;
        } else if (o.delta) {
          text += o.delta;
          raw.textContent = text;
        }
      } catch (e) {
        /* 忽略残缺的 SSE 行 */
      }
    }
  }

  const el = document.createElement("div");
  el.className = "explain-html";
  el.innerHTML = text ? renderRich(text) : '<div class="err">（未返回内容）</div>';
  explainBody.innerHTML = "";
  explainBody.appendChild(el);
}

async function onSubmit(mode) {
  const query = qEl.value.trim();
  if (!query) {
    qEl.focus();
    return;
  }
  setLoading(true);

  let computation = null;
  if (mode === "both") {
    computeCard.hidden = false;
    computeBody.innerHTML = '<div class="thinking">计算中…</div>';
    try {
      computation = await doCompute(query);
    } catch (e) {
      computation = { ok: false, error: String(e) };
    }
    renderCompute(computation);
  } else {
    computeCard.hidden = true;
  }

  await streamExplain(query, computation);
  setLoading(false);
}

btnBoth.onclick = () => onSubmit("both");
btnExplain.onclick = () => onSubmit("explain");

renderChips();
