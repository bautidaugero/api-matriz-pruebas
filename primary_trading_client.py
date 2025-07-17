import requests
from typing import Dict, Optional, Any, List
from datetime import datetime
from market_data_client import MarketDataClient

class PrimaryTradingClient:
    def __init__(self, client_id: str, client_secret: str, base_url: str = "https://api.demo.matrizoms.com.ar"):
        """
        Initialize the Primary Trading API client.
        
        Args:
            client_id: Your Primary API client ID
            client_secret: Your Primary API client secret
            base_url: The base URL for the API (defaults to production URL)
        """
        self.base_url = base_url.rstrip('/')
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.token_expiry = None

    def _get_access_token(self) -> str:
        """
        Get a valid access token, refreshing if necessary.
        
        Returns:
            str: The access token
        """
        if self.access_token and self.token_expiry and datetime.now() < self.token_expiry:
            return self.access_token

        # TODO: Implement token refresh logic
        # This is a placeholder - you'll need to implement the actual OAuth flow
        # Get token from the API using /auth/getToken and the header X-Username and X-Password	
        response = requests.post(f"{self.base_url}/auth/getToken", headers={"X-Username": self.client_id, "X-Password": self.client_secret})
        # save the token in the access_token variable. The token will be in the header response at X-Auth-Token
        self.access_token = response.headers["X-Auth-Token"]
        return self.access_token

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make an authenticated request to the API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            **kwargs: Additional arguments to pass to requests
            
        Returns:
            Dict containing the API response
        """
        headers = {
            "X-Auth-Token": self._get_access_token(),
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        if "headers" in kwargs:
            headers.update(kwargs.pop("headers"))
        
        url = f"{self.base_url}{endpoint}"
        response = requests.request(method, url, headers=headers, **kwargs)
        
        if response.status_code == 429:
            raise Exception("Rate limit exceeded")
        elif response.status_code >= 400:
            raise Exception(f"API Error: {response.text}")
            
        return response.json()

    def get_market_data(self, symbol: str) -> Dict[str, Any]:
        """Get market data for a specific symbol."""
        return self._make_request("GET", f"/rest/marketdata/{symbol}")

    def get_instruments(self) -> Dict[str, Any]:
        """Get all instruments."""
        return self._make_request("GET", "/rest/instruments/details")

    def get_instruments_by_symbol(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Get instruments that match a specific symbol.
        
        Args:
            symbol: The symbol to search for (e.g., "YPF")
            
        Returns:
            List of matching instruments
        """
        response = self.get_instruments()
        matching_instruments = []
        
        # Check if response has the expected structure
        if response.get("status") == "OK" and "instruments" in response:
            for instrument in response["instruments"]:
                # Get the symbol from the instrumentId
                instrument_symbol = instrument.get("instrumentId", {}).get("symbol", "")
                if symbol in instrument_symbol:
                    # Create a more detailed instrument dictionary
                    instrument_info = {
                        'symbol': instrument_symbol,
                        'market_id': instrument.get("instrumentId", {}).get("marketId", "N/A"),
                        'segment': {
                            'market_segment_id': instrument.get("segment", {}).get("marketSegmentId", "N/A"),
                            'market_id': instrument.get("segment", {}).get("marketId", "N/A")
                        },
                        'price_limits': {
                            'low': instrument.get("lowLimitPrice", "N/A"),
                            'high': instrument.get("highLimitPrice", "N/A")
                        },
                        'trading_info': {
                            'min_price_increment': instrument.get("minPriceIncrement", "N/A"),
                            'min_trade_vol': instrument.get("minTradeVol", "N/A"),
                            'max_trade_vol': instrument.get("maxTradeVol", "N/A"),
                            'tick_size': instrument.get("tickSize", "N/A"),
                            'contract_multiplier': instrument.get("contractMultiplier", "N/A")
                        },
                        'maturity_date': instrument.get("maturityDate", "N/A"),
                        'cficode': instrument.get("cficode", "N/A")
                    }
                    matching_instruments.append(instrument_info)
                
        return matching_instruments
    
    def get_instrument_detail(self, symbol: str, market_id: str = "ROFX") -> Dict[str, Any]:
        """Get instrument detail by symbol."""
        return self._make_request("GET", f"/rest/instruments/detail", params={"marketId": market_id, "symbol": symbol})

    def create_market_data_client(self) -> MarketDataClient:
        """
        Create a new MarketDataClient instance for real-time market data.
        
        Returns:
            MarketDataClient: A new instance of the market data client
        """
        # Convert https URL to wss URL for WebSocket and ensure it ends with a trailing slash
        ws_url = self.base_url.replace("https://", "wss://").rstrip('/') + '/'
        print(f"Creating WebSocket client with URL: {ws_url}")  # Debug print
        return MarketDataClient(access_token=self._get_access_token(), ws_url=ws_url)

# Example usage:
if __name__ == "__main__":
    # Initialize the client
    client = PrimaryTradingClient(
        client_id="api_provinciabursatil",
        client_secret="5aRg80zD_"
    )
    
    # Test get_instruments
    instruments = client.get_instruments()
    print("Instruments:")
    for instrument in instruments["instruments"]:
        print(f"Symbol: {instrument['instrumentId']['symbol']}, Market ID: {instrument['instrumentId']['marketId']}")

    try:
        # Create a market data client
        market_data_client = client.create_market_data_client()
        
        # Example callback function for market data updates
        def market_data_callback(data):
            print(f"Received market data update: {data}")

        # Subscribe to market data for specific symbols
        symbols = ["MERV - XMEV - YPFD - 24hs"]
        market_data_client.subscribe(symbols, depth=2, callback=market_data_callback)

        # Keep the main thread running
        while True:
            pass

    except KeyboardInterrupt:
        print("\nClosing connection...")
        market_data_client.close()
    except Exception as e:
        print(f"Error: {e}")
        market_data_client.close() 