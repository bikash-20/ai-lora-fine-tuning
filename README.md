# Cendrix AI

Cendrix AI is a personal AI assistant that runs fully on your own computer. After the first setup, it does not need the internet. Your chats stay on your device.

> Cendrix AI was first called **Bikash-AI**. Some older files, tests, and datasets still use the old name. They are kept on purpose and not deleted.

## What version 1.0 can do

Version 1.0 is **English-first**. It is built to:

- Chat in simple, easy-to-understand English.
- Explain code and help with coding questions.
- Solve basic maths problems.
- Remember the conversation while you chat, and save old chats on your device.
- Tell you who made it, in English, Bengali, and Banglish. The creator is **Bikash Talukder**.
- Work without an internet connection after setup.

Bengali and Banglish conversation is **not** a goal of version 1.0. Natural Bengali chat, Bengali reasoning, and Bengali coding help are planned for version 2.0. The creator answer is the only Bengali and Banglish feature that is promised now.

## How it works (the simple version)

- **The model** is Qwen3-1.7B, a small language model. "Language model" means a program that has learned to write text by reading a huge amount of text. We run it with **MLX**, a tool from Apple that runs models fast on Apple Silicon Macs (M1, M2, M3, M4).
- **The app** is a small Python program. It loads the model, sends your messages to it, and shows the answers on a web page.
- **The chat page** opens in your browser at `http://127.0.0.1:8765`. The address `127.0.0.1` means "this computer only", so other devices cannot reach it.
- **The page is a PWA.** A PWA (Progressive Web App) is a web page that can be installed like an app. Remember that the model still runs in the Python program, so the program must be running for the chat to answer.
- **Chat history** is saved in a small database on your computer (SQLite). Nothing is sent to the internet.

## Who made Cendrix AI? (identity)

The creator's facts are kept in `configs/identity.json`, separate from the model. This means you can change a fact there without training the model again.

Tests showed that the small model alone often answered creator questions wrongly, especially in Bengali and Banglish. So the app also has a simple **fallback**: when a message asks who created or developed the assistant, the app gives a fixed answer built from `identity.json`. All other messages are answered by the model.

## What you need

- A Mac with Apple Silicon (MLX needs it).
- Python 3.12, installed in the project's `.venv` folder. The `mlx-lm` package (version 0.32.2) is installed there too.
- The Qwen3-1.7B model files, kept in the `models/` folder. This folder is ignored by Git because the files are large.
- About 4 GB of free memory while the model is running.

## How to start the app

1. Open the **Terminal** app on your Mac.
2. Go to the project folder and start the app:

   ```sh
   cd path/to/assistant
   PYTHONPATH=. .venv/bin/python -m app.run
   ```

3. Wait a few seconds while the model loads, until the Terminal shows the address.
4. Open `http://127.0.0.1:8765` in your browser.

**Keep the Terminal window open while you chat.** To stop the app, click the Terminal window and press `Ctrl + C`.

## If something goes wrong

- **"Failed to fetch" in the chat:** The app is not running. Start it again with the command above, then refresh the page with `Cmd + Shift + R`.
- **The page does not open:** Check that the Terminal is still running the app and that you typed the address exactly.
- **An error appears in the Terminal:** Read the last lines. They usually say what is missing, such as the model folder. Fix that and start again.

## Speed and memory (measured)

These numbers were measured on a MacBook Air M4 with 16 GB of memory, using the full-size (BF16) model:

- Load time: about 2.2 seconds.
- Speed: about 25 tokens per second. A token is a small piece of a word.
- Peak memory: about 3.7 GB.

A smaller 4-bit version of the model may use less memory. It has not been tested yet. See [Cendrix v1 notes](docs/cendrix-v1.md) and [baseline report](docs/baseline.md) for details.

## Safety

- The model's answers are shown only as text. The app never runs commands that the model writes.
- The model cannot read or change files on your computer.
- Text from documents is treated as untrusted data, not as instructions.
- The app listens only on your own computer.

## Project folders

| Folder | What is inside |
|---|---|
| `app/` | The application: model loading, chat server, chat page, chat history, security checks |
| `configs/` | Settings, including `identity.json` |
| `data/` | Training, validation, and evaluation datasets (kept for future work) |
| `docs/` | Notes and reports |
| `experiments/` | Recorded test runs and their results |
| `models/` | Model files (not stored in Git) |
| `storage/` | Saved chat history on your computer |
| `tests/` | Automatic tests |
| `training/` | Scripts that prepare and check the datasets |

## Dataset preparation (for future training)

Version 1.0 does **not** use fine-tuning. Fine-tuning means teaching a model more with your own examples. The dataset tools are kept for version 2.0, when better Bengali and Banglish will be added. These tools use only the Python standard library:

```sh
python3 training/prepare_dataset.py
python3 training/validate_dataset.py
python3 -m unittest discover -s tests -v
```

See [dataset preparation and review](docs/dataset.md). Model downloads, fine-tuning, and freezing the evaluation set need the owner's approval first.

## Running all tests

```sh
PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -v
```

## Roadmap

- **v1.0:** English-first offline assistant with a simple chat page, saved chats, and correct creator identity in three languages.
- **v2.0:** Natural Bengali and Banglish conversation, Bengali reasoning, and Bengali coding explanations.
