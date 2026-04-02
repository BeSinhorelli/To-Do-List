// API Endpoints
const API_BASE_URL = '/api';

// Estado da aplicação
let tasks = [];
let currentFilter = 'all';

// Elementos DOM
const taskForm = document.getElementById('taskForm');
const tasksList = document.getElementById('tasksList');
const filterBtns = document.querySelectorAll('.filter-btn');

// Carregar tarefas ao iniciar
document.addEventListener('DOMContentLoaded', () => {
    loadTasks();
    setupEventListeners();
});

function setupEventListeners() {
    taskForm.addEventListener('submit', handleAddTask);
    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => handleFilterChange(btn.dataset.filter));
    });
}

async function loadTasks() {
    try {
        const response = await fetch(`${API_BASE_URL}/tasks`);
        tasks = await response.json();
        renderTasks();
    } catch (error) {
        console.error('Erro ao carregar tarefas:', error);
        showError('Erro ao carregar tarefas. Verifique sua conexão.');
    }
}

async function handleAddTask(e) {
    e.preventDefault();
    
    const title = document.getElementById('taskTitle').value.trim();
    const description = document.getElementById('taskDescription').value.trim();
    
    if (!title) {
        showError('Por favor, insira um título para a tarefa.');
        return;
    }
    
    const newTask = {
        title: title,
        description: description
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}/tasks`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(newTask)
        });
        
        const task = await response.json();
        tasks.push(task);
        renderTasks();
        taskForm.reset();
        
        // Mostrar mensagem de sucesso
        showSuccess('Tarefa adicionada com sucesso!');
    } catch (error) {
        console.error('Erro ao adicionar tarefa:', error);
        showError('Erro ao adicionar tarefa. Tente novamente.');
    }
}

async function handleToggleTask(taskId) {
    try {
        const response = await fetch(`${API_BASE_URL}/tasks/${taskId}/toggle`, {
            method: 'PATCH'
        });
        
        const updatedTask = await response.json();
        const index = tasks.findIndex(t => t.id === taskId);
        if (index !== -1) {
            tasks[index] = updatedTask;
            renderTasks();
        }
    } catch (error) {
        console.error('Erro ao alternar status da tarefa:', error);
        showError('Erro ao atualizar tarefa.');
    }
}

async function handleDeleteTask(taskId) {
    if (!confirm('Tem certeza que deseja excluir esta tarefa?')) return;
    
    try {
        await fetch(`${API_BASE_URL}/tasks/${taskId}`, {
            method: 'DELETE'
        });
        
        tasks = tasks.filter(t => t.id !== taskId);
        renderTasks();
        showSuccess('Tarefa excluída com sucesso!');
    } catch (error) {
        console.error('Erro ao excluir tarefa:', error);
        showError('Erro ao excluir tarefa.');
    }
}

function handleFilterChange(filter) {
    currentFilter = filter;
    
    // Atualizar classes dos botões
    filterBtns.forEach(btn => {
        if (btn.dataset.filter === filter) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
    
    renderTasks();
}

function getFilteredTasks() {
    switch (currentFilter) {
        case 'pending':
            return tasks.filter(task => !task.completed);
        case 'completed':
            return tasks.filter(task => task.completed);
        default:
            return tasks;
    }
}

function renderTasks() {
    const filteredTasks = getFilteredTasks();
    
    if (filteredTasks.length === 0) {
        tasksList.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-check-circle"></i>
                <p>Nenhuma tarefa encontrada</p>
                <small>Adicione sua primeira tarefa acima!</small>
            </div>
        `;
        return;
    }
    
    tasksList.innerHTML = filteredTasks.map(task => `
        <div class="task-card ${task.completed ? 'completed' : ''}" data-task-id="${task.id}">
            <div class="task-header">
                <div class="task-title">${escapeHtml(task.title)}</div>
                <div class="task-actions">
                    <button class="action-btn complete-btn" onclick="handleToggleTask(${task.id})">
                        <i class="fas ${task.completed ? 'fa-undo' : 'fa-check'}"></i>
                    </button>
                    <button class="action-btn delete-btn" onclick="handleDeleteTask(${task.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
            ${task.description ? `
                <div class="task-description">
                    ${escapeHtml(task.description)}
                </div>
            ` : ''}
            <div class="task-date">
                <i class="far fa-calendar-alt"></i>
                Criado em: ${formatDate(task.created_at)}
            </div>
        </div>
    `).join('');
}

// Funções utilitárias
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function showError(message) {
    showNotification(message, 'error');
}

function showSuccess(message) {
    showNotification(message, 'success');
}

function showNotification(message, type) {
    // Criar elemento de notificação
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'}"></i>
        <span>${message}</span>
    `;
    
    // Estilos da notificação
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 20px;
        background: ${type === 'success' ? '#28a745' : '#dc3545'};
        color: white;
        border-radius: 8px;
        z-index: 1000;
        animation: slideInRight 0.3s ease-out;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    `;
    
    document.body.appendChild(notification);
    
    // Remover após 3 segundos
    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Adicionar animações ao CSS dinamicamente
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);