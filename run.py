#!/usr/bin/env python3
"""
Main entry point for the Närvarorapportering application
"""
from app.app import init_app

if __name__ == '__main__':
    app = init_app()
    app.run(debug=True, host='0.0.0.0', port=8000)
