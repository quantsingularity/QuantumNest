#!/usr/bin/env python3
"""Run Flask application"""
import os

# Set environment variables for testing
os.environ["DATABASE_URL"] = "sqlite:///./quantumnest.db"
os.environ["SECRET_KEY"] = "test-secret-key-min-32-characters-long-for-security"

from app.main_flask import create_app

if __name__ == "__main__":
    app = create_app()
    print("\n" + "=" * 60)
    print("QuantumNest Capital API Server Starting...")
    print("=" * 60)
    print(f"Server running at: http://127.0.0.1:5000")
    print(f"Health check: http://127.0.0.1:5000/health")
    print("=" * 60 + "\n")

    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
