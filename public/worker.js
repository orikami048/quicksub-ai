// worker.js - Background Web Worker with Same-Origin Cloudflare/Local Proxy
import { pipeline, env } from 'https://cdn.jsdelivr.net/npm/@huggingface/transformers@3.3.3';

env.allowLocalModels = false;

// 线上与本地均统一启用浏览器 CacheStorage，避免反复拉取大模型
env.useBrowserCache = true;

let transcriber = null;
let currentModelId = null;
let currentDevice = null;
let currentMirror = null;

self.onmessage = async (e) => {
    const { type, payload } = e.data;

    if (type === 'transcribe') {
        const { audioData, modelId, language, device, mirror } = payload;

        try {
            // 无论是本地还是 Cloudflare Worker 线上，均通过同源 /model-proxy/ 反代，100% 解决 CORS 跨域
            const origin = self.location.origin;
            env.remoteHost = `${origin}/model-proxy/${mirror}`;
            env.remotePathTemplate = '{model}/resolve/{revision}/';

            if (!transcriber || currentModelId !== modelId || currentDevice !== device || currentMirror !== mirror) {
                const mirrorLabel = mirror === 'china' ? '国内极速镜像 (hf-mirror)' : '全球官方源 (HuggingFace)';
                self.postMessage({
                    type: 'status',
                    data: { 
                        phase: 'loading_model', 
                        message: `正在连接模型仓库 [${mirrorLabel}]...` 
                    }
                });

                let targetDevice = device;
                if (targetDevice === 'webgpu' && !navigator.gpu) {
                    console.warn("WebGPU not detected in worker, falling back to wasm");
                    targetDevice = 'wasm';
                }

                // Web 端极致优化：启用量化版 q4，体积缩减 70%，杜绝 Protobuf 内存溢出
                const modelOptions = {
                    device: targetDevice,
                    dtype: {
                        encoder_model: 'fp32',
                        decoder_model_merged: 'q4',
                    },
                    progress_callback: (progressInfo) => {
                        self.postMessage({
                            type: 'download_progress',
                            data: progressInfo
                        });
                    }
                };

                transcriber = await pipeline('automatic-speech-recognition', modelId, modelOptions);

                currentModelId = modelId;
                currentDevice = targetDevice;
                currentMirror = mirror;
            }

            self.postMessage({
                type: 'status',
                data: { phase: 'transcribing', message: '正在解码音频与提取精准时间戳...' }
            });

            // Start transcription with Simplified Chinese prompt guidance
            const startTime = performance.now();
            const result = await transcriber(audioData, {
                chunk_length_s: 30,
                stride_length_s: 5,
                return_timestamps: true,
                language: language && language !== 'auto' ? language : undefined,
                initial_prompt: language === 'chinese' ? "以下是普通话的简体中文句子，请输出规范简体字。" : undefined,
                task: 'transcribe',
            });
            const durationSec = ((performance.now() - startTime) / 1000).toFixed(2);

            self.postMessage({
                type: 'complete',
                data: {
                    chunks: result.chunks || [],
                    fullText: result.text || '',
                    durationSec: durationSec,
                    deviceUsed: currentDevice
                }
            });

        } catch (err) {
            console.error("Worker transcription error:", err);
            self.postMessage({
                type: 'error',
                data: { 
                    message: err.message || 'Transcription failed'
                }
            });
        }
    }
};
