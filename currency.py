import requests

API_URL = "https://api.exchangerate.host/convert"
SYMBOLS_URL = "https://api.exchangerate.host/symbols"

def available_currencies(base="USD"):
    try:
        resp = requests.get(SYMBOLS_URL)
        if resp.status_code == 200:
            data = resp.json()
            return sorted(list(data["symbols"].keys()))
    except:
        pass
    return [base, "USD", "EUR", "INR"]

def convert_amount(amount, from_currency, to_currency):
    if from_currency == to_currency:
        return amount
    resp = requests.get(API_URL, params={"from": from_currency, "to": to_currency, "amount": amount})
    if resp.status_code == 200:
        data = resp.json()
        return data.get("result", amount)
    raise Exception("Currency conversion failed")
