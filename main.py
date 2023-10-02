from flask import Flask, request, jsonify

from api.wise_api import WiseApi
from api.x_change_api import XChangeApi
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

    if code == Currency.CZK:
        currency_dict.pop(Currency.USD)
        currency_dict.pop(Currency.EUR)
    if code == Currency.USD:
        currency_dict.pop(Currency.CZK)
    if code == Currency.EUR:
        currency_dict.pop(Currency.CZK)

    result.update(own_czk_rates(give_currency=code))

    if code in currency_dict:
        currency_dict.pop(code)
    else:
        return f"Currency {code} is not available"

    for other_currencies in currency_dict:
        result[other_currencies] = WiseApi(sell=code, buy=other_currencies).current_curs()[0]

        if other_currencies == Currency.UAH:
            result[other_currencies]["rate"] = round(
                result[other_currencies]["rate"] + result[other_currencies]["rate"] * 0.0385, 3)
        else:
            result[other_currencies]["rate"] = round(result[other_currencies]["rate"], 3)

    return result


def validate_sell_buy_params(sell, buy):
    if not sell or not buy:
        return "'sell' and 'buy' are required"

    currencies = Currency.currency_dict.keys()

    if sell.upper() not in currencies:
        return f"Sell currency - {sell} is not available"

    if buy.upper() not in currencies:
        return f"Buy currency - {buy} is not available"


def own_czk_rates(give_currency):
    result = {}
    response = XChangeApi().czk_rates()["rates"]
    for rate in response:
        try:
            if give_currency == Currency.CZK:
                if rate["curr"] == Currency.USD or rate["curr"] == Currency.EUR:
                    result[rate["curr"]] = {
                        "rate": rate["sell"]["value"],
                        "source": "CZK",
                        "target": rate["curr"],
                    }
            elif give_currency == Currency.USD:
                if rate["curr"] == Currency.USD:
                    result["CZK"] = {
                        "rate": rate["buy"]["value"],
                        "source": rate["curr"],
                        "target": "CZK",
                    }
            elif give_currency == Currency.EUR:
                if rate["curr"] == Currency.EUR:
                    result["CZK"] = {
                        "rate": rate["buy"]["value"],
                        "source": rate["curr"],
                        "target": "CZK",
                    }
        except TypeError:
            print(f"JSON has invalid data in {rate}")

    return result


if __name__ == '__main__':
    app.run(port=5001)
