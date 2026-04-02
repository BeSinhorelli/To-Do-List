# <h1 align="center"> 📝 Gerenciador de Tarefas - To-Do List API </h1>

Aplicação web full stack para gerenciamento de tarefas, com backend em Python utilizando Flask, integração com banco de dados MySQL e interface web moderna construída com HTML, CSS e JavaScript.

O sistema permite o gerenciamento completo de tarefas, com foco em organização, produtividade e experiência do usuário.

---

## 🚀 Funcionalidades

- ✅ CRUD completo de tarefas (Criar, Ler, Atualizar, Deletar)
- ✅ Marcação de tarefas como concluídas ou pendentes
- ✅ Filtros por status: todas, pendentes e concluídas
- ✅ Interface responsiva (desktop e mobile)
- ✅ Notificações visuais para feedback de ações
- ✅ API RESTful estruturada
- ✅ Persistência em banco de dados MySQL
- ✅ Logging para debugging
- ✅ Endpoint de health check para monitoramento
- ✅ Estatísticas das tarefas

---

## 🛠️ Tecnologias Utilizadas

### Backend
- Python 3.8+
- Flask
- MySQL Connector
- python-dotenv

### Frontend
- HTML5
- CSS3 (Flexbox, Grid, animações)
- JavaScript (ES6+)
- Font Awesome

### Banco de Dados
- MySQL (executado em ambiente local via XAMPP)

---

## 📋 Pré-requisitos

Antes de começar, você vai precisar ter instalado:

- Python 3.8+
- MySQL ou MariaDB (ou XAMPP)
- pip
- Git

---

## 📦 Instalação

### 1. Clone o repositório
```bash
git clone https://github.com/BeSinhorelli/To-Do-List-API.git
cd To-Do-List-API

pip install -r requirements.txt
CREATE DATABASE todo_app;
python app.py
