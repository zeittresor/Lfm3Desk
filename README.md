# LFM3 Desk 1.5.1

Lokale Windows-Anwendung: C# / WinForms (.NET 8), mit offizieller Transformers-Inferenz für **LiquidAI/LFM3-Omni-2B**. GUI und CLI verwenden denselben lokalen Worker. Kein API-Schlüssel, Ollama, externer Agent oder Netzwerkserver erforderlich.

Die App verwendet das LFM3-Omni-2B Model sowie das TinySD Model und ermöglicht Multi-Format In-/Outputs. Die Funktionalität umfasst die Eingabe per Sprache, Textchat, Bilder, Videos (ohne/mit) Ton, Audio und als Ausgabe Sprachausgabe, Text, Office Dokumente, Audio, Bildgenerierung. Die App nutzt eingebaute Tools um Bilder zu erstellen (da das LFM3 Model diese zwar eingangs versteht jedoch keine erstellen kann hat das Model einen Harness erhalten um dies über TinySD dennoch zu realisieren und gibt die Bild Interpretation dann an das Model zurück damit das Model erfährt was auf dem Bild zu sehen ist. Das Model hat noch einige andere Tools erhalten wie eine lokale Wikipedia als Wissensquelle, schliesslich ist LFM3-Omni-2B ein recht kleines Model und kann somit bei Wissensfragen darauf zurückgreifen - selbst offline. Standardmäßig kann das Model auf Wetterdaten zugreifen (sofern man online ist), falls man offline sein sollte greift das Wetter tool auf die letzten 3 Tage/Wetterdaten lokal abgelegt zu um eine prognose zu erstellen. Für mathematische Berechnungen verwendet das tool keine Model spezifischen Überlegungen sondern verwendet ein Taschenrechner Tool uvm...

PS: Die Stabilität der Sprachausgabe wird dadurch erreicht das das Model erstmal die komplette Antwort generiert und dann jeweils jeden Satz für sich genommen stumm spricht, anschliessend wenn alle Fragmente erzeugt wurden, werden diese zusammengesetzt und durch einen Normalisierungs-Audiofilter geschickt und dann erst gesprochen, würde dies nicht so erfolgen wird jeder Folgesatz im zunehmend Verlauf schlechter bis zur nicht mehr konstistenten Aussprache daher wurde dies so realisiert.

https://github.com/user-attachments/assets/4d6db1d3-7fc5-4ecc-89ff-55b56f74e33d


## Neu in 1.4.0: optionale GPU-Bildgenerierung

Tiny-SD war bisher fest auf CPU eingestellt, unabhängig vom LFM3-Gerät. Die CPU bleibt Standard. Für die optionale GPU-Ausführung:

1. Im neuen Versionsordner das normale Setup ausführen (vorhandene Modelle/Wheels/ZIM werden wiederverwendet).
2. Unter **Einstellungen → Modell/Ausgabe → Bild-GPU einrichten** die kleine zusätzliche Laufzeit installieren. Der Vorgang erscheint im Einrichtungsprotokoll und ist abbrechbar. Nach Erfolg wird DirectML ausgewählt.
3. Der Bild-GPU-Index 0 bezeichnet den Standardadapter in DXGI-Reihenfolge. Bei mehreren GPUs kann ein anderer Index erforderlich sein. Die LFM3-Auswahl `auto/cuda/cpu` ist davon unabhängig.
4. Für reine CPU-Bildgenerierung „Bilder: CPU / DirectML“ auf CPU stellen. Die zusätzliche Umgebung bleibt erhalten und es wird nichts deinstalliert.

DirectML nutzt DirectX 12 unter Windows; ein eigenes CUDA-Toolkit ist für diesen Bildpfad nicht erforderlich. Die vorhandenen INT8-Modelldateien werden verwendet. Die zusätzliche private `.venv-image` enthält ONNX Runtime DirectML und kleine Abhängigkeiten, keine zweite PyTorch-/LFM3-Installation. CPU-/Sprachmodell-Umgebung `.venv` bleibt unverändert. Benötigte Wheels werden zuerst aus dem gemeinsamen Wheelhouse übernommen, nur fehlende Pakete heruntergeladen. Auch spätere Versionen können diese Wheels übernehmen; virtuelle Umgebungen werden am neuen Pfad neu eingerichtet. Offline-Einrichtung mit vollständigen Wheels ist möglich.

CLI: `lfm3gui -nogui -image-backend directml -image-gpu 0 -input "Erzeuge ein Bild eines Leuchtturms"`.
Einrichtung ohne GUI: `powershell -NoProfile -ExecutionPolicy Bypass -File Setup.ps1 -ImageGpuOnly -NoLaunch` (optional `-Offline`). Die normale Installation lädt die optionale GPU-Laufzeit nicht automatisch.

Falls GPU-Laufzeit, Adapter oder Ausführung scheitern, protokolliert die App den Grund und versucht dasselbe Bild auf CPU. Neben jedem PNG enthält die JSON-Datei das Backend, die registrierten Session-Provider, den Adapterindex, die Generierungsdauer und gegebenenfalls den Rückfallgrund. Registrierte Provider belegen keine vollständige GPU-Auslastung: nicht unterstützte Operatoren können auf CPU verbleiben. GPU-Speicher wird nach jedem Bild freigegeben; deshalb werden die Bildsessions beim nächsten Bild neu geladen.

**Prüfstand:** 99 Backendtests und 46 C#-Prüfungen bestanden, Windows-x64 neu kompiliert; optionale Python-3.12-x64-Wheels erfolgreich aufgelöst. Echter DirectML-GPU-Betrieb, Leistungsgewinn und neue Windows-UI hier nicht getestet. Die Sprechaufbereitung bleibt unverändert; der Nutzer bestätigt verständliche Ausgabe mit 1.3.1. Details: `docs/VALIDATION_1.4.0.md`.

Technische Referenz: https://onnxruntime.ai/docs/execution-providers/DirectML-ExecutionProvider.html

## Neu in 1.3.1: verständliche Zahlen und Einheiten beim Vorlesen

Die Sprechfassung wird vor der Fragmentbildung für Deutsch und Englisch aufbereitet. Beispielsweise wird `Max ≈ 4,5 °C` zu „maximal etwa vier Komma fünf Grad Celsius“, `0 %` zu „null Prozent“ und `−1,9 °C` zu „minus eins Komma neun Grad Celsius“. Auch Temperaturbereiche, Windgeschwindigkeit, Niederschlagsmengen und Luftdruck werden unterstützt. Markdown-Markierungen werden entfernt; „Nebelchance“ wird als „Nebelwahrscheinlichkeit“ gesprochen. Der angezeigte Text, Tooldaten und Chatverlauf bleiben unverändert.

Das gilt für generierte Antworten und die ausdrückliche TTS-Aufgabe. Letztere behält weiterhin Link-/Pfadinhalte bei; Zahlen und Formatierung werden nun fürs Vorlesen aufbereitet. Weitere Sprachen behalten ihre Zahlennotation. Keine neuen Abhängigkeiten oder Modelle. Bei gespeichertem Audio enthält die Fragment-Manifestdatei Ausgangstext, Sprechfassung und die tatsächlich übergebenen Fragmente.

Prüfstand: 85 Backendtests und 40 C#-Prüfungen bestanden; Windows-x64-Anwendung neu kompiliert. Ein Hörtest mit dem echten Modell und ein nativer Windows-Test waren hier nicht möglich. Details: `docs/VALIDATION_1.3.1.md`.

## Neu in 1.3.0: aufgeräumter Chat und Wetter mit Offline-Cache

**Links und Dateipfade ausblenden** ist unter Einstellungen → Verhalten standardmäßig eingeschaltet. Link-/Bildbeschriftungen und Quellenbezeichnungen bleiben lesbar, technische Zieladressen und Ablagepfade werden aus der Anzeige entfernt. Umschalten wirkt sofort auch auf den geöffneten Verlauf. Das Chatarchiv und der Modellkontext behalten den Originaltext, sodass Einblenden möglich bleibt; der Text-Export folgt der aktuellen Anzeige. Die Erkennung ist regelbasiert und kein vollständiger Markdown-Renderer.

**Wetter ist bei neuen Einstellungen standardmäßig aktiviert**, auch im CLI. Es wird nur bei einer Wetteranfrage kontaktiert, nicht automatisch beim Start. Gespeicherte explizite Schalterstellungen bleiben erhalten. Websuche, Online-Wikipedia und MCP bleiben separat und standardmäßig aus. Mit `-no-weather` wird das Wettertool einschließlich Cachezugriff abgeschaltet.

Jeder erfolgreiche Abruf holt zusätzlich die **drei zurückliegenden Tage** der abgefragten Region. Diese Werte stammen aus dem Open-Meteo-Wettermodell; sie sind keine garantierten Stationsmessungen. Vergangenheitswerte werden getrennt von den drei Vorhersagetagen gehalten. Pro Ort liegen unter `data/weather` bis zu drei tägliche Abrufstände; mehrere Abfragen am selben Tag ersetzen dort den älteren Stand. Abrufzeitpunkt, Ort, Land, Einheiten und Datenherkunft werden mitgespeichert. Es gibt keine automatische Standortbestimmung und keinen Hintergrunddienst.

**Falls ein Online-Abruf scheitert**, bekommt das Modell `online_available=false`, den Fehler sowie – falls vorhanden – passende regionale Cache-Daten aus den letzten 72 Stunden. Veraltete oder mehrdeutige Ortszuordnungen werden nicht stillschweigend verwendet. Alte Vorhersagen werden im Offline-Ergebnis nicht als frische Vorhersagen zurückgereicht. Die App zeigt den Ausfall und den letzten Cache-Zeitpunkt auch selbst als Hinweis im Verlauf an. Das Modell soll den Datenstand nennen und höchstens eine deutlich unsichere Einschätzung aus vergangener Entwicklung/Jahreszeit anbieten; keine amtliche oder aktuelle Vorhersage und keine erfundenen exakten Werte bzw. Regenwahrscheinlichkeiten. Ohne passende vergangene Werte ist keine lokale Trendprognose begründet; allenfalls allgemein gekennzeichnete saisonale Hinweise sind möglich. Diese Kennzeichnung ist eine Modellanweisung, keine Garantie für dessen Formulierungen.

**Offline-Modus** unter Einstellungen → Schnittstellen sperrt die Online-Tools. Das weiterhin freigegebene Wettertool liest dann ausschließlich lokale Daten; Websuche und Online-Wikipedia werden nicht angeboten. CLI: `-offline`. Ein dabei notwendiges Setup benutzt `-Offline`; fehlende Modelle werden nicht online nachgeladen. Die laufende App bleibt bedienbar, wenn kein aktueller Wetterbericht verfügbar ist.

```bat
Start.cmd -nogui -input "Wie wird das Wetter morgen in Norderstedt?"
Start.cmd -nogui -offline -input "Welche älteren Wetterdaten für Norderstedt sind vorhanden?"
Start.cmd -nogui -no-weather -input "Erkläre mir ein anderes Thema"
```

Bei Frischinstallationen werden vorhandene Wetter-Cache-Dateien aus benachbarten Versionen an den endgültigen Ort übernommen, ohne die Quelle zu verändern. Zur Nutzung werden sie erneut auf Alter und Ortszuordnung geprüft. Modelle, Wheels, Tools und ZIM werden wie bisher wiederverwendet. Neue Pakete oder Modelle sind nicht erforderlich.

Prüfstand: **70 Backendtests und 40 CLI-/Persistenz-/Anzeigeprüfungen**, PowerShell-Syntax/Argumente und Wiederverwendung einschließlich Wettercache bestanden. Neue Windows-x64-Version kompiliert; native UI und tatsächliche Modellformulierungen hier nicht getestet. Siehe `docs/VALIDATION_1.3.0.md`. API-Referenz: https://open-meteo.com/en/docs (`past_days`).

## Neu in 1.2.0: Chatliste, Sprachfragmente und aktuelle Tool-Zugriffe

**Chatliste links:** Ein sichtbarer Neuer-Chat-Button erstellt einen separaten Dialog. Einträge erhalten automatisch einen Titel aus der ersten Nachricht. Wechseln stellt Verlauf, Entwurf, Anhänge, Bildvorschau und gespeicherte Audioantwort wieder her. Jeder Chat besitzt einen eigenen Modellkontext; beim Senden wird genau dieser Kontext an den gemeinsam geladenen Worker übergeben. Dialoge werden unter `output/chats/<ID>.json` gespeichert und nach einem App-Neustart wieder geladen. Während einer laufenden Anfrage sind Wechsel und Neuanlage gesperrt. Ctrl+N und Datei → Neuer Chat sind weiter verfügbar.

Die Chat-Dateien liegen im jeweiligen Programmordner. Bei deinem Frischinstallations-Testablauf werden private Chatverläufe nicht automatisch aus anderen Versionsordnern importiert. Vor einem manuellen Löschen einer Version kannst du deren `output/chats` selbst sichern bzw. in die neue Version übernehmen. Vor 1.2.0 gab es keine automatisch gespeicherte Chatliste.

**Sprachausgabe in kurzen Fragmenten:** Antworten werden satzweise und bei langen Sätzen in höchstens etwa 140 Zeichen langen Wortgruppen verarbeitet. Jedes Fragment beginnt mit einer neuen TTS-Konversation ohne vorherige Sprachhistorie. Das Audio-Tokenlimit wird separat pro Fragment gewählt und hängt nicht mehr von der Textantwortlänge ab. Bei aktivem Audio-Speichern liegen Einzel-WAVs samt Text-/Versionsmanifest unter `output/audio/<Name>.parts`; die fertige Antwort bleibt eine WAV unter `output/audio`. Bei ausgeschaltetem Speichern bleiben Fragmente im RAM und nur die fertige WAV wird temporär für die Wiedergabe abgelegt.

Beim Zusammenfügen werden DC-Offset und überlange Randstille reduziert, kurze Ein-/Ausblendungen und 120 ms Pausen gesetzt, Pegelunterschiede begrenzt und die Gesamtlautstärke per RMS angeglichen. Die Spitze wird auf 0,95 begrenzt. Das ist eine einfache Pegelnormalisierung, keine EBU-R128-/LUFS-Messung. Sie repariert keine falschen Laute. Kürzere unabhängige TTS-Aufrufe sollen das gemeldete Abdriften nach dem ersten Satz vermindern; ob die Verständlichkeit mit dem echten LFM3 auf deinem Rechner ausreichend besser ist, muss ein Hörtest bestätigen. Die Fragmentierung kostet zusätzliche Aufrufe und kann die Sprechmelodie zwischen Fragmenten verändern. Fortschritt zeigt Fragmentnummer und Gesamtzahl.

Die zwei vom Nutzer beigefügten WAVs sind 24-kHz-Mono-PCM16, 14,56 bzw. 28,64 Sekunden lang. Technisch gemessene Spitzen etwa 0,433/0,385, RMS etwa −23,0/−23,7 dBFS; keine voll ausgesteuerten Samples. Daraus lässt sich keine korrekte Aussprache ableiten. Ein Hörtest/ASR-Vergleich mit echten neu erzeugten Fragmenten wurde hier nicht durchgeführt.

**Aktuelle Tools statt alter Absagen:** Aktuelle Berechtigungen haben Vorrang vor historischen Aussagen über fehlenden Zugriff. Klar erkennbare alte Absagen zu einem nun verfügbaren Tool werden aus dem Modellkontext ausgeblendet; die sichtbare Abschrift bleibt erhalten. Nach einem erfolgreichen Lookup werden entsprechende widersprüchliche Zugriff-Absagen aus der neuen Antwort entfernt. Die Regel ist gezielt auf solche Formulierungen begrenzt und keine allgemeine Faktenprüfung. Sachliche Aussagen wie „kein Niederschlag“ bleiben stehen.

Mehrere Tools waren bereits möglich: bis zu acht Aufrufe pro Runde, maximal vier Tool-Runden je Antwort. Die Anweisung betont nun sinnvolle Ketten, etwa Wetter abrufen und anschließend ein angefordertes Wetterbild erstellen. Zwei aufeinanderfolgende Tool-Aufrufe wurden im Backend getestet. Die Auswahl durch das kleine Modell bleibt modellabhängig; die App erzwingt nicht bei jeder Anfrage mehrere Tools.

**Buttons und Logs:** Der Entfernen-Button saß weiterhin in einer zu niedrigen Zeile. Er bekommt jetzt ausreichend Platz und gehört zur zentralen Größen-/Layoutdiagnose. Standard-Buttonhöhen und einzeilige Beschriftungen werden auch bei weiteren Buttons abgesichert. Die Chatliste richtet ihre Zeilenhöhe an der Schrift aus. Alle App-Logs tragen Version und Zeitstempel: setup.log, runtime.log (zusätzlich je Worker-Start), runtime-versions.txt, ui-layout.log sowie bei Lesefehlern chat-store.log. Das Sprachfragment-Manifest trägt ebenfalls die App-Version.

**Installation:** In einen neuen Versionsordner entpacken und Start.cmd öffnen. Die vorhandene Wiederverwendung für Modelle, Wheels, Tools und ZIM bleibt erhalten; alte Versionsordner/Quelldaten werden nicht gelöscht. Python-Abhängigkeiten und Modellbestände sind gegenüber 1.1.5 unverändert.

**Prüfstand:** 58 Backendtests und 31 CLI-/Persistenzprüfungen bestanden. Echte lokale ZIM-/TLS-/MCP-/pip-Tests bleiben enthalten; neu sind Fragmentierung, DSP mit echten Samplearrays, WAV-/Manifestdateien, Kontexttrennung und Tool-Ketten. Windows-x64-App neu kompiliert. Die neue Windows-Darstellung sowie echte LFM3-Sprachqualität sind hier nicht geprüft. Details: `docs/VALIDATION_1.2.0.md`.

## Korrektur 1.1.5: Links und Speicherpfade nicht vorlesen

Generierte Antworten werden für die Sprachausgabe separat aufbereitet: Markdown-Bild-/Linkbeschriftungen bleiben erhalten, die dahinterliegenden Adressen und Dateipfade entfallen. Ebenso werden direkt ausgeschriebene Webadressen, Windows-/UNC-/Unix-Pfade und bekannte Bildablageorte aus dem gesprochenen Text entfernt. Der angezeigte Text, Chatverlauf, Quellen und Text-Export bleiben unverändert.

Die Bereinigung greift bei generierten Audioantworten auch ohne aktivierte Tools. Deshalb werden solche Antworten zuerst als Text erzeugt, danach bereinigt und als Sprache ausgegeben; die frühere untrennbare Interleaved-Ausgabe ohne Tools entfällt für diesen Ablauf. Bei unterschiedlicher Text- und Sprachsprache wird die bereinigte Antwort übersetzt und vor dem Sprechen erneut geprüft. Die separate Aufgabe `-task tts` bleibt bewusst wortgetreues Vorlesen des ausdrücklich vorgegebenen Eingabetextes.

Die Erkennung ist regelbasiert. Eindeutige Links und Pfade werden gefiltert; ungewöhnliche, frei formulierte Adressen können weiterhin eine Nachbesserung benötigen. Maße, Temperaturen und gewöhnliche Angaben wie km/h oder 1/2 bleiben erhalten. Besteht eine Antwort ausschließlich aus nicht gesprochenen Verweisen, formuliert das Modell einen kurzen sprachlichen Hinweis auf das Ergebnis im Chat.

Der Nutzer hat die frische Windows-Installation von 1.1.4 sowie funktionierende Bildgenerierung und Sprachausgabe bestätigt. Der beigefügte Setup-Log endet erfolgreich: Wikipedia Mini mit 4.686.161.304 Byte heruntergeladen, ZIM-Prüfsumme bestätigt und Setup abgeschlossen. Die Bildqualität allein erlaubt keine Trennung zwischen Grenzen des Tiny-SD-Modells und einem möglicherweise unpassenden, vom Sprachmodell erzeugten Bildprompt.

**Frischer Versionsordner:** 1.1.5 separat entpacken und Start.cmd öffnen. Als Wiederverwendungsquelle kann die beibehaltene Basisversion dienen. Falls du zusätzlich 1.1.4 behältst, kann auch dessen fertige ZIM übernommen werden. Keine Quelldateien oder alten Versionsordner werden gelöscht. Gegenüber 1.1.4 sind Python-Abhängigkeiten und Modelle unverändert.

Prüfstand: 50 Backendtests und 25 CLI-Prüfungen bestanden; Windows-x64-App über .NET SDK neu veröffentlicht. Die neuen Tests erfassen den tatsächlich an TTS übergebenen Text für Chat mit/ohne Tools, ASR/Übersetzung mit Audio und unverändertes explizites Vorlesen. Echte LFM3-Audioerzeugung und Windows-GUI wurden hier nicht ausgeführt.

## Korrektur 1.1.4: HTTPS-Vertrauen und echte Fehlerdetails

Im bereitgestellten 1.1.3-Protokoll sind Paketinstallation, CUDA-Prüfung, LFM3 und Tiny-SD erfolgreich. Erst der Wikipedia-Katalogabruf scheitert an `CERTIFICATE_VERIFY_FAILED: unable to get local issuer certificate`. Die Ursache ist eine nicht bestätigte Zertifikatskette; welcher Aussteller bzw. welches Zwischenzertifikat auf dem Zielsystem fehlt, ist aus der Meldung allein nicht bestimmbar.

Wikipedia-Katalog, Größenabfrage und ZIM-Download verwenden jetzt einen expliziten HTTPS-Kontext: unter Windows den nativen Zertifikatsspeicher über truststore und zusätzlich das öffentliche CA-Paket certifi. Zertifikats- und Hostnamenprüfung bleiben zwingend aktiv; es gibt keinen ungesicherten Wiederholungsversuch. Derselbe Kontext wird für Tiny-SD-Downloads und die optionalen Wetter-/Webseitenabfragen verwendet. Systemweite SSL-Einstellungen oder Zertifikatsspeicher werden nicht verändert. Die beiden Hilfspakete sind jetzt explizite Anforderungen der eigenen .venv und können bereits im Wheelhouse vorhanden sein.

**Details anzeigen** öffnet ein eigenes, skalierbares Fenster mit den vollständigen gespeicherten Fehlerdetails und Schaltflächen zum Kopieren und Öffnen des Setup-Protokolls. Bisher wählte der Button nur den ohnehin sichtbaren Protokollreiter aus, weshalb der Klick scheinbar nichts tat.

**Frischinstallation ist der vorgesehene Testablauf:** ZIP in einen neuen Versionsordner entpacken, die ursprüngliche Basisversion als Datenquelle behalten, Start.cmd öffnen. Das Setup übernimmt vorhandene Modelle/Wheels/Tools aus dem begrenzten Suchbereich und erstellt eine neue eigene .venv. Fehlendes wird ergänzt. Bei außerhalb liegender Basis `Setup.cmd -ReuseFrom PFAD` verwenden. App und Setup löschen keine alten Versionsordner oder Quelldaten. Fehlgeschlagene Versionsordner entfernt ausschließlich der Nutzer selbst. Die älteren Hinweise zum Überschreiben sind keine Voraussetzung für eine funktionierende Installation.

**Optionaler Download mit Wiederholung:** Der Wikipedia-Schritt versucht die Vorbereitung bei einem Fehler genau ein weiteres Mal. Scheitern beide Versuche, protokolliert er eine Warnung und beendet das übrige Setup erfolgreich. Teil-Downloads bleiben für einen späteren Versuch erhalten. Offline-Wikipedia wird dem Modell nur angeboten, wenn tatsächlich ein lesbares ZIM-Archiv vorhanden ist. Ein bereits funktionierendes Archiv bleibt nutzbar, auch wenn der optionale Download einer anderen Ausgabe scheitert. Die Einstellungen und Statuszeile weisen auf ein fehlendes Offline-Lexikon hin.

**Online-Wikipedia separat erlauben:** Einstellungen → Optionale Schnittstellen → Online-Wikipedia. Standardmäßig aus, unabhängig von Websuche und Wetter. Bei Freigabe können `wikipedia_online_lookup` und `wikipedia_online_read` über die offizielle MediaWiki-API deutsche oder englische Artikel suchen/lesen; die Quellen erscheinen wie bei lokalen Treffern. Die automatische Nachschlagefunktion nutzt bevorzugt das lokale Archiv, sonst nur bei ausdrücklicher Freigabe die Online-Variante. CLI: `-wiki-online`; bleibt ohne diesen Parameter auch bei gespeicherter GUI-Freigabe aus. Die beiden Funktionen sind ebenso über MCP mit derselben Freigabe verfügbar. An die API gehen Suchbegriffe bzw. Artikeltitel. Ohne freigegebene Online-Funktionen bleibt der Chat offline.

43 Backendtests und 25 CLI-Prüfungen bestanden, einschließlich einer echten lokalen HTTPS-Verbindung: ein nicht vertrauenswürdiges Zertifikat wird abgewiesen, ein ausdrücklich vertrautes akzeptiert und ein falscher Hostname weiterhin abgewiesen. Windows-App neu kompiliert. Native Windows-Kettenprüfung, Fehlerfenster-Darstellung und vollständiger großer Wikipedia-Download hier nicht ausgeführt. Weitere Details in `docs/VALIDATION_1.1.4.md`.

## Korrektur 1.1.3: Installation und Fehler-Button

Das Setup konnte eine im Wheelhouse fehlende MCP-Abhängigkeit nicht nachladen, wenn pip eine Python-Bedingung hinter dem Paketnamen ausgab, konkret `pydantic<3.0.0,>=2.11.0; python_version < "3.14"`. Die bisherige Erkennung erlaubte solche gültigen Bedingungen nicht und meldete deshalb fälschlich einen nicht auflösbaren Paketbestand. Jetzt parst der Installer die vollständige Paketanforderung mit dem bei pip vorhandenen PEP-508-Parser und lädt nur das tatsächlich fehlende Paket mit seinen Versionsgrenzen. Der Python-Zusatz ist bereits im vorausgehenden pip-Lauf für die laufende Umgebung ausgewertet worden. Fremde URLs und ungültige Anforderungen werden weiterhin nicht übernommen. Keine zusätzliche Parser-Abhängigkeit erforderlich.

Der Details-Button im Fehlerbanner hat eine explizite DPI- und schriftgerechte Größe sowie eine vollständig definierte Tabellenzeile. Die Bannerhöhe und Buttonspalte passen sich daran an; die Abmessungen stehen zusätzlich im UI-Layoutprotokoll.

**Update nach dem fehlgeschlagenen Setup:** App schließen, Dateien aus 1.1.3 im bereits angelegten 1.1.2-Programmordner überschreiben und Start.cmd öffnen. So werden die schon überführten Modelle, Wheels und die dort erstellte .venv direkt weiterverwendet. Nicht löschen oder neu entpacken müssen: models, wheelhouse und .venv. Setup fortsetzen; fehlende Abhängigkeiten werden ergänzt. Wikipedia Mini wird erst geladen, falls noch kein passendes Archiv vorhanden ist.

34 Backendtests bestanden, darunter die konkrete pip-Meldung aus dem Nutzerlog und ein echter pip-Auflösungslauf mit bedingter fehlender Abhängigkeit. Windows-App neu kompiliert; Buttondarstellung und vollständiger Windows-Installationslauf hier nicht ausgeführt.

## Neu in 1.1.2: eigener Bildfortschritt im Chat

Eine kleine animierte Kachelgrafik mit eigenem Fortschrittsbalken steht direkt im Chat über dem Eingabefeld, sobald das Bildtool beginnt. Modellladen und Promptverarbeitung zeigen eine laufende Aktivitätsanzeige. Während der Bildberechnung stehen dort die tatsächlichen Schritte und deren Prozentwert (z. B. 7 / 20, 35 %). Anschließend zeigt die App Dekodieren und Speichern als eigene Phasen ohne erfundene Prozentwerte. Erst nach dem fertigen Bild steht dort abgeschlossen / 100 %. Die Anzeige bleibt nach Abschluss sichtbar, auch während das Sprachmodell seinen Antworttext oder die Sprachausgabe erzeugt. Fehler und Abbruch beenden die Aktivitätsanzeige; der Abbrechen-Button bleibt verfügbar. Beim nächsten Vorgang wird die Anzeige zurückgesetzt.

Windows-Build neu kompiliert, 31 Backendtests bestanden. Die Prozentwerte werden von Tiny-SD-Schritt-Ereignissen gespeist, nicht zeitlich geschätzt. Keine neuen Pakete oder Modelle gegenüber 1.1.1 erforderlich. Native Windows-Darstellung hier nicht getestet.

## Korrektur 1.1.1: Tiny-SD unter Windows

Die Tokenizer-Dateien `vocab.json` und `merges.txt` sind UTF-8. Bisher las Tiny-SD sie mit der Betriebssystem-Standardkodierung. Beide echten Modelldateien schlagen beim Lesen mit Windows CP1252 mit UnicodeDecodeError fehl; dies ist eine nachvollziehbare mögliche Ursache des gemeldeten Bildfehlers. Ohne das konkrete Laufzeitprotokoll ist nicht bestätigt, dass dieser Fehler im Nutzerfall auftrat. Alle Tiny-SD-Textdateien werden jetzt ausdrücklich als UTF-8 gelesen/geschrieben.

Toolfehler erscheinen jetzt direkt im Chat und im CLI auf stderr. Im GUI-Protokoll stehen Toolparameter und Ergebnis; die vollständige Python-Fehlerkette schreibt der Worker nach `output/logs/runtime.log`. Die Systemanweisung fordert das Modell auf, einen erneuten Versuch nur anzukündigen, wenn es den entsprechenden Toolaufruf auch ausführt, und nur mit einer konkreten Korrektur erneut aufzurufen. Das Verhalten eines kleinen Modells ist damit nicht garantiert.

Zum Update App schließen, Dateien im vorhandenen Ordner überschreiben und Start.cmd öffnen. Gegenüber 1.1.0 sind keine neuen Pakete oder Modelldownloads erforderlich.

Prüfstand: 31 Backendtests einschließlich simulierter Windows-CP1252-Standardkodierung und Fehlerdiagnostik bestanden. Echte Tiny-SD-Inferenz erzeugte erfolgreich eine PNG mit 256×384 Pixeln, zwei Schritten und festem Seed (Funktionstest, kein Qualitätstest). C#-Windows-Build neu kompiliert; keine native Windows-Ausführung hier.

## Neu in 1.1.0: Wikipedia, optionale Online-Tools und MCP

**Standard: deutsche Wikipedia Mini.** Beim Setup wird die neueste verfügbare deutsche Mini-ZIM von Kiwix nach `data/wikipedia` geladen (derzeit ungefähr 4,4 GB zusätzlich). Mini enthält Einleitungen. Unter **Einstellungen → Offline-Lexikon** kann stattdessen die vollständige Ausgabe ohne Bilder (`nopic`, ungefähr 17 GB) ausgewählt und mit **Gewählte Wikipedia-Ausgabe laden** heruntergeladen werden. Die gewählte Datei wird danach als aktive ZIM eingetragen. Für eine andere bereits vorhandene Ausgabe einfach **Vorhandene ZIM auswählen** benutzen; ein leerer Pfad erkennt lokale Archive automatisch. Bei mehreren lokalen Ausgaben bevorzugt die automatische Erkennung Vollartikel. Die Download-Auswahl und der aktive Dateipfad sind getrennt, damit kein vorhandenes Archiv ungefragt gelöscht wird.

Vorhandene Archive werden vor einem Download benutzt. Aus benachbarten Versionen wird höchstens **ein** Archiv kopiert, bevorzugt die neueste Mini-Ausgabe. Extern ausgewählte Dateien bleiben an ihrem Ort. Downloads können abgebrochen und fortgesetzt werden. Nur ein neuer Download erhält eine vollständige eingebettete ZIM-Prüfsummenprüfung; vorhandene Archive werden strukturell geprüft. Es entstehen keine entpackte Wikipedia-Kopie, kein zusätzlicher Suchindex und kein Kiwix-Server. Die Suche erfolgt direkt in der ZIM mit libzim.

**Wissensfragen:** `wikipedia_lookup` sucht und liefert Textauszüge; `wikipedia_read` liest längere Artikel weiter. Die standardmäßig aktive automatische Nachschlagefunktion lässt dasselbe lokale LFM3-Modell einen kurzen deutschen Suchbegriff aus einer Wissensfrage bilden und legt die Treffer vor die Antwort. Dafür wird kein weiterer Agent und kein weiteres Sprachmodell geladen. Abschaltbar unter Offline-Lexikon. Das Modell wird ausdrücklich angehalten, private Notizen nicht mit allgemeinem Wissen gleichzusetzen. Mini kann wichtige Details auslassen und Suchbegriffe/Antworten bleiben modellabhängig; Treffer sind keine Garantie für eine richtige Antwort. Verwendete Quellen erscheinen separat im Chat bzw. im CLI-Text, ohne die URLs automatisch mitzusprechen.

**Web und Wetter sind getrennt und standardmäßig AUS.** Unter Einstellungen → Optionale Schnittstellen können Websuche/Webseiten und Wetterabfragen einzeln erlaubt werden. Websuche verwendet DDGS; Webseiten werden nur aus Suchtreffern als begrenzter Text gelesen. Das Wettertool fragt Open-Meteo mit einem expliziten Ortsnamen ab und liefert Ort, Zeitpunkt, Einheiten, aktuelle modellbasierte Wetterwerte und drei Tage Vorhersage. Ein Wetterbericht ist keine Stationsmessung. Keine automatische Standortbestimmung. Eine Wetterfreigabe erlaubt keine Websuche und umgekehrt. Suchbegriffe/Ortsnamen werden bei erlaubten Abfragen an die jeweiligen Dienste übertragen. Freie Open-Meteo-API: nichtkommerzielle Nutzung, CC BY 4.0; Geocoding GeoNames. Im CLI sind beide Funktionen bei jedem Start AUS, bis `-web` bzw. `-weather` ausdrücklich angegeben wird, unabhängig von gespeicherten GUI-Schaltern.

**MCP ist ein optionaler lokaler stdio-Server, standardmäßig AUS.** Zum Nutzen in den Einstellungen erlauben und **MCP-Client-Konfiguration exportieren** wählen. Der MCP-Client startet dann `lfm3gui.exe -mcp`; es wird kein TCP-Port geöffnet. Alternativ gibt `lfm3gui.exe -mcp-config` die Konfiguration aus, ohne MCP einzuschalten. Der Export enthält bei lokaler .NET-Runtime auch `DOTNET_ROOT`. MCP ist hier eine Server-Schnittstelle für externe Clients, kein Client für fremde MCP-Server. Verfügbar sind `chat_with_model`, `generate_image`, `wikipedia_lookup`, `wikipedia_read`, `web_search`, `web_read` und `current_weather`. Die Einstellungen werden vor jedem Aufruf erneut geprüft: Das Ausschalten von MCP blockiert weitere Aufrufe; Web/Wetter bleiben separat geschützt. Das bloße Starten lädt noch keine Modellgewichte. Ein Modellaufruf über MCP lädt eine eigene Instanz; gleichzeitiger Modellbetrieb in GUI und MCP kann zusätzlich VRAM benötigen. Audio wird als lokaler Dateipfad zurückgegeben, ohne automatische Wiedergabe im Client.

### Aktualisieren / Setup

App beenden und die neuen Dateien im bisherigen `Lfm3Desk`-Ordner überschreiben, anschließend `Start.cmd` öffnen. Modelle, Wheelhouse, `.venv`, ZIM-Dateien und Ausgaben bleiben erhalten. Die neuen Python-Abhängigkeiten werden in die vorhandene **eigene `.venv`** ergänzt; vorhandene Wheels werden wiederverwendet. Alternativ neues Versionsverzeichnis neben den alten entpacken; Setup übernimmt vorhandene Downloads und erstellt dort eine eigene `.venv`. Benutzerkonfigurationen werden nicht blind aus Nachbarversionen importiert. Beim vollständigen Setup ist Mini der Standard. Start.cmd zeigt das Setup-Protokoll in der GUI.

```bat
Setup.cmd -SkipWikipedia
Setup.cmd -WikipediaPath "E:\Lexikon\wikipedia_de_all_mini_2026-10.zim"
Setup.cmd -WikipediaFlavour nopic
Setup.cmd -WikipediaOnly -WikipediaFlavour nopic
Setup.cmd -Offline
Start.cmd -nogui -language DE -input "Wie wurde der Eiffelturm gebaut?" -output txt,tts
Start.cmd -nogui -input "Wie ist das Wetter in Hamburg?" -weather
Start.cmd -nogui -input "Suche aktuelle Informationen zu Windows" -web
Start.cmd -nogui -input "Erkläre den Eiffelturm" -wiki "E:\Lexikon\wiki.zim"
Start.cmd -help
```

`-WikipediaOnly` lädt ausschließlich die angegebene Ausgabe und braucht eine bereits eingerichtete Runtime. `-WikipediaFlavour` ohne `-WikipediaOnly` wählt die Ausgabe für einen fehlenden Erstdownload; ein vorhandenes Archiv wird weiterverwendet. `-SkipWikipedia` überspringt Wikipedia beim Setup. Im CLI schalten `-no-wiki`, `-no-wiki-auto` bzw. `-no-tools` die entsprechenden Funktionen aus. Ein vollständig eingerichtetes Programm funktioniert weiterhin offline, solange Web und Wetter aus bleiben. Zusätzliche Online-Abhängigkeiten zu installieren öffnet keine Onlineverbindung beim normalen Offline-Chat.

### English: knowledge and connections

Setup downloads German Wikipedia **Mini** by default (introductions, about 4.4 GB). Full articles without pictures (`nopic`, about 17 GB) are an optional Settings download. Select an existing ZIM to reuse it in place. Resumable downloads and predecessor reuse avoid unnecessary new transfers. Wikipedia works entirely locally through libzim; no external agent or local HTTP server is needed.

Web search, weather and the **MCP stdio server** have independent Settings switches, all OFF by default. CLI web/weather require explicit `-web` / `-weather` every time. Enable MCP in Settings and export the client configuration; the client starts `lfm3gui -mcp`. `-mcp-config` prints the JSON without enabling anything. MCP calls honor live permission settings. A separate MCP model instance can consume extra GPU memory when the GUI also runs inference.

### Prüfstand dieser Version

C#-Windows-Build kompiliert; 22 CLI-Assertions und 29 Backendtests bestanden, darunter echte ZIM-Volltextsuche, fortgesetzter Download mit Prüfsummenprüfung, optionale Vollausgabe neben Mini und echter MCP-stdio-Client einschließlich Sperren. Live-Websuche lieferte einen Treffer. Wetterantworten wurden mit kontrollierten API-Daten getestet; ein Live-Wetteraufruf scheiterte hier an der DNS-Auflösung. Die neue Windows-Oberfläche und ein vollständiger Download des großen Wikipedia-Archivs wurden hier nicht ausgeführt. Der Nutzer hat zuvor funktionierenden Chat und gute Sprachausgabe der Vorversion bestätigt. Einzelheiten: `docs/VALIDATION_1.1.0.md`.

## Historische Versionshinweise

## Update 1.0.4: Abgeschnittene Button-Beschriftungen

Der Nutzer-Screenshot von 1.0.3 zeigte weiterhin nur obere Zeichenränder an der unteren Schaltflächenkante. Die vorherige Änderung der Zeichenroutine hatte das Problem nicht gelöst.

Die eigene Button-Zeichenroutine ist jetzt vollständig entfernt. Standard-WinForms zeichnet und zentriert die Beschriftungen. Einheitliche grafische Icons mit kurzen Texten kennzeichnen die Aktionen; die Icons werden ohne zusätzliche Downloads direkt aus Vektorgeometrie erzeugt. Die Toolbar-Buttons verwenden feste, DPI-skalierte Höhen und zur Beschriftung passende Breiten; die Kombination AutoSize + Dock.Fill entfällt. Die Toolbar-Zeilen bleiben in der vorgegebenen Höhe. Die tatsächlichen Control-Abmessungen werden zusätzlich in `output/logs/ui-layout.log` aufgezeichnet. Die Windows-EXE wurde neu kompiliert; die sichtbare Windows-Darstellung steht noch zur Bestätigung aus.

Laufendes Setup zuerst abschließen lassen. Dann App schließen und die Dateien im vorhandenen Programmordner überschreiben. Abhängigkeitsanforderungen und Modelldateien sind unverändert.

## Update 1.0.3: Vorgängerversionen übernehmen

Das Setup durchsucht jetzt gezielt benachbarte `Lfm3Desk*`-Versionsordner am aktuellen und nächsthöheren Verzeichnisniveau. Es erkennt sowohl direkte Installationen als auch die verschachtelte Struktur `Lfm3Desk_v.../Lfm3Desk` (höchstens 40 passende Verzeichnisse je Ebene). Es durchsucht keine kompletten Laufwerke.

Vor Downloads kopiert es fehlende Modelle, Wheel-Dateien und passende lokale Tools direkt an ihre endgültigen Orte im neuen Programmordner. Vollständige LFM3-Modellbestände werden bevorzugt; die Quellen und kopierten Datenmengen stehen als `[SOURCE]`/`[REUSE]` im Setup-Protokoll. Vorhandene Zieldateien werden nicht überschrieben. `.venv`, Benutzereinstellungen und Ausgaben werden nicht blind aus alten Releases kopiert.

Die eigene `.venv` wird am neuen Pfad frisch erstellt. Ein vorhandenes vollständiges Wheelhouse wird zunächst ohne Online-Index aufgelöst. Nur fehlende Anforderungen werden einzeln nachgeladen; bei einem echten Versionskonflikt hält das Setup mit Details an, statt ungefragt den ganzen Paketbestand zu aktualisieren. Die neue Umgebung wird ausschließlich aus dem lokalen Wheelhouse installiert. Der zusätzliche pip-Cache ist für diese Vorgänge abgeschaltet; vorhandene alte Caches werden nicht automatisch gelöscht.

Beispiel: Liegen `Lfm3Desk_v1.0.1_Windows_x64_Source_and_App/Lfm3Desk` und `Lfm3Desk_v1.0.3_Windows_x64_Source_and_App/Lfm3Desk` nebeneinander unter `E:\Debug_Enviroment`, kann das neue Setup die alten Downloads übernehmen. Liegt der Vorgänger außerhalb des Suchbereichs:

```bat
Setup.cmd -ReuseFrom "E:\Archiv\Lfm3Desk_v1.0.1_Windows_x64_Source_and_App\Lfm3Desk"
```

Kopieren vermeidet neue Netzdownloads, benötigt aber Speicher für den neuen, eigenständigen Bestand und erzeugt Laufwerkszugriffe. Der alte Ordner wird dabei nicht verändert. Die .NET-Runtime wird nur aus Vorgängern übernommen, wenn weder eine passende lokale noch eine System-Runtime bereitsteht.

Die allgemeine Vorgabe für gemeinsame Programme steht in `docs/INSTALLER_REUSE_POLICY.md`. Technischer Prüfstand: `docs/VALIDATION_1.0.3.md`.

## Update 1.0.2: Sichtbare Schaltflächen und Reitertitel

Die Beschriftung der eigenen Schaltflächen wird jetzt über GDI+ auf derselben Zeichenfläche wie Hintergrund und Rahmen gezeichnet. Das adressiert die im Nutzer-Screenshot leeren Buttons von 1.0.1. Das `&` im Reitertitel wird als normales Zeichen dargestellt; es wird nicht mehr als Tastenkürzel interpretiert. Der Windows-Build wurde neu kompiliert, die tatsächliche Darstellung muss noch auf Windows bestätigt werden.

Eine laufende Installation zuerst abschließen lassen. Danach App beenden, Dateien im vorhandenen Programmordner aktualisieren und Start.cmd öffnen. Die Abhängigkeiten und Modelldateien benötigen wegen dieser GUI-Korrektur keine Neuinstallation.

## Update 1.0.1: Startfehler und Oberfläche

Der gemeldete Fehler ist auf die Python-Versionsprüfung in Windows PowerShells Legacy-Argumentübergabe zurückgeführt: Die Anführungszeichen im `python -c`-Code gingen verloren. Dieselbe SyntaxError-Signatur wurde im Legacy-Modus reproduziert. Der Installer verwendet jetzt `backend/probe_python.py` und eine explizite native Argumentübergabe mit getrennt erfasstem stdout/stderr. Ein fehlgeschlagener Kandidat beendet die Python-Suche nicht mehr.

Die GUI hat jetzt ein Dateimenü sowie getrennte Reiter **Chat**, **Einstellungen** und **Einrichtung & Protokoll**. Einstellungen stehen in festen, beschrifteten Gruppen. Chat und Anhänge sind benannt, seltene Aktionen befinden sich im Menü. Männlich/Weiblich und Aufgaben sind übersetzt. Auch deaktivierte Schaltflächen erhalten lesbare Theme-Farben. Setup läuft mit Live-Protokoll im GUI, ist abbrechbar und zeigt konkrete Fehlerdetails; die Fortschrittsanzeige endet auch bei Fehlern.

Pythonpakete werden ausschließlich über die **eigene `.venv` im Programmordner** installiert und geladen. Setup prüft Pythonversion, 64-Bit-Architektur und venv-Präfix. Runtimeprüfung und Inferenz verweigern den Start außerhalb dieser App-Umgebung.

**Aktualisieren:** App beenden, den Inhalt des neuen `Lfm3Desk`-Ordners über den vorhandenen Programmordner kopieren und Dateien überschreiben. `models`, `.venv`, `wheelhouse`, `output` und eigene Einstellungen werden vom ZIP nicht ersetzt. Danach `Start.cmd` starten; falls die Einrichtung noch offen ist, startet sie erneut. Eine frische Installation ist ebenfalls möglich.

## Schnellstart (Deutsch)

1. ZIP vollständig in einen beschreibbaren Ordner entpacken, z. B. `D:\AI\Lfm3Desk`. Nicht in `Program Files` ablegen.
2. **Start.cmd** starten. Das Paket enthält bereits eine kompilierte Windows-x64-Anwendung. Bei Bedarf werden .NET 8 Desktop, Python 3.12, die lokale `.venv`, Python-Pakete, Shared-FFmpeg, LFM3-Omni und Tiny-SD eingerichtet. Für die erste Einrichtung wird Internet benötigt. Alternativ zuerst `Setup.cmd` ausführen.
3. Nach vollständigem Setup kann die Anwendung offline genutzt werden. Setup endet mit einem nach 10 Sekunden abbrechbaren Autostart. Nach der ersten Einrichtung startet die GUI mit `Start.cmd`.
4. **Build.cmd** erzeugt aus den C#-Quellen eine eigenständig ausführbare Windows-x64-Version; das SDK wird nötigenfalls lokal eingerichtet. `Build.cmd -FrameworkDependent` erstellt stattdessen eine kleinere Version, die .NET Desktop benötigt.

Das enthaltene `lfm3gui.exe` ist eine frameworkabhängige, kompilierte Windows-x64-Version. Direkter EXE-Aufruf benötigt eine installierte .NET-8-Desktop-Runtime oder die Umgebungsvariable `DOTNET_ROOT`, die auf die lokale Runtime zeigt. **Start.cmd setzt sie automatisch**, falls die Runtime lokal eingerichtet wurde. Der Standard-Build mit Build.cmd erzeugt anschließend eine selbstständige EXE.

### Funktionen

- Textchat mit Gesprächskontext und eigenem Systemhinweis.
- Bilder, Audiodateien und Videos anhängen; mehrere Medienarten in einer Anfrage kombinieren, z. B. Bild + gesprochene Frage. Videoton ist zuschaltbar; Video-FPS und Frame-Limit begrenzen den Aufwand (standardmäßig 1 FPS / 128 Frames).
- Mikrofon aufnehmen, Aufnahme beenden und als Audioanhang senden. Windows verwendet das Standard-Aufnahmegerät. Aufnahmen landen in `output/recordings`.
- `chat`: Fragen beantworten. `asr`: Sprache transkribieren. `translate`: übersetzen. `tts`: den Eingabetext vorlesen. Für ASR eine Audiodatei anhängen.
- Modelleigene 24-kHz-Sprachausgabe mit **female / male**, wählbar in GUI und CLI. `-output tts` im Chat beantwortet die Frage und spricht die Antwort; `-task tts` liest dagegen den Eingabetext vor.
- Getrennte Eingangs-, Textausgangs- und Sprachausgangssprache. Bei verschiedenen Ausgangssprachen übersetzt das Modell die Textantwort vor der Sprachsynthese.
- Audioantworten standardmäßig als WAV unter `output/audio` speichern. Abschaltbar: dann temporäre WAV unter `output/temp`; Löschen bei der nächsten Audioantwort bzw. beim normalen Beenden. Nach einem Absturz können temporäre Dateien zurückbleiben.
- Automatisches Abspielen abschaltbar; letzte Audioantwort erneut abspielen; Chat als UTF-8-Text exportieren.
- Abbrechen beendet den Worker samt laufender Generierung. Der nächste Aufruf lädt das Modell neu; der bisherige Modellkontext ist dann zurückgesetzt.
- Animierte Fortschrittsanzeige, Phasenstatus und Texttoken-/Audioframe-Zähler. Keine geschätzte Prozentanzeige oder Restzeit. Antworten und Sprache werden nach Abschluss ausgegeben; kein unterbrechbares Echtzeit-Sprachgespräch.
- Deutsche und englische Beschriftungen. `PIH` ist als englischer Fallback vorgesehen, nicht als behauptete Pitkern-Übersetzung.
- Light, Dark, Sepia, Ocean, Matrix, Hellfire, Purple, Aurora; anpassbar unter `themes/*.json`. Übersetzungen unter `lang/*.json`. Die Einstellungen liegen im gleichnamigen Reiter; Modellvorbereitung und Protokoll im Reiter „Einrichtung & Protokoll“.

### Kommandozeile

Ohne Parameter wird das GUI geöffnet. Alle folgenden Aufrufe arbeiten ohne GUI:

```bat
Start.cmd -help
Start.cmd -nogui -language DE -input "Bitte erkläre mir die Gezeiten" -output tts -voice male
Start.cmd -nogui -language DE -input "Erkläre ein schwarzes Loch" -output txt,tts -voice female
Start.cmd -nogui -language DE -input "Was zeigt dieses Foto?" -image "D:\Bilder\foto.jpg" -output txt
Start.cmd -nogui -language DE -task asr -audio "D:\Audio\aufnahme.wav" -output txt -out-file "D:\Audio\transkript.txt"
Start.cmd -nogui -language DE -input "Fasse das Video zusammen" -video "D:\Video\clip.mp4" -output txt
Start.cmd -nogui -input-language DE -output-language EN -speech-language DE -input "Warum ist der Himmel blau?" -output txt,tts -voice female
Start.cmd -nogui -language DE -task tts -input "Dieser Satz soll vorgelesen werden." -voice male
```

Mit installierter .NET Desktop Runtime oder nach einem selbstständigen Build ist `lfm3gui.exe` anstelle von `Start.cmd` direkt verwendbar, z. B.:

```bat
lfm3gui.exe -nogui -language DE -input "Bitte erkläre, wann Windows 12 zu erwarten ist" -output tts -voice male
lfm3gui.exe -help
```

Die Windows-12-Frage ist hier nur ein Aufrufbeispiel. Ein Offline-Modell hat keinen aktuellen Nachrichtenabruf und kann Ankündigungen nicht verifizieren.

| Parameter | Werte / Bedeutung |
| --- | --- |
| `-help` | Vollständige Parameterübersicht; lädt kein Modell |
| `-nogui` | Kommandozeilenmodus; jeder Aufruf mit Parametern nutzt bereits den CLI-Pfad |
| `-language` | Setzt Eingangs-, Text- und Sprachausgangssprache zusammen, z. B. `DE` |
| `-input-language` | Eingangssprache, z. B. `DE`, `EN`, `AUTO` |
| `-output-language` | Text- und Sprachausgangssprache zusammen |
| `-speech-language` | Eigene Sprachausgangssprache; hat Vorrang vor `-output-language` |
| `-input` | Text in Anführungszeichen |
| `-output` | `txt`, `tts`, `txt,tts`; CLI-Standard `txt` |
| `-voice` | `female` oder `male`; frische Einstellungen: `female` |
| `-task` | `chat`, `asr`, `translate`, `tts`; Standard `chat` |
| `-image`, `-audio`, `-video` | Dateipfad; mehrfach möglich |
| `-device` | `auto`, `cuda`, `cpu`; ein Wechsel lädt das Modell beim nächsten Senden neu und erhält den Gesprächsverlauf |
| `-max-tokens` | `32` bis `8192`; Standard `1024`; gemeinsames 32K-Kontextlimit beachten |
| `-fps` | Videoabtastung über `0` bis `2`, Standard `1`; Punkt als Dezimaltrennzeichen |
| `-system` | Zusätzliche Systemanweisung für Chat |
| `-no-tools` | Lokale Tools abschalten |
| `-no-video-audio` | Video nur visuell verarbeiten |
| `-no-play` | Audio erzeugen, ohne es abzuspielen |
| `-no-save-audio` | Temporäre statt dauerhafter Audioantwort; im CLI nach Abschluss gelöscht |
| `-out-file` | Antworttext als UTF-8-Datei speichern, auch bei `-output tts` |
| `-download` | Modell prüfen/herunterladen, anschließend beenden |

Textsprachen laut Modellkarte: `EN AR ZH FR DE IT JA KO PT ES VI TH ID HI RU PL`.
Sprachsynthese laut Modellkarte: `AR DA DE EL EN FI FR HE IT JA KO NL PL PT ES SV TR ZH`. `EN` wird als American English interpretiert. Nicht jede Sprache ist für jede Modalität dokumentiert; `RU`, `VI`, `TH`, `ID`, `HI` und `AUTO` sind für die Sprachausgabe gesperrt. Geschlecht und Sprachvorgaben werden dem Modell über seine dokumentierten Prompts vorgegeben; die konkrete Ausgabequalität hängt vom Modell ab.

Normale Textantworten stehen auf stdout, Diagnosemeldungen und Audiopfade auf stderr. Exitcodes: `0` erfolgreich, `1` Runtimefehler, `2` Parameterfehler, `130` abgebrochen. Strg+C bricht ab. Einstellungen werden im Programmordner gespeichert. CLI übernimmt viele gespeicherte Einstellungen; `-output` startet jedoch immer mit `txt`, Audiospeicherung und Wiedergabe sind im CLI standardmäßig an.

### Lokale Tools

Die App übergibt dem Modell offizielle Tool-Schemas und verarbeitet dessen dokumentiertes `<tool_call>`-Format. Das ist eine begrenzte lokale Tool-Schleife, kein zusätzlicher KI-Agent.

| Tool | Umfang |
| --- | --- |
| `generate_image` | Tiny-SD-Bildgenerierung, englischer Prompt, 256/384/512 Pixel, 1–50 Schritte, Seed; PNG + Metadaten unter `output/images` |
| `current_time` | Lokales Datum, Uhrzeit und UTC-Offset |
| `calculate` | Begrenzte Arithmetik einschließlich sqrt, sin, cos, log, pi, e; kein Python-eval |
| `list_notes` | Textnotizen im App-Arbeitsordner auflisten |
| `read_note` | UTF-8-Notiz im App-Arbeitsordner lesen, max. 64 KiB |
| `save_note` | Neue UTF-8-Notiz erstellen, max. 64 KiB; kein Überschreiben |

Bildgenerierung verwendet exakt den rund 434,4 MiB kleinen, festgelegten TinySDDesk-INT8-Export mit CLIP und TAESD. Installer lädt ihn unter `models/Tiny-SD` herunter. ONNX Runtime führt die Bilder auf der CPU aus, während LFM3 CUDA nutzen kann. Im GUI erscheint eine anklickbare Bildvorschau; die CLI schreibt den Bildpfad auf stderr. Beispiel: „Erstelle ein Bild eines roten Segelboots vor einer Insel.“ Lokale Tools müssen eingeschaltet sein. Der LFM3-Toolaufruf wird dabei noch nicht mit dem echten LFM3-Modell end-to-end getestet. Details: `docs/TINY_SD.md`.

Arbeitsordner: `workspace` direkt im Programmordner. Keine Shell, kein beliebiger Dateisystemzugriff, keine Netztools. Maximal vier Tool-Runden mit jeweils acht Aufrufen. Bei Tools und Sprachausgabe werden zuerst Textantwort und Tool-Ergebnisse aufgelöst und danach dieselbe Antwort gesprochen; ohne Tools ist modellnative interleaved-Ausgabe möglich.

### Setup, Wiederverwendung und Offlinebetrieb

- Modellziel: ausschließlich `models/LFM3-Omni-2B`, einschließlich Audiocodec. Kein zusätzlicher vollständiger Modellordner unter `imported`. Tiny-SD hat seinen eigenen separaten Modellordner unter `models/Tiny-SD`.
- Tiny-SD aus vorhandener TinySDDesk-Installation übernehmen: `Setup.cmd -TinySdPath "D:\AI\TinySDDesk\models"`. Dateien landen direkt am Ziel; nach Möglichkeit per Hardlink, sonst einmalige Kopie. SHA-256 wird bei der ersten Übernahme geprüft, danach nur Größe/Änderungszeit gegen gespeicherte Prüfmetadaten.
- Vollständiges LFM3-Manifest vorhanden: lokale Dateiexistenz und Dateigröße prüfen, ohne Internet und ohne erneutes vollständiges Hashen.
- Fehlender/unvollständiger Download: offizielles HF-Snapshot auf einen Commit auflösen und mit Hugging Face lokal fortsetzen. Vorhandene Dateien und Downloadmetadaten werden dabei wiederverwendet. Beim erstmaligen Übernehmen manuell hineinkopierter Dateien kann die Downloadbibliothek Dateien zusätzlich verifizieren.
- Liegt das Modell anderswo, den vollständigen Inhalt vor dem Setup direkt nach `models/LFM3-Omni-2B` kopieren/verschieben; das Setup lädt fehlende Teile nach. Es durchsucht nicht ungefragt alle Laufwerke.
- Python wird an lokalen Standardorten gesucht. FFmpeg wird unter `tools/ffmpeg/bin`, über PATH und in benachbarten Toolordnern gesucht. Bereits gesammelte Wheels unter `wheelhouse` werden wiederverwendet. Keine pauschale Vollsuche über die Platte.
- Pythonpakete werden aus dem lokalen Wheelhouse installiert. Nach erfolgreicher Einrichtung wird die Runtime wiederverwendet; keine automatischen Paket-Upgrades bei jedem Start. Installierte Versionen: `output/logs/runtime-versions.txt`.
- NVIDIA: `Setup.cmd -Device cuda`; CPU: `Setup.cmd -Device cpu`; automatische Auswahl ist Standard. Das Setup verwendet PyTorch 2.11.0 / torchvision 0.26.0, mit CUDA 12.8 bei NVIDIA, und TorchCodec 0.17.0. Ein separat installiertes CUDA Toolkit ist nicht vorgesehen; ein passender Treiber wird benötigt.
- Shared-FFmpeg wird lokal bereitgestellt; ein reines statisches `ffmpeg.exe` genügt für TorchCodec nicht.
- Einmal vollständig eingerichtet: Modellladen erfolgt mit `local_files_only=True`; der Worker setzt zusätzlich Offline-Flags. Die Notiztools benötigen ebenfalls kein Netz.
- `Setup.cmd -Offline -NoLaunch` richtet aus vorhandenen lokalen Bestandteilen ein; es funktioniert nur mit bereits vorhandenem .NET/Python, Wheelhouse, Shared-FFmpeg und vollständigem Modellmanifest. Eine bestehende `.venv` ist nicht beliebig zwischen unterschiedlichen Pfaden/Computern verschiebbar; bei Umzug am Ziel aus dem Wheelhouse neu erstellen.
- Für Erstinstallation mehrere GB Download und ausreichend Platz für Modell, Wheels und Runtime einplanen. Deine RTX 4060 Ti 16 GB ist die vorgesehene GPU-Zielkonfiguration. Ein gemessener VRAM-Wert oder bestätigte AVX-only-Kompatibilität deiner Ivy-Bridge-CPU liegt noch nicht vor.
- Ohne gespeicherte Audioantworten werden nur Antwort-WAVs temporär behandelt; ausdrücklich aufgenommene Mikrofondateien bleiben im Aufnahmeordner.

### Verifikation und Grenzen

C#-Quellen mit dem echten .NET-8-Roslyn-Compiler gegen .NET-8-/WindowsDesktop-Referenzassemblies erfolgreich kompiliert. Die beiliegende EXE verwendet Microsofts Windows-x64-Apphost. CLI-Parser: 17 erfolgreiche Assertions. Backend: elf erfolgreiche isolierte Tests für Tools, Tool-Schleife, ASR-Aufruf und Offline-Modellprüfung.

**Noch nicht durchgeführt:** Windows-GUI-Lauf, vollständige Windows-Erstinstallation, echter LFM3-Modelldownload/LFM3-Inferenz, CUDA-Test, Mikrofon- und Audio-/Videotest. Die Backend-Tests ersetzen diese Hardwaretests nicht. Keine vollständige Echtzeit-Sprachpipeline, kein Finetuning und keine Kamera-Liveaufnahme in Version 1.0. Die native Modellanbindung orientiert sich an der offiziellen Modellkarte und am tatsächlich gelesenen Generierungs-/Processor-Code (Stand 05.11.2026).

Tiny-SD wurde hier dagegen mit echten Gewichten getestet: 256×256, sechs Euler-Schritte, gültiges PNG mit visuell geprüftem Inhalt. Ein Testbild liegt unter `docs/tiny-sd-smoke.png`.

Details und Windows-Abnahmecheck: `docs/VALIDATION.md`. Fehlerprotokolle: `output/logs/runtime.log` und `output/logs/setup.log`; das Einrichtungsprotokoll wird zusätzlich live im GUI angezeigt.

## English quick start

Extract into a writable folder and run **Start.cmd**. It installs a local .NET Desktop runtime when needed, opens the precompiled C# Windows GUI, and bootstraps Python, packages, shared FFmpeg, the official LFM3 model and the same compact Tiny-SD INT8 image model used by TinySDDesk on first use. Subsequent inference works offline. **Build.cmd** publishes a self-contained Windows-x64 build from source.

Use `-voice male` or `-voice female`, `-output txt|tts|txt,tts`, and `-help`. `-task tts` reads the input; normal chat with `-output tts` answers it in speech. GUI supports text, images, recorded/file audio, video with optional soundtrack, independent language choices, local tools, themes, saving/playback controls and cancellation. Text and speech are presented after generation completes. This release has compiled C# and passing isolated tests, but no Windows or real-model end-to-end test yet.

## Sources / licenses

- Official model and API examples: https://huggingface.co/LiquidAI/LFM3-Omni-2B
- TorchCodec and Windows FFmpeg requirements: https://github.com/meta-pytorch/torchcodec
- PyTorch versions: https://pytorch.org/get-started/previous-versions/
- Shared FFmpeg build: https://github.com/BtbN/FFmpeg-Builds
- .NET installer: https://learn.microsoft.com/dotnet/core/tools/dotnet-install-script
- Project attribution: https://github.com/zeittresor

Application sources are MIT licensed; the downloaded model uses **LFM Open License v1.0**. Python, .NET, PyTorch, Transformers, TorchCodec and FFmpeg retain their respective licenses. Tiny-SD uses CreativeML Open RAIL-M, with included CLIP/TAESD notices. Model weights and third-party runtimes are not embedded in this small source/application ZIP; Setup downloads them.
