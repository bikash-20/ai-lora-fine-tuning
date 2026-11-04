# Deployment and export status

The local Cendrix PWA runs at `127.0.0.1:8765` with MLX-LM and the existing local Qwen3 model. It is designed to work offline after the model is present locally; follow [the v1 deployment and offline test guide](./cendrix-v1.md#run-locally). No Hugging Face service has been deployed.

No export or quantization has been run. GGUF `Q4_K_M` and MLX 4-bit are distinct formats and runtimes; evaluate them separately against the original base and any approved fine-tuned model. Record output validity, quality regression, peak memory, load time, and generation speed for each runtime. Do not copy model weights into Git.

Mobile deployment requires a platform-specific runtime and compatibility test; an exported file alone does not guarantee that a model runs on every device. No model conversion or fine-tuning was started.
