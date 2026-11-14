# Revisione umana della campagna finale da 20 candidate

Stato: `PENDING` — la campagna tecnica è completa, ma questa revisione non
deve essere marcata come conclusa automaticamente.

Campagna: `known-physics-final-twenty-baselines`  
Risultato tecnico: `20/20 PASS`  
Report principale:
`docs/validation/campaign_reports/known-physics-final-twenty-baselines/campaign_report.json`

## Scopo della revisione

La revisione umana non deve rifare tutti i calcoli numerici. Deve controllare
che ogni runner abbia eseguito esattamente il modello dichiarato, che i limiti
di validità siano rispettati e che il report non venga interpretato come una
validazione empirica o come selezione di una teoria.

Un esito umano deve essere registrato per ciascun gruppo e, se necessario, per
la singola candidate:

- `ACCEPTED_WITHIN_SCOPE`: il risultato è accettato nel perimetro dichiarato;
- `ACCEPTED_WITH_CAVEAT`: accettato, ma con una nota esplicita;
- `BLOCKED_FOR_REVIEW`: serve una correzione o un chiarimento prima di
  promuovere il risultato.

## Controlli comuni per tutte le 20 candidate

- [ ] `status` della candidate: `PASS`.
- [ ] `pipeline_status`: `COMPLETE`.
- [ ] `record_unchanged`: `true`.
- [ ] `known_physics_scope_explicit`: `true`.
- [ ] `external_comparison_not_authorized`: `true` oppure controllo
      equivalente.
- [ ] `no_experimental_parameters`: `true`.
- [ ] Nessuna candidate è stata selezionata automaticamente.
- [ ] Nessun ranking, fitting, ricerca o dato esterno è entrato nella
      campagna.
- [ ] Le osservabili sono lette come risultati del modello, non come accordo
      sperimentale.

## Revisione per gruppo

### K1–K3: meccanica, quantistica e campi classici

- [ ] Oscillatore armonico, campo scalare libero e particella nella scatola:
      azione/Hamiltoniana, condizioni al contorno, quantizzazione e osservabili
      corrispondono ai perimetri dichiarati.
- [ ] Idrogeno Coulomb e Pauli spin-1/2: spin, struttura orbitale, fine
      structure e Lamb shift non sono stati introdotti implicitamente.
- [ ] Maxwell classico, gravità newtoniana ed Einstein–Hilbert: le soluzioni
      sono interpretate come baseline controllate, non come trattamento
      completo della materia o della cosmologia.

### K4: campi quantistici liberi

- [ ] Dirac: algebra di Clifford, quantizzazione fermionica, vuoto e settore
      particella-antiparticella sono coerenti; nessuna interazione è implicata.
- [ ] Proca: vincolo di Lorenz e tre polarizzazioni fisiche sono coerenti con
      il campo massivo; non va interpretato come teoria di gauge massless.
- [ ] Maxwell quantizzato: riduzione di gauge, vuoto fotonico e due
      polarizzazioni trasverse sono coerenti; cariche e QED restano fuori.

### K5: interazioni controllate e struttura del Modello Standard

- [ ] Phi-four: è solo una teoria classica su reticolo periodico finito;
      nessuna affermazione su limite continuo o rinormalizzazione.
- [ ] Yang–Mills: è solo il baseline classico SU(2); nessuna affermazione su
      quantizzazione, confinamento o esistenza non perturbativa.
- [ ] Modello Standard: è una verifica strutturale di gruppi, contenuto di
      materia e anomalie; non contiene fitting di masse/coupling o accordo di
      precisione.

### K6: statistica e materia condensata controllata

- [ ] Ising: trasferimento esatto su catena periodica finita; nessun limite
      termodinamico o esponente critico è stato dichiarato.
- [ ] Catena armonica/phonons: modo zero traslazionale e spettro finito sono
      espliciti; nessuna calibrazione su materiale reale.
- [ ] Gas Bose: condizione sul potenziale chimico e insieme finito di modi
      sono rispettati; nessuna condensazione nel limite termodinamico.
- [ ] Gas Fermi: distribuzione finita e occupazioni sono rispettate; nessun
      modello materiale o confronto con dati.

### K7: cosmologia controllata

- [ ] FRW: geometria piatta, `Lambda=0`, equazione di stato costante e
      continuità sono ipotesi esplicite; nessun fit cosmologico.
- [ ] Perturbazioni: è una singola modalità scalare lineare su background
      power-law; non sono stati selezionati vuoto, spettro di potenza o
      condizioni iniziali cosmologiche complete.

## Cose ancora da fare

1. Leggere il report principale e i report per-candidate della campagna.
2. Compilare questa checklist con un esito umano per K4, K5, K6 e K7.
3. Registrare un breve verbale immutabile con esiti, caveat e blocchi, senza
   modificare retroattivamente i report tecnici.
4. Decidere esplicitamente se una o più candidate possono entrare in un gate
   empirico separato e target-blind.
5. Solo dopo autorizzazione distinta: dataset empirici, confronto,
   incertezze, fitting e possibili campagne di teorie nuove.

## Non è necessario fare adesso

- Non serve rilanciare la campagna da 20: è già `COMPLETE`.
- Non serve aumentare a 32 o 64 candidate prima della revisione.
- Non serve scegliere una “migliore” candidate: ranking e selezione restano
  disabilitati.
- Non serve dichiarare validata tutta la fisica: i risultati sono validi solo
  nei perimetri espliciti dei singoli baseline.

## Record da creare al termine della revisione

File consigliato:
`docs/validation/HUMAN_REVIEW_FINAL_TWENTY_2026-11-14.md`

Il record dovrà contenere data, revisore, commit esaminato, esito per gruppo,
caveat, eventuali blocchi e la decisione sui gate successivi. Finché quel
file non esiste, lo stato corretto resta `HUMAN_REVIEW_PENDING`.
