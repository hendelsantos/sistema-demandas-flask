// Funções JavaScript para o Sistema de Controle de Demandas

// Inicialização quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', function() {
    initializeTooltips();
    initializeAnimations();
    initializeFormValidations();
    initializeFileUploads();
});

// Inicializar tooltips do Bootstrap
function initializeTooltips() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Animações suaves para cards
function initializeAnimations() {
    const cards = document.querySelectorAll('.card');
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate');
            }
        });
    }, {
        threshold: 0.1
    });

    cards.forEach(card => {
        observer.observe(card);
    });
}

// Validações de formulário
function initializeFormValidations() {
    // Validação em tempo real para campos obrigatórios
    const requiredFields = document.querySelectorAll('input[required], textarea[required], select[required]');
    
    requiredFields.forEach(field => {
        field.addEventListener('blur', function() {
            validateField(this);
        });
        
        field.addEventListener('input', function() {
            if (this.classList.contains('is-invalid')) {
                validateField(this);
            }
        });
    });
}

// Validar campo individual
function validateField(field) {
    const value = field.value.trim();
    const isValid = value !== '';
    
    if (isValid) {
        field.classList.remove('is-invalid');
        field.classList.add('is-valid');
    } else {
        field.classList.remove('is-valid');
        field.classList.add('is-invalid');
    }
    
    return isValid;
}

// Inicializar uploads de arquivo
function initializeFileUploads() {
    const fileInputs = document.querySelectorAll('input[type="file"]');
    
    fileInputs.forEach(input => {
        input.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                validateFileUpload(this, file);
            }
        });
    });
}

// Validar upload de arquivo
function validateFileUpload(input, file) {
    const maxSize = 10 * 1024 * 1024; // 10MB
    const allowedTypes = ['application/pdf'];
    
    // Validar tamanho
    if (file.size > maxSize) {
        showAlert('Arquivo muito grande. Tamanho máximo: 10MB', 'error');
        input.value = '';
        return false;
    }
    
    // Validar tipo
    if (!allowedTypes.includes(file.type)) {
        showAlert('Apenas arquivos PDF são permitidos', 'error');
        input.value = '';
        return false;
    }
    
    return true;
}

// Mostrar alertas dinâmicos
function showAlert(message, type = 'info', duration = 5000) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Adicionar ao container de alertas ou ao topo da página
    const container = document.querySelector('.container') || document.body;
    container.insertBefore(alertDiv, container.firstChild);
    
    // Auto-remover após duração especificada
    if (duration > 0) {
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, duration);
    }
}

// Confirmar ações importantes
function confirmAction(message, callback) {
    if (confirm(message)) {
        if (typeof callback === 'function') {
            callback();
        }
        return true;
    }
    return false;
}

// Formatação de valores monetários
function formatCurrency(value) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(value);
}

// Formatação de datas
function formatDate(dateString, options = {}) {
    const defaultOptions = {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
    };
    
    const finalOptions = { ...defaultOptions, ...options };
    return new Date(dateString).toLocaleDateString('pt-BR', finalOptions);
}

// Debounce para pesquisas
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Loading spinner para botões
function showButtonLoading(button, text = 'Carregando...') {
    const originalText = button.innerHTML;
    button.innerHTML = `
        <span class="spinner-border spinner-border-sm me-2" role="status"></span>
        ${text}
    `;
    button.disabled = true;
    
    return () => {
        button.innerHTML = originalText;
        button.disabled = false;
    };
}

// Copiar texto para clipboard
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showAlert('Texto copiado para a área de transferência!', 'success', 3000);
    }).catch(() => {
        showAlert('Erro ao copiar texto', 'error', 3000);
    });
}

// Atualizar contadores em tempo real
function updateCounters() {
    const counters = document.querySelectorAll('[data-counter]');
    
    counters.forEach(counter => {
        const target = parseInt(counter.getAttribute('data-counter'));
        const current = parseInt(counter.textContent) || 0;
        const increment = target / 100;
        
        if (current < target) {
            counter.textContent = Math.ceil(current + increment);
            setTimeout(() => updateCounters(), 20);
        }
    });
}

