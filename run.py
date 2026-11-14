"""
SeemaSetu — Local Development Server Launcher.
"""

import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("=" * 70)
    print("  SeemaSetu — Border Infrastructure Monitoring & Maintenance System")
    print(f"  Starting local server at http://127.0.0.1:{port}")
    print("  Demonstration Data: Unclassified & Fictional")
    print("=" * 70)
    app.run(host='127.0.0.1', port=port, debug=True)
