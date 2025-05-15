/**
 * SISTEMA INTEGRA UBS - JavaScript Principal
 * 
 * Arquivo contendo funções JavaScript comuns para todo o sistema.
 */

// Inicialização quando o DOM estiver completamente carregado
document.addEventListener('DOMContentLoaded', function() {
    // Inicializar tooltips do Bootstrap
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Inicializar popovers do Bootstrap
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Adicionar funcionalidade para fechar alertas automaticamente
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
    
    // Função para confirmar ações de exclusão
    setupDeleteConfirmations();
    
    // Inicializar campos de data com datepicker (se disponível)
    initializeDatepickers();
});

/**
 * Configurar confirmações para ações de exclusão
 */
function setupDeleteConfirmations() {
    var deleteButtons = document.querySelectorAll('.delete-confirm');
    
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            if (!confirm('Tem certeza que deseja excluir este item? Esta ação não pode ser desfeita.')) {
                e.preventDefault();
                return false;
            }
        });
    });
}

/**
 * Inicializar campos de data com datepicker
 */
function initializeDatepickers() {
    var dateInputs = document.querySelectorAll('input[type="date"]');
    dateInputs.forEach(function(input) {
        // Adicionar placeholder se não houver
        if (!input.getAttribute('placeholder')) {
            input.setAttribute('placeholder', 'dd/mm/aaaa');
        }
    });
}

/**
 * Formatar um valor numérico como moeda (BRL)
 */
function formatCurrency(value) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(value);
}

/**
 * Função para adicionar linhas dinâmicas em formulários
 */
function addDynamicRow(tableId, templateId) {
    var table = document.getElementById(tableId);
    var template = document.getElementById(templateId);
    var newRow = template.content.cloneNode(true);
    var tbody = table.querySelector('tbody');
    
    // Adicionar eventos aos novos elementos
    var deleteButton = newRow.querySelector('.btn-remove-row');
    if (deleteButton) {
        deleteButton.addEventListener('click', function(e) {
            e.preventDefault();
            var row = this.closest('tr');
            row.parentNode.removeChild(row);
        });
    }
    
    tbody.appendChild(newRow);
}

/**
 * Exibir mensagem de alerta temporária
 */
function showAlert(message, type = 'success', duration = 3000) {
    var alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
    alertDiv.setAttribute('role', 'alert');
    alertDiv.style.zIndex = '9999';
    alertDiv.style.maxWidth = '500px';
    
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Fechar"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Remover o alerta após a duração especificada
    setTimeout(function() {
        var bsAlert = new bootstrap.Alert(alertDiv);
        bsAlert.close();
    }, duration);
}