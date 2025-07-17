import websocket
import json
import threading
from typing import Dict, Optional, Any, List, Callable
from datetime import datetime

class MarketDataClient:
    def __init__(self, access_token: str, ws_url: str = "wss://api.demo.matrizoms.com.ar"):
        """
        Initialize the Market Data WebSocket client.
        
        Args:
            access_token: The access token for authentication
            ws_url: The WebSocket URL (defaults to production URL)
        """
        # Ensure the URL ends with a trailing slash
        ws_url = ws_url.rstrip('/') + '/'
        self.ws_url = ws_url
        self.access_token = access_token
        self.ws = None
        self.ws_thread = None
        self.subscriptions = {}
        self.callbacks = {}
        self.connected = False
        self.connection_event = threading.Event()

    def subscribe(self, symbols: List[str], depth: int = 1, callback: Optional[Callable] = None) -> None:
        """
        Subscribe to real-time market data for specified symbols.
        
        Args:
            symbols: List of symbols to subscribe to
            depth: Order book depth (default: 1)
            callback: Optional callback function to handle updates
        """
        if not self.ws:
            self._connect_websocket()
            
        # Wait for connection to be established
        if not self.connection_event.wait(timeout=10):
            raise Exception("Failed to establish WebSocket connection - connection timeout")
            
        # Create subscription message
        subscription_msg = {
            "type": "smd",
            "level": 1,
            "entries": ["OF"],
            "products": [{"symbol": symbol, "marketId": "ROFX"} for symbol in symbols],
            "depth": depth
        }
        
        try:
            self.ws.send(json.dumps(subscription_msg))
            
            # Store subscription and callback
            for symbol in symbols:
                self.subscriptions[symbol] = depth
                if callback:
                    self.callbacks[symbol] = callback
        except Exception as e:
            raise

    def unsubscribe(self, symbols: List[str]) -> None:
        """
        Unsubscribe from market data for specified symbols.
        
        Args:
            symbols: List of symbols to unsubscribe from
        """
        if not self.ws or not self.ws.sock or not self.ws.sock.connected:
            return

        # Prepare unsubscribe message in the correct format
        unsubscribe_msg = {
            "type": "smd",
            "level": 1,
            "entries": ["OF"],
            "products": [
                {
                    "symbol": symbol,
                    "marketId": "ROFX"  # Default market ID, you might want to make this configurable
                }
                for symbol in symbols
            ],
            "depth": 0  # Set depth to 0 to unsubscribe
        }

        # Send unsubscribe message
        self.ws.send(json.dumps(unsubscribe_msg))

        # Remove subscriptions and callbacks
        for symbol in symbols:
            self.subscriptions.pop(symbol, None)
            self.callbacks.pop(symbol, None)

    def _connect_websocket(self) -> None:
        """Establish WebSocket connection with authentication."""
        try:
            # Create WebSocket connection with authentication header
            self.ws = websocket.WebSocketApp(
                self.ws_url,
                header={'X-Auth-Token': self.access_token},
                on_message=self._on_ws_message,
                on_error=self._on_ws_error,
                on_close=self._on_ws_close,
                on_open=self._on_ws_open
            )

            # Start WebSocket connection in a separate thread
            self.ws_thread = threading.Thread(target=self.ws.run_forever)
            self.ws_thread.daemon = True
            self.ws_thread.start()
            
            # Wait for connection to be established
            if not self.connection_event.wait(timeout=10):
                raise Exception("WebSocket connection timeout - failed to establish connection within 10 seconds")
                
        except Exception as e:
            raise

    def _on_ws_message(self, ws, message: str) -> None:
        """Handle incoming WebSocket messages."""
        try:
            data = json.loads(message)
            
            # Check if this is a market data message
            if data.get("type") == "Md":
                symbol = data.get("instrumentId", {}).get("symbol")
                if symbol in self.callbacks:
                    self.callbacks[symbol](data)
        except json.JSONDecodeError as e:
            pass

    def _on_ws_error(self, ws, error) -> None:
        """Handle WebSocket errors."""
        self.connected = False
        self.connection_event.clear()
        # Attempt to reconnect after a delay
        threading.Timer(5.0, self._connect_websocket).start()

    def _on_ws_close(self, ws, close_status_code, close_msg) -> None:
        """Handle WebSocket connection close."""
        self.connected = False
        self.connection_event.clear()
        # Attempt to reconnect after a delay
        threading.Timer(5.0, self._connect_websocket).start()

    def _on_ws_open(self, ws) -> None:
        """Handle WebSocket connection open."""
        self.connected = True
        self.connection_event.set()
        
    def close(self):
        """Close the WebSocket connection."""
        if self.ws:
            self.ws.close()
            self.ws = None
        if self.ws_thread:
            self.ws_thread.join(timeout=1)
            self.ws_thread = None
        self.connected = False
        self.connection_event.clear()

# Example usage:
if __name__ == "__main__":
    # Initialize the client with your access token
    client = MarketDataClient(access_token="your_access_token")
    
    try:
        # Example callback function for market data updates
        def market_data_callback(data):
            print(f"Received market data update: {data}")

        # Subscribe to market data for specific symbols
        symbols = ["DLR/DIC23", "SOJ.ROS/MAY23"]
        client.subscribe(symbols, depth=2, callback=market_data_callback)

        # Keep the main thread running
        while True:
            pass

    except KeyboardInterrupt:
        print("\nClosing connection...")
        client.close()
    except Exception as e:
        print(f"Error: {e}")
        client.close() 