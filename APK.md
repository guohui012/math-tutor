# 打包成安卓 App（APK）

目标：把部署好的网址打包成真正的安卓安装包，装到手机后像普通软件一样打开（桌面图标、全屏、无浏览器地址栏）。

## 前置
- 已部署到 Render，拿到 `https://xxx.onrender.com` 地址。
- 一台安卓手机。

## 步骤（用 PWABuilder，免费、无需装 Android Studio）

1. 电脑浏览器打开 https://www.pwabuilder.com/
2. 输入框粘贴你的 Render 地址，点 **Start**。
3. 它会自动校验 PWA（manifest + service worker + 图标，本项目已满足）。
4. 点 **Package for Stores** → 选 Android → **Generate Package**（或 Download）。
5. 它会让你设一个签名密钥（signing key），随便填、记住密码即可，随后生成一个 `.apk` 下载。

## 装到手机

1. 把 `.apk` 传到手机（微信 / QQ / 数据线都行）。
2. 手机上点开安装，系统提示"允许安装未知来源应用"→ 允许。
3. 装好后桌面出现「数学助教」图标，点开即用。

## 说明

- 这是 **TWA（Trusted Web Activity）** 封装：本质仍是打开你的网页，但以独立 App 运行——无地址栏、独立图标、独立任务卡片，用户感知就是"一个软件"。这也是很多中小厂快速出 App 的标准做法。
- 想上架应用商店（华为/小米/Google Play）需要额外的签名与审核，属于另一件事，需要时再说。
