import asyncio
import logging
import signal
import sys
from datetime import datetime
from typing import List, Dict

from config import Config
from database import DatabaseManager
from deribit_client import DeribitRestClient, DeribitWebSocketClient

# Configure logging
def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, Config.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(Config.LOG_FILE),
            logging.StreamHandler(sys.stdout)
        ]
    )

logger = logging.getLogger(__name__)

class DeribitDataCollector:
    """Main application class for collecting Deribit data"""
    
    def __init__(self):
        self.db_manager = DatabaseManager(Config.DATABASE_PATH)
        self.ws_client = None
        self.running = True
        
    async def data_callback(self, data: Dict):
        """Callback function for processing WebSocket data"""
        try:
            # Store data in database
            self.db_manager.insert_option_data(data)
            
            # Log the data
            logger.info(f"Stored data for {data['instrument_name']}: "
                       f"Price={data['price']}, IV={data['volatility']}, Delta={data['delta']}")
            
        except Exception as e:
            logger.error(f"Error in data callback: {e}")
    
    async def fetch_instruments(self) -> List[str]:
        """Fetch option instruments using REST API"""
        try:
            async with DeribitRestClient() as client:
                instruments = await client.get_instruments(currency="BTC", kind="option")
                
                if not instruments:
                    logger.warning("No instruments found")
                    return []
                
                # Filter instruments and select first 5 for WebSocket subscription
                # You can modify this logic to filter by expiry date or other criteria
                selected_instruments = []
                for instrument in instruments[:10]:  # Take first 10 to have options
                    if len(selected_instruments) >= 5:
                        break
                    
                    # Filter for active instruments with reasonable expiry
                    if (instrument.get('is_active') and 
                        instrument.get('expiration_timestamp', 0) > datetime.now().timestamp() * 1000):
                        selected_instruments.append(instrument['instrument_name'])
                
                logger.info(f"Selected {len(selected_instruments)} instruments for subscription")
                return selected_instruments
                
        except Exception as e:
            logger.error(f"Error fetching instruments: {e}")
            return []
    
    async def start_websocket_client(self, instruments: List[str]):
        """Start WebSocket client and subscribe to instruments"""
        try:
            self.ws_client = DeribitWebSocketClient(self.data_callback)
            
            # Connect and subscribe
            await self.ws_client.connect()
            await self.ws_client.subscribe_to_ticker(instruments)
            
        except Exception as e:
            logger.error(f"WebSocket client error: {e}")
            raise
    
    async def run(self):
        """Main application loop"""
        try:
            logger.info("Starting Deribit Data Collector")
            
            # Validate configuration
            Config.validate()
            
            # Fetch instruments via REST API
            instruments = await self.fetch_instruments()
            if not instruments:
                logger.error("No instruments available for subscription")
                return
            
            logger.info(f"Selected instruments: {', '.join(instruments)}")
            
            # Start WebSocket client
            await self.start_websocket_client(instruments)
            
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down...")
            self.running = False
        except Exception as e:
            logger.error(f"Application error: {e}")
            raise
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            if self.ws_client:
                await self.ws_client.close()
            logger.info("Application cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def show_last_records(self, limit: int = 10):
        """Show last N records from database"""
        try:
            records = self.db_manager.get_last_records(limit)
            
            if not records:
                print("No records found in database")
                return
            
            print(f"\n=== Last {len(records)} Records ===")
            for record in records:
                print(f"ID: {record['id']}")
                print(f"Instrument: {record['instrument_name']}")
                print(f"Price: {record['price']}")
                print(f"Volatility: {record['volatility']}")
                print(f"Delta: {record['delta']}")
                print(f"Timestamp: {record['timestamp']}")
                print("-" * 50)
                
        except Exception as e:
            logger.error(f"Error showing records: {e}")
    
    def show_database_stats(self):
        """Show database statistics"""
        try:
            stats = self.db_manager.get_database_stats()
            
            print("\n=== Database Statistics ===")
            print(f"Total Records: {stats.get('total_records', 0)}")
            print(f"Unique Instruments: {stats.get('unique_instruments', 0)}")
            print(f"Latest Timestamp: {stats.get('latest_timestamp', 'N/A')}")
            print("=" * 30)
            
        except Exception as e:
            logger.error(f"Error showing stats: {e}")

def signal_handler(signum, frame):
    """Handle system signals for graceful shutdown"""
    logger.info(f"Received signal {signum}, preparing to shutdown...")
    sys.exit(0)

async def main():
    """Main function"""
    setup_logging()
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    collector = DeribitDataCollector()
    
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "show-records":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            collector.show_last_records(limit)
            return
        elif sys.argv[1] == "show-stats":
            collector.show_database_stats()
            return
    
    # Run the main collector
    await collector.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)