"""
Vercel Serverless Function Entry Point for SeemaSetu.
"""

from wsgi import app

# Vercel serverless function handler
handler = app
