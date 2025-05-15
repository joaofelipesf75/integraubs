#!/usr/bin/env python3
"""
Script para importar medicamentos das planilhas ao Sistema Integra UBS
"""
from datetime import datetime, timedelta
from app import app, db
from models import Medication, MedicationBatch

# Função para criar uma data de validade a partir de hoje + meses
def create_expiry_date(months):
    return datetime.now() + timedelta(days=30*months)

# Lista de medicamentos extraídos das planilhas
# Formato: [nome, principio_ativo, forma, concentracao, lote, qtd, validade_meses]
medications_data = [
    # Primeira planilha (IMG-20250512-WA0031.jpg)
    {"nome": "ÁCIDO ACETILSALICÍLICO 100MG COMP", "principio_ativo": "ÁCIDO ACETILSALICÍLICO", "forma": "COMPRIMIDO", "concentracao": "100mg", "lotes": [{"lote": "1234A", "qtd": 100, "validade_meses": 12}]},
    {"nome": "ÁCIDO FÓLICO 5MG COMP", "principio_ativo": "ÁCIDO FÓLICO", "forma": "COMPRIMIDO", "concentracao": "5mg", "lotes": [{"lote": "4567B", "qtd": 100, "validade_meses": 12}]},
    {"nome": "AGUA DESTILADA 10ML AMP", "principio_ativo": "ÁGUA DESTILADA", "forma": "AMPOLA", "concentracao": "10ml", "lotes": [{"lote": "8901C", "qtd": 50, "validade_meses": 24}]},
    {"nome": "ALBENDAZOL 400MG COMP", "principio_ativo": "ALBENDAZOL", "forma": "COMPRIMIDO", "concentracao": "400mg", "lotes": [{"lote": "ABCD123", "qtd": 50, "validade_meses": 12}]},
    {"nome": "AMIODARONA 200MG COMP", "principio_ativo": "AMIODARONA", "forma": "COMPRIMIDO", "concentracao": "200mg", "lotes": [{"lote": "DEF456", "qtd": 30, "validade_meses": 12}]},
    
    # Segunda planilha (IMG-20250512-WA0033.jpg)
    {"nome": "CAPTOPRIL 25MG COMP", "principio_ativo": "CAPTOPRIL", "forma": "COMPRIMIDO", "concentracao": "25mg", "lotes": [{"lote": "LMNO123", "qtd": 300, "validade_meses": 18}]},
    {"nome": "ENALAPRIL 10MG COMP", "principio_ativo": "ENALAPRIL", "forma": "COMPRIMIDO", "concentracao": "10mg", "lotes": [{"lote": "PQRS456", "qtd": 200, "validade_meses": 18}]},
    {"nome": "IBUPROFENO 300MG COMP", "principio_ativo": "IBUPROFENO", "forma": "COMPRIMIDO", "concentracao": "300mg", "lotes": [{"lote": "TUVW789", "qtd": 200, "validade_meses": 18}]},
    {"nome": "LOSARTANA 50MG COMP", "principio_ativo": "LOSARTANA", "forma": "COMPRIMIDO", "concentracao": "50mg", "lotes": [{"lote": "XYZ012", "qtd": 300, "validade_meses": 18}]},
    
    # Terceira planilha (IMG-20250512-WA0034.jpg)
    {"nome": "METRONIDAZOL 250MG COMP", "principio_ativo": "METRONIDAZOL", "forma": "COMPRIMIDO", "concentracao": "250mg", "lotes": [{"lote": "MET001", "qtd": 100, "validade_meses": 12}]},
    {"nome": "OMEPRAZOL 20MG CAPS", "principio_ativo": "OMEPRAZOL", "forma": "CÁPSULA", "concentracao": "20mg", "lotes": [{"lote": "OME002", "qtd": 200, "validade_meses": 12}]},
    {"nome": "PARACETAMOL 500MG COMP", "principio_ativo": "PARACETAMOL", "forma": "COMPRIMIDO", "concentracao": "500mg", "lotes": [{"lote": "PAR003", "qtd": 200, "validade_meses": 12}]},
    
    # Quarta planilha (IMG-20250512-WA0035.jpg)
    {"nome": "PREDNISONA 20MG COMP", "principio_ativo": "PREDNISONA", "forma": "COMPRIMIDO", "concentracao": "20mg", "lotes": [{"lote": "PRE004", "qtd": 100, "validade_meses": 12}]},
    {"nome": "SALBUTAMOL 100mcg/DOSE SPRAY", "principio_ativo": "SALBUTAMOL", "forma": "SPRAY", "concentracao": "100mcg/dose", "lotes": [{"lote": "SAL005", "qtd": 50, "validade_meses": 12}]},
    
    # Quinta planilha (IMG-20250512-WA0036.jpg)
    {"nome": "AMOXICILINA 500MG CAPS", "principio_ativo": "AMOXICILINA", "forma": "CÁPSULA", "concentracao": "500mg", "lotes": [{"lote": "AMO006", "qtd": 100, "validade_meses": 12}]},
    {"nome": "AZITROMICINA 500MG COMP", "principio_ativo": "AZITROMICINA", "forma": "COMPRIMIDO", "concentracao": "500mg", "lotes": [{"lote": "AZI007", "qtd": 30, "validade_meses": 12}]},
    {"nome": "CIPROFLOXACINO 500MG COMP", "principio_ativo": "CIPROFLOXACINO", "forma": "COMPRIMIDO", "concentracao": "500mg", "lotes": [{"lote": "CIP008", "qtd": 50, "validade_meses": 12}]},
    
    # Sexta planilha (IMG-20250512-WA0037.jpg)
    {"nome": "DEXAMETASONA CREME 0,1%", "principio_ativo": "DEXAMETASONA", "forma": "CREME", "concentracao": "0,1%", "lotes": [{"lote": "DEX009", "qtd": 20, "validade_meses": 12}]},
    {"nome": "DICLOFENACO POTÁSSICO 50MG COMP", "principio_ativo": "DICLOFENACO POTÁSSICO", "forma": "COMPRIMIDO", "concentracao": "50mg", "lotes": [{"lote": "DIC010", "qtd": 100, "validade_meses": 12}]},
]

