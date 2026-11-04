# Qwen3-1.7B model assets

The base model is stored as GitHub Release assets rather than Git blobs. The
largest original safetensors shard is over 2 GiB, while GitHub limits an
individual release asset to less than 2 GiB. The release therefore contains
the model directory as a tar archive split into ordered parts.

The files are the Qwen/Qwen3-1.7B model and tokenizer at revision
`70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`. The model's original license is
included in the archive.

Download and restore the model from the repository root with GitHub CLI:

```sh
gh release download cendrix-qwen3-1.7b \
  --repo bikash-20/bikash-ai-lora \
  --dir /tmp/cendrix-model-assets
cat /tmp/cendrix-model-assets/cendrix-qwen3-1.7b.tar.part-* \
  > /tmp/cendrix-qwen3-1.7b.tar
tar -xf /tmp/cendrix-qwen3-1.7b.tar
```

The restored files are placed under `models/base/Qwen3-1.7B/`. Do not commit
the restored weights into Git; this repository ignores local model files.
