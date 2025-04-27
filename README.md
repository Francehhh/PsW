<<<<<<< HEAD
# PsW - Password Manager 🚀🔐

![status](https://img.shields.io/badge/status-prerelease-yellow) ![version](https://img.shields.io/badge/version-v1.4.3--alpha-blue)

> **Prerilascio v1.4.3 alpha**
> 
> ⚠️ Questa versione è una *prerelease* destinata a test e feedback. Potrebbero esserci bug, funzionalità incomplete o modifiche frequenti. Usare con cautela e segnalare eventuali problemi tramite [Issue](https://github.com/Francehhh/PsW/issues).

---

## ✨ Caratteristiche Principali

- 🔒 **Crittografia End-to-End** (AES-256)
- 👤 **Gestione Profili** multipli
- ☁️ **Sincronizzazione Cloud** (Google Drive)
- 🖥️ **Interfaccia Moderna** (PySide6)
- 🛡️ **Protezione Master Password** (Argon2)
- 💻 **Multi-piattaforma**: Windows, Linux, macOS
- 🧩 **Estendibile** e facile da personalizzare
- 🏷️ **Tag e categorie** per organizzare le credenziali
- ⚡ **Shortcut globali** per accesso rapido
- 🧪 **Prerilascio**: nuove feature in test!

---

## 🚀 Come Usare PsW

### 🐍 Metodo 1: Avvio da Sorgente (Python)

1. **Clona il repository:**
   ```bash
   git clone https://github.com/Francehhh/PsW.git
   cd PsW
   ```
2. **Installa le dipendenze:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Avvia l'applicazione:**
   ```bash
   python main.py
   ```

> 👨‍💻 *Consigliato per sviluppatori o chi vuole personalizzare il codice.*

---

### 🖱️ Metodo 2: Avvio da Eseguibile (.exe)

1. **Scarica i file dalla repository** (o dalla cartella `dist/` se già buildato)
2. **Esegui direttamente:**
   - Su Windows: doppio click su `PsW.exe`
   - Non serve Python installato!

> 🟢 *L'eseguibile include tutte le dipendenze e l'icona personalizzata.*

---

## 🗂️ Struttura del Progetto

```text
PsW/
├── src/                # Codice sorgente (core, ui, utils)
├── tests/              # Test unitari
├── dist/               # Eseguibili generati (.exe)
├── build/              # File temporanei di build
├── main.py             # Entry point
├── PsW.ico             # Icona applicazione
├── requirements.txt    # Dipendenze Python
├── setup.py            # Script di setup
├── VERSION             # Versione app
├── LICENSE             # Licenza
├── README.md           # Questo file
├── .gitignore          # File ignorati da git
├── PsWLayout.md        # Layout UI (ignorato da git)
├── descrizione.md      # Descrizione tecnica
├── progress.md         # Note di sviluppo
└── ...
```

---

## 🔐 Sicurezza

- 🔑 Crittografia AES-256
- 🧬 Key derivation Argon2
- 🚫 Nessuna password di default
- 🛡️ Validazione input rigorosa
- 🕵️ Audit regolare del codice

---

## 🤝 Contribuire

1. Fai un fork del repository
2. Crea un branch (`git checkout -b feature/nome`)
3. Committa (`git commit -am 'Aggiungi feature'`)
4. Pusha (`git push origin feature/nome`)
5. Crea una Pull Request

---

## 📜 Licenza

MIT License - vedi [LICENSE](LICENSE)

---

## 💬 Supporto & Contatti

- [Apri una Issue su GitHub](https://github.com/Francehhh/PsW/issues)
- [Documentazione tecnica](descrizione.md)

---

## 🙏 Ringraziamenti

- PySide6 (Qt for Python)
- cryptography
- Google Drive API

---

> Powered by ❤️ Open Source. Sviluppato da [Francehhh](https://github.com/Francehhh/PsW) 
=======
# PsW - Password Manager (Alpha 1.3.0)

## 🔨 Work In Progress (more feature incoming)

🔐 A modern, secure, and easy-to-use password manager.

## Key Features

- **End-to-End Encryption**: Data protection with AES-256
- **Profile Management**: Organize your credentials in separate profiles
- **Cloud Synchronization**: Secure backup on Google Drive
- **Modern Interface**: Clean and intuitive design
- **Advanced Security**: Master password protection with Argon2
- **Cross-Platform**: Support for Windows, Linux, and macOS

## Installation

### Prerequisites
- Python 3.8+
- pip

### Steps
1. Clone the repository:
   ```bash
   git clone [https://github.com/Francehhh/PsW.git](https://github.com/Francehhh/PsW.git)
   cd PsW
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python main.py
   ```

## Usage

1. Upon first launch, create a secure master password
2. Use the master password to access the application
3. Create profiles to organize your credentials
4. Add and manage credentials within profiles


## Security

- AES-256 encryption for data
- Key derivation with Argon2
- No default passwords
- Strict input validation
- Regular code audit

## Contributing

1. Fork the repository
2. Create a branch for your feature (`git checkout -b feature/name`)
3. Commit your changes (`git commit -am 'Add feature'`)
4. Push to the branch (`git push origin feature/name`)
5. Create a Pull Request

## License

MIT License - see [LICENSE](LICENSE) for details.

## Specifications

- PySide6 for the GUI
- cryptography for encryption
- Google Drive API for synchronization
>>>>>>> 968c5a70e7627a248501224c259899cd57183c8e
