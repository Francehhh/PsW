# PsW - Password Manager Sicuro 🔒

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Version](https://img.shields.io/badge/version-Alpha%201.2.1-orange)
![Build](https://img.shields.io/badge/build-passing-brightgreen)

<div align="center">
  <img src="assets/logo.png" alt="PsW Logo" width="200"/>
  <h3>La sicurezza delle tue credenziali, semplificata.</h3>
</div>

## 🌟 Caratteristiche Principali

- **🔐 Crittografia End-to-End**: Tutte le tue credenziali sono protette con AES-256
- **👤 Gestione Profili**: Organizza le tue credenziali in profili separati
- **☁️ Sincronizzazione Cloud**: Backup sicuro su Google Drive
- **🎨 Interfaccia Moderna**: Design intuitivo e user-friendly
- **🛡️ Sicurezza Avanzata**: Protezione master password e autenticazione a due fattori
- **📱 Multi-Device**: Accedi alle tue credenziali da qualsiasi dispositivo

## 🚀 Installazione

### Prerequisiti
- Python 3.8+
- pip

### Passaggi
1. Clona il repository
```bash
git clone https://github.com/Francehhh/PsW.git
cd PsW
```

2. Installa le dipendenze
```bash
pip install -r requirements.txt
```

3. Avvia l'applicazione
```bash
python main.py
```

## 💻 Utilizzo

1. Al primo avvio, crea una master password sicura
2. Crea uno o più profili per organizzare le tue credenziali
3. Aggiungi le tue credenziali nei profili
4. Usa le funzioni di ricerca e filtro per gestire facilmente le tue password

## 📁 Struttura del Progetto

```
PsW/
├── src/
│   ├── ui/           # Interfaccia utente
│   ├── utils/        # Utilità e helper
│   └── core/         # Logica core
├── data/            # Dati (crittografati)
├── tests/          # Test unitari
└── docs/           # Documentazione
```

## 🔒 Sicurezza

- Crittografia AES-256 per tutte le credenziali
- Nessun dato sensibile salvato in chiaro
- Audit regolari del codice
- Protezione contro attacchi comuni

## 🤝 Contribuire

Le contribuzioni sono benvenute! Per favore:

1. Fai un fork del progetto
2. Crea un branch per la tua feature (`git checkout -b feature/AmazingFeature`)
3. Committa i tuoi cambiamenti (`git commit -m 'Add some AmazingFeature'`)
4. Pusha sul branch (`git push origin feature/AmazingFeature`)
5. Apri una Pull Request

## 📝 Licenza

Distribuito sotto licenza MIT. Vedi `LICENSE` per maggiori informazioni.

## 📞 Supporto

- Discord: [Entra nel server](https://discord.gg/psw)
- Documentazione: [Leggi la docs](https://psw.readthedocs.io)
- Issues: [Apri un issue](https://github.com/Francehhh/PsW/issues)

## 🙏 Ringraziamenti

- PySide6 per l'interfaccia grafica
- cryptography per la crittografia
- Google Drive API per la sincronizzazione
- Tutti i contributori che hanno reso possibile questo progetto 