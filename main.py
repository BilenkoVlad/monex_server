from flask import Flask, request, jsonify

from api.wise_api import WiseApi
from currency.currency import Currency
import dotenv

dotenv.load_dotenv()

app = Flask(__name__)


@app.route('/', methods=['GET'])
def start():
    return "Currency Rates API"


@app.route('/api/available-currencies', methods=['GET'])
def available_currencies():
    # 'list(...)' is required as jsonify(...) fails otherwise
    currencies = list(Currency.currency_dict.keys())

    return jsonify({
        "available_currencies": currencies
    })


@app.route('/api/rates', methods=['GET'])
def current_rates():
    sell = request.args.get('sell')
    buy = request.args.get('buy')

    validation_error = validate_sell_buy_params(sell, buy)
    if validation_error:
        return jsonify({"message": validation_error}), 400

    data = WiseApi(sell=sell, buy=buy).current_curs()
    return jsonify(data)


@app.route('/api/rates/monthly', methods=['GET'])
def monthly_rates():
    sell = request.args.get('sell')
    buy = request.args.get('buy')

    validation_error = validate_sell_buy_params(sell, buy)
    if validation_error:
        return jsonify({"message": validation_error}), 400

    data = WiseApi(sell=sell, buy=buy).monthly_range()
    return jsonify(data)


@app.route('/api/rates/<code>', methods=['GET'])
async def specific_currency(code):
    result = {}
    currency_dict = Currency.currency_dict.copy()

    if code in currency_dict:
        currency_dict.pop(code)
    else:
        return f"Currency {code} is not available"

    for other_currencies in currency_dict:
        result[other_currencies] = WiseApi(sell=code, buy=other_currencies).current_curs()

    return result


def validate_sell_buy_params(sell, buy):
    if not sell or not buy:
        return "'sell' and 'buy' are required"

    currencies = Currency.currency_dict.keys()

    if sell.upper() not in currencies:
        return f"Sell currency - {sell} is not available"

    if buy.upper() not in currencies:
        return f"Buy currency - {buy} is not available"


if __name__ == '__main__':
    app.run()
