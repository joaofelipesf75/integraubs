"""
Servidor simples para o preview no Replit
Use:
python replit_preview.py
"""
from flask import Flask, send_from_directory

# Cria um app Flask extremamente simples
app = Flask(__name__, static_folder=".", static_url_path="")

@app.route('/')
def serve_index():
    """Serve o arquivo HTML estático"""
    return send_from_directory(".", "index.html")

# Apenas para executar este arquivo diretamente
if __name__ == "__main__":
    print("Servidor simples para preview iniciado")
    print("Acesse http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)