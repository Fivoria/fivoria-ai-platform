"""
Database schema and connection utilities for Fivoria AI Platform
"""

import os
from dotenv import load_dotenv

load_dotenv()

class MockConnection:
    """Mock database connection for development"""
    def __init__(self):
        self.closed = False
        self.data = {
            'projects': [],
            'conversations': [],
            'files': []
        }
    
    def cursor(self, dictionary=False):
        return MockCursor(self, dictionary)
    
    def commit(self):
        pass
    
    def close(self):
        self.closed = True

class MockCursor:
    """Mock database cursor for development"""
    def __init__(self, connection, dictionary=False):
        self.connection = connection
        self.dictionary = dictionary
        self._results = []
    
    def execute(self, query, params=None):
        # Mock execute - in production this would run the actual query
        pass
    
    def fetchone(self):
        if self._results:
            return self._results.pop(0)
        return None
    
    def fetchall(self):
        results = self._results
        self._results = []
        return results
    
    def close(self):
        pass

def get_db_connection():
    """Get database connection (mock for development)"""
    return MockConnection()
