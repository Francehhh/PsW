# PsW - Password Manager

🔐 Un moderno gestore di password sicuro e facile da usare.

## Caratteristiche Principali

- **Crittografia End-to-End**: Protezione dei dati con AES-256
- **Gestione Profili**: Organizza le tue credenziali in profili separati
- **Sincronizzazione Cloud**: Backup sicuro su Google Drive
- **Interfaccia Moderna**: Design pulito e intuitivo
- **Sicurezza Avanzata**: Protezione master password con Argon2
- **Multi-piattaforma**: Supporto per Windows, Linux e macOS

## Installazione

### Prerequisiti
- Python 3.8+
- pip

### Passi
1. Clona il repository:
   ```bash
   git clone https://github.com/Francehhh/PsW.git
   cd PsW
   ```

2. Installa le dipendenze:
   ```bash
   pip install -r requirements.txt
   ```

3. Avvia l'applicazione:
   ```bash
   python main.py
   ```

## Utilizzo

1. Al primo avvio, crea una master password sicura
2. Usa la master password per accedere all'applicazione
3. Crea profili per organizzare le tue credenziali
4. Aggiungi e gestisci le credenziali all'interno dei profili

## Struttura del Progetto

```
PsW/
├── src/
│   ├── core/         # Logica di business
│   ├── ui/           # Interfaccia utente
│   └── utils/        # Utilità e helper
├── data/             # Storage dati (crittografato)
├── tests/            # Test unitari
└── docs/             # Documentazione
```

## Sicurezza

- Crittografia AES-256 per i dati
- Key derivation con Argon2
- Nessuna password di default
- Validazione input rigorosa
- Audit regolare del codice

## Contribuire

1. Fai un fork del repository
2. Crea un branch per la tua feature (`git checkout -b feature/nome`)
3. Committa i tuoi cambiamenti (`git commit -am 'Aggiungi feature'`)
4. Pusha al branch (`git push origin feature/nome`)
5. Crea una Pull Request

## Licenza

MIT License - vedi [LICENSE](LICENSE) per i dettagli.

## Supporto

- Discord: [Entra nel server](https://discord.gg/psw)
- Documentazione: [Leggi la docs](https://psw.readthedocs.io)

## Ringraziamenti

- PySide6 per l'interfaccia grafica
- cryptography per la crittografia
- Google Drive API per la sincronizzazione 