"""
SISTEMA INTEGRA UBS - Ponto de entrada
"""
import os
import webbrowser
from threading import Timer
from app import app

# No ambiente Replit, use o arquivo estático simples caso seja solicitado um preview
if os.environ.get("REPL_SLUG") is not None and os.environ.get("REPL_OWNER") is not None:
    # Estamos no Replit
    from flask import send_from_directory
    
    @app.route('/replit-static')
    def serve_static_preview():
        """Serve o arquivo HTML estático para o preview do Replit"""
        return send_from_directory(".", "index.html")

# Função para abrir o navegador automaticamente
def open_browser():
    webbrowser.open_new('http://127.0.0.1:5000/')
    print("Navegador aberto automaticamente!")

if __name__ == '__main__':
    print("Iniciando Sistema Integra UBS...")
    print("Acesse: http://127.0.0.1:5000")
    print("Use admin/1234 para login")
    
    # Inicia um timer para abrir o navegador após 1 segundo
    Timer(1.0, open_browser).start()
    
    # Inicia o servidor
    app.run(host='0.0.0.0', port=5000, debug=True)