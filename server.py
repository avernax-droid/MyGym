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
# 01/08/26: Criação da rota /logout para encerramento de sessão e limpeza de cookies.
# 01/08/26: Criação da rota /api/funcionarios/buscar para auto-preenchimento AJAX via Nome Completo.
# 03/08/26: Adição da rota /cadastrar_usuario para salvar novos acessos na tabela usuarios.
# 03/08/26: Atualização da busca AJAX e da rota /backoffice/funcionarios/salvar para tratar UPDATE através do ID (Chave Primária).
# 03/08/26: Atualização da rota index para validar login com banco de dados e redirect com parâmetro show_login.
# 03/08/26: Adição de validação de existência na base (funcionarios/professores/alunos) antes de criar o usuário.
# 03/08/26: Ajuste na validação do Professor para buscar na tabela funcionarios (Opção B) e correção de aspas na msg_erro.
# ==============================================================================

import os
from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from dotenv import load_dotenv
import re
from werkzeug.security import generate_password_hash, check_password_hash

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
            # Validação via banco de dados para os demais usuários
            conn = get_connection()
            if conn:
                try:
                    cursor = conn.cursor()
                    sql = "SELECT password_hash, perfil, nome_completo FROM usuarios WHERE username = %s"
                    cursor.execute(sql, (username,))
                    usuario = cursor.fetchone()
                    
                    if usuario and check_password_hash(usuario[0], password):
                        session['perfil'] = usuario[1]
                        session['nome_completo'] = usuario[2]
                        return redirect(url_for('index'))
                except Exception as e:
                    print(f"Erro ao validar login no banco: {e}")
                finally:
                    cursor.close()
                    conn.close()

            # Falha de autenticação (recarrega a página inicial por segurança)
            return redirect(url_for('index'))

    mobile = is_mobile(request.user_agent)
    
    if mobile:
        # Entrega a versão fluida focada em usabilidade touch
        return render_template('mobile/cover.html')
    else:
        # Renderiza o cover do desktop que herda o base.html e injeta o conteúdo central
        return render_template('cover.html')

@app.route('/logout')
def logout():
    """
    Rota responsável por encerrar a sessão do usuário, limpando os cookies e redirecionando para a capa.
    """
    session.clear()
    return redirect(url_for('index'))

@app.route('/toggle-admin')
def toggle_admin():
    """
    Rota de conveniência para testes de desenvolvimento.
    """
    if session.get('perfil') == 'admin':
        session.pop('perfil', None)
    else:
        session['perfil'] = 'admin'
        
    return redirect(url_for('index'))

@app.route('/cadastrar_usuario', methods=['POST'])
def cadastrar_usuario():
    """
    Rota responsável por receber os dados do modal de Cadastro de Primeiro Acesso
    e inserir na tabela `usuarios`, validando antes se o registro existe na base raiz.
    """
    perfil = request.form.get('perfil_acesso')
    nome_completo = request.form.get('nome_completo')
    username = request.form.get('novo_username')
    senha = request.form.get('nova_senha')
    confirma_senha = request.form.get('confirma_senha')

    if senha != confirma_senha:
        # Redireciona em caso de senhas divergentes
        return redirect(url_for('index', erro_cadastro="As senhas não conferem."))

    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # --- VALIDAÇÃO DE EXISTÊNCIA NA BASE RAIZ ---
            # O professor é primeiramente um funcionário, então validamos na tabela de funcionarios
            tabela_map = {
                'funcionario': 'funcionarios',
                'professor': 'funcionarios',
                'aluno': 'alunos'
            }
            
            tabela_alvo = tabela_map.get(perfil)
            if tabela_alvo:
                sql_check = f"SELECT id FROM {tabela_alvo} WHERE nome_completo = %s LIMIT 1"
                try:
                    cursor.execute(sql_check, (nome_completo,))
                    existe = cursor.fetchone()
                    if not existe:
                        # Removidas as aspas simples ao redor de {nome_completo} para evitar erro visual no JavaScript
                        msg_erro = f"{perfil.capitalize()} {nome_completo} não encontrado(a) na base de dados do sistema."
                        return redirect(url_for('index', erro_cadastro=msg_erro))
                except Exception as e:
                    print(f"Erro ao verificar existência na tabela {tabela_alvo}: {e}")
                    msg_erro = f"Não foi possível validar o cadastro de {perfil.capitalize()}. Verifique com o administrador."
                    return redirect(url_for('index', erro_cadastro=msg_erro))
            # --------------------------------------------

            # Criptografa a senha antes de salvar no banco
            password_hash = generate_password_hash(senha)

            sql = """
                INSERT INTO usuarios (username, password_hash, perfil, status, nome_completo, senha_provisoria)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            # Define o status padrão como ativo e senha_provisoria como false (0)
            valores = (username, password_hash, perfil, 'ativo', nome_completo, 0)
            cursor.execute(sql, valores)
            conn.commit()
            print(f"Usuário {username} cadastrado com sucesso!")
        except Exception as e:
            print(f"Erro ao cadastrar usuário: {e}")
            return redirect(url_for('index', erro_cadastro="Erro interno ao tentar salvar o usuário."))
        finally:
            cursor.close()
            conn.close()
            
    # Redireciona de volta passando o parâmetro para exibir o login automaticamente
    return redirect(url_for('index', show_login='true'))

@app.route('/api/funcionarios/buscar', methods=['GET'])
def buscar_funcionario():
    """
    Rota API para buscar um funcionário pelo nome completo.
    Retorna JSON com os dados e o ID caso encontrado.
    """
    nome = request.args.get('nome')
    if not nome:
        return jsonify({'encontrado': False})

    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            # Adicionado o ID na busca SQL
            sql = "SELECT id, email, telefone, cargo, status FROM funcionarios WHERE nome_completo = %s LIMIT 1"
            cursor.execute(sql, (nome,))
            row = cursor.fetchone()
            
            if row:
                return jsonify({
                    'encontrado': True,
                    'dados': {
                        'id': row[0],
                        'email': row[1],
                        'telefone': row[2],
                        'cargo': row[3],
                        'status': row[4]
                    }
                })
        except Exception as e:
            print(f"Erro ao buscar funcionário via API: {e}")
        finally:
            cursor.close()
            conn.close()
            
    return jsonify({'encontrado': False})

@app.route('/backoffice/funcionarios/novo')
def novo_funcionario():
    """
    Rota para exibir o formulário de cadastro de novos funcionários no backoffice.
    """
    return render_template('backoffice/cadastro_funcionario.html')

@app.route('/backoffice/funcionarios/salvar', methods=['POST'])
def salvar_funcionario():
    """
    Rota responsável por receber os dados do formulário, verificar se possui ID 
    e executar UPDATE ou INSERT no banco de dados.
    """
    funcionario_id = request.form.get('funcionario_id')
    nome_completo = request.form.get('nome_completo')
    email = request.form.get('email')
    telefone = request.form.get('telefone')
    cargo = request.form.get('cargo')
    status = request.form.get('status')
    
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            if funcionario_id: # Se houver ID, executa UPDATE
                sql = """
                    UPDATE funcionarios 
                    SET nome_completo=%s, email=%s, telefone=%s, cargo=%s, status=%s 
                    WHERE id=%s
                """
                valores = (nome_completo, email, telefone, cargo, status, funcionario_id)
                cursor.execute(sql, valores)
                conn.commit()
                print(f"Funcionário {nome_completo} atualizado com sucesso!")
            else: # Se não houver ID, executa INSERT
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
            
    return redirect(url_for('novo_funcionario'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)