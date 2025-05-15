/**
 * SISTEMA INTEGRA UBS - JavaScript para Gráficos
 * 
 * Arquivo contendo funções para criação e manipulação de gráficos.
 */

/**
 * Cores padrão para gráficos
 */
const defaultColors = [
    'rgba(54, 162, 235, 0.7)',
    'rgba(75, 192, 192, 0.7)',
    'rgba(255, 206, 86, 0.7)',
    'rgba(255, 99, 132, 0.7)',
    'rgba(153, 102, 255, 0.7)',
    'rgba(255, 159, 64, 0.7)',
    'rgba(201, 203, 207, 0.7)',
    'rgba(0, 162, 120, 0.7)',
    'rgba(155, 89, 182, 0.7)',
    'rgba(230, 126, 34, 0.7)'
];

const defaultBorderColors = [
    'rgba(54, 162, 235, 1)',
    'rgba(75, 192, 192, 1)',
    'rgba(255, 206, 86, 1)',
    'rgba(255, 99, 132, 1)',
    'rgba(153, 102, 255, 1)',
    'rgba(255, 159, 64, 1)',
    'rgba(201, 203, 207, 1)',
    'rgba(0, 162, 120, 1)',
    'rgba(155, 89, 182, 1)',
    'rgba(230, 126, 34, 1)'
];

/**
 * Criar um gráfico de barras simples
 */
function createBarChart(elementId, labels, values, title = '', colors = defaultColors, borderColors = defaultBorderColors) {
    const ctx = document.getElementById(elementId).getContext('2d');
    
    // Garantir que temos cores suficientes
    while (colors.length < values.length) {
        colors = colors.concat(colors);
    }
    while (borderColors.length < values.length) {
        borderColors = borderColors.concat(borderColors);
    }
    
    // Limitar ao número necessário
    colors = colors.slice(0, values.length);
    borderColors = borderColors.slice(0, values.length);
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: title,
                data: values,
                backgroundColor: colors,
                borderColor: borderColors,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            },
            plugins: {
                legend: {
                    display: title !== ''
                }
            }
        }
    });
}

/**
 * Criar um gráfico de pizza
 */
function createPieChart(elementId, labels, values, title = '', colors = defaultColors) {
    const ctx = document.getElementById(elementId).getContext('2d');
    
    // Garantir que temos cores suficientes
    while (colors.length < values.length) {
        colors = colors.concat(colors);
    }
    
    // Limitar ao número necessário
    colors = colors.slice(0, values.length);
    
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                label: title,
                data: values,
                backgroundColor: colors,
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'right'
                },
                title: {
                    display: title !== '',
                    text: title
                }
            }
        }
    });
}

/**
 * Criar um gráfico de linha
 */
function createLineChart(elementId, labels, datasets, title = '') {
    const ctx = document.getElementById(elementId).getContext('2d');
    
    // Processar datasets
    for (let i = 0; i < datasets.length; i++) {
        if (!datasets[i].backgroundColor) {
            datasets[i].backgroundColor = defaultColors[i % defaultColors.length];
        }
        if (!datasets[i].borderColor) {
            datasets[i].borderColor = defaultBorderColors[i % defaultBorderColors.length];
        }
        datasets[i].tension = 0.1;
    }
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            },
            plugins: {
                title: {
                    display: title !== '',
                    text: title
                }
            }
        }
    });
}

/**
 * Criar um gráfico de rosca (doughnut)
 */
function createDoughnutChart(elementId, labels, values, title = '', colors = defaultColors) {
    const ctx = document.getElementById(elementId).getContext('2d');
    
    // Garantir que temos cores suficientes
    while (colors.length < values.length) {
        colors = colors.concat(colors);
    }
    
    // Limitar ao número necessário
    colors = colors.slice(0, values.length);
    
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                label: title,
                data: values,
                backgroundColor: colors,
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'right'
                },
                title: {
                    display: title !== '',
                    text: title
                }
            }
        }
    });
}