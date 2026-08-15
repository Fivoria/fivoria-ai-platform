"""
Database setup script for Fivoria AI Platform
Creates database and imports schema
"""

import pymysql
import sys
import os

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'charset': 'utf8mb4'
}

def create_database():
    """Create fivoria database"""
    try:
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # Create database
        cursor.execute("CREATE DATABASE IF NOT EXISTS fivoria CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print("✓ Database 'fivoria' created successfully")
        
        cursor.close()
        connection.close()
        return True
    except Exception as e:
        print(f"✗ Failed to create database: {e}")
        print("Please ensure MySQL is running and accessible")
        return False

def import_schema():
    """Import schema from database/schema.sql"""
    schema_path = os.path.join(os.path.dirname(__file__), '../database/schema.sql')
    
    if not os.path.exists(schema_path):
        print(f"✗ Schema file not found: {schema_path}")
        return False
    
    try:
        connection = pymysql.connect(**DB_CONFIG, database='fivoria')
        cursor = connection.cursor()
        
        with open(schema_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        # Split by semicolon and execute each statement
        statements = [s.strip() for s in sql_script.split(';') if s.strip()]
        
        for statement in statements:
            if statement:
                try:
                    cursor.execute(statement)
                except Exception as e:
                    print(f"Warning: Failed to execute statement: {e}")
                    print(f"Statement: {statement[:100]}...")
        
        connection.commit()
        print("✓ Schema imported successfully")
        
        cursor.close()
        connection.close()
        return True
    except Exception as e:
        print(f"✗ Failed to import schema: {e}")
        return False

if __name__ == "__main__":
    print("Setting up Fivoria AI Platform database...")
    print()
    
    if create_database():
        import_schema()
    
    print()
    print("Database setup complete!")
