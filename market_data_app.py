from flask import Flask, request, jsonify, render_template
from flask_sock import Sock
from market_data_client import MarketDataClient
from primary_trading_client import PrimaryTradingClient
import threading
import json
from dotenv import load_dotenv
import os

load_dotenv()

"""Funcion que asegura que las credenciales van a ser un string"""
def get_required_env(key: str) -> str:
    """Get required environment variable or raise error"""
    value = os.getenv(key)
    if value is None:
        raise ValueError(f"{key} environment variable is required")
    return value

app = Flask(__name__)
sock = Sock(app)

# Global variables
market_data_client = None
market_data_thread = None
primary_client = None
connected_clients = set()
received_messages = []

# Hardcoded credentials
CLIENT_ID = get_required_env('CLIENT_ID')
CLIENT_SECRET = get_required_env('CLIENT_SECRET')
WS_URL = get_required_env('WS_URL')

def market_data_callback(data):
    """Callback function to handle market data updates"""
    # Send the message to all connected WebSocket clients
    for client in connected_clients:
        try:
            client.send(json.dumps(data))
        except:
            connected_clients.remove(client)

@sock.route('/ws')
def handle_websocket(ws):
    connected_clients.add(ws)
    try:
        while True:
            # Keep the connection alive
            ws.receive()
    except:
        connected_clients.remove(ws)

@app.route('/')
def index():
    return render_template('market_data.html')

@app.route('/get_instruments', methods=['GET'])
def get_instruments():
    global primary_client
    try:
        if primary_client is None:
            return jsonify({'error': 'Not connected'}), 400
            
        instruments = primary_client.get_instruments()
        if instruments.get('status') == 'OK':
            # Extract symbols from instruments
            symbols = [instrument['instrumentId']['symbol'] for instrument in instruments['instruments']]
            return jsonify({'symbols': symbols})
        return jsonify({'error': 'Failed to get instruments'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/connect', methods=['POST'])
def connect():
    global market_data_client, market_data_thread, primary_client
    if market_data_client is None:
        try:
            # Initialize PrimaryTradingClient with hardcoded credentials
            primary_client = PrimaryTradingClient(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
            access_token = primary_client._get_access_token()
            
            # Create MarketDataClient with the obtained token and explicit WebSocket URL
            ws_url = WS_URL  # Explicit WebSocket URL
            market_data_client = MarketDataClient(access_token=access_token, ws_url=ws_url)
            return jsonify({'status': 'connected'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    return jsonify({'status': 'already connected'})

@app.route('/disconnect', methods=['POST'])
def disconnect():
    global market_data_client, market_data_thread, primary_client
    if market_data_client:
        market_data_client.close()
        market_data_client = None
        primary_client = None
        return jsonify({'status': 'disconnected'})
    return jsonify({'status': 'not connected'})

@app.route('/subscribe', methods=['POST'])
def subscribe():
    global market_data_client
    if not market_data_client:
        return jsonify({'error': 'Not connected'}), 400
    
    symbol = request.json.get('symbol')
    if not symbol:
        return jsonify({'error': 'Symbol is required'}), 400
    
    try:
        market_data_client.subscribe([symbol], callback=market_data_callback)
        return jsonify({'status': 'subscribed', 'symbol': symbol})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/messages', methods=['GET'])
def get_messages():
    return jsonify({'messages': received_messages})

@app.route('/market-data')
def market_data():
    return render_template('market_data.html')

if __name__ == '__main__':
    app.run(debug=True) 