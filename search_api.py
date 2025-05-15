"""
SISTEMA INTEGRA UBS - API de pesquisa inteligente
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from search import (
    search_medications, 
    search_patients, 
    search_prescriptions,
    format_medication_result,
    format_patient_result,
    format_prescription_result
)

# Criar blueprint para a API de pesquisa
search_api = Blueprint('search_api', __name__)

@search_api.route('/api/search', methods=['GET'])
@login_required
def global_search():
    """
    Endpoint para pesquisa global que busca em medicamentos, pacientes e prescrições
    
    Parâmetros:
      - q: termo de pesquisa
      - type: tipo de pesquisa (all, medication, patient, prescription)
      - limit: limite de resultados por categoria (padrão: 5)
    """
    query = request.args.get('q', '')
    search_type = request.args.get('type', 'all')
    limit = int(request.args.get('limit', 5))
    
    if not query or len(query.strip()) < 2:
        return jsonify({
            'success': True,
            'results': {
                'medications': [],
                'patients': [],
                'prescriptions': []
            }
        })
    
    results = {'medications': [], 'patients': [], 'prescriptions': []}
    
    # Filtrar por tipo de pesquisa
    if search_type in ['all', 'medication']:
        try:
            # Usa consulta otimizada para medicamentos
            medications = search_medications(query, limit)
            
            # Pré-carregar lotes para evitar múltiplas consultas
            med_ids = [med.id for med in medications]
            
            # Só carregamos lotes se temos medicamentos para melhorar desempenho
            if med_ids:
                # Carrega lotes de uma vez só para todos os medicamentos
                from models import MedicationBatch
                batches_by_med = {}
                all_batches = MedicationBatch.query.filter(
                    MedicationBatch.medication_id.in_(med_ids)
                ).all()
                
                # Agrupa lotes por medicamento
                for batch in all_batches:
                    if batch.medication_id not in batches_by_med:
                        batches_by_med[batch.medication_id] = []
                    batches_by_med[batch.medication_id].append(batch)
                
                # Formata resultados com lotes pré-carregados
                results['medications'] = []
                for med in medications:
                    med_batches = batches_by_med.get(med.id, [])
                    results['medications'].append(
                        format_medication_result(med, preloaded_batches=med_batches)
                    )
            else:
                results['medications'] = []
                
        except Exception as e:
            print(f"Erro na busca de medicamentos: {str(e)}")
            results['medications'] = []
    
    if search_type in ['all', 'patient']:
        # Verificar permissões para pesquisa de pacientes
        if current_user.role in ['admin', 'medico', 'enfermeiro', 'recepcionista']:
            patients = search_patients(query, limit)
            results['patients'] = [format_patient_result(patient) for patient in patients]
    
    if search_type in ['all', 'prescription']:
        # Verificar permissões para pesquisa de prescrições
        if current_user.role in ['admin', 'medico', 'enfermeiro', 'farmaceutico']:
            prescriptions = search_prescriptions(query, limit)
            results['prescriptions'] = [format_prescription_result(prescription) for prescription in prescriptions]
    
    return jsonify({
        'success': True,
        'results': results
    })

def register_search_api(app):
    """Registra as rotas da API de pesquisa no app Flask"""
    app.register_blueprint(search_api)