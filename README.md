# envault

> Lightweight local secrets manager that encrypts `.env` files with a master passphrase.

---

## Installation

```bash
pip install envault
```

Or with [pipx](https://pypa.github.io/pipx/) for isolated CLI usage:

```bash
pipx install envault
```

---

## Usage

**Lock (encrypt) your `.env` file:**

```bash
envault lock .env
# Enter master passphrase: ••••••••
# ✔ Encrypted → .env.vault
```

**Unlock (decrypt) when you need it:**

```bash
envault unlock .env.vault
# Enter master passphrase: ••••••••
# ✔ Decrypted → .env
```

**Load secrets directly into a subprocess without writing to disk:**

```bash
envault run .env.vault -- python app.py
```

Envault uses AES-256-GCM encryption with a key derived from your passphrase via Argon2id — no plaintext secrets are ever stored or transmitted.

---

## Why envault?

- 🔒 Strong encryption out of the box
- 🪶 Zero config, no server, no cloud
- 📦 Single dependency footprint
- 🔁 Drop-in replacement for plain `.env` workflows

---

## Contributing

Pull requests are welcome. Please open an issue first to discuss any significant changes.

---

## License

[MIT](LICENSE) © 2024 envault contributors