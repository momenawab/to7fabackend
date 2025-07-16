import pymysql
import os
import sys
import subprocess

def create_database():
    """Create the MySQL database if it doesn't exist"""
    try:
        # Connect to MySQL server
        conn = pymysql.connect(
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
    except pymysql.Error as err:
        print(f"Error: {err}")
        return False

def create_user():
    """Create a Django user for the database"""
    try:
        # Connect to MySQL server as root
        conn = pymysql.connect(
            host="localhost",
            user="root",
            password=""
        )
        
        cursor = conn.cursor()
        
        # Create user and grant privileges
        cursor.execute("CREATE USER IF NOT EXISTS 'django_user'@'localhost' IDENTIFIED BY 'strongpass'")
        cursor.execute("GRANT ALL PRIVILEGES ON to7fa_db.* TO 'django_user'@'localhost'")
        cursor.execute("FLUSH PRIVILEGES")
        
        print("Django user created successfully or already exists.")
        
        # Close connection
        cursor.close()
        conn.close()
        
        return True
    except pymysql.Error as err:
        print(f"Error: {err}")
        return False

def run_migrations():
    """Run Django migrations"""
    try:
        subprocess.run([sys.executable, "manage.py", "migrate"], check=True)
        print("Migrations completed successfully.")
        return True
    except subprocess.CalledProcessError as err:
        print(f"Error running migrations: {err}")
        return False

if __name__ == "__main__":
    print("Setting up MySQL database for To7fa backend...")
    
    if create_database():
        if create_user():
            if run_migrations():
                print("Database setup completed successfully!")
            else:
                print("Failed to run migrations.")
        else:
            print("Failed to create Django user.")
    else:
        print("Failed to create database.") 