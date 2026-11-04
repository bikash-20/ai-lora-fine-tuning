# Bikash-AI

Bikash-AI is a local-first Bengali, English, and Banglish assistant. Its model, runtime, identity configuration, local memory, document retrieval, and tools are kept as separate components.

## Dataset preparation

The dataset pipeline uses only the Python standard library:

```sh
python3 training/prepare_dataset.py
python3 training/validate_dataset.py
python3 -m unittest discover -s tests -v
```

See [dataset preparation and review](docs/dataset.md). Model downloads, tokenizer downloads, fine-tuning, and baseline benchmarks are intentionally deferred until explicit approval.
