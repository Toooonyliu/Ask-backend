"""Ask HW4: calendar lookup and deterministic readings, without question text."""

import os
import re
from datetime import date, datetime, timezone
from functools import lru_cache
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import requests
from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 4096
ALLOWED_ORIGINS = set(os.environ.get(
    'ALLOWED_ORIGINS',
    'https://toooonyliu.github.io,http://localhost:4173,http://127.0.0.1:4173'
).split(','))
CALENDAR_URL = 'https://data.weather.gov.hk/weatherAPI/opendata/lunardate.php'
NAMES = ['大安', '留连', '速喜', '赤口', '小吉', '空亡']
NUMBERS = dict(zip('一二三四五六七八九', range(1, 10)))
NUMBERS.update({'十': 10, '十一': 11, '十二': 12, '正': 1, '冬': 11, '腊': 12, '臘': 12})


class APIError(Exception):
    def __init__(self, code, message, status=400):
        self.code, self.message, self.status = code, message, status


@app.after_request
def cors(response):
    # This permits browser requests from the portfolio; it is not authentication.
    origin = request.headers.get('Origin')
    if origin in ALLOWED_ORIGINS:
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.vary.add('Origin')
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response


@app.errorhandler(APIError)
def api_error(error):
    return jsonify(error={'code': error.code, 'message': error.message}), error.status


@app.errorhandler(HTTPException)
def http_error(error):
    return jsonify(error={'code': 'input', 'message': error.description}), error.code


def validate_date(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        raise APIError('date', 'Use a date formatted YYYY-MM-DD.')
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        raise APIError('date', 'That calendar date does not exist.')
    if parsed.year < 2023 or parsed.year > datetime.now(timezone.utc).year + 2:
        raise APIError('date', 'Supported dates are 2023 through the current year plus two.')
    return value


def parse_lunar(text):
    match = re.fullmatch(r'([閏闰]?)(正|冬|腊|臘|十一|十二|十|[一二三四五六七八九])月(.+)', text.strip()) if isinstance(text, str) else None
    if not match:
        raise APIError('format', 'The calendar service returned an unreadable lunar date.', 502)
    token = match[3]
    day = NUMBERS.get(token)
    if token.startswith('初'):
        day = NUMBERS.get(token[1:])
    elif token in ('二十', '廿'):
        day = 20
    elif token == '三十':
        day = 30
    elif len(token) == 2 and token.startswith('十') and token[1] in NUMBERS:
        day = 10 + NUMBERS[token[1]]
    elif token.startswith('廿') and token[1:] in NUMBERS:
        day = 20 + NUMBERS[token[1:]]
    elif len(token) == 3 and token.startswith('二十') and token[2] in NUMBERS:
        day = 20 + NUMBERS[token[2]]
    if not isinstance(day, int) or not 1 <= day <= 30:
        raise APIError('format', 'The calendar service returned an unreadable lunar day.', 502)
    return {'month': NUMBERS[match[2]], 'day': day, 'isLeap': bool(match[1]), 'text': text}


@lru_cache(maxsize=512)
def lookup_lunar(value):
    # Only successful results are cached. The fixed URL cannot be overridden by clients.
    try:
        response = requests.get(CALENDAR_URL, params={'date': value}, timeout=(3, 10))
        response.raise_for_status()
        data = response.json()
    except requests.Timeout:
        raise APIError('network', 'The calendar service timed out. Please retry.', 504)
    except requests.RequestException:
        raise APIError('network', 'The calendar service is temporarily unavailable. Please retry.', 502)
    except ValueError:
        raise APIError('format', 'The calendar service returned invalid JSON.', 502)
    if not isinstance(data, dict):
        raise APIError('format', 'The calendar service returned an unexpected response.', 502)
    lunar = parse_lunar(data.get('LunarDate'))
    lunar.update(year=data.get('LunarYear') if isinstance(data.get('LunarYear'), str) else '', date=value)
    return lunar


def calculate(month, day, hour_index):
    for value, maximum in ((month, 12), (day, 30), (hour_index, 12)):
        if type(value) is not int or not 1 <= value <= maximum:
            raise APIError('input', 'Invalid month, lunar day, or traditional hour.')
    month_palace = (month - 1) % 6
    day_palace = (month_palace + day - 1) % 6
    time_palace = (day_palace + hour_index - 1) % 6
    return {
        'monthPalace': month_palace, 'dayPalace': day_palace, 'timePalace': time_palace,
        'stages': [
            {'start': 0, 'count': month, 'end': month_palace},
            {'start': month_palace, 'count': day, 'end': day_palace},
            {'start': day_palace, 'count': hour_index, 'end': time_palace},
        ],
    }


def validate_clock(body):
    if not isinstance(body, dict) or set(body) != {'date', 'clock', 'timeZone'}:
        raise APIError('input', 'Send only date, clock, and timeZone. Question text is not needed.')
    validate_date(body['date'])
    clock, zone = body['clock'], body['timeZone']
    if not isinstance(clock, str) or not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d', clock):
        raise APIError('timeError', 'Use a valid 24-hour time formatted HH:MM.')
    if not isinstance(zone, str) or len(zone) > 100:
        raise APIError('timeError', 'Provide a valid IANA time zone.')
    try:
        tz = ZoneInfo(zone)
    except (ValueError, ZoneInfoNotFoundError):
        raise APIError('timeError', 'Unknown time zone.')
    wall = datetime.fromisoformat(body['date'] + 'T' + clock)
    # Detect the skipped hour during spring DST. fold=0 chooses the earlier repeated hour.
    local = wall.replace(tzinfo=tz, fold=0)
    if local.astimezone(timezone.utc).astimezone(tz).replace(tzinfo=None) != wall:
        raise APIError('dst', 'This local time does not exist because clocks move forward.')
    return wall.hour


@app.get('/')
def index():
    return jsonify(service='Ask backend', endpoints=['GET /health', 'GET /api/calendar?date=YYYY-MM-DD', 'POST /api/reading'])


@app.get('/health')
def health():
    return jsonify(status='ok', service='ask-backend')


@app.get('/api/calendar')
def calendar():
    return jsonify(lookup_lunar(validate_date(request.args.get('date'))))


@app.post('/api/reading')
def reading():
    body = request.get_json()
    hour = validate_clock(body)
    lunar = lookup_lunar(body['date'])
    hour_index = ((hour + 1) % 24) // 2 + 1
    calculation = calculate(lunar['month'], lunar['day'], hour_index)
    return jsonify(**body, lunar=lunar, hourIndex=hour_index, **calculation,
                   sign=NAMES[calculation['timePalace']])


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=int(os.environ.get('PORT', '5050')), debug=False)
