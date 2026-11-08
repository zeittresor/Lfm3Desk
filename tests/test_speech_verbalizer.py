import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from speech_verbalizer import verbalize

class VerbalizerTests(unittest.TestCase):
 def test_user_temperature_example(self):
  text='- **Temperatur:** Max\u202f≈\u202f4,5\u202f°C, Min\u202f≈\u202f1,9\u202f°C'
  self.assertEqual(verbalize(text,'German'),'Temperatur: maximal etwa vier Komma fünf Grad Celsius, minimal etwa eins Komma neun Grad Celsius')
  self.assertIn('**',text)
 def test_fog(self):
  self.assertEqual(verbalize('- **Nebelchance:** 0\xa0%','DE'),'Nebelwahrscheinlichkeit: null Prozent')
 def test_signed_temperatures(self):
  self.assertEqual(verbalize('−1,9 °C, -4 °C und +2 °C','de'),'minus eins Komma neun Grad Celsius, minus vier Grad Celsius und plus zwei Grad Celsius')
 def test_bullet_not_negative(self):
  self.assertEqual(verbalize('- 4 °C\n- -2 °C','de'),'vier Grad Celsius. minus zwei Grad Celsius')
 def test_decimal_zeroes(self):
  self.assertEqual(verbalize('1,05 % und 0,01 °C','de'),'eins Komma null fünf Prozent und null Komma null eins Grad Celsius')
 def test_range(self):
  self.assertEqual(verbalize('4–6 °C; -4 bis -1 °C','de'),'vier bis sechs Grad Celsius; minus vier bis minus ein Grad Celsius')
 def test_other_units(self):
  self.assertEqual(verbalize('95 %, 5,3 km/h, 1013 hPa, 2 mm','de'),'fünfundneunzig Prozent, fünf Komma drei Kilometer pro Stunde, eintausenddreizehn Hektopascal, zwei Millimeter')
 def test_locale_grouping(self):
  self.assertEqual(verbalize('1.013 hPa und 4.5 °C','de'),'eintausenddreizehn Hektopascal und vier Komma fünf Grad Celsius')
  self.assertEqual(verbalize('1,013 hPa and 4.5 °C','en'),'one thousand thirteen hectopascals and four point five degrees Celsius')
 def test_english(self):
  self.assertEqual(verbalize('**Max** ≈ 4.5 °C, 0 %','English'),'maximum approximately four point five degrees Celsius, zero percent')
 def test_original_identifiers(self):
  self.assertEqual(verbalize('Max kommt am 2026‑11‑07 um 10:30. Wettercode: 61. Datei x123mm','de'),'Max kommt am siebten November zweitausendsechsundzwanzig um zehn Uhr dreißig. Wettercode: 61. Datei x123mm')
 def test_saved_summary(self):
  self.assertEqual(verbalize('ca. 4,5 °C max, 1,9 °C min; 0 %‑Nebelchance','de'),'etwa vier Komma fünf Grad Celsius maximal, eins Komma neun Grad Celsius minimal; null Prozent Nebelwahrscheinlichkeit')
 def test_unknown_language(self):
  self.assertEqual(verbalize('**4,5 °C**','French'),'4,5 °C')
 def test_comparisons(self):
  self.assertEqual(verbalize('≤ 2 % und ≥ 3 °C; ~4 °C','de'),'höchstens zwei Prozent und mindestens drei Grad Celsius; etwa vier Grad Celsius')
 def test_unusual_notation_does_not_crash(self):
  self.assertEqual(verbalize('1.2.3 °C','de'),'1.2.3 °C')
 def test_idempotent(self):
  text=verbalize('**Max:** ≈ 4,5 °C; 0 %','de')
  self.assertEqual(verbalize(text,'de'),text)

if __name__=='__main__':unittest.main()
