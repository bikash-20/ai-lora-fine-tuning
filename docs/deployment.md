# Deployment and export plan (not started)

No export or quantization has been run. GGUF `Q4_K_M` and MLX 4-bit are distinct formats and runtimes; evaluate them separately against the original base and any approved fine-tuned model. Record output validity, quality regression, peak memory, load time, and generation speed for each runtime. Do not copy model weights into Git.

Mobile deployment requires a platform-specific runtime and compatibility test; an exported file alone does not guarantee that a model runs on every device.
