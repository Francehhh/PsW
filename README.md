# PsW - Password Manager 🚀🔐

![status](https://img.shields.io/badge/status-alpha-red) ![version](https://img.shields.io/badge/version-v2.0.0--alpha-orange)

> **Version Alfa 2.0.0**
>
> ⚠️ This is an **alpha** version intended for development, testing, and feedback. Expect bugs, incomplete features, and potentially breaking changes. Use with caution and report any issues via [Issues](https://github.com/Francehh/PsW/issues).

---

## ✨ Main Features

- 🔒 **Local Encryption** (AES-256 via Fernet)
- 🔑 **Robust Master Password Protection** (PBKDF2-HMAC-SHA256)
- 👤 **Multiple Profile Management**
- 🗄️ **SQLite Database Backend** (replaces JSON files)
- 🖥️ **Modernized Interface** (PySide6 with custom styling and animations)
- 🖱️ **Quick Credential Access** via Global Hotkey (basic implementation)
- ☁️ **Cloud Synchronization** (Google Drive - *basic setup, sync logic pending*)
- 🛡️ **Secure Credential Storage**
- 💻 **Cross-platform**: Windows, Linux, macOS (Linux/macOS less tested)
- 🏷️ **Basic Credential Organization**
- ⚡ **Password Generation**
- ❗️ **some features are not yet available, with the next updates PsW will allow users to use them all!**

---

## 🚀 Getting Started

### 🐍 Option 1: Run from Source (Recommended for Dev/Testing)

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Francehh/PsW.git
    cd PsW
    ```
2.  **Create a virtual environment (Recommended):**
    ```bash
    python -m venv .venv
    # Activate it:
    # Windows:
    .venv\Scripts\activate
    # Linux/macOS:
    # source .venv/bin/activate 
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Run the application:**
    ```bash
    python main.py
    ```

### 🏗️ Option 2: Build the Executable (Using PyInstaller)

1.  **Ensure prerequisites are met:**
    *   Python installed.
    *   Repository cloned and dependencies installed (see Option 1).
    *   PyInstaller installed: `pip install pyinstaller`
2.  **Navigate to the project root directory** (where `main.py` is).
3.  **Run PyInstaller:**
    ```bash
    pyinstaller --noconsole --onefile --windowed --icon=src/ui/icons/icon.ico main.py 
    ```
    *   `--noconsole` or `--windowed`: Prevents the command prompt from showing when the app runs.
    *   `--onefile`: Packages everything into a single `.exe` file.
    *   `--icon`: Specifies the application icon (adjust path if needed).
4.  **Find the executable:** The generated `.exe` file will be inside the `dist` folder.
5.  **Run:** Double-click the `.exe` file in the `dist` folder to run the application.

---

## 🗂️ Project Structure (Simplified)

```text
PsW/
├── src/                # Source code (core, ui, utils)
│   ├── core/           # Core logic (managers, data classes)
│   ├── ui/             # User interface (widgets, dialogs, icons)
│   └── utils/          # Utility functions (crypto, sync)
├── data/               # Application data (database - *ignored by git*)
├── tests/              # Unit tests (*structure pending*)
├── main.py             # Application entry point
├── requirements.txt    # Python dependencies
├── README.md           # This file
├── progress.md         # Development progress tracker
├── LICENSE             # License
└── .gitignore          # Git ignored files
```

---

## 🔐 Security Overview

- 🔑 **Master Key Derivation:** PBKDF2-HMAC-SHA256 with high iterations and unique salt.
- 🔒 **Data Encryption:** AES-128-GCM via Fernet for sensitive fields in the database.
- 💾 **Storage:** SQLite database (`data/pswcursor_data.db`) stores application data. Sensitive fields are encrypted.

---

## 🤝 Contributing

1.  Fork the repository
2.  Create a branch (`git checkout -b feature/your-feature`)
3.  Commit your changes (`git commit -am 'Add some feature'`)
4.  Push to the branch (`git push origin feature/your-feature`)
5.  Create a new Pull Request

---

## 📜 License

MIT License - see [LICENSE](LICENSE)

---

## 💬 Support & Contacts

- [Open an Issue on GitHub](https://github.com/Francehh/PsW/issues)

---

> Developed by [Francehh](https://github.com/Francehh)
