[English](README.md) | **Deutsch**

# Haas+Sohn Stove (Local)

[![Validate](https://github.com/dwyschka/hsp_local/actions/workflows/validate.yml/badge.svg)](https://github.com/dwyschka/hsp_local/actions/workflows/validate.yml)

Eine **Custom Integration** für Home Assistant, die Haas+Sohn Pelletofen
**direkt** über das WLAN-Modul im lokalen Netz anspricht. Kein Cloud-Konto,
keine Internetverbindung nötig.

Sie ist an die offizielle Home-Assistant-Integration
[`fumis`](https://www.home-assistant.io/integrations/fumis/) angelehnt
(Climate + Sensoren + Switches + Button), verwendet aber das lokale
`status.cgi`-Protokoll statt einer Cloud-API.

## Funktionen

- **Climate**-Entität: Ein/Aus, aktuelle und Ziel-Raumtemperatur.
- **Sensoren**: aktuelle/Ziel-Temperatur, Ofenstatus (`mode`), Fehler,
  Zündungen, Betriebsstunden, Pelletverbrauch, Wartungs-/Reinigungs-Countdown
  und Heizkurve.
- **Switches**: Ein/Aus, Wochenprogramm und Eco-Modus.
- **Binärsensoren**: Wochentimer, PGI.
- **Button**: aktiven Fehler quittieren.
- Einstellbares Abfrageintervall.
- Lokales Polling, keine Cloud, keine externen Python-Abhängigkeiten.

## Installation

### Über HACS (empfohlen)

1. Stelle sicher, dass [HACS](https://hacs.xyz) installiert ist.
2. Gehe zu **HACS → Integrationen**.
3. Öffne das Drei-Punkte-Menü (oben rechts) und wähle **Benutzerdefinierte
   Repositories**.
4. Füge die Repository-URL `https://github.com/dwyschka/hsp_local` mit der
   Kategorie **Integration** hinzu.
5. Suche nach **Haas+Sohn Stove (Local)** und installiere sie.
6. Starte Home Assistant neu.

### Manuell

Kopiere den Ordner `custom_components/hsp_local` in dein
Home-Assistant-Konfigurationsverzeichnis (sodass du
`<config>/custom_components/hsp_local/manifest.json` erhältst) und starte Home
Assistant neu.

## Konfiguration

1. Gehe zu **Einstellungen → Geräte & Dienste → Integration hinzufügen**.
2. Suche nach **Haas+Sohn Stove (Local)**.
3. Gib die IP-Adresse (oder den Hostnamen) des WLAN-Moduls und den PIN-Code
   ein. Die PIN findest du am Ofen unter **Menü → Netzwerk → WLAN-PIN** oder
   auf dem Aufkleber des WLAN-Moduls.

Die PIN wird nur zum Senden von Befehlen benötigt; das Lesen des Status ist
unauthentifiziert. Die Einrichtung prüft daher die Erreichbarkeit, nicht die
PIN. Falls Befehle mit einem Authentifizierungsfehler fehlschlagen, prüfe die
PIN.

Das Abfrageintervall (Standard 15 Sekunden) lässt sich über **Konfigurieren**
am Integrationseintrag ändern.

## Entitäten

| Plattform       | Entität              | Beschreibung                                        |
|-----------------|----------------------|-----------------------------------------------------|
| `climate`       | Ofen                 | Ein/Aus, aktuelle und Zieltemperatur                |
| `sensor`        | Aktuelle Temperatur  | Raumtemperatur (`is_temp`)                          |
| `sensor`        | Zieltemperatur       | Zieltemperatur (`sp_temp`)                          |
| `sensor`        | Status               | Roher Ofenmodus (`mode`)                            |
| `sensor`        | Fehler               | Aktiver Fehlercode, `none` wenn keiner vorliegt     |
| `sensor`        | Zündungen            | Gesamtzahl der Zündungen (`ignitions`)              |
| `sensor`        | Betriebsstunden      | Gesamte Betriebsstunden (`on_time`)                 |
| `sensor`        | Verbrauch            | Gesamter Pelletverbrauch in kg (`consumption`)      |
| `sensor`        | Wartung in           | Pellets bis zur nächsten Wartung in kg              |
| `sensor`        | Reinigung in         | Stunden bis zur nächsten Reinigung (`cleaning_in`/60) |
| `sensor`        | Heizkurve            | Heizkurven-Stufe (`ht_char`)                        |
| `binary_sensor` | Wochentimer          | Wochenprogramm aktiv (`wprg`)                       |
| `binary_sensor` | PGI                  | `pgi`-Flag (standardmäßig deaktiviert)              |
| `switch`        | Ein/Aus              | Ofen ein-/ausschalten (`prg`)                       |
| `switch`        | Wochenprogramm       | Wochenprogramm aktivieren/deaktivieren (`wprg`)    |
| `switch`        | Eco-Modus            | Eco-Modus aktivieren/deaktivieren (falls unterstützt) |
| `button`        | Fehler quittieren    | Aktiven Fehler bestätigen                           |

Der **Wochenprogramm**-Switch stellt den kompletten Wochenplan als
`schedule`-Attribut bereit.

## Protokoll

Das WLAN-Modul stellt eine kleine JSON-Schnittstelle bereit:

```
GET  http://<host>/status.cgi
POST http://<host>/status.cgi   (JSON-Body + X-HS-PIN-Header)
```

Der `X-HS-PIN`-Header ist `md5(nonce + md5_hex(pin))`, wobei `nonce` vor jedem
Befehl über ein frisches `GET` gelesen wird. Unterstützte Befehle:

```json
{"prg": true}                 // Ein/Aus
{"sp_temp": 22}               // Zieltemperatur
{"wprg": true}                // Wochenprogramm
{"eco_mode": true}            // Eco-Modus
{"seen_error": [{"nr": 101}]} // Fehler quittieren
```

## Danksagung

Das Protokollverständnis basiert auf dem Projekt
[`hsp-mqtt-bridge`](https://github.com/dwyschka/hsp-mqtt-bridge) und dem
openHAB-Binding für Haas+Sohn Pelletöfen.

## Lizenz

Dieses Projekt steht unter der [MIT-Lizenz](LICENSE).