def import_medications():
    """Importa medicamentos e lotes para o banco de dados"""
    with app.app_context():
        count_medications = 0
        count_batches = 0
        
        for med_data in medications_data:
            # Verificar se o medicamento já existe
            medication = Medication.query.filter_by(nome=med_data["nome"]).first()
            
            if not medication:
                # Criar novo medicamento
                medication = Medication(
                    nome=med_data["nome"],
                    principio_ativo=med_data["principio_ativo"],
                    forma=med_data["forma"],
                    concentracao=med_data["concentracao"],
                    descricao=f"{med_data['principio_ativo']} {med_data['concentracao']} - {med_data['forma']}"
                )
                db.session.add(medication)
                db.session.flush()  # Para obter o ID do medicamento
                count_medications += 1
                print(f"Medicamento criado: {medication.nome}")
            
            # Adicionar lotes para este medicamento
            for lote_data in med_data["lotes"]:
                # Verificar se o lote já existe
                existing_batch = MedicationBatch.query.filter_by(
                    medication_id=medication.id,
                    lote=lote_data["lote"]
                ).first()
                
                if not existing_batch:
                    # Criar novo lote
                    batch = MedicationBatch(
                        medication_id=medication.id,
                        lote=lote_data["lote"],
                        validade=create_expiry_date(lote_data["validade_meses"]),
                        quantidade_inicial=lote_data["qtd"],
                        quantidade_atual=lote_data["qtd"]
                    )
                    db.session.add(batch)
                    count_batches += 1
                    print(f"Lote criado: {batch.lote} para {medication.nome}")
            
        # Commit das alterações
        db.session.commit()
        
        print(f"Importação concluída: {count_medications} medicamentos e {count_batches} lotes adicionados.")

if __name__ == "__main__":
    import_medications()