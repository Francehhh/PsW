# PsW - Password Manager 🚀🔐

![status](https://img.shields.io/badge/status-prerelease-yellow) ![version](https://img.shields.io/badge/version-v1.4.3--alpha-blue)

> **Pre-release v1.4.3 alpha**
>
> ⚠️ This version is a *prerelease* intended for testing and feedback. There may be bugs, incomplete features, or frequent changes. Use with caution and report any issues via [Issue](https://github.com/Francehhh/PsW/issues).

---

## ✨ Main Features

- 🔒 **End-to-End Encryption** (AES-256)
- 👤 **Multiple Profile Management**
- ☁️ **Cloud Synchronization** (Google Drive)
- 🖥️ **Modern Interface** (PySide6)
- 🛡️ **Master Password Protection** (Argon2)
- 💻 **Cross-platform**: Windows, Linux, macOS
- 🧩 **Extensible** and easy to customize
- 🏷️ **Tags and categories** to organize credentials
- ⚡ **Global shortcuts** for quick access
- 🧪 **Prerelease**: new features in testing!

---

## 🚀 How to Use PsW

### 🐍 Method 1: Run from Source (Python)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Francehhh/PsW.git
   cd PsW
   ```
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Start the application:**
   ```bash
   python main.py
   ```

> 👨‍💻 *Recommended for developers or those who want to customize the code.*

---

### 🖱️ Method 2: Run from Executable (.exe)

1. **Download the files from the repository** (or from the `dist/` folder if already built)
2. **Run directly:**
   - On Windows: double-click `PsW.exe`
   - No need to have Python installed!

> 🟢 *The executable includes all dependencies and the custom icon.*

---

## 🗂️ Project Structure

```text
PsW/
├── src/                # Source code (core, ui, utils)
├── tests/              # Unit tests
├── dist/               # Generated executables (.exe)
├── build/              # Temporary build files
├── main.py             # Entry point
├── PsW.ico             # Application icon
├── requirements.txt    # Python dependencies
├── setup.py            # Setup script
├── VERSION             # App version
├── LICENSE             # License
├── README.md           # This file
├── .gitignore          # Git ignored files
├── PsWLayout.md        # UI layout (git ignored)
├── descrizione.md      # Technical description
├── progress.md         # Development notes
└── ...
```

---

## 🔐 Security

- 🔑 AES-256 encryption
- 🧬 Argon2 key derivation
- 🚫 No default passwords
- 🛡️ Strict input validation
- 🕵️ Regular code audit

---

## 🤝 Contributing

1. Fork the repository
2. Create a branch (`git checkout -b feature/name`)
3. Commit (`git commit -am 'Add feature'`)
4. Push (`git push origin feature/name`)
5. Create a Pull Request

---

## 📜 License

MIT License - see [LICENSE](LICENSE)

---

## 💬 Support & Contacts

- [Open an Issue on GitHub](https://github.com/Francehhh/PsW/issues)
- [Technical documentation](descrizione.md)

---

## 🙏 Acknowledgements

- PySide6 (Qt for Python)
- cryptography
- Google Drive API

---

> Powered by ❤️ Open Source. Developed by [Francehhh](https://github.com/Francehhh/PsW)
