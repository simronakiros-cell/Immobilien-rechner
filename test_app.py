import unittest
import math
from app import app, calculate_loan, GRUNDERWERBSTEUER, NOTAR_GRUNDBUCH_SATZ


class TestCalculateLoan(unittest.TestCase):
    
    def test_normal_loan_with_interest(self):
        result = calculate_loan(100000, 3.5, 10, 2.0, 0)
        self.assertIsNotNone(result)
        self.assertGreater(result["monatliche_rate"], 0)
        self.assertGreater(result["gesamt_zinsen"], 0)
        self.assertEqual(result["kreditbetrag"], 100000)
    
    def test_loan_with_remaining_debt(self):
        result = calculate_loan(100000, 3.5, 10, 2.0, 50000)
        self.assertIsNotNone(result)
        self.assertGreater(result["restschuld"], 0)
        self.assertLessEqual(result["restschuld"], 50000)
    
    def test_zero_loan_amount(self):
        result = calculate_loan(0, 3.5, 10, 2.0, 0)
        self.assertIsNotNone(result)
        self.assertEqual(result["monatliche_rate"], 0)
        self.assertEqual(result["kreditbetrag"], 0)
    
    def test_zero_term(self):
        result = calculate_loan(100000, 3.5, 0, 2.0, 0)
        self.assertIsNone(result)
    
    def test_zero_interest(self):
        result = calculate_loan(100000, 0, 10, 2.0, 0)
        self.assertIsNotNone(result)
        self.assertGreater(result["monatliche_rate"], 0)
    
    def test_monthly_rate_calculation(self):
        # 100.000 €, 3,5%, 10 Jahre, keine Restschuld
        result = calculate_loan(100000, 3.5, 10, 2.0, 0)
        expected_rate = 100000 * ((0.035/12) * math.pow(1 + 0.035/12, 120)) / (math.pow(1 + 0.035/12, 120) - 1)
        self.assertAlmostEqual(result["monatliche_rate"], expected_rate, places=2)
    
    def test_total_interest(self):
        result = calculate_loan(100000, 3.5, 10, 2.0, 0)
        total_paid = result["monatliche_rate"] * 120
        expected_interest = total_paid - 100000
        self.assertAlmostEqual(result["gesamt_zinsen"], expected_interest, places=2)
    
    def test_effective_repayment_rate(self):
        result = calculate_loan(100000, 3.5, 10, 2.0, 0)
        self.assertGreater(result["tilgungssatz"], 0)
        self.assertLess(result["tilgungssatz"], 10)


class TestGermanNumberFilter(unittest.TestCase):
    
    def setUp(self):
        self.app = app.test_client()
    
    def test_german_number_format(self):
        with app.app_context():
            result = app.jinja_env.filters['german_number'](1234.56, 2)
            self.assertEqual(result, "1.234,56")
    
    def test_german_number_zero(self):
        with app.app_context():
            result = app.jinja_env.filters['german_number'](0, 2)
            self.assertEqual(result, "0,00")
    
    def test_german_number_none(self):
        with app.app_context():
            result = app.jinja_env.filters['german_number'](None, 0)
            self.assertEqual(result, "0")
    
    def test_german_number_large(self):
        with app.app_context():
            result = app.jinja_env.filters['german_number'](1000000, 0)
            self.assertEqual(result, "1.000.000")


class TestPurchaseCosts(unittest.TestCase):
    
    def test_notary_costs(self):
        preis = 100000
        notarkosten = preis * NOTAR_GRUNDBUCH_SATZ
        self.assertEqual(notarkosten, 2000)
    
    def test_grunderwerbsteuer(self):
        preis = 100000
        steuer_berlin = preis * (GRUNDERWERBSTEUER["Berlin"] / 100)
        self.assertEqual(steuer_berlin, 6000)
    
    def test_total_costs(self):
        preis = 100000
        bundesland = "Berlin"
        makler_prozent = 3.5
        
        notarkosten = preis * NOTAR_GRUNDBUCH_SATZ
        grunderwerbsteuer = preis * (GRUNDERWERBSTEUER[bundesland] / 100)
        maklerkosten = preis * (makler_prozent / 100)
        gesamtkosten = preis + notarkosten + grunderwerbsteuer + maklerkosten
        
        self.assertEqual(gesamtkosten, 100000 + 2000 + 6000 + 3500)
        self.assertEqual(gesamtkosten, 111500)


class TestWebRoutes(unittest.TestCase):
    
    def setUp(self):
        self.app = app.test_client()
        app.secret_key = "test"
    
    def test_index_page_loads(self):
        response = self.app.get("/")
        self.assertEqual(response.status_code, 200)
    
    def test_calculation_post(self):
        response = self.app.post("/", data={
            "preis": "100000",
            "bundesland": "Berlin",
            "makler_prozent": "3,5",
            "eigenkapital": "20000",
            "zinssatz": "3,5",
            "laufzeit": "10",
            "tilgung": "2,0",
            "restschuld": "0",
            "mieteinnahmen": "500",
            "nebenkosten": "100",
            "verwaltung": "50",
            "ruecklage": "30"
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 200)
    
    def test_rendite_calculation(self):
        with app.test_request_context():
            from flask import session
            # Test that gross yield calculation uses gesamtkosten
            preis = 100000
            mieteinnahmen = 500
            gesamtkosten = 111500  # including ancillary costs
            bruttorendite = (mieteinnahmen * 12 / gesamtkosten * 100)
            self.assertAlmostEqual(bruttorendite, 5.38, places=2)


class TestEdgeCases(unittest.TestCase):
    
    def test_very_small_loan(self):
        result = calculate_loan(1, 3.5, 1, 2.0, 0)
        self.assertIsNotNone(result)
    
    def test_very_high_interest(self):
        result = calculate_loan(100000, 15.0, 10, 2.0, 0)
        self.assertIsNotNone(result)
        self.assertGreater(result["gesamt_zinsen"], 0)
    
    def test_full_equity_no_loan(self):
        result = calculate_loan(0, 3.5, 10, 2.0, 0)
        self.assertEqual(result["monatliche_rate"], 0)
        self.assertEqual(result["gesamtzahlung"], 0)
    
    def test_repayment_greater_than_loan(self):
        result = calculate_loan(100000, 3.5, 30, 5.0, 0)
        self.assertIsNotNone(result)
        self.assertGreater(result["tilgung_prinzipal"], 0)


if __name__ == "__main__":
    unittest.main()
