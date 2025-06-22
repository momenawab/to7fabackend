import mysql.connector
import os
import sys
import subprocess

def create_database():
    """Create the MySQL database if it doesn't exist"""
    try:
        # Connect to MySQL server
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password=""
        )
        
        cursor = conn.cursor()
        
        # Create database if it doesn't exist
        cursor.execute("CREATE DATABASE IF NOT EXISTS to7fa_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        
        print("Database 'to7fa_db' created successfully or already exists.")
        
        # Close connection
        cursor.close()
        conn.close()
        
        return True
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return False

def run_migrations():
    """Run Django migrations"""
    try:
        # Run migrations
        subprocess.run([sys.executable, "manage.py", "migrate"], check=True)
        print("Migrations completed successfully.")
        
        return True
    except subprocess.CalledProcessError as err:
        print(f"Error running migrations: {err}")
        return False

def create_superuser():
    """Create a superuser if needed"""
    try:
        # Check if we want to create a superuser
        create = input("Do you want to create a superuser? (y/n): ").lower()
        
        if create == 'y':
            subprocess.run([sys.executable, "manage.py", "createsuperuser"], check=False)
            print("Superuser creation process completed.")
        
        return True
    except Exception as err:
        print(f"Error creating superuser: {err}")
        return False

if __name__ == "__main__":
    print("Setting up MySQL database for Tohfa Backend...")
    
    if create_database():
        if run_migrations():
            create_superuser()
    
    print("Setup process completed.") 