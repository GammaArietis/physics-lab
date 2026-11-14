# Verbale della revisione bibliografica K4–K7

Data: 14 novembre 2026  
Campagna esaminata: `known-physics-final-twenty-baselines`  
Commit della campagna: `8cd4684236e29664fa1c0536de636a204ba41f48`  
Report: `docs/validation/campaign_reports/known-physics-final-twenty-baselines/campaign_report.json`  
Esito tecnico della campagna: `20/20 PASS`  
Modalità: audit documentale basato su letteratura scientifica, manuali
universitari, fonti ufficiali e dataset pubblici; nessun nuovo fitting è stato
eseguito.

## 1. Oggetto e limiti

La revisione risponde ai cinque controlli richiesti:

1. coerenza tra modello dichiarato e runner;
2. correttezza dei limiti di validità;
3. assenza di parametri sperimentali nascosti;
4. assenza di selezione o ranking automatico;
5. interpretazione corretta delle osservabili.

La letteratura può confermare la formulazione matematica, la terminologia e il
perimetro fisico. Non può, da sola, trasformare una baseline teorica in una
validazione sperimentale. Per questo il verbale distingue:

- `SUPPORTED_WITHIN_SCOPE`: formulazione e caveat coerenti;
- `SUPPORTED_WITH_CAVEAT`: coerente, ma con una riduzione o assunzione che
  deve restare esplicita;
- `NOT_READY_FOR_EMPIRICAL_TEST`: la letteratura offre dati potenziali, ma il
  runner non produce ancora l’osservabile necessaria per un confronto diretto.

## 2. Controlli trasversali

| Controllo | Evidenza nella campagna | Esito |
|---|---|---|
| Candidate non modificate | `record_unchanged: true` per 20/20 candidate | SUPERATO |
| Runner completati | `pipeline_status: COMPLETE` per 20/20 | SUPERATO |
| Scope esplicito | controllo `known_physics_scope_explicit` presente nei report | SUPERATO |
| Parametri sperimentali nascosti | i parametri sono registrati come input/derivati; nessun dato esterno usato | SUPERATO |
| Selezione automatica | `performed: false` | SUPERATO |
| Ranking automatico | `ranking_performed: false` | SUPERATO |
| Search/fitting/data esterni | tutti i gate chiusi | SUPERATO |
| Interpretazione delle osservabili | verificata con le fonti e con le caveat sotto riportate | SUPERATO CON CAVEAT |

Conclusione trasversale: la campagna è un’esecuzione riproducibile di baseline
conosciute. Non è una classifica di teorie e non costituisce una misura del
grado di verità fisica delle candidate.

## 3. Esiti K4

### K4.1 Campo libero di Dirac

Esito: `SUPPORTED_WITHIN_SCOPE`.

