# TOXAPP

### Cos'è TOXAPP
TOXAPP è uno strumento dinamico ed efficiente progettato per estrarre valori tossicologici, in particolare NOAEL (No Observed Adverse Effect Level) e LD50 (Lethal Dose 50%), per gli ingredienti presenti nei prodotti cosmetici.

##### CARTELLA APP
Comprende tutto il progetto

Link al sito : toxapp.streamlit.app

### Richiesta del committente
Il committente Livio Marossi, direttore dell’azienda 
”LMB Laboratorio Microbiologico Biotecnologie ”, ci ha richiesto un tool veloce e dinamico in grado di ricavare i seguenti valori tossicologici: NOAEL e LD50 relativi a degli ingredienti presenti nei prodotti cosmetici. 

### Qual’è il problema?
Il committente del progetto incontra notevoli difficoltà nella ricerca dei valori tossicologici necessari per l'approvazione dei cosmetici sul sito CIR. 
Attualmente, ogni ingrediente richiede diversi minuti per ottenere i valori di NOAEL (No Observed Adverse Effect Level) e LD50 (Lethal Dose 50%), rendendo il processo lungo e inefficiente. 
Questa lentezza rappresenta un ostacolo nella valutazione rapida e accurata dei prodotti, evidenziando la necessità di un sistema che possa velocizzare significativamente la ricerca di tali valori tossicologici.

### Il nostro approccio al problema 
Abbiamo deciso di approcciare il problema creando un tool efficace e intuitivo, affidandoci al linguaggio di programmazione Python per creare gli algoritmi per le varie funzionalità del nostro sito web, che abbiamo creato utilizzando la libreria streamlit. 
Il nostro approccio era quello di fornire dati e funzionalità il più chiare ed esaustive possibili. 

### Siti utilizzati per la funzioni del sito:
- CIR
- ECHA
- PubChem
- EFSA OpenFoodTox
- Cosmile Europe

### Database creato personalmente:
ingredients.db 

##### Struttura db
- Table: ingredients
  - Column: pcpc_ingredientid - Type: TEXT
  - Column: pcpc_ingredientname - Type: TEXT
  - Column: NOAEL_CIR - Type: TEXT
  - Column: LD50_CIR - Type: TEXT
  - Column: LD50_PubChem - Type: TEXT
  - Column: value_updated - Type: TEXT
  - Column: cir_page - Type: TEXT
  - Column: cir_pdf - Type: TEXT
  - Column: pubchem_page - Type: TEXT
  - Column: echa_value - Type: TEXT
  - Column: echa_dossier - Type: TEXT
  - Column: EFSA_value - Type: TEXT
  - Column: cosmile_page - Type: TEXT
- Table: cosmetics
  - Column: id - Type: INTEGER
  - Column: cosmetic_name - Type: TEXT
  - Column: company_name - Type: TEXT
  - Column: ingredients - Type: TEXT
  - Column: toxic - Type: TEXT
- Table: sqlite_sequence
  - Column: name - Type:
  - Column: seq - Type:


### File presenti nella repository

PS
Alcuni file è possibile che sono stati eliminati e di conseguenza non si vedono tutti i tentativi effettuati per la ricerca dei valori e delle informazioni per i vari ingredienti. Purtroppo per creare una repositoty che avesse un senso e fosse facilemente interpretabile sono andati persi.
Potrebbero esserci dele funzioni che non sono utilizzate ma servivano in versioni precedenti del progetto, queste sono state sostituite con nuove funzioni per il corretto funzionamento del sito.

La cartella save è stata usata per fare i salvataggi del progetto

### Requirements.txt

In questo file ci sono tutte le librerie necessarie per il sito.
pytesseract ha bisogno anche di un'installazione dal sito ufficiale per l'estrapolazione del testo dalle immagini (funzione che si trova in Other_Functions)

Fumagalli & Indryas
