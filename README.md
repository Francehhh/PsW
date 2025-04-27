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