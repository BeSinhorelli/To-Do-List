from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from datetime import datetime
import mysql.connector
from mysql.connector import Error
import os
import logging
from dotenv import load_dotenv
from functools import wraps

# Carregar variáveis de ambiente
load_dotenv()

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Habilitar CORS para todas as rotas

# Configuração do banco de dados
class DatabaseConfig:
    """Classe de configuração do banco de dados"""
    
    DB_CONFIG = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': os.getenv('DB_NAME', 'todo_app'),
        'charset': 'utf8mb4',
        'use_unicode': True,
        'autocommit': False,
        'pool_name': 'todo_pool',
        'pool_size': 5
    }
    
    @classmethod
    def get_connection(cls):
        """Obtém uma conexão com o banco de dados"""
        try:
            connection = mysql.connector.connect(**cls.DB_CONFIG)
            logger.info("Conexão com o banco de dados estabelecida")
            return connection
        except Error as e:
            logger.error(f"Erro ao conectar ao MySQL: {e}")
            return None

def handle_db_errors(f):
    """Decorator para tratamento de erros do banco de dados"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Erro em {f.__name__}: {str(e)}")
            return jsonify({
                'error': 'Erro interno do servidor',
                'message': str(e) if app.debug else 'Tente novamente mais tarde'
            }), 500
    return decorated_function

def init_database():
    """Inicializa o banco de dados e cria a tabela se não existir"""
    connection = DatabaseConfig.get_connection()
    if not connection:
        logger.error("Não foi possível inicializar o banco de dados")
        return False
    
    try:
        cursor = connection.cursor()
        
        # Criar tabela de tarefas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                completed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        connection.commit()
        logger.info("Banco de dados inicializado com sucesso!")
        return True
        
    except Error as e:
        logger.error(f"Erro ao criar tabela: {e}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if connection:
            connection.close()

def validate_task_data(data):
    """Valida os dados da tarefa"""
    errors = []
    
    # Validar título
    title = data.get('title', '').strip()
    if not title:
        errors.append('Título é obrigatório')
    elif len(title) > 255:
        errors.append('Título deve ter no máximo 255 caracteres')
    elif len(title) < 3:
        errors.append('Título deve ter no mínimo 3 caracteres')
    
    # Validar descrição (opcional)
    description = data.get('description', '').strip()
    if description and len(description) > 1000:
        errors.append('Descrição deve ter no máximo 1000 caracteres')
    
    return {
        'is_valid': len(errors) == 0,
        'errors': errors,
        'cleaned_data': {
            'title': title,
            'description': description
        }
    }

def format_task_for_response(task):
    """Formata a tarefa para resposta JSON"""
    if not task:
        return None
    
    formatted = {
        'id': task['id'],
        'title': task['title'],
        'description': task['description'] or '',
        'completed': bool(task['completed']),
        'created_at': task['created_at'].strftime('%Y-%m-%d %H:%M:%S') if isinstance(task['created_at'], datetime) else task['created_at'],
        'updated_at': task['updated_at'].strftime('%Y-%m-%d %H:%M:%S') if isinstance(task.get('updated_at'), datetime) else task.get('updated_at')
    }
    return formatted

@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')

@app.route('/api/health', methods=['GET'])
def health_check():
    """Verifica a saúde da aplicação"""
    # Testar conexão com o banco
    connection = DatabaseConfig.get_connection()
    db_status = 'connected' if connection else 'disconnected'
    if connection:
        connection.close()
    
    return jsonify({
        'status': 'ok',
        'database': db_status,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/tasks', methods=['GET'])
@handle_db_errors
def get_tasks():
    """Retorna todas as tarefas"""
    connection = DatabaseConfig.get_connection()
    if not connection:
        return jsonify({'error': 'Erro de conexão com o banco de dados'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Suporte a filtros via query parameters
        filter_status = request.args.get('status')  # all, pending, completed
        
        query = "SELECT * FROM tasks WHERE 1=1"
        params = []
        
        if filter_status == 'pending':
            query += " AND completed = 0"
        elif filter_status == 'completed':
            query += " AND completed = 1"
        
        query += " ORDER BY created_at DESC"
        
        cursor.execute(query, params)
        tasks = cursor.fetchall()
        
        # Formatar tarefas para resposta
        formatted_tasks = [format_task_for_response(task) for task in tasks]
        
        logger.info(f"Retornando {len(formatted_tasks)} tarefas")
        return jsonify(formatted_tasks)
        
    except Error as e:
        logger.error(f"Erro ao buscar tarefas: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if connection:
            connection.close()

@app.route('/api/tasks', methods=['POST'])
@handle_db_errors
def add_task():
    """Adiciona uma nova tarefa"""
    data = request.json
    
    # Validar dados
    validation = validate_task_data(data)
    if not validation['is_valid']:
        return jsonify({
            'error': 'Dados inválidos',
            'details': validation['errors']
        }), 400
    
    cleaned_data = validation['cleaned_data']
    
    connection = DatabaseConfig.get_connection()
    if not connection:
        return jsonify({'error': 'Erro de conexão com o banco de dados'}), 500
    
    try:
        cursor = connection.cursor()
        query = """
            INSERT INTO tasks (title, description, completed, created_at)
            VALUES (%s, %s, %s, %s)
        """
        created_at = datetime.now()
        cursor.execute(query, (
            cleaned_data['title'],
            cleaned_data['description'],
            False,
            created_at
        ))
        connection.commit()
        
        task_id = cursor.lastrowid
        logger.info(f"Nova tarefa criada: ID {task_id}")
        
        # Buscar a tarefa criada
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
        new_task = cursor.fetchone()
        
        return jsonify(format_task_for_response(new_task)), 201
        
    except Error as e:
        connection.rollback()
        logger.error(f"Erro ao adicionar tarefa: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if connection:
            connection.close()

@app.route('/api/tasks/<int:task_id>', methods=['GET'])
@handle_db_errors
def get_task(task_id):
    """Retorna uma tarefa específica"""
    connection = DatabaseConfig.get_connection()
    if not connection:
        return jsonify({'error': 'Erro de conexão com o banco de dados'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
        task = cursor.fetchone()
        
        if not task:
            return jsonify({'error': 'Tarefa não encontrada'}), 404
        
        return jsonify(format_task_for_response(task))
        
    except Error as e:
        logger.error(f"Erro ao buscar tarefa {task_id}: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if connection:
            connection.close()

@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
@handle_db_errors
def update_task(task_id):
    """Atualiza uma tarefa existente"""
    data = request.json
    
    # Validar dados
    validation = validate_task_data(data)
    if not validation['is_valid']:
        return jsonify({
            'error': 'Dados inválidos',
            'details': validation['errors']
        }), 400
    
    cleaned_data = validation['cleaned_data']
    completed = data.get('completed', False)
    
    connection = DatabaseConfig.get_connection()
    if not connection:
        return jsonify({'error': 'Erro de conexão com o banco de dados'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Verificar se a tarefa existe
        cursor.execute("SELECT id FROM tasks WHERE id = %s", (task_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Tarefa não encontrada'}), 404
        
        # Atualizar tarefa
        query = """
            UPDATE tasks 
            SET title = %s, description = %s, completed = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        cursor.execute(query, (
            cleaned_data['title'],
            cleaned_data['description'],
            completed,
            task_id
        ))
        connection.commit()
        
        logger.info(f"Tarefa {task_id} atualizada")
        
        # Buscar a tarefa atualizada
        cursor.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
        updated_task = cursor.fetchone()
        
        return jsonify(format_task_for_response(updated_task))
        
    except Error as e:
        connection.rollback()
        logger.error(f"Erro ao atualizar tarefa {task_id}: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if connection:
            connection.close()

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
@handle_db_errors
def delete_task(task_id):
    """Remove uma tarefa"""
    connection = DatabaseConfig.get_connection()
    if not connection:
        return jsonify({'error': 'Erro de conexão com o banco de dados'}), 500
    
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
        connection.commit()
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Tarefa não encontrada'}), 404
        
        logger.info(f"Tarefa {task_id} deletada")
        return jsonify({
            'message': 'Tarefa deletada com sucesso',
            'id': task_id
        }), 200
        
    except Error as e:
        connection.rollback()
        logger.error(f"Erro ao deletar tarefa {task_id}: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if connection:
            connection.close()

@app.route('/api/tasks/<int:task_id>/toggle', methods=['PATCH'])
@handle_db_errors
def toggle_task(task_id):
    """Alterna o status de conclusão da tarefa"""
    connection = DatabaseConfig.get_connection()
    if not connection:
        return jsonify({'error': 'Erro de conexão com o banco de dados'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Primeiro, pegar o status atual
        cursor.execute("SELECT completed FROM tasks WHERE id = %s", (task_id,))
        result = cursor.fetchone()
        
        if not result:
            return jsonify({'error': 'Tarefa não encontrada'}), 404
        
        new_status = not bool(result['completed'])
        
        # Atualizar o status
        cursor.execute(
            "UPDATE tasks SET completed = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
            (new_status, task_id)
        )
        connection.commit()
        
        logger.info(f"Tarefa {task_id} status alterado para {new_status}")
        
        # Buscar a tarefa atualizada
        cursor.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
        updated_task = cursor.fetchone()
        
        return jsonify(format_task_for_response(updated_task))
        
    except Error as e:
        connection.rollback()
        logger.error(f"Erro ao alternar status da tarefa {task_id}: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if connection:
            connection.close()

@app.route('/api/tasks/stats', methods=['GET'])
@handle_db_errors
def get_stats():
    """Retorna estatísticas das tarefas"""
    connection = DatabaseConfig.get_connection()
    if not connection:
        return jsonify({'error': 'Erro de conexão com o banco de dados'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Total de tarefas
        cursor.execute("SELECT COUNT(*) as total FROM tasks")
        total = cursor.fetchone()['total']
        
        # Tarefas completadas vs pendentes
        cursor.execute("""
            SELECT 
                SUM(completed) as completed,
                SUM(NOT completed) as pending
            FROM tasks
        """)
        status = cursor.fetchone()
        
        return jsonify({
            'total': total,
            'completed': status['completed'] or 0,
            'pending': status['pending'] or 0
        })
        
    except Error as e:
        logger.error(f"Erro ao buscar estatísticas: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if connection:
            connection.close()

@app.errorhandler(404)
def not_found(error):
    """Tratamento de erro 404"""
    return jsonify({'error': 'Recurso não encontrado'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Tratamento de erro 500"""
    logger.error(f"Erro interno: {error}")
    return jsonify({'error': 'Erro interno do servidor'}), 500

if __name__ == '__main__':
    # Inicializar o banco de dados
    if init_database():
        logger.info("Aplicação iniciando...")
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        logger.error("Falha ao inicializar o banco de dados. Aplicação não iniciada.")