# ==============================================================================
# PROJETO: MyGym
# MÓDULO: MyGym.py
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
# 04/08/26: Implementação do decorador de segurança @requer_permissao e criação das rotas para o Controle de Acessos.
# 04/08/26: Alteração na rota /api/permissoes/salvar para aplicar lógica de UPDATE caso o registro exista, ou INSERT caso contrário.
# 04/08/26: Injeção dinâmica de permissões (permissoes_cargo) na session durante o login para renderização de menu.
# 04/08/26: Correção na função is_mobile para detecção mais robusta de dispositivos móveis, sem dependência de regex.
# 05/08/26: Injeção de logs no roteamento, ativação de auto-reload de templates e bloqueio de cache HTTP na rota index para debug mobile.
# 05/08/26: Adição de dump completo dos cabeçalhos HTTP (request.headers) para investigar mascaramento pelo Ngrok.
# 05/08/26: Correção na detecção mobile utilizando request.headers brutos (User-Agent e Sec-Ch-Ua-Mobile) substituindo o objeto parseado do Flask.
# 05/08/26: Criação das rotas /recuperar_senha e /trocar_senha_obrigatoria, e interceptação de login provisório.
# 05/08/26: Implementação do envio real de e-mail de recuperação utilizando smtplib e credenciais do .env.
# 05/08/26: Ajuste de usabilidade: limpeza de espaços (.strip()) no login e remoção de caracteres ambíguos na geração da senha provisória.
# 05/08/26: Migração das validações de segurança e buscas para utilizar CPF e ID (usuario_id) em vez do nome em texto puro.
# 05/08/26: Correção no cadastro de usuário para vincular o usuario_id na tabela raiz e herdar o cargo como perfil; ajuste na recuperação de senha.
# 06/08/26: Criação das rotas para o Cadastro de Professores (/backoffice/professores/novo, /api/valida_professor_funcionario e /backoffice/professores/salvar) com validação de vínculo na tabela funcionários.
# 07/08/26: Atualização nas queries de Professores para refletir os campos nome_emergencia, telefone_emergencia e remoção do status redundante.
# 07/08/26: Implementação de upload de certificados no cadastro de professores e gravação do pathway no banco, inclusão da rota para buscar a foto_url do RH.
# 08/08/26: Refatoração estrutural (Normalização de BD). Rota de Funcionários passa a processar upload de fotos, dados demográficos e endereço.
# 08/08/26: Rota do Professor otimizada para gravar apenas dados pedagógicos, vinculando-se via 'funcionario_id' ao RH. API AJAX reestruturada.
# 08/08/26: Remoção de máscaras (hífens) das datas na inserção do funcionário.
# 08/08/26: Migração para suporte a múltiplos certificados via tabela 'professor_certificados'.
# ==============================================================================

import os
import time
from functools import wraps
from flask import Flask, render_template, request, session, redirect, url_for, jsonify, make_response
from dotenv import load_dotenv
import re
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import string
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Importa a função de conexão com o banco
from database.connection import get_connection

# Carrega as variáveis do arquivo .env
load_dotenv()

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True # Força a recarga de templates em ambiente de desenvolvimento
# Agora a chave de segurança é lida do arquivo .env
app.secret_key = os.getenv('SECRET_KEY', 'chave_padrao_fallback')

def is_mobile(req):
    """
    Função auxiliar que analisa os cabeçalhos HTTP da requisição.
    Retorna True se identificar um dispositivo móvel, False para Desktop.
    """
    # Verificação primária: cabeçalho moderno do Chromium (ex: enviado pelo Chrome via Ngrok)
    sec_mobile = req.headers.get('Sec-Ch-Ua-Mobile')
    if sec_mobile == '?1':
        return True

    # Verificação secundária: leitura direta da string bruta do User-Agent
    ua_string = req.headers.get('User-Agent', '').lower()
    if not ua_string:
        return False
    
    # Validação blindada e direta na string (sem depender da biblioteca re)
    if 'mobi' in ua_string or 'android' in ua_string or 'iphone' in ua_string:
        return True
        
    return False

