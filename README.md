# 数学助教（Math Tutor）

一个**手机可用**的数学问答软件：**SymPy 负责精确计算**（保证答案严谨、不会算错），**DeepSeek 负责讲透原理与步骤**（概念、推导依据、易错点）。定位是"提升数学能力的助教"，而不是只吐答案的做题机器。

---

## 一、为什么这样设计（原理）

大语言模型直接"算"数学题会一本正经地出错（它会编造答案，且自己不知道错）。所以本软件把两件事**分开**，各用最擅长的一方：

| 环节 | 谁来做 | 为什么可靠 |
|------|--------|-----------|
| **计算（求值）** | SymPy 符号计算引擎 | 返回的是**解析解**（精确值），如 `√2`、`π`、`2/3`，不是四舍五入的近似；每一步都可验证，不存在"幻觉" |
| **讲解（原理）** | DeepSeek 大模型 | 擅长用自然语言讲概念、推导依据、直觉和易错点；它**只负责解释**，答案以 SymPy 的精确结果为准 |

关键点：**讲解时把 SymPy 的精确结果一并传给 DeepSeek，并要求它"以此为准、不要自行重算"**。这样既得到精确答案，又得到清晰的原理讲解。

软件还强调"**输入理解**"——先回显软件如何理解你输入的式子，让你能核验它有没有误解题目（严谨的第一步是确认题目没错）。

---

## 二、安装与运行

### 1. 安装依赖（一次性）
本机 Python 已装 Flask / SymPy / requests。若换机器：
```bash
pip install flask sympy requests -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 2. 填入 DeepSeek API Key
编辑 `config.json`，把 `deepseek_api_key` 填上你的 key（在 https://platform.deepseek.com 申请）：
```json
{
  "deepseek_api_key": "sk-你的key",
  "deepseek_model": "deepseek-chat"
}
```
> 想更强推理可把 `deepseek_model` 改成 `deepseek-reasoner`（更慢、推导更严谨）。

### 3. 启动
双击 `start.bat`，或命令行：
```bash
python app.py
```
启动后终端会打印两个地址：
- 本机：`http://127.0.0.1:5000`
- **手机：`http://<电脑IP>:5000`**（手机与电脑连**同一个 WiFi**）

### 4. 手机端"装成 App"
手机浏览器打开上面的地址后：
- **iPhone（Safari）**：点"分享"→"添加到主屏幕"。
- **Android（Chrome）**：点右上角"⋮"→"添加到主屏幕 / 安装应用"。

之后桌面会出现"数学助教"图标，点开就是全屏 App 体验（PWA）。

> 手机打不开时，多半是 Windows 防火墙拦了端口，放行 5000 端口即可。

---

## 三、怎么输入（语法示例）

计算类问题用"**命令 + 式子**"，`^` 表示幂，`*` 表示乘：

| 想做的事 | 输入示例 |
|----------|----------|
| 解方程 | `解方程 x^2 - 5x + 6 = 0` |
| 解方程组 | `solve x + y = 1, x - y = 0` |
| 求导 | `求导 x*sin(x)`（可 `求导 sin(x), x, 2` 二阶） |
| 积分（不定） | `积分 x*sin(x)` |
| 积分（定） | `积分 x^2 from 0 to 1` |
| 极限 | `极限 sin(x)/x as x->0` |
| 泰勒展开 | `泰勒展开 sin(x) at x=0` |
| 化简 | `化简 (x^2 - 1)/(x - 1)` |
| 因式分解 | `因式分解 x^2 - 4` |
| 微分方程 | `微分方程 diff(f(x), x) - f(x) = 0` |

**概念 / 证明 / 文字题**（不需要精确计算）直接问，点"**💡 只讲原理**"即可，例如：
- `证明 √2 是无理数`
- `解释极限的 ε-δ 定义`
- `泰勒展开为什么能近似函数`

---

## 四、项目结构

```
math-tutor/
├── app.py            # Flask 后端（路由 /api/compute、/api/explain）
├── solver.py         # SymPy 计算引擎（严谨、解析解）
├── explainer.py      # DeepSeek 讲解（流式 SSE）
├── config.py         # 读取 config.json / 环境变量
├── config.json       # 填 API key 和模型
├── requirements.txt
├── start.bat         # 双击启动
├── generate_icons.py # 生成 PWA 图标（Pillow）
└── static/
    ├── index.html    # 前端（手机优先）
    ├── style.css
    ├── app.js
    ├── manifest.json # PWA 配置
    └── sw.js         # Service Worker（可离线缓存壳）
```

---

## 五、局限与说明

- 计算引擎默认在**复数域**求解（如 `x^2+1=0` 会给出 `±i`），这是"全部解"的严谨做法。
- 部分积分/方程无初等闭式解，引擎会明确提示，而不是编一个答案。
- 手机需能连到运行本软件的电脑（同一局域网）。若想**随时随地在手机上用**（电脑关机也能用），需要部署到一台云服务器（可后续用 Render / 阿里云等，我可以帮你做）。
- DeepSeek 按 token 计费，本软件只调用 `deepseek-chat`，费用很低；`deepseek-reasoner` 更贵。

## 六、部署到云端（手机随时用，电脑不用开机）

原理：现在 SymPy 计算跑在你的电脑上，所以电脑必须开机。把后端部署到一台**常开的服务器**后，手机直接连服务器，就和你桌面的 DeepSeek App 一样"随时可用"。已准备好 [Dockerfile](Dockerfile)（Linux 容器，含 gunicorn）。

**路线 A：免费（有冷启动）**
- Render / Railway / Hugging Face Spaces，免费额度够个人用；闲置后首次请求会慢几十秒（冷启动）。
- Render 步骤：把本目录推到 GitHub → 新建 Web Service 连该仓库 → 环境变量 `DEEPSEEK_API_KEY` 填 key → 启动命令 `gunicorn -b 0.0.0.0:$PORT app:app`。

**路线 B：国内常开服务器（真·24h 在线）**
- 阿里云 / 腾讯云轻量服务器（约 ¥24–50/月）。
- 步骤：买一台 Linux 轻量 → 上传本目录 → `pip install -r requirements.txt gunicorn` → `nohup gunicorn -b 0.0.0.0:5000 app:app &` → 安全组放行 5000 端口 → 手机访问 `http://<服务器公网IP>:5000`。

**路线 C：保持本地**（不花钱，电脑开机才能用）。