// Filtrar tabelas
function filterTable(input, tableId) {
    const filter = input.value.toLowerCase();
    const table = document.getElementById(tableId);
    const rows = table.getElementsByTagName('tbody')[0].getElementsByTagName('tr');
    
    for (let i = 0; i < rows.length; i++) {
        const row = rows[i];
        const cells = row.getElementsByTagName('td');
        let found = false;
        
        for (let j = 0; j < cells.length; j++) {
            const cell = cells[j];
            if (cell.textContent.toLowerCase().indexOf(filter) > -1) {
                found = true;
                break;
            }
        }
        
        row.style.display = found ? '' : 'none';
    }
}

// Auto-save para formulários
function enableAutoSave(formId, interval = 30000) {
    const form = document.getElementById(formId);
    if (!form) return;
    
    const saveData = () => {
        const formData = new FormData(form);
        const data = Object.fromEntries(formData);
        localStorage.setItem(`autosave_${formId}`, JSON.stringify(data));
        showAlert('Dados salvos automaticamente', 'info', 2000);
    };
    
    // Salvar a cada intervalo
    setInterval(saveData, interval);
    
    // Restaurar dados salvos
    const savedData = localStorage.getItem(`autosave_${formId}`);
    if (savedData) {
        const data = JSON.parse(savedData);
        Object.keys(data).forEach(key => {
            const field = form.querySelector(`[name="${key}"]`);
            if (field) {
                field.value = data[key];
            }
        });
    }
}

// Validação de formulário antes do envio
function validateForm(form) {
    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!validateField(field)) {
            isValid = false;
        }
    });
    
    return isValid;
}

// Prevenção de duplo clique em formulários
document.addEventListener('submit', function(e) {
    const form = e.target;
    const submitButton = form.querySelector('button[type="submit"]');
    
    if (submitButton && !submitButton.disabled) {
        const stopLoading = showButtonLoading(submitButton, 'Enviando...');
        
        // Restaurar botão após 5 segundos se não houver resposta
        setTimeout(() => {
            if (submitButton.disabled) {
                stopLoading();
            }
        }, 5000);
    }
});

// Mascaras para campos
function applyMasks() {
    // Máscara para valores monetários
    const moneyInputs = document.querySelectorAll('input[data-mask="money"]');
    moneyInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            value = (value / 100).toFixed(2);
            e.target.value = value;
        });
    });
    
    // Máscara para telefone
    const phoneInputs = document.querySelectorAll('input[data-mask="phone"]');
    phoneInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            value = value.replace(/(\d{2})(\d)/, '($1) $2');
            value = value.replace(/(\d{4})(\d)/, '$1-$2');
            value = value.replace(/(\d{4})-(\d)(\d{4})/, '$1$2-$3');
            e.target.value = value;
        });
    });
}

// Inicializar máscaras quando a página carregar
document.addEventListener('DOMContentLoaded', applyMasks);

// Funções específicas para o sistema de demandas

// Atualizar status da demanda
function atualizarStatusDemanda(demandaId, novoStatus) {
    const confirmMessage = `Confirma a alteração do status para "${novoStatus}"?`;
    
    return confirmAction(confirmMessage, () => {
        // O formulário será enviado normalmente
        return true;
    });
}

// Mostrar preview de arquivo antes do upload
function previewFile(input) {
    const file = input.files[0];
    if (file && file.type === 'application/pdf') {
        const reader = new FileReader();
        reader.onload = function(e) {
            // Mostrar informações do arquivo
            const info = `
                <div class="alert alert-info">
                    <strong>Arquivo selecionado:</strong> ${file.name}<br>
                    <strong>Tamanho:</strong> ${(file.size / 1024 / 1024).toFixed(2)} MB
                </div>
            `;
            
            const preview = document.getElementById('file-preview');
            if (preview) {
                preview.innerHTML = info;
            }
        };
        reader.readAsDataURL(file);
    }
}

// Exportar funções globalmente
window.SistemaDemandas = {
    showAlert,
    confirmAction,
    formatCurrency,
    formatDate,
    updateCounters,
    filterTable,
    validateForm,
    atualizarStatusDemanda,
    previewFile
};
