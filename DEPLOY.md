# 部署到 Render（免费）

目标：手机随时能用，不依赖你的电脑。

## 前置条件
- 一个 GitHub 账号（免费）。
- DeepSeek API key。

## 第 1 步：把代码推到 GitHub

在本目录（`D:\AI\math-tutor`）执行：

```bash
git init
git add .
git commit -m "数学助教：SymPy 计算 + DeepSeek 讲解"
git branch -M main
```

在 github.com 新建一个空仓库（**不要**勾选 README），然后：

```bash
git remote add origin https://github.com/<你的用户名>/math-tutor.git
git push -u origin main
```

> 已装 `gh` 的话可一步完成：`gh repo create math-tutor --public --source=. --push`
>
> **安全**：`config.json` 已被 `.gitignore` 忽略，你的 API key 不会上传。key 通过 Render 的环境变量传入。

## 第 2 步：在 Render 部署

1. 打开 render.com，用 GitHub 账号直接登录。
2. **New → Web Service** → 连接刚才的 GitHub 仓库。
3. Render 会自动识别根目录的 `Dockerfile`。
4. 在环境变量里加：`DEEPSEEK_API_KEY` = 你的 key。
5. 选免费实例（Free）→ **Create Web Service**，等它构建完成。

> 仓库里已带 `render.yaml`，也可以用 **New → Blueprint** 一键部署。

## 第 3 步：手机使用

Render 会给你 `https://xxx.onrender.com` 地址，手机浏览器打开 → 添加到主屏幕。

## 两个注意点（诚实说明）

1. **冷启动**：免费实例闲置约 15 分钟后休眠，下次打开要等约 30–60 秒启动。介意就升付费实例。
2. **国内访问**：`onrender.com` 从中国大陆访问可能慢或不稳定。若手机打不开，改用国内轻量服务器（阿里云/腾讯云，约 ¥24/月），命令见 README「路线 B」。

## 回滚到本地

任何时候想回本地跑，双击 `start.bat` 即可。