def requer_permissao(modulo):
    """
    Decorador para proteger as rotas. Verifica se o perfil logado tem acesso ao módulo
    especificado ou se possui a chave mestra 'mod_free'.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            perfil = session.get('perfil')
            
            # Se não estiver logado, redireciona para a capa
            if not perfil:
                return redirect(url_for('index'))
            
            # O admin master tem acesso irrestrito
            if perfil == 'admin':
                return f(*args, **kwargs)
            
            conn = get_connection()
            if conn:
                try:
                    cursor = conn.cursor()
                    # Verifica se o cargo tem acesso ao módulo solicitado OU ao módulo Free
                    sql = """
                        SELECT pode_acessar FROM permissoes_cargo 
                        WHERE cargo = %s AND (modulo = %s OR modulo = 'mod_free')
                    """
                    cursor.execute(sql, (perfil, modulo))
                    permissoes = cursor.fetchall()
                    
                    tem_acesso = False
                    for (pode_acessar,) in permissoes:
                        if pode_acessar == 1:
                            tem_acesso = True
                            break
                            
                    if tem_acesso:
                        return f(*args, **kwargs)
                except Exception as e:
                    print(f"Erro ao verificar permissão no banco: {e}")
                finally:
                    cursor.close()
                    conn.close()

            # Se não tiver acesso, bloqueia e retorna para a home
            return redirect(url_for('index'))
        return decorated_function
    return decorator

def enviar_email_recuperacao(email_destino, nome, username, senha_provisoria):
    """
    Função auxiliar para envio de e-mail de recuperação utilizando SMTP.
    """
    smtp_host = os.getenv('EMAIL_HOST')
    smtp_port = int(os.getenv('EMAIL_PORT', 587))
    smtp_user = os.getenv('EMAIL_USER')
    smtp_pass = os.getenv('EMAIL_PASS')
    
    if not smtp_host or not smtp_user or not smtp_pass:
        print("Erro: Credenciais de e-mail (SMTP) ausentes no .env.")
        return False
        
    try:
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = email_destino
        msg['Subject'] = "MyGym - Recuperação de Senha"
        
        body = f"""Olá, {nome}.
        
Uma redefinição de senha foi solicitada para o seu usuário: {username}

Sua senha provisória é: {senha_provisoria}

ATENÇÃO: Ao fazer o login com essa senha, o sistema obrigará você a cadastrar uma nova senha definitiva por motivos de segurança.

Equipe MyGym"""
        
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Erro ao tentar enviar o e-mail: {e}")
        return False

@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Rota principal. Processa o login via POST e direciona para o template adequado com base no dispositivo.
    """
    if request.method == 'POST':
        # Aplica .strip() para evitar falhas geradas por espaços em branco acidentais ao colar a senha
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        # Validação do Usuário Master (Seed) conforme a Especificação V4
        if username == 'admin' and password == 'admin#123':
            session['perfil'] = 'admin'
            session['nome_completo'] = 'Administrador Master'
            # O master sempre recebe a chave mestra na sessão
            session['permissoes'] = {'mod_free': True}
            return redirect(url_for('index'))
        else:
            # Validação via banco de dados para os demais usuários
            conn = get_connection()
            if conn:
                try:
                    cursor = conn.cursor()
                    # Adicionado senha_provisoria na query
                    sql = "SELECT password_hash, perfil, nome_completo, senha_provisoria FROM usuarios WHERE username = %s AND status = 'ativo'"
                    cursor.execute(sql, (username,))
                    usuario = cursor.fetchone()
                    
                    if usuario and check_password_hash(usuario[0], password):
                        # Se tiver senha provisória, bloqueia sessão e envia flag para trocar senha
                        if usuario[3] == 1:
                            return redirect(url_for('index', force_reset='true', reset_user=username))
                        
                        session['perfil'] = usuario[1]
                        session['nome_completo'] = usuario[2]
                        
                        # --- CARGA DINÂMICA DE PERMISSÕES NA SESSÃO ---
                        # Busca todos os módulos que este perfil tem permissão (pode_acessar = 1)
                        sql_permissoes = "SELECT modulo FROM permissoes_cargo WHERE cargo = %s AND pode_acessar = 1"
                        cursor.execute(sql_permissoes, (usuario[1],))
                        perms = cursor.fetchall()
                        
                        # Transforma o resultado em um dicionário para acesso fácil no Jinja2 (HTML)
                        session['permissoes'] = {p[0]: True for p in perms}
                        # ----------------------------------------------
                        
                        return redirect(url_for('index'))
                except Exception as e:
                    print(f"Erro ao validar login no banco: {e}")
                finally:
                    cursor.close()
                    conn.close()

            # Falha de autenticação (recarrega a página inicial por segurança)
            return redirect(url_for('index', erro_login='Credenciais inválidas.'))

    # Captura o User-Agent bruto direto dos headers para o log
    user_agent_str = request.headers.get('User-Agent', 'Desconhecido')
    # Passa o objeto request inteiro para nossa nova função
    mobile = is_mobile(request)
    
    if mobile:
        # Entrega a versão fluida focada em usabilidade touch
        resp = make_response(render_template('mobile/cover.html'))
    else:
        # Renderiza o cover do desktop que herda o base.html e injeta o conteúdo central
        resp = make_response(render_template('cover.html'))
        
    # Injeção de headers para bloquear o uso de cache em navegadores móveis
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    
    return resp

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
        session['permissoes'] = {'mod_free': True} # Atualiza a chave mestra no toggle
        
    return redirect(url_for('index'))

