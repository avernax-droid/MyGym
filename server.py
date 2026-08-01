# ==============================================================================
# PROJETO: MyGym
# MÓDULO: server.py
# DATA DE CRIAÇÃO: 26/07/30
# TÍTULO: Servidor Principal (Motor e Roteamento)
# FUNÇÃO: Inicializar a aplicação Flask, gerenciar a sessão dos usuários e executar o roteamento de templates com base na análise do User-Agent (Desktop vs Mobile).
#
# HISTÓRICO DE ALTERAÇÕES:
# 26/07/30: Criação do módulo principal com detecção de dispositivos e rotas iniciais de teste.
# 26/07/30: Correção na rota index para renderizar 'cover.html' no ambiente desktop ao invés de 'base.html'.
# 31/07/26: Inclusão da rota /backoffice/funcionarios/novo para exibir o formulário de cadastro.
# 31/07/26: Ajuste na rota raiz (index) para aceitar requisições POST e validar o login master.
# 31/07/26: Integração com o arquivo .env e criação da rota POST para salvar funcionários no banco de dados.
# ==============================================================================

import os
from flask import Flask, render_template, request, session, redirect, url_for
from dotenv import load_dotenv
import re

# Importa a função de conexão com o banco
from database.connection import get_connection

# Carrega as variáveis do arquivo .env
load_dotenv()

app = Flask(__name__)
# Agora a chave de segurança é lida do arquivo .env
app.secret_key = os.getenv('SECRET_KEY', 'chave_padrao_fallback')

def is_mobile(user_agent):
    """
    Função auxiliar que analisa o User-Agent do navegador.
    Retorna True se identificar um dispositivo móvel, False para Desktop.
    """
    if not user_agent:
        return False
        
    mobile_patterns = [
        'Android', 'webOS', 'iPhone', 'iPad', 'iPod', 'BlackBerry', 'Windows Phone'
    ]
    
    for pattern in mobile_patterns:
        if re.search(pattern, user_agent.string, re.IGNORECASE):
            return True
            
    return False

@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Rota principal. Processa o login via POST e direciona para o template adequado com base no dispositivo.
    """
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Validação do Usuário Master (Seed) conforme a Especificação V4
        if username == 'admin' and password == 'admin#123':
            session['perfil'] = 'admin'
            session['nome_completo'] = 'Administrador Master'
            return redirect(url_for('index'))
        else:
            # Falha de autenticação (recarrega a página inicial por segurança)
            return redirect(url_for('index'))

    mobile = is_mobile(request.user_agent)
    
    if mobile:
        # Entrega a versão fluida focada em usabilidade touch
        return render_template('mobile/cover.html')
    else:
        # Renderiza o cover do desktop que herda o base.html e injeta o conteúdo central
        return render_template('cover.html')

@app.route('/toggle-admin')
def toggle_admin():
    """
    Rota de conveniência para testes de desenvolvimento.
    Acessar http://localhost:5000/toggle-admin vai ativar ou desativar o status de Admin na sessão,
    permitindo testar a exibição condicional do menu "Cadastro Admin" no Backoffice.
    """
    if session.get('perfil') == 'admin':
        session.pop('perfil', None) # Remove o perfil (simula logout)
    else:
        session['perfil'] = 'admin' # Define o perfil como administrador master
        
    return redirect(url_for('index'))

@app.route('/backoffice/funcionarios/novo')
def novo_funcionario():
    """
    Rota para exibir o formulário de cadastro de novos funcionários no backoffice.
    """
    # TODO: Adicionar futuramente a validação de sessão (verificar se está logado e é admin)
    return render_template('backoffice/cadastro_funcionario.html')

@app.route('/backoffice/funcionarios/salvar', methods=['POST'])
def salvar_funcionario():
    """
    Rota responsável por receber os dados do formulário e inseri-los no banco de dados.
    """
    # TODO: Adicionar futuramente a validação de sessão (verificar se está logado e é admin)
    
    # Captura os dados enviados pelo formulário HTML
    nome_completo = request.form.get('nome_completo')
    email = request.form.get('email')
    telefone = request.form.get('telefone')
    cargo = request.form.get('cargo')
    status = request.form.get('status')
    
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            sql = """
                INSERT INTO funcionarios (nome_completo, email, telefone, cargo, status)
                VALUES (%s, %s, %s, %s, %s)
            """
            valores = (nome_completo, email, telefone, cargo, status)
            cursor.execute(sql, valores)
            conn.commit()
            print(f"Funcionário {nome_completo} salvo com sucesso!")
        except Exception as e:
            print(f"Erro ao salvar o funcionário no banco: {e}")
        finally:
            cursor.close()
            conn.close()
            
    # Redireciona o usuário de volta para a tela de cadastro
    return redirect(url_for('novo_funcionario'))

if __name__ == '__main__':
    # host='0.0.0.0' permite acessar a aplicação a partir de outras máquinas/dispositivos na rede local
    app.run(host='0.0.0.0', port=5000, debug=True)