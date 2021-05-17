from flask import Flask, abort, jsonify, request, redirect
from flask.json import JSONEncoder
from flask_cors import CORS
from common import scraper
from datetime import datetime


# for customizing the format of datetime objects
class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        try:
            if isinstance(obj, datetime):
                return obj.timestamp()
            iterable = iter(obj)
        except TypeError:
            pass
        else:
            return list(iterable)
        return JSONEncoder.default(self, obj)


app = Flask(__name__)
app.json_encoder = CustomJSONEncoder
cors = CORS(app, origins=["http://localhost:3000"], supports_credentials=True)


@app.route("/get_user_data", methods=["POST"])
def get_user_transactions():
    data = request.json
    df, account_balances = scraper.get_user_transactions(data["email"], data["password"])
    user_transactions_summary = scraper.summarize_user_transactions_df(df)
    timeseries_data = scraper.get_timeseries_data_from_df(df)
    df = df.reset_index()
    return jsonify({
        "user_transactions": list(reversed(df.to_dict('records'))),
        "user_transactions_summary": user_transactions_summary,
        "timeseries_data": timeseries_data,
        "account_balances": account_balances
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