La lagrangiana libera, l’equazione relativistica, l’algebra di Clifford, la
quantizzazione fermionica tramite anticommutatori e la decomposizione in
settori particella/antiparticella sono standard. La formulazione originale è
Dirac, *The Quantum Theory of the Electron*, Proc. R. Soc. A 117 (1928),
DOI [10.1098/rspa.1928.0023](https://doi.org/10.1098/rspa.1928.0023). Una
trattazione didattica CERN della quantizzazione dei campi liberi esplicita gli
anticommutatori fermionici e il ruolo del vuoto:
[CERN-97-03](https://cds.cern.ch/record/334107/files/CERN-97-03.pdf).

Il runner produce la relazione di massa e la sua forma normalizzata. Queste
sono conseguenze interne dell’equazione libera, non una nuova previsione
indipendente. La massa `m` e il momento `p` restano input espliciti; non sono
stati importati valori sperimentali.

Caveat: il confronto con elettroni/positroni richiederebbe un dataset
energia–momento con incertezze e una definizione operativa dell’osservabile.
Il report attuale non lo esegue.

### K4.2 Campo libero di Proca

Esito: `SUPPORTED_WITHIN_SCOPE`.

L’azione massiva, il vincolo trasverso/Lorenz derivato dall’equazione del moto,
la shell massiva e le tre polarizzazioni fisiche sono coerenti con la teoria
di Proca. La formulazione moderna dei vincoli Maxwell/Proca e della differenza
tra vincoli di prima e seconda classe è discussa da Errasti Díez et al.,
*Complete theory of Maxwell and Proca fields*, Phys. Rev. D 101, 045008
(2020), DOI
[10.1103/PhysRevD.101.045008](https://doi.org/10.1103/PhysRevD.101.045008).
Il runner mantiene correttamente `m>0` e non interpreta il vincolo di Lorenz
come una scelta di gauge del campo Proca.

Caveat: non esiste un dataset sperimentale generico di “campo Proca libero” da
confrontare senza specificare quale particella massiva vettoriale si intenda.
I limiti sulla massa del fotone sarebbero un test di un’estensione
fenomenologica, non una verifica diretta dell’intera candidate Proca.

### K4.3 Maxwell quantizzato

Esito: `SUPPORTED_WITHIN_SCOPE`.

La riduzione di gauge, la quantizzazione canonica, le due polarizzazioni
trasverse e la dispersione massless sono standard. Le note CERN e il lavoro
su formulazione canonica dei campi di gauge mostrano che, dopo vincoli e gauge
fixing, restano due gradi di libertà fisici. Il runner non introduce cariche,
materia o interazioni QED, in accordo con lo scope.

Caveat: il rapporto `omega/|k|=1` è un’identità della dispersione nel vuoto,
non una misura indipendente della quantizzazione del campo. Un confronto
sperimentale dovrebbe separare dispersione del vuoto, mezzo materiale,
calibrazione strumentale e polarizzazione.

## 4. Esiti K5

### K5.1 Phi-four classico su reticolo finito

Esito: `SUPPORTED_WITH_CAVEAT`.

La densità di potenziale quartica e la discretizzazione periodica sono
standard. La letteratura sulle teorie lattice `phi^4` mostra però che limite
continuo, volume infinito, transizioni di fase e rinormalizzazione sono
problemi aggiuntivi: si vedano Callaway e Maloof, Phys. Rev. D 27, 406
(1983), DOI
[10.1103/PhysRevD.27.406](https://doi.org/10.1103/PhysRevD.27.406), e
Akiyama et al., Phys. Rev. D 104, 034507 (2021), DOI
[10.1103/PhysRevD.104.034507](https://doi.org/10.1103/PhysRevD.104.034507).

Il runner fa correttamente una cosa più limitata: controlla un reticolo finito,
un potenziale locale e un rapporto di forza. Non reclama il limite continuo,
la rinormalizzazione o un vuoto quantistico.

Caveat: il rapporto quartico è dipendente dai parametri e dalla configurazione;
non è una predizione universale direttamente confrontabile con un singolo
numero sperimentale.

### K5.2 Yang–Mills classico SU(2)

Esito: `SUPPORTED_WITH_CAVEAT`.

La struttura non abeliana del campo di forza, il termine di commutatore,
l’equazione covariante e l’identità di Bianchi sono coerenti con la teoria
originaria di Yang e Mills, *Conservation of Isotopic Spin and Isotopic Gauge
Invariance*, Phys. Rev. 96, 191 (1954), DOI
[10.1103/PhysRev.96.191](https://doi.org/10.1103/PhysRev.96.191).

Il runner utilizza un’ansatz omogenea dichiarata. L’osservabile normalizzata
del commutatore verifica la scala scelta dall’ansatz; non misura confinamento,
quantizzazione o dinamica non perturbativa.

Caveat: il campo SU(2) classico isolato non è direttamente il settore
sperimentale del QCD SU(3) quantistico. Per un confronto fisico servirebbe una
teoria estesa e un mapping verso osservabili di gauge invarianti.

### K5.3 Baseline strutturale del Modello Standard

Esito: `SUPPORTED_WITHIN_SCOPE`.

Il gruppo di gauge, il contenuto chirale, il doppietto di Higgs e i conteggi
strutturali sono coerenti con le rassegne PDG 2025/2026. La cancellazione delle
anomalie è storicamente associata a Bouchiat, Iliopoulos e Meyer, *An
anomaly-free version of Weinberg’s model*, Phys. Lett. B 38, 519 (1972), DOI
[10.1016/0370-2693(72)90532-1](https://doi.org/10.1016/0370-2693(72)90532-1).
La rassegna elettrodebole PDG 2025 descrive esplicitamente il gruppo
`SU(2)xU(1)`, i doppietti chirali e i settori di precisione:
[PDG 2025](https://pdg.lbl.gov/2025/reviews/rpp2025-rev-standard-model.pdf).

Il runner non dichiara di aver validato masse, accoppiamenti, rottura
spontanea, correzioni radiative, neutrini massivi, materia oscura o gravità.
Questa limitazione è corretta e necessaria.

## 5. Esiti K6

### K6.1 Ising 1D finito

Esito: `SUPPORTED_WITHIN_SCOPE`.

Per condizioni periodiche la funzione di partizione finita può essere scritta
come traccia di una potenza della matrice di trasferimento e, per la matrice
2x2, come `lambda_+^N + lambda_-^N`. Risultati esatti recenti per il caso
finito e periodico sono riportati da Dantchev e Rudnick, Phys. Rev. E 106,
L042103 (2022), DOI
[10.1103/PhysRevE.106.L042103](https://doi.org/10.1103/PhysRevE.106.L042103).

Il runner usa correttamente `N` finito. Non dichiara transizione di fase,
esponente critico o limite termodinamico.

### K6.2 Catena armonica e modi fononici

Esito: `SUPPORTED_WITH_CAVEAT`.

La dispersione della catena monoatomica a primi vicini,
`omega(k)=2 sqrt(K/m) |sin(ka/2)|`, il modo zero traslazionale e il massimo
al bordo di zona sono standard nella dinamica reticolare. Una sintesi
autorevole e verificabile è disponibile nella documentazione Materials Project
sulla dispersione fononica:
[Phonon Dispersion](https://docs.materialsproject.org/methodology/materials-methodology/phonon-dispersion),
che distingue inoltre calcolo DFT/DFPT e dato sperimentale.

Il runner esegue modi normali classici finiti; non afferma di aver costruito
operatori fononici o una teoria quantizzata. Il rapporto di frequenze dipende
da `N` e non è un numero universale.

Caveat: per confrontare un materiale reale occorrono struttura, masse,
costanti elastiche, rami multipli, fattore di struttura e risoluzione dello
strumento. Materials Project fornisce principalmente risultati DFT, non un
dataset sperimentale diretto.

### K6.3 Gas ideale di Bose e Fermi

Esito: `SUPPORTED_WITHIN_SCOPE`.

La forma grand-canonica `H-mu N = sum_i (epsilon_i-mu)n_i`, la distribuzione
di Bose e quella di Fermi, con `n_i` illimitato per bosoni e `n_i` uguale a 0 o
1 per fermioni, sono standard. Una trattazione recente in forma di manuale è
Tuckerman, capitolo *Quantum ideal gases*, Oxford University Press (2023),
DOI [10.1093/oso/9780198825562.003.0011](https://doi.org/10.1093/oso/9780198825562.003.0011).
Le definizioni matematiche degli integrali di Bose–Einstein e Fermi–Dirac
sono mantenute dal NIST DLMF, §25.12:
[NIST DLMF](https://dlmf.nist.gov/25.12).

Il runner usa un insieme finito di modi e impone la condizione corretta
`mu < epsilon_min` per il caso bosonico. Non dichiara condensazione, limite
termodinamico o interazioni.

## 6. Esiti K7

### K7.1 Background FRW piatto, Lambda=0

Esito: `SUPPORTED_WITH_CAVEAT`.

La riduzione omogenea e isotropa delle equazioni di Einstein produce le
equazioni di Friedmann; per un fluido perfetto con `p=w rho` la conservazione
porta a `rho proportional to a^(-3(1+w))`. La base storica è Friedmann,
*Über die Krümmung des Raumes*, Z. Phys. 10 (1922), DOI
[10.1007/BF01332580](https://doi.org/10.1007/BF01332580), insieme alla
geometria FLRW formalizzata nei lavori di Robertson e Walker.

Il runner controlla correttamente il caso piatto, `Lambda=0`, densità positiva
e `w` costante.

Caveat importante: `S_perfect_fluid` è una riduzione efficace, non una
specifica microfisica completa della materia. Il baseline non è il modello
cosmologico oggi usato per confrontare direttamente CMB, BAO e supernovae,
perché non contiene in modo esplicito Lambda, materia oscura, radiazione,
neutrini e la catena completa di osservabili.

### K7.2 Perturbazione scalare lineare

Esito: `SUPPORTED_WITH_CAVEAT`.

La variabile gauge-invariant di Mukhanov–Sasaki e l’equazione
`v_k'' + (c_s^2 k^2 - z''/z) v_k = 0` sono standard. La rassegna di Mukhanov,
Feldman e Brandenberger, *Theory of cosmological perturbations*, Phys. Rep.
215 (1992), 203–333, DOI
[10.1016/0370-1573(92)90044-Z](https://doi.org/10.1016/0370-1573(92)90044-Z),
separa chiaramente perturbazioni classiche, quantizzazione, condizioni
iniziali e spettro.

Il runner calcola solo coefficienti locali della modalità e un rapporto di
orizzonte. Non seleziona un vuoto e non produce uno spettro di potenza.

Caveat importante: il background power-law e `c_s` sono parametri dichiarati,
ma non costituiscono da soli un modello completo di materia/gravitazione.
Per `c_s != 1` occorre una teoria sottostante, ad esempio una dinamica scalare
non canonica, prima di interpretare il risultato come predizione cosmologica.

## 7. Valutazione dei dati empirici disponibili

| Candidate/gruppo | Dati in letteratura | Prontezza per confronto diretto | Cosa manca |
|---|---|---|---|
| Dirac | Dati di particelle e masse valutate da PDG/NIST | PARZIALE | dataset energia–momento, covarianza e mapping operativo |
| Proca | Limiti sulla massa del fotone e ricerche di vettori massivi | NO, per il runner attuale | modello fenomenologico specifico e osservabile misurabile |
| Maxwell quantizzato | Dati di propagazione/polarizzazione fotonica | PARZIALE | separare vuoto, mezzo, calibrazione e quantizzazione |
| Phi-four | Simulazioni lattice e risultati numerici | NO empirico | estensione dinamica/statistica e definizione dell’esperimento |
| Yang–Mills SU(2) classico | Dati QCD e gauge theory, ma non lo stesso modello | NO | mapping a osservabili gauge-invarianti e settore fisico |
| Standard Model strutturale | PDG 2025/2026 e dati di precisione | NO per il runner attuale | rottura elettrodebole, parametri, rinormalizzazione e likelihood |
| Ising finito | Risultati esatti, simulazioni e sistemi magnetici quasi-1D | PARZIALE | campione/materiale, finite-size reale e incertezze |
| Catena fononica | Materials Project, INS/IXS e repository STFC | PARZIALE | scelta del materiale, rami, fattore di struttura e risoluzione |
| Gas Bose/Fermi ideale | Esperimenti su gas ultrafreddi e dati di termodinamica | PARZIALE | sistema debolmente interagente, livelli/trappola e finite-size |
| FRW | Planck, DESI DR2, Pantheon+/DES-SN | NO per il runner attuale | materia completa, Lambda, likelihood e fit |
| Perturbazioni scalari | CMB, BAO, lensing e supernovae | NO per il runner attuale | vuoto, spettro primordiale, transfer functions e Boltzmann solver |

Per la cosmologia esistono dati recenti sufficienti per una futura analisi,
ma non per il runner K7 attuale senza ampliarlo. Planck 2018 fornisce una
baseline CMB con parametri cosmologici e spettro primordiale:
[Planck 2018 VI](https://doi.org/10.1051/0004-6361/201833910). DESI DR2 2025
fornisce BAO da oltre 14 milioni di galassie e quasar e confronti con CMB e
supernovae:
[DESI DR2 II](https://doi.org/10.1103/tr6y-kpc6). Pantheon+ fornisce 1701
curve di luce di 1550 supernovae:
[Pantheon+](https://arxiv.org/abs/2202.04077). Questi dataset sono quindi
disponibili, ma appartengono a un modello cosmologico più ricco di FRW
Lambda=0 e della singola modalità perturbativa attualmente implementata.
Un risultato più recente, la combinazione `Unite` di Pantheon+ e DES-SN5YR,
riunisce 2884 supernovae e aggiorna il diagramma di Hubble:
[Supernovae Unite](https://arxiv.org/abs/2609.05053). Anche questo dataset
richiede però una pipeline cosmologica completa e non può essere inserito
direttamente nel runner K7 attuale.

Per i fononi, Materials Project è una fonte riproducibile di calcoli DFT/DFPT,
mentre i dati sperimentali di scattering neutronico possono essere ottenuti da
repository come [ISIS Data](https://data.isis.stfc.ac.uk/). La documentazione
ISIS avverte correttamente che il confronto con INS richiede fattore di
struttura, convoluzione strumentale e finestre in `Q,E`.

## 8. Decisione del verbale

1. K4 è coerente con la letteratura entro i perimetri dichiarati.
2. K5 è coerente entro i perimetri dichiarati; phi-four e Yang–Mills restano
   baseline classiche finite/controllate, mentre il record SM resta strutturale.
3. K6 è coerente; il termine “phonon” va letto come spettro di modi normali,
   non come quantizzazione fononica già implementata.
4. K7 è coerente come riduzione controllata, ma non è ancora un modello pronto
   per un fit cosmologico.
5. Nessun parametro sperimentale nascosto è stato identificato.
6. Nessun risultato della campagna autorizza selezione, ranking o ricerca di
   nuove teorie.

Stato complessivo: `LITERATURE_REVIEW_COMPLETED_WITH_CAVEATS`.

## 9. Passi successivi autorizzabili

### Prima di un confronto empirico

- congelare una versione del runner e dei record;
- scegliere una sola candidate o un gruppo omogeneo;
- definire osservabile, unità, likelihood, incertezze e nuisance parameters;
- congelare un dataset target-blind con provenienza, DOI, versione, checksum e
  regole di inclusione/esclusione;
- eseguire il confronto senza modificare il modello dopo aver visto il target.

### Estensioni necessarie per la cosmologia

- aggiungere materia/radiazione/Lambda/curvatura secondo uno scope esplicito;
- costruire `H(z)`, distanze, crescita e, per K7.2, spettro primordiale e
  transfer functions;
- validare contro Planck, DESI e supernovae con una likelihood documentata.

### Esperimenti realmente necessari

Per K4, K5 e K6 la letteratura è sufficiente per la revisione teorica; non è
necessario costruire subito un laboratorio. Un esperimento dedicato diventerebbe
necessario solo se si volesse testare una predizione che non sia già coperta
da dataset pubblici o se si scegliesse un sistema fisico specifico, ad esempio
una catena quasi-1D, un gas ultrafreddo o un setup di propagazione fotonica.

Questo verbale non certifica la verità ontologica delle teorie: certifica che
la struttura implementata è riconoscibile nella letteratura e che i limiti
dichiarati sono coerenti e non occultano risultati empirici non eseguiti.
