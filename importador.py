"""
SISTEMA INTEGRA UBS - Módulo importador de medicamentos
"""
from datetime import datetime, timedelta

# Lista de medicamentos extraídos das planilhas
# Formato: [nome, principio_ativo, forma, concentracao, lote, qtd, validade_meses]
def get_medications_data():
    """Retorna a lista de medicamentos para importação"""
    return [
        # Medicamentos das planilhas originais
        {"nome": "ACETATO DE MEDROXIPROGESTERONA 150MG/ML", "principio_ativo": "ACETATO DE MEDROXIPROGESTERONA", "forma": "AMPOLA", "concentracao": "150mg/ml", "lotes": [{"lote": "MED001", "qtd": 10, "validade_meses": 24}]},
        {"nome": "ACETILCISTEÍNA 20MG/ML XPE INFANTIL 120ML", "principio_ativo": "ACETILCISTEÍNA", "forma": "FRASCO", "concentracao": "20mg/ml", "lotes": [{"lote": "ACI001", "qtd": 10, "validade_meses": 12}]},
        {"nome": "ACETILCISTEÍNA 40MG/ML SOL. ORAL ADULTO 120ML", "principio_ativo": "ACETILCISTEÍNA", "forma": "FRASCO", "concentracao": "40mg/ml", "lotes": [{"lote": "ACI002", "qtd": 10, "validade_meses": 12}]},
        {"nome": "ACICLOVIR 200 MG", "principio_ativo": "ACICLOVIR", "forma": "COMPRIMIDO", "concentracao": "200mg", "lotes": [{"lote": "ACV001", "qtd": 200, "validade_meses": 24}]},
        {"nome": "ACICLOVIR CREME 50MG/G", "principio_ativo": "ACICLOVIR", "forma": "BEG", "concentracao": "50mg/g", "lotes": [{"lote": "ACV002", "qtd": 10, "validade_meses": 18}]},
        {"nome": "ÁCIDO ACETILSALICÍLICO 100 MG", "principio_ativo": "ÁCIDO ACETILSALICÍLICO", "forma": "COMPRIMIDO", "concentracao": "100mg", "lotes": [{"lote": "AAS001", "qtd": 300, "validade_meses": 24}]},
        {"nome": "ÁCIDO ASCÓRBICO 100MG/ML 5ML SOL. INJ. (VITAMINA C)", "principio_ativo": "ÁCIDO ASCÓRBICO", "forma": "AMPOLA", "concentracao": "100mg/ml", "lotes": [{"lote": "ASC001", "qtd": 20, "validade_meses": 24}]},
        {"nome": "ÁCIDO ASCÓRBICO 200MG/ML 20ML GOTAS (VITAMINA C)", "principio_ativo": "ÁCIDO ASCÓRBICO", "forma": "FRASCO", "concentracao": "200mg/ml", "lotes": [{"lote": "ASC002", "qtd": 20, "validade_meses": 18}]},
        {"nome": "ÁCIDO ASCÓRBICO 500MG (VITAMINA C)", "principio_ativo": "ÁCIDO ASCÓRBICO", "forma": "COMPRIMIDO", "concentracao": "500mg", "lotes": [{"lote": "ASC003", "qtd": 200, "validade_meses": 24}]},
        {"nome": "ÁCIDO FÓLICO 5MG COMPRIMIDO", "principio_ativo": "ÁCIDO FÓLICO", "forma": "COMPRIMIDO", "concentracao": "5mg", "lotes": [{"lote": "FOL001", "qtd": 200, "validade_meses": 24}]},
        {"nome": "ALBENDAZOL 400 MG", "principio_ativo": "ALBENDAZOL", "forma": "COMPRIMIDO", "concentracao": "400mg", "lotes": [{"lote": "ABZ001", "qtd": 300, "validade_meses": 24}]},
        {"nome": "ALBENDAZOL 40MG/ML SUSPENSÃO ORAL", "principio_ativo": "ALBENDAZOL", "forma": "FRASCO", "concentracao": "40mg/ml", "lotes": [{"lote": "ABZ002", "qtd": 20, "validade_meses": 18}]},
        {"nome": "AMBROXOL 30MG/ML XAROPE ADULTO", "principio_ativo": "AMBROXOL", "forma": "FRASCO", "concentracao": "30mg/ml", "lotes": [{"lote": "AMB001", "qtd": 10, "validade_meses": 12}]},
        {"nome": "AMBROXOL 15MG/ML XAROPE INFANTIL", "principio_ativo": "AMBROXOL", "forma": "FRASCO", "concentracao": "15mg/ml", "lotes": [{"lote": "AMB002", "qtd": 10, "validade_meses": 12}]},
        {"nome": "AMOXICILINA 500MG", "principio_ativo": "AMOXICILINA", "forma": "CÁPSULA", "concentracao": "500mg", "lotes": [{"lote": "AMX001", "qtd": 200, "validade_meses": 24}]},
        {"nome": "AMOXICILINA 250MG/5ML SUSPENSÃO ORAL", "principio_ativo": "AMOXICILINA", "forma": "FRASCO", "concentracao": "250mg/5ml", "lotes": [{"lote": "AMX002", "qtd": 10, "validade_meses": 12}]},
        {"nome": "AMPICILINA 500 MG", "principio_ativo": "AMPICILINA", "forma": "COMPRIMIDO", "concentracao": "500mg", "lotes": [{"lote": "AMP001", "qtd": 200, "validade_meses": 24}]},
        {"nome": "AMPICILINA 50MG/ML SUSPENSÃO ORAL", "principio_ativo": "AMPICILINA", "forma": "FRASCO", "concentracao": "50mg/ml", "lotes": [{"lote": "AMP002", "qtd": 10, "validade_meses": 12}]},
        {"nome": "ATENOLOL 25MG", "principio_ativo": "ATENOLOL", "forma": "COMPRIMIDO", "concentracao": "25mg", "lotes": [{"lote": "ATN001", "qtd": 200, "validade_meses": 24}]},
        {"nome": "ATENOLOL 50MG", "principio_ativo": "ATENOLOL", "forma": "COMPRIMIDO", "concentracao": "50mg", "lotes": [{"lote": "ATN002", "qtd": 200, "validade_meses": 24}]},
        {"nome": "ATENOLOL 100MG", "principio_ativo": "ATENOLOL", "forma": "COMPRIMIDO", "concentracao": "100mg", "lotes": [{"lote": "ATN003", "qtd": 200, "validade_meses": 24}]},
        {"nome": "AZITROMICINA 500MG", "principio_ativo": "AZITROMICINA", "forma": "COMPRIMIDO", "concentracao": "500mg", "lotes": [{"lote": "AZT001", "qtd": 300, "validade_meses": 24}]},
        {"nome": "AZITROMICINA 600MG/ML SUSPENSÃO ORAL", "principio_ativo": "AZITROMICINA", "forma": "FRASCO", "concentracao": "600mg/ml", "lotes": [{"lote": "AZT002", "qtd": 20, "validade_meses": 18}]},
        {"nome": "BENZILPENICILINA BENZATINA 1.200.000 UI F/A", "principio_ativo": "BENZILPENICILINA BENZATINA", "forma": "AMPOLA", "concentracao": "1.200.000 UI", "lotes": [{"lote": "PEN001", "qtd": 20, "validade_meses": 24}]},
        {"nome": "BENZILPENICILINA BENZATINA 600.000 UI F/A", "principio_ativo": "BENZILPENICILINA BENZATINA", "forma": "AMPOLA", "concentracao": "600.000 UI", "lotes": [{"lote": "PEN002", "qtd": 20, "validade_meses": 24}]},
        {"nome": "BESILATO DE ANLODIPINO 5MG", "principio_ativo": "BESILATO DE ANLODIPINO", "forma": "COMPRIMIDO", "concentracao": "5mg", "lotes": [{"lote": "ANL001", "qtd": 100, "validade_meses": 24}]},
        {"nome": "BESILATO DE ANLODIPINO 10MG", "principio_ativo": "BESILATO DE ANLODIPINO", "forma": "COMPRIMIDO", "concentracao": "10mg", "lotes": [{"lote": "ANL002", "qtd": 100, "validade_meses": 24}]},
        {"nome": "BROMOPRIDA 10 MG COMPRIMIDO", "principio_ativo": "BROMOPRIDA", "forma": "COMPRIMIDO", "concentracao": "10mg", "lotes": [{"lote": "BRM001", "qtd": 100, "validade_meses": 24}]},
        {"nome": "BROMOPRIDA 5MG/ML 2ML", "principio_ativo": "BROMOPRIDA", "forma": "AMPOLA", "concentracao": "5mg/ml", "lotes": [{"lote": "BRM002", "qtd": 10, "validade_meses": 24}]},
        {"nome": "BUSCOPAM COMPOSTO COMPRIMIDO", "principio_ativo": "BUSCOPAM COMPOSTO", "forma": "COMPRIMIDO", "concentracao": "", "lotes": [{"lote": "BSC001", "qtd": 300, "validade_meses": 24}]},
        {"nome": "BUSCOPAM COMPOSTO GOTAS", "principio_ativo": "BUSCOPAM COMPOSTO", "forma": "FRASCO", "concentracao": "", "lotes": [{"lote": "BSC002", "qtd": 10, "validade_meses": 18}]},
        {"nome": "BUSCOPAM COMPOSTO INJETÁVEL", "principio_ativo": "BUSCOPAM COMPOSTO", "forma": "AMPOLA", "concentracao": "", "lotes": [{"lote": "BSC003", "qtd": 10, "validade_meses": 24}]},
        {"nome": "CAPTOPRIL 25MG", "principio_ativo": "CAPTOPRIL", "forma": "COMPRIMIDO", "concentracao": "25mg", "lotes": [{"lote": "CAP001", "qtd": 200, "validade_meses": 24}]},
        {"nome": "CAPTOPRIL 50MG", "principio_ativo": "CAPTOPRIL", "forma": "COMPRIMIDO", "concentracao": "50mg", "lotes": [{"lote": "CAP002", "qtd": 200, "validade_meses": 24}]},
        {"nome": "CARVEDILOL 3,125 MG COMPRIMIDO", "principio_ativo": "CARVEDILOL", "forma": "COMPRIMIDO", "concentracao": "3,125mg", "lotes": [{"lote": "CRV001", "qtd": 100, "validade_meses": 24}]},
        {"nome": "CARVEDILOL 6,25 MG COMPRIMIDO", "principio_ativo": "CARVEDILOL", "forma": "COMPRIMIDO", "concentracao": "6,25mg", "lotes": [{"lote": "CRV002", "qtd": 100, "validade_meses": 24}]},
        {"nome": "CARVEDILOL 12,5 MG COMPRIMIDO", "principio_ativo": "CARVEDILOL", "forma": "COMPRIMIDO", "concentracao": "12,5mg", "lotes": [{"lote": "CRV003", "qtd": 100, "validade_meses": 24}]},
        {"nome": "CARVEDILOL 25 MG COMPRIMIDO", "principio_ativo": "CARVEDILOL", "forma": "COMPRIMIDO", "concentracao": "25mg", "lotes": [{"lote": "CRV004", "qtd": 100, "validade_meses": 24}]},
        {"nome": "CEFALEXINA 250MG/5ML SUSPENSÃO ORAL", "principio_ativo": "CEFALEXINA", "forma": "FRASCO", "concentracao": "250mg/5ml", "lotes": [{"lote": "CFX001", "qtd": 10, "validade_meses": 18}]},
        {"nome": "CEFALEXINA 500MG COMPRIMIDO", "principio_ativo": "CEFALEXINA", "forma": "COMPRIMIDO", "concentracao": "500mg", "lotes": [{"lote": "CFX002", "qtd": 100, "validade_meses": 24}]},
        {"nome": "CETOCONAZOL 200MG", "principio_ativo": "CETOCONAZOL", "forma": "COMPRIMIDO", "concentracao": "200mg", "lotes": [{"lote": "CTZ001", "qtd": 100, "validade_meses": 24}]},
        {"nome": "CIPROFLOXACINO 500MG", "principio_ativo": "CIPROFLOXACINO", "forma": "COMPRIMIDO", "concentracao": "500mg", "lotes": [{"lote": "CIP001", "qtd": 100, "validade_meses": 24}]},
        {"nome": "CLORIDRATO DE PROPRANOLOL 40MG", "principio_ativo": "CLORIDRATO DE PROPRANOLOL", "forma": "COMPRIMIDO", "concentracao": "40mg", "lotes": [{"lote": "PRN001", "qtd": 100, "validade_meses": 24}]},
        {"nome": "DEXAMETASONA 1MG/G CREME", "principio_ativo": "DEXAMETASONA", "forma": "BEG", "concentracao": "1mg/g", "lotes": [{"lote": "DXM001", "qtd": 20, "validade_meses": 18}]},
        {"nome": "DEXAMETASONA 2MG/ML SOL. INJETÁVEL 1ML", "principio_ativo": "DEXAMETASONA", "forma": "AMPOLA", "concentracao": "2mg/ml", "lotes": [{"lote": "DXM002", "qtd": 20, "validade_meses": 24}]},
        {"nome": "DEXAMETASONA 4MG", "principio_ativo": "DEXAMETASONA", "forma": "COMPRIMIDO", "concentracao": "4mg", "lotes": [{"lote": "DXM003", "qtd": 100, "validade_meses": 24}]},
        {"nome": "DEXAMETASONA ELIXIR 10MG SUSPENSÃO", "principio_ativo": "DEXAMETASONA", "forma": "FRASCO", "concentracao": "10mg", "lotes": [{"lote": "DXM004", "qtd": 10, "validade_meses": 18}]},
        {"nome": "DICLOFENACO POTÁSSICO 50MG", "principio_ativo": "DICLOFENACO POTÁSSICO", "forma": "COMPRIMIDO", "concentracao": "50mg", "lotes": [{"lote": "DCP001", "qtd": 200, "validade_meses": 24}]},
        {"nome": "DICLOFENACO SÓDICO 25MG/ML INJETÁVEL", "principio_ativo": "DICLOFENACO SÓDICO", "forma": "AMPOLA", "concentracao": "25mg/ml", "lotes": [{"lote": "DCS001", "qtd": 10, "validade_meses": 24}]},
        {"nome": "DICLOFENACO SÓDICO 50MG", "principio_ativo": "DICLOFENACO SÓDICO", "forma": "COMPRIMIDO", "concentracao": "50mg", "lotes": [{"lote": "DCS002", "qtd": 200, "validade_meses": 24}]},
        {"nome": "DIPIRONA SÓDICA 500MG", "principio_ativo": "DIPIRONA SÓDICA", "forma": "COMPRIMIDO", "concentracao": "500mg", "lotes": [{"lote": "DPS001", "qtd": 500, "validade_meses": 24}]},
        {"nome": "DIPIRONA SÓDICA 500MG/ML GOTAS", "principio_ativo": "DIPIRONA SÓDICA", "forma": "FRASCO", "concentracao": "500mg/ml", "lotes": [{"lote": "DPS002", "qtd": 30, "validade_meses": 18}]},
        {"nome": "DIPIRONA SÓDICA 500MG/ML SOL. INJETÁVEL IM/EV", "principio_ativo": "DIPIRONA SÓDICA", "forma": "AMPOLA", "concentracao": "500mg/ml", "lotes": [{"lote": "DPS003", "qtd": 30, "validade_meses": 24}]},
        {"nome": "ENALAPRIL 5MG", "principio_ativo": "ENALAPRIL", "forma": "COMPRIMIDO", "concentracao": "5mg", "lotes": [{"lote": "ENL001", "qtd": 100, "validade_meses": 24}]},
        {"nome": "ENALAPRIL 10MG", "principio_ativo": "ENALAPRIL", "forma": "COMPRIMIDO", "concentracao": "10mg", "lotes": [{"lote": "ENL002", "qtd": 200, "validade_meses": 24}]},
        {"nome": "ENALAPRIL 20MG", "principio_ativo": "ENALAPRIL", "forma": "COMPRIMIDO", "concentracao": "20mg", "lotes": [{"lote": "ENL003", "qtd": 200, "validade_meses": 24}]},
        {"nome": "ENANTATO DE NORESTISTERONA + VALERATO DE ESTRADIOL 50+5MG/ML", "principio_ativo": "ENANTATO DE NORESTISTERONA + VALERATO DE ESTRADIOL", "forma": "AMPOLA", "concentracao": "50+5mg/ml", "lotes": [{"lote": "ENT001", "qtd": 10, "validade_meses": 24}]},
        {"nome": "FLUCONAZOL 150MG CÁPSULA", "principio_ativo": "FLUCONAZOL", "forma": "CÁPSULA", "concentracao": "150mg", "lotes": [{"lote": "FLZ001", "qtd": 30, "validade_meses": 24}]},
        {"nome": "FUROSEMIDA 40MG", "principio_ativo": "FUROSEMIDA", "forma": "COMPRIMIDO", "concentracao": "40mg", "lotes": [{"lote": "FRS001", "qtd": 100, "validade_meses": 24}]},
        {"nome": "GLICOSE 25% 10ML", "principio_ativo": "GLICOSE", "forma": "AMPOLA", "concentracao": "25%", "lotes": [{"lote": "GLC001", "qtd": 10, "validade_meses": 24}]},
        {"nome": "GLICOSE 50% 10ML", "principio_ativo": "GLICOSE", "forma": "AMPOLA", "concentracao": "50%", "lotes": [{"lote": "GLC002", "qtd": 10, "validade_meses": 24}]},
        {"nome": "GLIBENCLAMIDA 5MG", "principio_ativo": "GLIBENCLAMIDA", "forma": "COMPRIMIDO", "concentracao": "5mg", "lotes": [{"lote": "GLB001", "qtd": 300, "validade_meses": 24}]},
        {"nome": "HIDROCLOROTIAZIDA 25MG", "principio_ativo": "HIDROCLOROTIAZIDA", "forma": "COMPRIMIDO", "concentracao": "25mg", "lotes": [{"lote": "HCT001", "qtd": 300, "validade_meses": 24}]},
        {"nome": "HIDRÓXIDO DE ALUMÍNIO 100 ML", "principio_ativo": "HIDRÓXIDO DE ALUMÍNIO", "forma": "FRASCO", "concentracao": "100ml", "lotes": [{"lote": "HAL001", "qtd": 10, "validade_meses": 18}]},
        {"nome": "IBUPROFENO 300MG", "principio_ativo": "IBUPROFENO", "forma": "COMPRIMIDO", "concentracao": "300mg", "lotes": [{"lote": "IBP001", "qtd": 300, "validade_meses": 24}]},
        {"nome": "IBUPROFENO 600MG", "principio_ativo": "IBUPROFENO", "forma": "COMPRIMIDO", "concentracao": "600mg", "lotes": [{"lote": "IBP002", "qtd": 300, "validade_meses": 24}]},
        {"nome": "IBUPROFENO GOTAS", "principio_ativo": "IBUPROFENO", "forma": "FRASCO", "concentracao": "", "lotes": [{"lote": "IBP003", "qtd": 10, "validade_meses": 18}]},
        {"nome": "INSULINA HUMANA NPH 100UI/ML", "principio_ativo": "INSULINA HUMANA NPH", "forma": "UNIDADE", "concentracao": "100ui/ml", "lotes": [{"lote": "INS001", "qtd": 50, "validade_meses": 12}]},
        {"nome": "INSULINA HUMANA REGULAR 100UI/ML", "principio_ativo": "INSULINA HUMANA REGULAR", "forma": "UNIDADE", "concentracao": "100ui/ml", "lotes": [{"lote": "INS002", "qtd": 50, "validade_meses": 12}]},
        {"nome": "IODOPOVIDONA DEGERMANTE 1000ML", "principio_ativo": "IODOPOVIDONA", "forma": "LITRO", "concentracao": "", "lotes": [{"lote": "IPV001", "qtd": 10, "validade_meses": 24}]},
        {"nome": "LOSARTANA POTÁSSICA 50MG", "principio_ativo": "LOSARTANA POTÁSSICA", "forma": "COMPRIMIDO", "concentracao": "50mg", "lotes": [{"lote": "LST001", "qtd": 300, "validade_meses": 24}]},
        {"nome": "LIDOCAÍNA 20MG/G GEL 2% 30GR", "principio_ativo": "LIDOCAÍNA", "forma": "BEG", "concentracao": "20mg/g", "lotes": [{"lote": "LDC001", "qtd": 10, "validade_meses": 18}]},
        {"nome": "MALEATO DE DEXCLORFENIRAMINA 2MG/ML SUSPENSÃO", "principio_ativo": "MALEATO DE DEXCLORFENIRAMINA", "forma": "FRASCO", "concentracao": "2mg/ml", "lotes": [{"lote": "DCF001", "qtd": 20, "validade_meses": 18}]},
        {"nome": "MEBENDAZOL 100MG", "principio_ativo": "MEBENDAZOL", "forma": "COMPRIMIDO", "concentracao": "100mg", "lotes": [{"lote": "MBD001", "qtd": 200, "validade_meses": 24}]},
        {"nome": "METFORMINA 500MG COMPRIMIDO", "principio_ativo": "METFORMINA", "forma": "COMPRIMIDO", "concentracao": "500mg", "lotes": [{"lote": "MTF001", "qtd": 200, "validade_meses": 24}]},
        {"nome": "METFORMINA 850MG COMPRIMIDO", "principio_ativo": "METFORMINA", "forma": "COMPRIMIDO", "concentracao": "850mg", "lotes": [{"lote": "MTF002", "qtd": 200, "validade_meses": 24}]},
        {"nome": "METILDOPA 250MG", "principio_ativo": "METILDOPA", "forma": "COMPRIMIDO", "concentracao": "250mg", "lotes": [{"lote": "MTP001", "qtd": 100, "validade_meses": 24}]},
        {"nome": "METILDOPA 500MG", "principio_ativo": "METILDOPA", "forma": "COMPRIMIDO", "concentracao": "500mg", "lotes": [{"lote": "MTP002", "qtd": 100, "validade_meses": 24}]},
        {"nome": "METRONIDAZOL 100MG/G CREME VAGINAL", "principio_ativo": "METRONIDAZOL", "forma": "BEG", "concentracao": "100mg/g", "lotes": [{"lote": "MTZ001", "qtd": 20, "validade_meses": 18}]},
        {"nome": "METRONIDAZOL 250MG", "principio_ativo": "METRONIDAZOL", "forma": "COMPRIMIDO", "concentracao": "250mg", "lotes": [{"lote": "MTZ002", "qtd": 200, "validade_meses": 24}]},
        {"nome": "METRONIDAZOL 400 MG", "principio_ativo": "METRONIDAZOL", "forma": "COMPRIMIDO", "concentracao": "400mg", "lotes": [{"lote": "MTZ003", "qtd": 200, "validade_meses": 24}]},
        {"nome": "METRONIDAZOL 40MG/ML SUSPENSÃO", "principio_ativo": "METRONIDAZOL", "forma": "FRASCO", "concentracao": "40mg/ml", "lotes": [{"lote": "MTZ004", "qtd": 10, "validade_meses": 18}]},
        {"nome": "METRONIDAZOL + NISTATINA 100 MG/G + 20.000UI/G - CREME VAGINAL", "principio_ativo": "METRONIDAZOL + NISTATINA", "forma": "BEG", "concentracao": "100mg/g + 20.000ui/g", "lotes": [{"lote": "MTN001", "qtd": 20, "validade_meses": 18}]},
        {"nome": "NEOMICINA 5MG/G + BACITRACINA 250 UI/G", "principio_ativo": "NEOMICINA + BACITRACINA", "forma": "BEG", "concentracao": "5mg/g + 250ui/g", "lotes": [{"lote": "NMB001", "qtd": 20, "validade_meses": 18}]},
        {"nome": "NIFEDIPINO 10 MG", "principio_ativo": "NIFEDIPINO", "forma": "COMPRIMIDO", "concentracao": "10mg", "lotes": [{"lote": "NFP001", "qtd": 100, "validade_meses": 24}]},
        {"nome": "NIFEDIPINO 20 MG", "principio_ativo": "NIFEDIPINO", "forma": "COMPRIMIDO", "concentracao": "20mg", "lotes": [{"lote": "NFP002", "qtd": 100, "validade_meses": 24}]},
        {"nome": "NIMESULIDA COMPRIMIDO", "principio_ativo": "NIMESULIDA", "forma": "COMPRIMIDO", "concentracao": "100mg", "lotes": [{"lote": "NMS001", "qtd": 200, "validade_meses": 24}]},
        {"nome": "NIMESULIDA 50MG/ML", "principio_ativo": "NIMESULIDA", "forma": "FRASCO", "concentracao": "50mg/ml", "lotes": [{"lote": "NMS002", "qtd": 20, "validade_meses": 18}]},
        {"nome": "NITRATO DE MICONAZOL 20MG/G CREME DERMATOLÓGICO", "principio_ativo": "NITRATO DE MICONAZOL", "forma": "BEG", "concentracao": "20mg/g", "lotes": [{"lote": "MCZ001", "qtd": 20, "validade_meses": 18}]},
        {"nome": "NITRATO DE MICONAZOL 20MG/G CREME VAGINAL", "principio_ativo": "NITRATO DE MICONAZOL", "forma": "BEG", "concentracao": "20mg/g", "lotes": [{"lote": "MCZ002", "qtd": 20, "validade_meses": 18}]},
        {"nome": "OMEPRAZOL 20MG", "principio_ativo": "OMEPRAZOL", "forma": "CÁPSULA", "concentracao": "20mg", "lotes": [{"lote": "OME001", "qtd": 300, "validade_meses": 24}]},
        {"nome": "PARACETAMOL 200MG/ML 10ML GOTAS", "principio_ativo": "PARACETAMOL", "forma": "FRASCO", "concentracao": "200mg/ml", "lotes": [{"lote": "PCT001", "qtd": 50, "validade_meses": 18}]},
        {"nome": "PARACETAMOL 500MG", "principio_ativo": "PARACETAMOL", "forma": "COMPRIMIDO", "concentracao": "500mg", "lotes": [{"lote": "PCT002", "qtd": 300, "validade_meses": 24}]},
        {"nome": "PARACETAMOL 750MG", "principio_ativo": "PARACETAMOL", "forma": "COMPRIMIDO", "concentracao": "750mg", "lotes": [{"lote": "PCT003", "qtd": 300, "validade_meses": 24}]},
        {"nome": "PREDNISONA 5MG", "principio_ativo": "PREDNISONA", "forma": "COMPRIMIDO", "concentracao": "5mg", "lotes": [{"lote": "PRD001", "qtd": 100, "validade_meses": 24}]},
        {"nome": "PREDNISONA 20MG", "principio_ativo": "PREDNISONA", "forma": "COMPRIMIDO", "concentracao": "20mg", "lotes": [{"lote": "PRD002", "qtd": 200, "validade_meses": 24}]},
        {"nome": "SALBUTAMOL 0,4MG/ML XAROPE", "principio_ativo": "SALBUTAMOL", "forma": "FRASCO", "concentracao": "0,4mg/ml", "lotes": [{"lote": "SLB001", "qtd": 3, "validade_meses": 18}]},
        {"nome": "SALBUTAMOL 100mcg/DOSE SPRAY", "principio_ativo": "SALBUTAMOL", "forma": "SPRAY", "concentracao": "100mcg/dose", "lotes": [{"lote": "SLB002", "qtd": 3, "validade_meses": 18}]},
        {"nome": "SINVASTATINA 20MG", "principio_ativo": "SINVASTATINA", "forma": "COMPRIMIDO", "concentracao": "20mg", "lotes": [{"lote": "SNV001", "qtd": 300, "validade_meses": 24}]},
        {"nome": "SINVASTATINA 40MG", "principio_ativo": "SINVASTATINA", "forma": "COMPRIMIDO", "concentracao": "40mg", "lotes": [{"lote": "SNV002", "qtd": 300, "validade_meses": 24}]},
        {"nome": "SULFAMETOXAZOL + TRIMETOPRIMA 200MG + 80MG", "principio_ativo": "SULFAMETOXAZOL + TRIMETOPRIMA", "forma": "COMPRIMIDO", "concentracao": "200mg + 80mg", "lotes": [{"lote": "SMT001", "qtd": 20, "validade_meses": 24}]},
        {"nome": "SULFAMETOXAZOL + TRIMETOPRIMA 200MG/5ML + 40MG/5ML SUSPENSÃO", "principio_ativo": "SULFAMETOXAZOL + TRIMETOPRIMA", "forma": "FRASCO", "concentracao": "200mg/5ml + 40mg/5ml", "lotes": [{"lote": "SMT002", "qtd": 300, "validade_meses": 18}]},
        {"nome": "SULFATO FERROSO 40MG COMPRIMIDO", "principio_ativo": "SULFATO FERROSO", "forma": "COMPRIMIDO", "concentracao": "40mg", "lotes": [{"lote": "SFR001", "qtd": 300, "validade_meses": 24}]},
        {"nome": "SULFATO FERROSO GOTAS", "principio_ativo": "SULFATO FERROSO", "forma": "FRASCO", "concentracao": "", "lotes": [{"lote": "SFR002", "qtd": 20, "validade_meses": 18}]},
        {"nome": "VITAMINAS DO COMPLEXO B COMPRIMIDO", "principio_ativo": "VITAMINAS DO COMPLEXO B", "forma": "COMPRIMIDO", "concentracao": "", "lotes": [{"lote": "VCB001", "qtd": 300, "validade_meses": 24}]},
        {"nome": "VITAMINAS DO COMPLEXO B INJETÁVEL", "principio_ativo": "VITAMINAS DO COMPLEXO B", "forma": "AMPOLA", "concentracao": "", "lotes": [{"lote": "VCB002", "qtd": 10, "validade_meses": 24}]},
        {"nome": "VITAMINAS DO COMPLEXO B SUSPENSÃO", "principio_ativo": "VITAMINAS DO COMPLEXO B", "forma": "FRASCO", "concentracao": "", "lotes": [{"lote": "VCB003", "qtd": 20, "validade_meses": 18}]},
        
        # Materiais médico-hospitalares
        {"nome": "ABAIXADOR DE LÍNGUA C/100UND", "principio_ativo": "", "forma": "PACOTE", "concentracao": "", "lotes": [{"lote": "ABL001", "qtd": 1, "validade_meses": 36}]},
        {"nome": "ÁGUA OXIGENADA 10V 1000ML", "principio_ativo": "ÁGUA OXIGENADA", "forma": "LITRO", "concentracao": "10 volumes", "lotes": [{"lote": "AOX001", "qtd": 1, "validade_meses": 24}]},
        {"nome": "AGULHA DESCARTÁVEL 13X4,5MM C/100 UND", "principio_ativo": "", "forma": "UNIDADE", "concentracao": "13x4,5mm", "lotes": [{"lote": "AGD001", "qtd": 2, "validade_meses": 36}]},
        {"nome": "ÁLCOOL 70% 1000ML", "principio_ativo": "ÁLCOOL ETÍLICO", "forma": "LITRO", "concentracao": "70%", "lotes": [{"lote": "ALC001", "qtd": 10, "validade_meses": 24}]},
        {"nome": "ALGODÃO HIDRÓFILO 500G", "principio_ativo": "", "forma": "PACOTE", "concentracao": "500g", "lotes": [{"lote": "ALG001", "qtd": 2, "validade_meses": 36}]},
        {"nome": "AVENTAL DESCARTÁVEL MANGA LONGA 30G C/10", "principio_ativo": "", "forma": "PACOTE", "concentracao": "", "lotes": [{"lote": "AVD001", "qtd": 2, "validade_meses": 36}]},
        {"nome": "BOLSA COLETORA DE URINA 2000ML", "principio_ativo": "", "forma": "UNIDADE", "concentracao": "2000ml", "lotes": [{"lote": "BCU001", "qtd": 5, "validade_meses": 36}]},
        {"nome": "CAIXA PERFURO CORTANTE 7L", "principio_ativo": "", "forma": "UNIDADE", "concentracao": "7 litros", "lotes": [{"lote": "CPC001", "qtd": 2, "validade_meses": 36}]},
        {"nome": "CLORETO DE SÓDIO 0,9% 1000ML", "principio_ativo": "CLORETO DE SÓDIO", "forma": "FRASCO", "concentracao": "0,9%", "lotes": [{"lote": "SFI001", "qtd": 10, "validade_meses": 24}]},
    ]

def create_expiry_date(months):
    """Cria uma data de validade a partir da data atual + meses"""
    return datetime.now() + timedelta(days=30*months)

def import_medications(db, Medication, MedicationBatch):
    """Importa medicamentos e lotes para o banco de dados"""
    medications_data = get_medications_data()
    count_medications = 0
    count_batches = 0
    log_entries = []
    
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
            log_entries.append(f"Medicamento criado: {medication.nome}")
        else:
            log_entries.append(f"Medicamento já existe: {medication.nome}")
        
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
                log_entries.append(f"Lote criado: {batch.lote} para {medication.nome}")
            else:
                log_entries.append(f"Lote já existe: {lote_data['lote']} para {medication.nome}")
        
    # Commit das alterações
    db.session.commit()
    
    log_entries.append(f"Importação concluída: {count_medications} medicamentos e {count_batches} lotes adicionados.")
    
    return {
        'medications_added': count_medications,
        'batches_added': count_batches,
        'log': log_entries
    }