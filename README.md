# QuickSub AI — 纯前端免上传·免费 AI 视频自动生成字幕 (WebGPU)

基于纯浏览器端 WebGPU / Web Worker 本地神经网络推理，免上传音视频，零服务器成本，秒级自动提取高精度时间轴字幕。

## ✨ 特性
- **零服务器成本 & 绝对隐私**：音视频不离电脑，纯浏览器端 WebGPU 硬件加速推理。
- **高精度 Whisper Small 模型**：支持量化版 q4，体积优化 70%，内存稳定不崩溃。
- **规范简体中文**：集成词汇级 OpenCC 转换模块，自动消除繁体字偏置。
- **多格式导出**：一键导出剪映 / PR / Final Cut Pro 兼容的标准 `.SRT`、`.VTT`、`.TXT` 及文本快速复制。
- **模型本地持久化**：首次按需加载后永久缓存在设备中，后续使用零网络延迟秒开；支持一键释放空间。

## 🚀 部署指南 (Cloudflare Pages)
本仓库完全为纯静态结构设计，支持直接在 Cloudflare Pages 关联 GitHub 部署：
1. 登录 [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. 进入 **Workers & Pages** -> **Create application** -> **Pages** -> **Connect to Git**
3. 选择本仓库 `quicksub-ai`
4. 构建配置留空（Framework preset: `None`，Build command: 空，Build output directory: `/`）
5. 点击 **Save and Deploy** 即可获得全球 Anycast CDN 高速访问链接！
