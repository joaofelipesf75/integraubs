"""
SISTEMA INTEGRA UBS - Utilitários
"""
import json
import random
from datetime import datetime, timedelta

def format_date(date, format='%d/%m/%Y'):
    """Formata uma data para exibição"""
    if not date:
        return ""
    
    if isinstance(date, str):
        try:
            date = datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            return date
    
    return date.strftime(format)

def format_datetime(dt, format='%d/%m/%Y %H:%M'):
    """Formata uma data e hora para exibição"""
    if not dt:
        return ""
    
    if isinstance(dt, str):
        try:
            dt = datetime.strptime(dt, '%Y-%m-%dT%H:%M:%S')
        except ValueError:
            try:
                dt = datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                return dt
    
    return dt.strftime(format)

def generate_random_dates(num_dates, start_date=None, end_date=None):
    """Gera datas aleatórias entre start_date e end_date"""
    if not start_date:
        start_date = datetime.now() - timedelta(days=180)
    if not end_date:
        end_date = datetime.now()
    
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    
    random_dates = []
    for _ in range(num_dates):
        random_number_of_days = random.randrange(days_between_dates)
        random_date = start_date + timedelta(days=random_number_of_days)
        random_dates.append(random_date)
    
    return sorted(random_dates)

def generate_chart_colors(num_colors):
    """Gera cores aleatórias para gráficos"""
    colors = []
    for _ in range(num_colors):
        r = random.randint(50, 200)
        g = random.randint(50, 200)
        b = random.randint(50, 200)
        colors.append(f'rgba({r}, {g}, {b}, 0.8)')
    
    return colors