@app.route('/cadastrar_usuario', methods=['POST'])
def cadastrar_usuario():
    """
    Rota responsável por receber os dados do modal de Cadastro de Primeiro Acesso
    e inserir na tabela `usuarios`, validando antes se o registro existe na base raiz via CPF,
    garantindo que o vínculo (usuario_id) seja preenchido na tabela de origem.
    """
    perfil_form = request.form.get('perfil_acesso')
    cpf = request.form.get('cpf')
    nome_completo = request.form.get('nome_completo')
    username = request.form.get('novo_username')
    senha = request.form.get('nova_senha')
    confirma_senha = request.form.get('confirma_senha')

    if senha != confirma_senha:
        return redirect(url_for('index', erro_cadastro="As senhas não conferem."))

    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # --- VALIDAÇÃO DE EXISTÊNCIA E CAPTURA DO CARGO REAL ---
            tabela_map = {
                'funcionario': 'funcionarios',
                'professor': 'funcionarios',
                'aluno': 'alunos'
            }
            
            tabela_alvo = tabela_map.get(perfil_form)
            base_id = None
            perfil_final = perfil_form # Fallback inicial
            
            if tabela_alvo:
                # Busca o ID na base raiz, e se for funcionário, traz também o cargo
                if tabela_alvo == 'funcionarios':
                    sql_check = f"SELECT id, cargo FROM {tabela_alvo} WHERE cpf = %s LIMIT 1"
                else:
                    sql_check = f"SELECT id FROM {tabela_alvo} WHERE cpf = %s LIMIT 1"
                    
                try:
                    cursor.execute(sql_check, (cpf,))
                    existe = cursor.fetchone()
                    if not existe:
                        msg_erro = f"{perfil_form.capitalize()} portador do CPF informado não encontrado na base de dados do sistema."
                        return redirect(url_for('index', erro_cadastro=msg_erro))
                    
                    base_id = existe[0]
                    # Sobrescreve o perfil genérico pelo cargo real para garantir as permissões
                    if tabela_alvo == 'funcionarios':
                        perfil_final = existe[1]
                        
                except Exception as e:
                    print(f"Erro ao verificar existência na tabela {tabela_alvo}: {e}")
                    msg_erro = f"Não foi possível validar o cadastro de {perfil_form.capitalize()}. Verifique com o administrador."
                    return redirect(url_for('index', erro_cadastro=msg_erro))
            # --------------------------------------------

            # Criptografa a senha antes de salvar no banco
            password_hash = generate_password_hash(senha)

            # Salva na tabela usuarios com o perfil correto (ex: 'gerente')
            sql = """
                INSERT INTO usuarios (username, password_hash, perfil, status, nome_completo, senha_provisoria)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            valores = (username, password_hash, perfil_final, 'ativo', nome_completo, 0)
            cursor.execute(sql, valores)
            
            # Captura o ID auto incremental que acabou de ser gerado para o usuário
            novo_usuario_id = cursor.lastrowid
            
            # Criação do vínculo relacional: Atualiza a base raiz (funcionarios/alunos) preenchendo o usuario_id
            if tabela_alvo and base_id:
                sql_update_vinculo = f"UPDATE {tabela_alvo} SET usuario_id = %s WHERE id = %s"
                cursor.execute(sql_update_vinculo, (novo_usuario_id, base_id))
            
            conn.commit()
            print(f"Usuário {username} cadastrado e vinculado com sucesso!")
        except Exception as e:
            print(f"Erro ao cadastrar usuário: {e}")
            return redirect(url_for('index', erro_cadastro="Erro interno ao tentar salvar o usuário."))
        finally:
            cursor.close()
            conn.close()
            
    # Redireciona de volta passando o parâmetro para exibir o login automaticamente
    return redirect(url_for('index', show_login='true'))

@app.route('/recuperar_senha', methods=['POST'])
def recuperar_senha():
    """
    Rota que gera senha provisória limpa (sem caracteres ambíguos), atualiza o banco e envia o e-mail real.
    A busca agora utiliza o username como chave única, ignorando o perfil para evitar conflitos de herança de cargo.
    """
    perfil = request.form.get('perfil_recuperacao')
    username_recuperacao = request.form.get('username_recuperacao')
    
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # 1. Verifica se o usuário existe pesquisando apenas pelo username
            cursor.execute("SELECT id, username, nome_completo FROM usuarios WHERE username = %s LIMIT 1", (username_recuperacao,))
            user_exist = cursor.fetchone()
            
            if not user_exist:
                return redirect(url_for('index', erro_recuperacao="Usuário não encontrado ou sem acesso ao sistema."))
            
            usuario_id = user_exist[0]
            username = user_exist[1]
            nome_completo = user_exist[2]
            
            # 2. Resgata o email real cadastrado na base, mapeando pela Chave Estrangeira (usuario_id)
            tabela_map = {
                'funcionario': 'funcionarios',
                'professor': 'funcionarios', 
                'aluno': 'alunos'
            }
            
            tabela_alvo = tabela_map.get(perfil)
            email_destino = None
            
            if tabela_alvo:
                cursor.execute(f"SELECT email FROM {tabela_alvo} WHERE usuario_id = %s LIMIT 1", (usuario_id,))
                row = cursor.fetchone()
                if row and row[0]:
                    email_destino = row[0]
                    
            if not email_destino:
                return redirect(url_for('index', erro_recuperacao="Usuário sem e-mail cadastrado. Contate a secretaria."))

            # 3. Gera a senha provisória sem caracteres ambíguos (exclui 0, O, 1, l, I) para facilitar a leitura visual
            caracteres_seguros = "23456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz"
            senha_provisoria = ''.join(random.choice(caracteres_seguros) for i in range(8))
            password_hash = generate_password_hash(senha_provisoria)
            
            # 4. Atualiza o banco, ativando a flag de bloqueio/provisória
            cursor.execute("UPDATE usuarios SET password_hash = %s, senha_provisoria = 1 WHERE username = %s", (password_hash, username))
            conn.commit()
            
            # 5. Envia o e-mail real
            sucesso = enviar_email_recuperacao(email_destino, nome_completo, username, senha_provisoria)
            
            if sucesso:
                return redirect(url_for('index', msg_alerta="Senha provisória enviada para o seu e-mail!"))
            else:
                return redirect(url_for('index', erro_recuperacao="Senha gerada, mas houve falha ao enviar o e-mail. Contate o suporte."))
            
        except Exception as e:
            print(f"Erro na recuperação de senha: {e}")
            return redirect(url_for('index', erro_recuperacao="Falha ao processar solicitação."))
        finally:
            cursor.close()
            conn.close()
            
    return redirect(url_for('index'))

@app.route('/trocar_senha_obrigatoria', methods=['POST'])
def trocar_senha_obrigatoria():
    """
    Rota ativada quando o usuário entra com uma senha provisória e cadastra a nova.
    """
    username = request.form.get('reset_user')
    nova_senha = request.form.get('nova_senha', '').strip()
    confirma_senha = request.form.get('confirma_senha', '').strip()
    
    if nova_senha != confirma_senha:
        return redirect(url_for('index', force_reset='true', reset_user=username, erro_reset="As senhas não conferem."))
        
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Gera o hash da senha definitiva e zera a flag provisória
            password_hash = generate_password_hash(nova_senha)
            cursor.execute("UPDATE usuarios SET password_hash = %s, senha_provisoria = 0 WHERE username = %s", (password_hash, username))
            conn.commit()
            
            print(f"Senha definitiva cadastrada com sucesso para o usuário: {username}")
            return redirect(url_for('index', show_login='true', msg_alerta="Senha atualizada com sucesso! Por favor, faça login."))
            
        except Exception as e:
            print(f"Erro ao trocar senha obrigatória: {e}")
            return redirect(url_for('index', force_reset='true', reset_user=username, erro_reset="Erro ao salvar a nova senha."))
        finally:
            cursor.close()
            conn.close()
            
    return redirect(url_for('index'))

@app.route('/api/funcionarios/buscar', methods=['GET'])
def buscar_funcionario():
    """
    Rota API para buscar um funcionário utilizando o CPF como identificador estrutural único.
    Retorna JSON com os dados e o ID caso encontrado.
    """
    cpf = request.args.get('cpf')
    if not cpf:
        return jsonify({'encontrado': False})

    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            # Busca ampliada para incluir os novos campos centralizados
            sql = """
                SELECT id, email, telefone, cargo, status, nome_completo, sexo, 
                       data_nascimento, cep, endereco, bairro, cidade, uf, data_inicio, foto_url 
                FROM funcionarios WHERE cpf = %s LIMIT 1
            """
            cursor.execute(sql, (cpf,))
            row = cursor.fetchone()
            
            if row:
                return jsonify({
                    'encontrado': True,
                    'dados': {
                        'id': row[0],
                        'email': row[1],
                        'telefone': row[2],
                        'cargo': row[3],
                        'status': row[4],
                        'nome_completo': row[5],
                        'sexo': row[6],
                        'data_nascimento': str(row[7]) if row[7] else '',
                        'cep': row[8],
                        'endereco': row[9],
                        'bairro': row[10],
                        'cidade': row[11],
                        'uf': row[12],
                        'data_inicio': str(row[13]) if row[13] else '',
                        'foto_url': row[14]
                    }
                })
        except Exception as e:
            print(f"Erro ao buscar funcionário via API: {e}")
        finally:
            cursor.close()
            conn.close()
            
    return jsonify({'encontrado': False})

@app.route('/backoffice/funcionarios/novo')
@requer_permissao('mod_cad_func')
def novo_funcionario():
    """
    Rota para exibir o formulário de cadastro de novos funcionários no backoffice.
    """
    return render_template('backoffice/cadastro_funcionario.html')

@app.route('/backoffice/funcionarios/salvar', methods=['POST'])
@requer_permissao('mod_cad_func')
def salvar_funcionario():
    """
    Rota responsável por receber os dados do formulário, verificar se possui ID 
    e executar UPDATE ou INSERT no banco de dados, incluindo a coluna CPF e upload da foto.
    """
    funcionario_id = request.form.get('funcionario_id')
    cpf = request.form.get('cpf')
    nome_completo = request.form.get('nome_completo')
    sexo = request.form.get('sexo')
    data_nascimento = request.form.get('data_nascimento')
    email = request.form.get('email')
    telefone = request.form.get('telefone')
    cep = request.form.get('cep')
    endereco = request.form.get('endereco')
    bairro = request.form.get('bairro')
    cidade = request.form.get('cidade')
    uf = request.form.get('uf')
    cargo = request.form.get('cargo')
    data_inicio = request.form.get('data_inicio')
    status = request.form.get('status')
    
    # Tratamento para datas vazias e remoção da máscara (hífens)
    if data_nascimento: 
        data_nascimento = data_nascimento.replace('-', '')
    else: 
        data_nascimento = None
        
    if data_inicio: 
        data_inicio = data_inicio.replace('-', '')
    else: 
        data_inicio = None
    
    # --- UPLOAD DA FOTO DO FUNCIONÁRIO ---
    foto_arquivo = request.files.get('foto_arquivo')
    foto_url = None
    
    if foto_arquivo and foto_arquivo.filename != '':
        upload_folder = os.path.join(app.root_path, 'static', 'uploads', 'fotos')
        os.makedirs(upload_folder, exist_ok=True)
        
        extensao = os.path.splitext(foto_arquivo.filename)[1]
        cpf_limpo = re.sub(r'\D', '', cpf) if cpf else str(int(time.time()))
        nome_seguro = secure_filename(f"{cpf_limpo}_{int(time.time())}_foto{extensao}")
        
        caminho_fisico = os.path.join(upload_folder, nome_seguro)
        foto_arquivo.save(caminho_fisico)
        
        foto_url = f"/static/uploads/fotos/{nome_seguro}"
    # -------------------------------------
    
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            if funcionario_id: # UPDATE
                if foto_url:
                    sql = """
                        UPDATE funcionarios 
                        SET cpf=%s, nome_completo=%s, sexo=%s, data_nascimento=%s, email=%s, 
                            telefone=%s, cep=%s, endereco=%s, bairro=%s, cidade=%s, uf=%s, 
                            cargo=%s, data_inicio=%s, status=%s, foto_url=%s
                        WHERE id=%s
                    """
                    valores = (cpf, nome_completo, sexo, data_nascimento, email, telefone, cep, 
                               endereco, bairro, cidade, uf, cargo, data_inicio, status, foto_url, funcionario_id)
                else:
                    sql = """
                        UPDATE funcionarios 
                        SET cpf=%s, nome_completo=%s, sexo=%s, data_nascimento=%s, email=%s, 
                            telefone=%s, cep=%s, endereco=%s, bairro=%s, cidade=%s, uf=%s, 
                            cargo=%s, data_inicio=%s, status=%s
                        WHERE id=%s
                    """
                    valores = (cpf, nome_completo, sexo, data_nascimento, email, telefone, cep, 
                               endereco, bairro, cidade, uf, cargo, data_inicio, status, funcionario_id)
                
                cursor.execute(sql, valores)
                conn.commit()
                print(f"Funcionário {nome_completo} atualizado com sucesso!")
                
            else: # INSERT
                sql = """
                    INSERT INTO funcionarios (cpf, nome_completo, sexo, data_nascimento, email, 
                                             telefone, cep, endereco, bairro, cidade, uf, 
                                             cargo, data_inicio, status, foto_url)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                valores = (cpf, nome_completo, sexo, data_nascimento, email, telefone, cep, 
                           endereco, bairro, cidade, uf, cargo, data_inicio, status, foto_url)
                cursor.execute(sql, valores)
                conn.commit()
                print(f"Funcionário {nome_completo} salvo com sucesso!")
                
        except Exception as e:
            print(f"Erro ao salvar o funcionário no banco: {e}")
        finally:
            cursor.close()
            conn.close()
            
    return redirect(url_for('novo_funcionario'))

