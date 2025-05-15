"""
SISTEMA INTEGRA UBS - Módulo de pesquisa inteligente
"""
from sqlalchemy import or_, and_, func
from models import Medication, Patient, Prescription, MedicationBatch, User

def search_medications(query, limit=10):
    """
    Pesquisa inteligente de medicamentos
    
    Busca por nome, princípio ativo, descrição, forma ou concentração
    Prioriza resultados mais relevantes
    """
    if not query or len(query.strip()) < 2:
        return []
    
    search_term = f"%{query.lower()}%"
    exact_term = query.lower()
    starts_term = f"{query.lower()}%"
    
    # Consulta otimizada que prioriza resultados mais relevantes na própria query SQL
    # Isso melhora significativamente o desempenho para grandes conjuntos de dados
    medications = Medication.query.filter(
        or_(
            func.lower(Medication.nome).like(search_term),
            func.lower(Medication.principio_ativo).like(search_term),
            func.lower(Medication.descricao).like(search_term),
            func.lower(Medication.forma).like(search_term),
            func.lower(Medication.concentracao).like(search_term)
        )
    ).order_by(
        # Prioriza correspondências exatas no nome (usando case when)
        (func.lower(Medication.nome) == exact_term).desc(),
        # Depois prioriza nomes que começam com o termo
        (func.lower(Medication.nome).like(starts_term)).desc(),
        # Por último, prioriza correspondências no princípio ativo
        (func.lower(Medication.principio_ativo).like(starts_term)).desc(),
        # Ordenação alfabética como critério final
        Medication.nome
    ).limit(limit).all()
    
    return medications

def search_patients(query, limit=10):
    """
    Pesquisa inteligente de pacientes
    
    Busca por nome, CPF, número do cartão SUS, telefone
    Ordena por relevância baseado na correspondência exata com CPF ou cartão SUS
    """
    if not query or len(query.strip()) < 2:
        return []
    
    search_term = f"%{query.lower()}%"
    exact_cpf = query.replace(".", "").replace("-", "")
    
    # Busca básica por diferentes campos
    patients = Patient.query.filter(
        or_(
            func.lower(Patient.nome).like(search_term),
            Patient.cpf.like(f"%{exact_cpf}%"),
            Patient.sus_card.like(f"%{query}%"),
            Patient.telefone.like(f"%{query}%")
        )
    ).all()
    
    # Ordenar resultados por relevância
    def relevance_score(patient):
        cpf_match = 5 if patient.cpf and exact_cpf in patient.cpf.replace(".", "").replace("-", "") else 0
        sus_match = 4 if patient.sus_card and query in patient.sus_card else 0
        name_match = 3 if query.lower() in patient.nome.lower() else 0
        starts_with = 4 if patient.nome.lower().startswith(query.lower()) else 0
        
        return cpf_match + sus_match + name_match + starts_with
    
    # Ordenar por relevância e limitar resultados
    patients.sort(key=relevance_score, reverse=True)
    return patients[:limit]

def search_prescriptions(query, limit=10):
    """
    Pesquisa inteligente de prescrições
    
    Busca por nome do paciente, nome do médico, ID da prescrição, status
    Permite pesquisar por data no formato dd/mm/yyyy
    """
    if not query or len(query.strip()) < 2:
        return []
    
    search_term = f"%{query.lower()}%"
    
    # Verificar se a pesquisa é por ID numérico
    id_search = False
    prescription_id = None
    
    try:
        prescription_id = int(query)
        id_search = True
    except ValueError:
        id_search = False
    
    # Buscar prescrições relacionadas à consulta
    prescriptions_query = Prescription.query.join(
        Patient, Prescription.patient_id == Patient.id
    ).join(
        User, Prescription.doctor_id == User.id
    )
    
    # Filtrar com base no tipo de pesquisa
    if id_search and prescription_id is not None:
        prescriptions = prescriptions_query.filter(
            Prescription.id == prescription_id
        ).all()
    else:
        prescriptions = prescriptions_query.filter(
            or_(
                func.lower(Patient.nome).like(search_term),
                func.lower(User.nome).like(search_term),
                func.lower(Prescription.status).like(search_term)
            )
        ).all()
    
    # Ordenar resultados por relevância
    def relevance_score(prescription):
        id_match = 10 if id_search and prescription_id is not None and prescription.id == prescription_id else 0
        patient_match = 5 if query.lower() in prescription.patient.nome.lower() else 0
        doctor_match = 3 if query.lower() in prescription.doctor.nome.lower() else 0
        status_match = 2 if query.lower() in prescription.status.lower() else 0
        # Prescrições mais recentes têm maior prioridade
        recency = 1  # base score
        
        return id_match + patient_match + doctor_match + status_match + recency
    
    # Ordenar por relevância e limitar resultados
    prescriptions.sort(key=relevance_score, reverse=True)
    return prescriptions[:limit]

def format_medication_result(medication, preloaded_batches=None):
    """
    Formata um medicamento para exibição nos resultados da pesquisa
    
    Args:
        medication: Objeto do medicamento
        preloaded_batches: Opcional - Lista de lotes pré-carregados para evitar consultas
    """
    try:
        # Garante que não haverá erro mesmo se algum dado estiver ausente
        estoque = medication.stock_total(preloaded_batches=preloaded_batches) or 0
        proxima_validade = medication.next_expiry_date(preloaded_batches=preloaded_batches)
        
        # Tratamento seguro para a data de validade
        try:
            validade_formatada = proxima_validade.strftime("%d/%m/%Y") if proxima_validade else "N/A"
        except:
            validade_formatada = "N/A"
        
        # Constrói a descrição de forma segura
        principio = medication.principio_ativo or ""
        concentracao = medication.concentracao or ""
        descricao = f"{principio} {concentracao}".strip()
        
        return {
            'id': medication.id,
            'texto': medication.nome,
            'descricao': descricao,
            'detalhe': f"Estoque: {estoque} | Próx. validade: {validade_formatada}",
            'tipo': 'medicamento',
            'url': f"/medicamento/lotes/{medication.id}"
        }
    except Exception as e:
        # Formato mínimo para evitar quebrar o frontend
        return {
            'id': medication.id if hasattr(medication, 'id') else 0,
            'texto': getattr(medication, 'nome', 'Medicamento'),
            'descricao': 'Informações indisponíveis',
            'detalhe': 'Erro ao carregar detalhes',
            'tipo': 'medicamento',
            'url': '#'
        }

def format_patient_result(patient):
    """Formata um paciente para exibição nos resultados da pesquisa"""
    identificador = patient.cpf or patient.sus_card or "Sem identificação"
    nascimento = patient.data_nascimento.strftime("%d/%m/%Y") if patient.data_nascimento else "N/A"
    
    return {
        'id': patient.id,
        'texto': patient.nome,
        'descricao': f"ID: {identificador}",
        'detalhe': f"Nascimento: {nascimento} | Telefone: {patient.telefone or 'N/A'}",
        'tipo': 'paciente',
        'url': f"/prontuario/{patient.id}"
    }

def format_prescription_result(prescription):
    """Formata uma prescrição para exibição nos resultados da pesquisa"""
    data = prescription.date.strftime("%d/%m/%Y") if prescription.date else "N/A"
    
    return {
        'id': prescription.id,
        'texto': f"Prescrição #{prescription.id}",
        'descricao': f"Paciente: {prescription.patient.nome}",
        'detalhe': f"Médico: {prescription.doctor.nome} | Data: {data} | Status: {prescription.status}",
        'tipo': 'prescricao',
        'url': f"/prescricao/ver/{prescription.id}"
    }