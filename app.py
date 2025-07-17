from flask import Flask, render_template, request, jsonify
from primary_trading_client import PrimaryTradingClient
from dotenv import load_dotenv
import os

load_dotenv()

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')

'''Garantiza que las credenciales son un string'''
if not CLIENT_ID or not CLIENT_SECRET:
    raise ValueError("CLIENT_ID and CLIENT_SECRET must be set in .env file")

app = Flask(__name__)

# Initialize the client
client = PrimaryTradingClient(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/market_data')
def market_data():
    return render_template('market_data.html')

@app.route('/get_instrument_detail', methods=['POST'])
def get_instrument_detail():
    try:
        symbol = request.form.get('symbol')
        if not symbol:
            return jsonify({'error': 'Symbol is required'}), 400
        
        instrument_detail = client.get_instrument_detail(symbol=symbol)
        return jsonify(instrument_detail)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 