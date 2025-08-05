import sqlite3
import logging
from datetime import datetime
from typing import Dict, List, Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Handles all database operations for Deribit data"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database and create tables"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Create table for option instrument data
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS option_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        instrument_name TEXT NOT NULL,
                        price REAL,
                        volatility REAL,
                        delta REAL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create index for faster queries
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_instrument_timestamp 
                    ON option_data(instrument_name, timestamp)
                ''')
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def insert_option_data(self, data: Dict):
        """Insert option data into database"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO option_data 
                    (instrument_name, price, volatility, delta, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    data.get('instrument_name'),
                    data.get('price'),
                    data.get('volatility'),
                    data.get('delta'),
                    data.get('timestamp', datetime.now())
                ))
                
                conn.commit()
                logger.debug(f"Inserted data for {data.get('instrument_name')}")
                
        except Exception as e:
            logger.error(f"Error inserting data: {e}")
            raise
    
    def get_last_records(self, limit: int = 10) -> List[Dict]:
        """Get the last N records from the database"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM option_data 
                    ORDER BY created_at DESC 
                    LIMIT ?
                ''', (limit,))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Error fetching records: {e}")
            return []
    
    def get_instrument_data(self, instrument_name: str, hours: int = 24) -> List[Dict]:
        """Get data for a specific instrument within the last N hours"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM option_data 
                    WHERE instrument_name = ? 
                    AND datetime(timestamp) >= datetime('now', '-{} hours')
                    ORDER BY timestamp DESC
                '''.format(hours), (instrument_name,))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Error fetching instrument data: {e}")
            return []
    
    def get_database_stats(self) -> Dict:
        """Get basic database statistics"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Total records
                cursor.execute('SELECT COUNT(*) as total FROM option_data')
                total_records = cursor.fetchone()['total']
                
                # Unique instruments
                cursor.execute('SELECT COUNT(DISTINCT instrument_name) as unique_instruments FROM option_data')
                unique_instruments = cursor.fetchone()['unique_instruments']
                
                # Latest record timestamp
                cursor.execute('SELECT MAX(timestamp) as latest_timestamp FROM option_data')
                latest_timestamp = cursor.fetchone()['latest_timestamp']
                
                return {
                    'total_records': total_records,
                    'unique_instruments': unique_instruments,
                    'latest_timestamp': latest_timestamp
                }
                
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {}