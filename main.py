from flask import Flask, request

from api.wise_api import WiseApi
from currency.currency import Currency

app = Flask(__name__)


@app.route('/api/current_curs')
def current_curs():
    sell = request.args.get('sell')
    buy = request.args.get('buy')

    if sell is not None and buy is not None:
        if sell in Currency.currency_dict.keys() and buy in Currency.currency_dict.keys():
            return WiseApi(sell=sell, buy=buy).current_curs()
        return f"{sell} currency is not available" if sell not in Currency.currency_dict.keys() else f"{buy} currency is not available"


@app.route('/api/monthly_curs')
def monthly_curs():
    sell = request.args.get('sell')
    buy = request.args.get('buy')

    if sell is not None and buy is not None:
        if sell in Currency.currency_dict.keys() and buy in Currency.currency_dict.keys():
            return WiseApi(sell=sell, buy=buy).monthly_range()
        return f"{sell} currency is not available" if sell not in Currency.currency_dict.keys() else f"{buy} currency is not available"


@app.route('/api/curs/<curs_code>')
def specific_currency(curs_code):
    result = {}
    currency_dict = Currency.currency_dict
    if curs_code in currency_dict.keys():
        currency_dict.pop(curs_code)

    for code in currency_dict:
        result[code] = WiseApi(sell=curs_code, buy=code).current_curs()

    return result


if __name__ == '__main__':
    app.run()
