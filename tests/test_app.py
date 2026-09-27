import unittest
from unittest.mock import Mock, patch

import requests
from app import app, calculate, lookup_lunar, parse_lunar


class BackendTests(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        lookup_lunar.cache_clear()
        self.clock = {'date': '2026-09-19', 'clock': '09:30', 'timeZone': 'America/New_York'}

    def response(self, lunar='八月初九'):
        return Mock(json=lambda: {'LunarDate': lunar, 'LunarYear': '丙午年，馬'})

    def test_all_counts_match_independent_hand_count(self):
        for month in range(1, 13):
            for day in range(1, 31):
                for hour in range(1, 13):
                    position = 0
                    for count in (month, day, hour):
                        for _ in range(count - 1):
                            position = (position + 1) % 6
                    self.assertEqual(calculate(month, day, hour)['timePalace'], position)

    def test_worked_examples(self):
        self.assertEqual([s['end'] for s in calculate(3, 3, 5)['stages']], [2, 4, 2])
        self.assertEqual([s['end'] for s in calculate(4, 5, 11)['stages']], [3, 1, 5])

    def test_official_lunar_formats(self):
        for text, month, day in [('八月初九',8,9),('閏六月初一',6,1),('闰六月十一',6,11),('正月廿一',1,21),('十一月二十九',11,29),('十二月三十',12,30),('冬月二十',11,20)]:
            result = parse_lunar(text)
            self.assertEqual((result['month'], result['day']), (month, day))
        self.assertTrue(parse_lunar('閏六月初一')['isLeap'])

    @patch('app.requests.get')
    def test_reading_and_calendar_share_success_cache(self, get):
        get.return_value = self.response()
        response = self.client.post('/api/reading', json=self.clock)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['hourIndex'], 6)
        self.assertEqual([s['end'] for s in data['stages']], [1, 3, 2])
        self.assertEqual(data['sign'], '速喜')
        self.assertEqual(self.client.get('/api/calendar?date=2026-09-19').get_json(), data['lunar'])
        get.assert_called_once_with('https://data.weather.gov.hk/weatherAPI/opendata/lunardate.php', params={'date': '2026-09-19'}, timeout=(3, 10))

    @patch('app.requests.get')
    def test_invalid_input_never_reaches_calendar(self, get):
        for body in [None, [], {}, {**self.clock, 'date':'2026-02-30'}, {**self.clock, 'date':'2022-01-01'}, {**self.clock, 'clock':'24:00'}, {**self.clock, 'timeZone':'Unknown/Zone'}, {**self.clock, 'question':'private'}, {**self.clock, 'date':'2026-03-08', 'clock':'02:30'}]:
            response = self.client.post('/api/reading', json=body)
            self.assertIn(response.status_code, [400, 415])
            self.assertIn('error', response.get_json())
        get.assert_not_called()

    @patch('app.requests.get')
    def test_hour_boundaries_and_autumn_dst(self, get):
        get.return_value = self.response()
        for hour, expected in [(23,1),(0,1),(1,2),(2,2),(3,3),(21,12),(22,12)]:
            response = self.client.post('/api/reading', json={**self.clock, 'clock':f'{hour:02}:00'})
            self.assertEqual(response.get_json()['hourIndex'], expected)
        response = self.client.post('/api/reading', json={**self.clock, 'date':'2026-11-01', 'clock':'01:30'})
        self.assertEqual(response.status_code, 200)

    @patch('app.requests.get')
    def test_upstream_timeout_and_retry(self, get):
        get.side_effect = [requests.Timeout(), self.response()]
        first = self.client.post('/api/reading', json=self.clock)
        self.assertEqual(first.status_code, 504)
        self.assertEqual(first.get_json()['error']['code'], 'network')
        self.assertEqual(self.client.post('/api/reading', json=self.clock).status_code, 200)
        self.assertEqual(get.call_count, 2)

    @patch('app.requests.get')
    def test_bad_upstream_results_return_json_errors(self, get):
        for value in [{'LunarDate':'bad'}, [], {'LunarDate':'八月三十一'}]:
            get.return_value = Mock(json=lambda: value)
            response = self.client.get('/api/calendar?date=2026-09-19')
            self.assertEqual(response.status_code, 502)
            self.assertEqual(response.get_json()['error']['code'], 'format')
        get.side_effect = requests.HTTPError()
        self.assertEqual(self.client.get('/api/calendar?date=2026-09-19').status_code, 502)

    def test_cors_preflight_and_untrusted_origins(self):
        response = self.client.options('/api/reading', headers={'Origin':'https://toooonyliu.github.io','Access-Control-Request-Method':'POST','Access-Control-Request-Headers':'content-type'})
        self.assertEqual(response.headers['Access-Control-Allow-Origin'], 'https://toooonyliu.github.io')
        self.assertIn('POST', response.headers['Access-Control-Allow-Methods'])
        response = self.client.get('/health', headers={'Origin':'https://unrelated.example'})
        self.assertNotIn('Access-Control-Allow-Origin', response.headers)

    def test_health_malformed_json_and_body_limit(self):
        self.assertEqual(self.client.get('/health').get_json()['status'], 'ok')
        for data, expected in [('{',400),('x'*5000,413)]:
            response = self.client.post('/api/reading', data=data, content_type='application/json')
            self.assertEqual(response.status_code, expected)
            self.assertIn('error', response.get_json())
        self.assertEqual(self.client.get('/missing').status_code, 404)


if __name__ == '__main__':
    unittest.main()
