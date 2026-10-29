# CLAUDE.md - Anti-AI-Slop Directives for Claude

## Visual & UI Rules
- Do NOT use purple/pink gradients, neon shadows, or glassmorphism.
- Use solid neutral backgrounds (`bg-zinc-900`, `bg-zinc-950`) with sharp 1px borders (`border-zinc-800`).
- Use compact padding and tight radii: `rounded-lg` (8px) for inputs/buttons, `rounded-xl` (12px) for cards.
- Do NOT use emojis (🚀, ✨, 🤖, 💡) in titles, headers, or buttons. Use monochrome SVG icons.

## UX & Interaction Rules
- Do NOT display raw file names (e.g. `encoder_model.onnx`) to end users. Translate to human operational stages.
- Progress bars MUST be globally aggregated and strictly monotonic (never jump backwards during concurrent downloads).
- Always synchronize UI state on lifecycle completion (never leave stale storage indicators).
- Intercept errors; do NOT dump raw stack traces or protobuf errors into alerts.

## Copywriting Rules
- Strip fluff words: "赋能", "颠覆", "无恶心水印", "无需充值会员", "开启全新时代".
- Speak like a senior staff engineer: terse, calm, confident, and factual.

## Architecture Rules
- Use multi-threaded or async concurrency by default (never blocking single-threaded TCPServer).
- Deduplicate storage: single unified model pool keyed by canonical artifact ID, never split by mirror.
- Byte-level integrity check before renaming streaming `.tmp` files.
- Automatically normalize dialect/traditional text (e.g. OpenCC) for simplified Chinese audiences.
