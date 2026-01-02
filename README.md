# Integrazione CUPRA per HACS

Integrazione HACS per gestire i veicoli CUPRA in Home Assistant. Il progetto
include un client asincrono per l'API CUPRA e un flusso di configurazione che
permette l'autenticazione, la selezione del veicolo e l'esposizione di sensori
per dati principali (batteria, autonomia, chilometraggio, stato ricarica).

## Installazione

1. Copia la cartella `custom_components/cupra` dentro la cartella
   `custom_components` della tua installazione Home Assistant.
2. Riavvia Home Assistant.
3. Aggiungi l'integrazione **CUPRA** da **Impostazioni → Dispositivi e Servizi**.

> Suggerimento HACS: aggiungi questo repository come _Custom Repository_ (tipo
> integrazione) per ricevere aggiornamenti automatici.

## Configurazione

- **Email e password**: le stesse usate nell'app _My CUPRA_.
- **Regione**: scegli dalla lista di regioni supportate (es. `eu`, `na`, `apac`).
- Durante il primo setup il flusso propone i veicoli CUPRA disponibili e
  permette di scegliere quello da associare a Home Assistant.
- Nelle opzioni puoi modificare l'intervallo di aggiornamento (in secondi, min 60).

### Entità esposte

- Stato batteria (%)
- Autonomia residua (km)
- Chilometraggio (km)
- Stato ricarica (stringa fornita dall'API)
- Ultimo aggiornamento (timestamp)

## Note sull'API

L'integrazione usa gli endpoint CARIAD/VW Group: `https://identity.vwgroup.io`
per l'autenticazione e `https://emea.bff.cariad.digital` per i dati veicolo.
Alcuni mercati potrebbero usare host o payload differenti. Puoi adattare il
client in `custom_components/cupra/api.py` regolando `api_base`, `auth_base` o
gli scope richiesti in `async_login`.
