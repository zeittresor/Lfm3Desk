# Fresh-install test workflow and source preservation

Each release must install into a new directory using a fresh private .venv. A retained base installation can supply models, wheelhouse and tools without repeated downloads. Updating over a failed installation is optional and must never be required for success. The app/installer must not delete predecessor version directories or source assets; deletion of failed versions is performed manually by the user. Copies go directly to canonical destination paths; the source remains intact.

# Gemeinsame Installer-Vorgabe

Vom Nutzer am 05.11.2026 als allgemeine Regel für gemeinsam entwickelte Programme bestätigt:

1. Vor jedem Download passende vorhandene Dateien berücksichtigen, insbesondere aus Vorgängerversionen und deren Wheelhouse/Tool-/Modellordnern.
2. Verschachtelte Release-Strukturen wie `Programm_vX/Programm` erkennen. Zielgerichtete, begrenzte Suche in passenden Nachbarordnern und typischen Cache-/Dependency-Orten; keine pauschale Vollsuche über Laufwerke.
3. Kompatible Dateien direkt am endgültigen Ziel wiederverwenden/kopieren. Keine vollständigen Zwischenkopien unter `imported` oder ähnlichen Zusatzverzeichnissen.
4. Nur fehlende oder tatsächlich inkompatible Bestandteile herunterladen; vorhandene passende Versionen nicht allein wegen eines neueren Indexangebots aktualisieren.
5. Python pro App in eigener venv. Bei einem neuen Installationspfad die venv aus vorhandenen Wheels neu erstellen, statt nicht relocatable Umgebungen blind zu kopieren. Keine globale pip-Installation.
6. Dateigröße und gespeicherte Prüfmetadaten für schnelle Wiederholungen nutzen; volle Hashprüfungen bei neuer/unsicherer Übernahme oder erforderlicher Integritätsprüfung. Keine wiederholten Vollhashes aller großen Modelle bei jedem Start.
7. Zusätzliche, redundante Downloadcaches vermeiden. Lokales Wheelhouse als sichtbare Offline-Installationsreserve behalten; bestehende Benutzer-Caches nicht ungefragt löschen.
8. Quellen, Übernahmen und notwendige Nachdownloads verständlich protokollieren. Quellinstallationen, aktuelle Zieldateien, Benutzereinstellungen und Ausgaben nicht ungefragt überschreiben.
9. Prüfen: Neuinstallation, neue Version im benachbarten verschachtelten Ordner, vollständige Offline-Übernahme, Teilbestand mit einem fehlenden Paket, Versionskonflikte und Wiederholung ohne weitere Downloads.

LFM3 Desk 1.0.3 implementiert diese Regel für seine benachbarten Releases. Die konkrete Kompatibilitätsprüfung und mögliche weitere Cache-Orte müssen bei anderen Programmen zu deren Komponenten passen.
