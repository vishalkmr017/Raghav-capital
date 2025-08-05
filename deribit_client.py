import asyncio
import json
import logging
import websockets
import aiohttp
from datetime import datetime
from typing import Dict, List, Optional, Callable
from config import Config

logger = logging.getLogger(__name__)

class DeribitRestClient:
    """REST API client for Deribit"""
    
    def __init__(self):
        self.base_url = Config.DERIBIT_BASE_URL
        self.client_id = Config.DERIBIT_CLIENT_ID
        self.client_secret = Config.DERIBIT_CLIENT_SECRET
        self.access_token = None
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        await self.authenticate()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def authenticate(self):
        """Authenticate with Deribit API"""
        try:
            auth_data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'grant_type': 'client_credentials'
            }
            
            async with self.session.post(
                f"{self.base_url}/api/v2/public/auth",
                json=auth_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    self.access_token = result['result']['access_token']
                    logger.info("Successfully authenticated with Deribit API")
                else:
                    error_text = await response.text()
                    raise Exception(f"Authentication failed: {error_text}")
                    
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise
    
    async def get_instruments(self, currency: str = "BTC", kind: str = "option", expired: bool = False) -> List[Dict]:
        """Fetch option instruments"""
        try:
            params = {
                'currency': currency,
                'kind': kind,
                'expired': expired
            }
            
            headers = {'Authorization': f'Bearer {self.access_token}'}
            
            async with self.session.get(
                f"{self.base_url}/api/v2/public/get_instruments",
                params=params,
                headers=headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    instruments = result['result']
                    logger.info(f"Fetched {len(instruments)} {kind} instruments for {currency}")
                    return instruments
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to fetch instruments: {error_text}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error fetching instruments: {e}")
            return []
    
    async def get_ticker(self, instrument_name: str) -> Optional[Dict]:
        """Get ticker data for a specific instrument"""
        try:
            params = {'instrument_name': instrument_name}
            headers = {'Authorization': f'Bearer {self.access_token}'}
            
            async with self.session.get(
                f"{self.base_url}/api/v2/public/ticker",
                params=params,
                headers=headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result['result']
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to fetch ticker for {instrument_name}: {error_text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error fetching ticker: {e}")
            return None

class DeribitWebSocketClient:
    """WebSocket client for Deribit real-time data"""
    
    def __init__(self, data_callback: Callable[[Dict], None]):
        self.ws_url = Config.DERIBIT_WS_URL
        self.client_id = Config.DERIBIT_CLIENT_ID
        self.client_secret = Config.DERIBIT_CLIENT_SECRET
        self.data_callback = data_callback
        self.websocket = None
        self.is_authenticated = False
        self.subscribed_instruments = set()
        
    async def connect(self):
        """Connect to WebSocket and authenticate"""
        try:
            self.websocket = await websockets.connect(self.ws_url)
            logger.info("Connected to Deribit WebSocket")
            
            # Authenticate
            await self.authenticate()
            
            # Start listening for messages
            await self.listen()
            
        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")
            raise
    
    async def authenticate(self):
        """Authenticate WebSocket connection"""
        try:
            auth_message = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "public/auth",
                "params": {
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret
                }
            }
            
            await self.websocket.send(json.dumps(auth_message))
            
            # Wait for authentication response
            response = await self.websocket.recv()
            data = json.loads(response)
            
            if 'result' in data and 'access_token' in data['result']:
                self.is_authenticated = True
                logger.info("WebSocket authenticated successfully")
            else:
                raise Exception(f"WebSocket authentication failed: {data}")
                
        except Exception as e:
            logger.error(f"WebSocket authentication error: {e}")
            raise
    
    async def subscribe_to_ticker(self, instrument_names: List[str]):
        """Subscribe to ticker updates for multiple instruments"""
        try:
            if not self.is_authenticated:
                raise Exception("Not authenticated")
            
            channels = [f"ticker.{instrument}.raw" for instrument in instrument_names]
            
            subscribe_message = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "public/subscribe",
                "params": {
                    "channels": channels
                }
            }
            
            await self.websocket.send(json.dumps(subscribe_message))
            
            # Wait for subscription response
            response = await self.websocket.recv()
            data = json.loads(response)
            
            if 'result' in data:
                self.subscribed_instruments.update(instrument_names)
                logger.info(f"Subscribed to {len(instrument_names)} instruments")
            else:
                logger.error(f"Subscription failed: {data}")
                
        except Exception as e:
            logger.error(f"Subscription error: {e}")
            raise
    
    async def listen(self):
        """Listen for WebSocket messages"""
        try:
            while True:
                try:
                    message = await asyncio.wait_for(self.websocket.recv(), timeout=30.0)
                    data = json.loads(message)
                    
                    # Process ticker data
                    if 'params' in data and 'data' in data['params']:
                        ticker_data = data['params']['data']
                        await self.process_ticker_data(ticker_data)
                    
                except asyncio.TimeoutError:
                    # Send ping to keep connection alive
                    ping_message = {
                        "jsonrpc": "2.0",
                        "id": 99,
                        "method": "public/ping"
                    }
                    await self.websocket.send(json.dumps(ping_message))
                    
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    
        except Exception as e:
            logger.error(f"WebSocket listening error: {e}")
            raise
    
    async def process_ticker_data(self, ticker_data: Dict):
        """Process incoming ticker data"""
        try:
            processed_data = {
                'instrument_name': ticker_data.get('instrument_name'),
                'price': ticker_data.get('mark_price') or ticker_data.get('last_price'),
                'volatility': ticker_data.get('mark_iv'),
                'delta': ticker_data.get('greeks', {}).get('delta') if ticker_data.get('greeks') else None,
                'timestamp': datetime.fromtimestamp(ticker_data.get('timestamp', 0) / 1000)
            }
            
            # Call the data callback
            if self.data_callback:
                await self.data_callback(processed_data)
                
        except Exception as e:
            logger.error(f"Error processing ticker data: {e}")
    
    async def close(self):
        """Close WebSocket connection"""
        if self.websocket:
            await self.websocket.close()
            logger.info("WebSocket connection closed")