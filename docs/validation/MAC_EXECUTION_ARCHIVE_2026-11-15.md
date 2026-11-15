# Archivio esecuzioni Mac — 15 novembre 2026

Questo documento raccoglie le evidenze macchina-specifiche provenienti dai run
eseguiti sul MacBook Air M4 dell'utente. Non duplica i report JSON delle
campagne deterministiche: se un run rigenera un report byte-identico, il report
esistente resta l'unica copia canonica.

## Hardware dichiarato

- MacBook Air, Apple M4, 10 core CPU (4 performance + 6 efficiency);
- 24 GB RAM;
- macOS 27.2, build 26B123;
- Python 3.13.5;
- Docker 29.6.2.

## Evidenze registrate

| Run | Risultato | Tempo osservato | Memoria osservata | Note |
| --- | --- | ---: | ---: | --- |
| Multi-candidate pilot, worker isolato | PASS | 1.29 s | 195,248,128 byte RSS; 129,385,336 byte peak footprint | Test di isolamento dei worker |
| Benchmark multi-candidate, 4 worker | 4/4 PASS | 0.513198 s interno; 0.85 s con /usr/bin/time | 110,723,072 byte RSS interno; 116,588,544 byte con /usr/bin/time | Controlli: deduplicazione, isolamento, failure isolation; nessun ranking/selezione |
| Benchmark multi-candidate, 64 candidati e 4 worker | 64/64 PASS | 7.823285 s interno; 8.15 s con /usr/bin/time | 114,327,552 byte RSS interno; 116,457,472 byte con /usr/bin/time | 64 varianti completate; circa 109 MiB RSS del parent nel report |
| Suite Python dopo l'espansione K4/K5/K6/K7 | PASS | non archiviato | non archiviato | Output terminale concluso al 100% |

## Campagne già canoniche nel repository

Le campagne note di fisica conosciuta e i relativi report per-candidato,
checkpoint e manifest sono già versionati nei rami di sviluppo e confluiscono
nel ramo W9. Non vengono ricopiati qui.

Anche i report W4, W5, W6, W7, W8 e W9 sono deterministici rispetto a codice,
activation e griglia: un nuovo run sul Mac è nuovo solo se cambia il codice,
l'attivazione, l'ambiente dichiarato o il risultato hash del report.

## Regola di consolidamento

Prima di committare nuovi risultati dal Mac:

    git status --short
    git diff --name-status
    git ls-files --others --exclude-standard

Si archiviano soltanto:

1. report o manifest realmente nuovi;
2. modifiche di codice o test;
3. benchmark hardware-specifici;
4. log di fallimento o non-determinismo.

Non si archiviano .Rhistory, cache, __pycache__, ambienti virtuali o una
seconda copia di un JSON identico.

## Stato W9 sul Mac

Il tentativo precedente di checkout è stato bloccato da modifiche locali a
docs/CURRENT_STATUS.md e src/physics_lab/search/__init__.py; il test W9 non è
quindi ancora una nuova evidenza Mac. Dopo la conservazione dello stash e il
checkout corretto, il test e il run W9 potranno essere eseguiti e confrontati
con il report canonico già presente.

Questo archivio è una registrazione di performance e riproducibilità del Mac,
non una validazione fisica aggiuntiva.