# ==============================================================================
# ROTAS DO CADASTRO DE PROFESSORES
# ==============================================================================

@app.route('/backoffice/professores/novo')
@requer_permissao('mod_cad_prof')
def novo_professor():
    """
    Rota para exibir o formulário de cadastro de professores no backoffice.
    """
    return render_template('backoffice/cadastro_professor.html')

@app.route('/api/valida_professor_funcionario', methods=['GET'])
def valida_professor_funcionario():
    """
    Rota API que valida se um CPF pertence a um funcionário.
    Se sim, verifica se já é um professor cadastrado e retorna os dados
    junto com a lista de certificados cadastrados para popular o formulário.
    """
    cpf = request.args.get('cpf')
    if not cpf:
        return jsonify({'sucesso': False, 'msg': 'CPF não fornecido.'})

    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # 1. Busca os dados consolidados no RH
            sql_func = """
                SELECT id, nome_completo, email, telefone, status, usuario_id, foto_url, 
                       sexo, data_inicio 
                FROM funcionarios WHERE cpf = %s LIMIT 1
            """
            cursor.execute(sql_func, (cpf,))
            func = cursor.fetchone()
            
            if not func:
                return jsonify({
                    'sucesso': False, 
                    'is_funcionario': False,
                    'msg': 'Funcionário não encontrado. Cadastre no módulo de Funcionários primeiro.'
                })
            
            func_id = func[0]
            
            # 2. Verifica vínculo na tabela de professores através do ID
            sql_prof = """
                SELECT id, nome_emergencia, telefone_emergencia, cref, modalidades, certificacoes
                FROM professores WHERE funcionario_id = %s LIMIT 1
            """
            cursor.execute(sql_prof, (func_id,))
            prof = cursor.fetchone()
            
            if prof:
                prof_id = prof[0]
                
                # 3. Busca todos os certificados cadastrados para este professor na tabela filha
                sql_certs = "SELECT id, arquivo_url, nome_original FROM professor_certificados WHERE professor_id = %s"
                cursor.execute(sql_certs, (prof_id,))
                certs_rows = cursor.fetchall()
                
                certificados_lista = []
                for c in certs_rows:
                    certificados_lista.append({
                        'id': c[0],
                        'arquivo_url': c[1],
                        'nome_original': c[2]
                    })
                
                return jsonify({
                    'sucesso': True,
                    'is_funcionario': True,
                    'is_professor': True,
                    'dados': {
                        'funcionario_id': func_id,
                        'usuario_id': func[5],
                        'nome_completo': func[1],
                        'email': func[2],
                        'telefone': func[3],
                        'status': func[4], 
                        'foto_url': func[6], 
                        'sexo': func[7],
                        'data_inicio': str(func[8]) if func[8] else '',
                        
                        'professor_id': prof_id,
                        'nome_emergencia': prof[1],
                        'telefone_emergencia': prof[2],
                        'cref': prof[3],
                        'modalidades': prof[4],
                        'certificacoes': prof[5],
                        'certificados': certificados_lista
                    }
                })
            else:
                return jsonify({
                    'sucesso': True,
                    'is_funcionario': True,
                    'is_professor': False,
                    'dados': {
                        'funcionario_id': func_id,
                        'usuario_id': func[5],
                        'nome_completo': func[1],
                        'email': func[2],
                        'telefone': func[3], 
                        'status': func[4],
                        'foto_url': func[6],
                        'sexo': func[7],
                        'data_inicio': str(func[8]) if func[8] else ''
                    }
                })
                
        except Exception as e:
            print(f"Erro ao validar professor/funcionário via API: {e}")
        finally:
            cursor.close()
            conn.close()
            
    return jsonify({'sucesso': False, 'msg': 'Erro de conexão com o banco de dados.'})

