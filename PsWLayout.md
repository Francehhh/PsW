# Layout Password Manager

## Struttura Principale
```
+------------------------------------------+
|              Top Menu Bar                 |
| File                              Aiuto   |
+------------------------------------------+
|            Navigation Bar                 |
| Dashboard | Profili | Impostazioni       |
+------------------------------------------+
|                                          |
|             Main Content                 |
|                                          |
+------------------------------------------+
```

## Sezioni Dettagliate

### 1. Dashboard
- Statistiche generali
- Ultimi accessi
- Stato sincronizzazione
- Avvisi di sicurezza

### 2. Profili
```
+------------------------------------------+
|  ← Indietro                              |
+------------------------------------------+
|                                          |
|    +-------------+    +-------------+    |
|    |  Profilo 1  |    |  Profilo 2  |    |
|    |             |    |             |    |
|    +-------------+    +-------------+    |
|                                          |
|    +-------------+    +-------------+    |
|    |  Profilo 3  |    |  Profilo 4  |    |
|    |             |    |             |    |
|    +-------------+    +-------------+    |
|                                          |
+------------------------------------------+
```

#### Vista Credenziali (dopo doppio click su profilo)
```
+------------------+----------------------+
|  ← Indietro     |                      |
+------------------+----------------------+
| [Nuova][Elimina]|                      |
+------------------+                      |
| Nome Profilo    |    Dettagli          |
| +------------+  |    Credenziale       |
| |□ Cred. 1   |  |                      |
| |  [Copia]   |  |    Nome App:         |
| +------------+  |    Username:          |
| |□ Cred. 2   |  |    Password:         |
| |  [Copia]   |  |    URL:              |
| +------------+  |    Note:              |
| |□ Cred. 3   |  |                      |
| |  [Copia]   |  |    [Salva][Annulla]  |
| +------------+  |                      |
+------------------+----------------------+
```

### 3. Impostazioni
- Preferenze applicazione
- Gestione backup
- Sincronizzazione cloud
- Temi e personalizzazione

## Modali e Popup

### Dialog Autenticazione
```
+-------------------------+
|    Accedi              |
|                        |
| Master Password: [   ] |
|                        |
| [Accedi]    [Annulla] |
+-------------------------+
```

### Dialog Registrazione
```
+-------------------------+
|    Nuovo Account       |
|                        |
| Master Password: [   ] |
| Conferma:       [   ] |
|                        |
| [Registra]   [Annulla]|
+-------------------------+
```

### Dialog Nuova Credenziale
```
+-------------------------+
|   Nuova Credenziale    |
|                        |
| Nome App:    [      ] |
| Username:    [      ] |
| Password:    [      ] |
| URL:         [      ] |
| Note:        [      ] |
|                        |
| [Salva]     [Annulla] |
+-------------------------+
```

## Navigazione e Interazione

### Mouse
- Click singolo: seleziona elemento
- Doppio click su profilo: apre vista credenziali
- Click su checkbox: seleziona credenziale per eliminazione
- Click su [Copia]: copia password negli appunti
- Click su credenziale: mostra dettagli a destra

### Tastiera
- Enter: conferma azione
- Esc: annulla/chiudi
- Tab: navigazione campi
- Ctrl+N: nuova credenziale
- Ctrl+S: salva modifiche

### Touch
- Tap singolo: seleziona elemento
- Tap doppio: apre vista credenziali
- Tap lungo: mostra menu contestuale
- Swipe: navigazione liste 