import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from speech_verbalizer import verbalize

class DateSpeechTests(unittest.TestCase):
 def test_iso_example(self):
  self.assertEqual(verbalize('2026-11-09','de'),'neunter November zweitausendsechsundzwanzig')
 def test_contextual_date(self):
  self.assertEqual(verbalize('am 2026-11-09','de'),'am neunten November zweitausendsechsundzwanzig')
 def test_german_date(self):
  self.assertEqual(verbalize('09.11.2026','de'),'neunter November zweitausendsechsundzwanzig')
 def test_named_month(self):
  self.assertEqual(verbalize('9. Nov. 2026','de'),'neunter November zweitausendsechsundzwanzig')
 def test_date_at_start_is_not_list_item(self):
  self.assertEqual(verbalize('9. November 2026','de'),'neunter November zweitausendsechsundzwanzig')
 def test_leap_date(self):
  self.assertEqual(verbalize('2024-02-29','de'),'neunundzwanzigster Februar zweitausendvierundzwanzig')
 def test_invalid_dates_untouched(self):
  for value in ('2026-02-29','2026-13-09','31.02.2026'):
   self.assertEqual(verbalize(value,'de'),value)
 def test_historical_year(self):
  self.assertEqual(verbalize('1989-11-09','de'),'neunter November neunzehnhundertneunundachtzig')
 def test_clock(self):
  self.assertEqual(verbalize('um 14:05 Uhr und 01:00 Uhr','de'),'um vierzehn Uhr fünf und ein Uhr')
 def test_clock_seconds(self):
  self.assertEqual(verbalize('00:00:01','de'),'null Uhr und eine Sekunde')
 def test_invalid_clock(self):
  for value in ('25:00','12:65','23:59:99'):
   self.assertEqual(verbalize(value,'de'),value)
 def test_ratios_and_versions(self):
  self.assertEqual(verbalize('Verhältnis 12:30; Version v1.5.1; Spielstand 10:20','de'),'Verhältnis 12:30; Version v1.5.1; Spielstand 10:20')
 def test_destinations_preserved_for_explicit_tts(self):
  text='https://example.org/2026-11-09?at=12:30'
  self.assertEqual(verbalize(text,'de'),text)
 def test_temperature_labels(self):
  self.assertEqual(verbalize('**Temperaturmax:** ca. 8,6 °C; **Temperaturmin:** ca. 5,5 °C','de'),'Höchsttemperatur: etwa acht Komma sechs Grad Celsius; Mindesttemperatur: etwa fünf Komma fünf Grad Celsius')
 def test_spaced_temperature(self):
  self.assertEqual(verbalize('Temperatur-Max: 4 °C; Temp. min: 0 °C','de'),'Höchsttemperatur: vier Grad Celsius; Mindesttemperatur: null Grad Celsius')
 def test_abbreviations(self):
  self.assertEqual(verbalize('z. B. bzw. d. h. ggf. evtl. inkl. u. a. usw.','de'),'zum Beispiel beziehungsweise das heißt gegebenenfalls eventuell inklusive unter anderem und so weiter')
 def test_duration(self):
  self.assertEqual(verbalize('5 min, 1 Std. und 2 Sek.','de'),'fünf Minuten, eine Stunde und zwei Sekunden')
 def test_english(self):
  self.assertEqual(verbalize('2026-11-09 at 14:05','en'),'ninth November two thousand twenty six at fourteen oh five')
 def test_unknown_language(self):
  self.assertEqual(verbalize('2026-11-09 14:05','French'),'2026-11-09 14:05')
 def test_filename_and_build_date_not_reinterpreted(self):
  for text in ('2026-11-09.png','Datei: 2026-11-09','Version 01.02.2026'):
   self.assertEqual(verbalize(text,'de'),text)
 def test_dotted_clock_and_hour_only(self):
  self.assertEqual(verbalize('um 14.05 Uhr, ab 1 Uhr','de'),'um vierzehn Uhr fünf, ab ein Uhr')
 def test_preparation_idempotent(self):
  s=verbalize('am 2026-11-09 um 14:05 Uhr: Temperaturmin 2 °C','de')
  self.assertEqual(verbalize(s,'de'),s)

if __name__=='__main__':unittest.main()