@app.route('/backoffice/professores/salvar', methods=['POST'])
@requer_permissao('mod_cad_prof')
def salvar_professor():
    """
    Rota responsável por receber os dados do formulário e gravar na tabela professores
    e múltiplos certificados na tabela professor_certificados.
    """
    professor_id = request.form.get('professor_id')
    cpf = request.form.get('cpf') # Usado apenas para descobrir o ID raiz
    nome_emergencia = request.form.get('nome_emergencia')
    telefone_emergencia = request.form.get('telefone_emergencia')
    cref = request.form.get('cref')
    modalidades = request.form.get('modalidades')
    certificacoes = request.form.get('certificacoes')
    
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Descobre o funcionario_id e usuario_id atualizados baseados no CPF
            cursor.execute("SELECT id, usuario_id FROM funcionarios WHERE cpf = %s LIMIT 1", (cpf,))
            func_data = cursor.fetchone()
            if not func_data:
                print("Erro: Tentativa de salvar professor com CPF inexistente no RH.")
                return redirect(url_for('novo_professor'))
                
            funcionario_id = func_data[0]
            usuario_id = func_data[1]
            
            if professor_id: 
                # UPDATE focado apenas em dados pedagógicos
                sql = """
                    UPDATE professores 
                    SET nome_emergencia=%s, telefone_emergencia=%s, cref=%s, 
                        modalidades=%s, certificacoes=%s
                    WHERE id=%s
                """
                valores = (nome_emergencia, telefone_emergencia, cref, modalidades, certificacoes, professor_id)
                cursor.execute(sql, valores)
                print("Dados pedagógicos atualizados com sucesso!")
                
            else: 
                # INSERT amarrado pelo funcionario_id
                sql = """
                    INSERT INTO professores (funcionario_id, usuario_id, nome_emergencia, telefone_emergencia, 
                                            cref, modalidades, certificacoes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                valores = (funcionario_id, usuario_id, nome_emergencia, telefone_emergencia, 
                           cref, modalidades, certificacoes)
                cursor.execute(sql, valores)
                professor_id = cursor.lastrowid
                print("Professor vinculado e cadastrado com sucesso!")
            
            # --- LÓGICA DE UPLOAD DE MÚLTIPLOS CERTIFICADOS ---
            arquivos_certificados = request.files.getlist('certificado_arquivo')
            if arquivos_certificados:
                upload_folder = os.path.join(app.root_path, 'static', 'uploads', 'certificados')
                os.makedirs(upload_folder, exist_ok=True)
                
                for cert_arq in arquivos_certificados:
                    if cert_arq and cert_arq.filename != '':
                        extensao = os.path.splitext(cert_arq.filename)[1]
                        cpf_limpo = re.sub(r'\D', '', cpf) if cpf else str(int(time.time()))
                        nome_seguro = secure_filename(f"{cpf_limpo}_{int(time.time())}_{random.randint(100,999)}_certificado{extensao}")
                        
                        caminho_fisico = os.path.join(upload_folder, nome_seguro)
                        cert_arq.save(caminho_fisico)
                        
                        certificado_arquivo_url = f"/static/uploads/certificados/{nome_seguro}"
                        
                        sql_cert = """
                            INSERT INTO professor_certificados (professor_id, arquivo_url, nome_original)
                            VALUES (%s, %s, %s)
                        """
                        cursor.execute(sql_cert, (professor_id, certificado_arquivo_url, cert_arq.filename))
            # -------------------------------------------------
                
            conn.commit()
        except Exception as e:
            print(f"Erro ao salvar o professor no banco: {e}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
            
    return redirect(url_for('novo_professor'))

# ==============================================================================
# ROTAS DO CONTROLE DE ACESSOS E PERMISSÕES
# ==============================================================================

@app.route('/backoffice/permissoes')
@requer_permissao('mod_cad_perm')
def controles_de_acesso():
    """
    Renderiza a interface do Controle de Acessos.
    """
    return render_template('backoffice/permissoes.html')

@app.route('/api/permissoes/buscar', methods=['GET'])
def buscar_permissoes():
    """
    Rota API que busca no banco de dados todas as permissões cadastradas para um cargo específico.
    """
    cargo = request.args.get('cargo')
    if not cargo:
        return jsonify({'sucesso': False, 'msg': 'Cargo não informado.'})
    
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            sql = "SELECT modulo, pode_acessar FROM permissoes_cargo WHERE cargo = %s"
            cursor.execute(sql, (cargo,))
            rows = cursor.fetchall()
            
            # Monta um dicionário com os módulos (ex: {'mod_free': 1, 'mod_cad_func': 0})
            permissoes = {row[0]: row[1] for row in rows}
            
            return jsonify({'sucesso': True, 'permissoes': permissoes})
        except Exception as e:
            print(f"Erro ao buscar permissões via API: {e}")
        finally:
            cursor.close()
            conn.close()
            
    return jsonify({'sucesso': False})

@app.route('/api/permissoes/salvar', methods=['POST'])
@requer_permissao('mod_cad_perm')
def salvar_permissoes():
    """
    Rota API que recebe um JSON com o cargo e a matriz de permissões 
    para gravar na tabela permissoes_cargo (via UPDATE ou INSERT).
    """
    dados = request.get_json()
    cargo = dados.get('cargo')
    permissoes = dados.get('permissoes') # Dicionário de módulos e valores (1 ou 0)
    
    if not cargo or not permissoes:
        return jsonify({'sucesso': False, 'msg': 'Dados incompletos.'})
        
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Percorre cada permissão enviada da tela
            for modulo, valor in permissoes.items():
                # Verifica se a regra de permissão para este cargo e módulo já existe
                cursor.execute("SELECT id FROM permissoes_cargo WHERE cargo = %s AND modulo = %s", (cargo, modulo))
                registro = cursor.fetchone()
                
                if registro:
                    # Se existe, atualiza o valor
                    sql_update = "UPDATE permissoes_cargo SET pode_acessar = %s WHERE id = %s"
                    cursor.execute(sql_update, (valor, registro[0]))
                else:
                    # Se não existe, cria o novo registro
                    sql_insert = "INSERT INTO permissoes_cargo (cargo, modulo, pode_acessar) VALUES (%s, %s, %s)"
                    cursor.execute(sql_insert, (cargo, modulo, valor))
            
            conn.commit()
            return jsonify({'sucesso': True})
        except Exception as e:
            print(f"Erro ao salvar permissões no banco: {e}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
            
    return jsonify({'sucesso': False})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)