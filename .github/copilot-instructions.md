# Regole di Contesto e Sviluppo per Copilot: Progetto ExaAiCore

# Rispondi sempre in lingua Italiana alle mie domande!
* Quando ti chiedo qualcosa a cui devi rispondere, rispondi sempre in lingua Italiana

## 0. Per risparmiare token non analizzare mai i file contenuti in cartelle .venv, .git, .vscode, .idea, __pycache__, build, dist, logs, tmp e simili.
* Anche se te lo chiedo non analizzare mai queste folder o file contenuti in esse! Non rilevarle nemmeno se te lo chiedo.

## 1. Contesto del Progetto
ExaAiCore è un architettura modulare progettata per distribuire e gestire ambienti Python isolati chiamati microservizi
per gli addon di Blender come HDRi Maker. L obiettivo primario è eseguire framework AI pesanti come PyTorch e Diffusers
in un processo totalmente separato. Questo approccio previene i conflitti di dipendenze con l interprete Python nativo
di Blender ed evita il blocco o il crash dell interfaccia utente.
.
## 2. Architettura di Riferimento
* Magazzino Remoto: Repository GitHub che ospita file ZIP contenenti motori Python standalone per Windows, macOS e Linux,
* accompagnati da un file exa_manifest.json che mappa gli URL di download diretto. Bootstrapper Locale cartella
* exa_service_builder: Modulo integrato nell addon di Blender. Contiene un file di configurazione service_config.json,
* uno script Python puro installer.py per la logica di rete ed estrazione, e un interfaccia Blender installer_ops.py per
* l interazione con l utente. Microservizio Worker: Uno script Python che viene eseguito fisicamente all interno dell
* ambiente isolato. Si occupa di caricare i modelli AI, elaborare i dati e restituire i risultati a Blender.

## 3. Direttive Generali di Sviluppo

* Separazione Ingegneristica: Mantieni sempre una distinzione netta tra il codice specifico di Blender basato su bpy e
* la logica Python standard. Il codice di rete, di estrazione e il worker isolato non devono avere alcuna dipendenza
* dalle librerie interne di Blender.
*
* Esecuzione Asincrona: Nessuna operazione pesante download, installazione o calcolo AI deve mai bloccare il thread
* principale di Blender. Utilizza tassativamente threading e operatori modali bpy.types.Operator con timer per aggiornare
* l interfaccia utente.
*
* Isolamento Ambientale: Tutte le installazioni di pacchetti tramite pip devono essere circoscritte alla cartella del
* microservizio. Usa il modulo subprocess per invocare l eseguibile Python isolato passando liste concatenate di librerie
* in un singolo comando per ottimizzare la risoluzione delle dipendenze.
*
* Gestione Dinamica dei Percorsi: Non scrivere mai percorsi assoluti nel codice o nei file JSON. Usa sempre os.path per
* costruire i percorsi a runtime basandoti sulla posizione effettiva dell addon nel computer dell utente.
*
* Comunicazione Interprocesso: Il passaggio di parametri e risultati tra Blender e il motore isolato deve avvenire tramite
* stringhe JSON standardizzate. Utilizza sys.argv, file temporanei o la lettura dello standard output tramite subprocess.
* Popen, includendo sempre la gestione avanzata di eccezioni e timeout per intercettare eventuali crash del motore esterno.
* Stile di Scrittura: Scrivi codice pulito, modulare e orientato alla produzione, privilegiando la libreria standard di
* Python per le funzioni base ed evitando l introduzione di dipendenze esterne non strettamente necessarie nel bootstrapper.

## 4. Importazione moduli python
* Per importare una funzione o una classe o qualsiasi altra cosa che è parte costruita nel progetto, usa sempre il . relativo.
* Esempio: Se siamo nello stesso package non utilizzeremo mai il nome del pacakge, ma il . relativo.
* Se siamo in un package figlio useremo .. per risalire di un livello e così via.
* Questo perchè in oltre Blender non gestisce bene i pacchetti python e quindi per evitare errori di importazione è meglio usare sempre il . relativo.

## 5. Commenta il codice in maniera chiara e sempre in inglese.
* Commenta il codice se necessario

## 6. Docstrings
* Usa docstrings per tutte le funzioni, classi e metodi. Le docstrings devono essere in inglese e seguire lo standard 
* PEP 257. Rigorosamente in Inglese


