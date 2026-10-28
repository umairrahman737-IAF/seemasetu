"""
Production WSGI Entrypoint for SeemaSetu.
Compatible with Gunicorn, uWSGI, Vercel Serverless Functions, and Azure App Service.
"""

from app import create_app

app = create_app()

# For serverless platforms where handler/app is expected
handler = app

if __name__ == "__main__":
    app.run()
