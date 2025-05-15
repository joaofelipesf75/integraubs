"""
SISTEMA INTEGRA UBS - Módulo de API para o Chat Rápido
"""
from datetime import datetime
from flask import jsonify, request, Blueprint
from flask_login import login_required, current_user
from app import db
from models import ChatMensagem, User

# Criar um Blueprint para as rotas da API do chat
chat_api = Blueprint('chat_api', __name__)

@chat_api.route('/api/chat-rapido/mensagens', methods=['GET'])
@login_required
def get_mensagens():
    """Retorna as últimas 50 mensagens do chat rápido"""
    try:
        # Obter as últimas 50 mensagens do banco de dados
        mensagens = ChatMensagem.query.order_by(
            ChatMensagem.created_at.desc()
        ).limit(50).all()
        
        # Inverter para ordem cronológica (mais antigas primeiro)
        mensagens.reverse()
        
        # Converter para dicionários
        mensagens_dict = [msg.to_dict() for msg in mensagens]
        
        return jsonify({
            'success': True,
            'mensagens': mensagens_dict
        })
    except Exception as e:
        return jsonify({
            'success': False, 
            'message': f'Erro ao obter mensagens: {str(e)}'
        }), 500

@chat_api.route('/api/chat-rapido/enviar', methods=['POST'])
@login_required
def enviar_mensagem():
    """Envia uma nova mensagem para o chat rápido"""
    try:
        # Obter dados da requisição
        data = request.get_json(silent=True)
        if not data:
            return jsonify({
                'success': False,
                'message': 'Dados da requisição inválidos'
            }), 400
            
        texto = data.get('texto', '').strip()
        
        if not texto:
            return jsonify({
                'success': False,
                'message': 'Texto da mensagem não pode ser vazio'
            }), 400
        
        # Criar nova mensagem
        nova_mensagem = ChatMensagem(
            usuario_id=current_user.id,
            texto=texto,
            created_at=datetime.utcnow()
        )
        
        # Salvar no banco de dados
        db.session.add(nova_mensagem)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'mensagem': nova_mensagem.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao enviar mensagem: {str(e)}'
        }), 500
        
@chat_api.route('/api/chat-rapido/editar/<int:id>', methods=['PUT'])
@login_required
def editar_mensagem(id):
    """Edita uma mensagem existente no chat rápido"""
    try:
        # Obter a mensagem pelo ID
        mensagem = ChatMensagem.query.get_or_404(id)
        
        # Verificar se o usuário é o autor da mensagem
        if mensagem.usuario_id != current_user.id:
            return jsonify({
                'success': False,
                'message': 'Você só pode editar suas próprias mensagens'
            }), 403
            
        # Obter dados da requisição
        data = request.get_json(silent=True)
        if not data:
            return jsonify({
                'success': False,
                'message': 'Dados da requisição inválidos'
            }), 400
            
        novo_texto = data.get('texto', '').strip()
        
        if not novo_texto:
            return jsonify({
                'success': False,
                'message': 'Texto da mensagem não pode ser vazio'
            }), 400
            
        # Atualizar a mensagem
        mensagem.texto = novo_texto
        db.session.commit()
        
        return jsonify({
            'success': True,
            'mensagem': mensagem.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao editar mensagem: {str(e)}'
        }), 500
        
@chat_api.route('/api/chat-rapido/excluir/<int:id>', methods=['DELETE'])
@login_required
def excluir_mensagem(id):
    """Exclui uma mensagem do chat rápido"""
    try:
        # Obter a mensagem pelo ID
        mensagem = ChatMensagem.query.get_or_404(id)
        
        # Verificar se o usuário é o autor da mensagem
        if mensagem.usuario_id != current_user.id:
            return jsonify({
                'success': False,
                'message': 'Você só pode excluir suas próprias mensagens'
            }), 403
            
        # Excluir a mensagem
        db.session.delete(mensagem)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Mensagem excluída com sucesso'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao excluir mensagem: {str(e)}'
        }), 500

def register_chat_api(app):
    """Registra o Blueprint da API de chat no app Flask"""
    app.register_blueprint(chat_api)