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
# 10/08/26: Inclusão das rotas de cadastro, busca e persistência para Alunos.
# 10/08/26: Aprimoramento da API de busca de alunos para suportar localização via CPF do responsável com suporte a múltiplos vínculos (irmãos).
# 12/08/26: Inclusão de limpeza de caracteres não numéricos (máscaras) antes do INSERT/UPDATE na rota de salvar aluno.
# 13/08/26: Inclusão da rota GET para o módulo de Matrículas e Grade.
# 13/08/26: Criação da rota POST /backoffice/matriculas/salvar para processar e persistir matrícula e grade.
# 14/08/26: Atualização da API /api/alunos/buscar para retornar dados da matrícula e grade.
# 14/08/26: Criação da rota assíncrona /api/matriculas/validar_horario para trava de colisão de agendas na base de dados.
# 14/08/26: Correção no parsing da taxa de matrícula para evitar inflação decimal em conflito com o Front-end.
# 14/08/26: Implementação de lógica UPDATE na rota de salvar matrícula e suporte ao campo oculto matricula_id.
# 14/08/26: Correção de parsing e formatação de horas (TIME) para evitar erro 1292 no MySQL ao atualizar grade de matrículas.
# 17/08/26: Inclusão de disparo de e-mail transacional de confirmação na rota de salvamento de matrículas (correção da query de e-mail do aluno).
# 18/08/26: Inclusão das rotas de Gestão de Turmas (nova, salvar e API de busca de professores por modalidade).
# 18/08/26: Inclusão das rotas do Quadro de Vagas e salvamento de Lista de Espera.
# 19/08/26: Inclusão das rotas de gestão da Tabela de Preços (nova, buscar e salvar).
# 21/08/26: Alteração na rota salvar_aluno para retornar JSON (Ponte Inteligente com Quadro de Vagas).
# 21/08/26: Inclusão dos campos forma_pagamento e parcelas na API de busca de aluno e na persistência de matrículas.
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
from datetime import datetime

# Importa a função de conexão com o banco
from database.connection import get_connection

# Carrega as variáveis do arquivo .env
load_dotenv()

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.secret_key = os.getenv('SECRET_KEY', 'chave_padrao_fallback')

def enviar_email_html(destinatario, assunto, corpo_html):
    smtp_host = os.getenv('EMAIL_HOST')
    smtp_port = int(os.getenv('EMAIL_PORT', 587))
    smtp_user = os.getenv('EMAIL_USER')
    smtp_pass = os.getenv('EMAIL_PASS')
    
    if not smtp_host or not smtp_user or not smtp_pass:
        print("Erro: Credenciais de e-mail (SMTP) ausentes no .env.")
        return False
        
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = f"MyGym <{smtp_user}>"
        msg['To'] = destinatario
        msg['Subject'] = assunto
        
        msg.attach(MIMEText(corpo_html, 'html'))
        
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Erro ao tentar enviar o e-mail: {e}")
        return False
    
def is_mobile(req):
    sec_mobile = req.headers.get('Sec-Ch-Ua-Mobile')
    if sec_mobile == '?1':
        return True

    ua_string = req.headers.get('User-Agent', '').lower()
    if not ua_string:
        return False
    
    if 'mobi' in ua_string or 'android' in ua_string or 'iphone' in ua_string:
        return True
        
    return False

def requer_permissao(modulo):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            perfil = session.get('perfil')
            
            if not perfil:
                return redirect(url_for('index'))
            
            if perfil == 'admin':
                return f(*args, **kwargs)
            
            conn = get_connection()
            if conn:
                try:
                    cursor = conn.cursor()
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

            return redirect(url_for('index'))
        return decorated_function
    return decorator

def enviar_email_recuperacao(email_destino, nome, username, senha_provisoria):
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
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if username == 'admin' and password == 'admin#123':
            session['perfil'] = 'admin'
            session['nome_completo'] = 'Administrador Master'
            session['permissoes'] = {'mod_free': True}
            return redirect(url_for('index'))
        else:
            conn = get_connection()
            if conn:
                try:
                    cursor = conn.cursor()
                    sql = "SELECT password_hash, perfil, nome_completo, senha_provisoria FROM usuarios WHERE username = %s AND status = 'ativo'"
                    cursor.execute(sql, (username,))
                    usuario = cursor.fetchone()
                    
                    if usuario and check_password_hash(usuario[0], password):
                        if usuario[3] == 1:
                            return redirect(url_for('index', force_reset='true', reset_user=username))
                        
                        session['perfil'] = usuario[1]
                        session['nome_completo'] = usuario[2]
                        
                        sql_permissoes = "SELECT modulo FROM permissoes_cargo WHERE cargo = %s AND pode_acessar = 1"
                        cursor.execute(sql_permissoes, (usuario[1],))
                        perms = cursor.fetchall()
                        
                        session['permissoes'] = {p[0]: True for p in perms}
                        
                        return redirect(url_for('index'))
                except Exception as e:
                    print(f"Erro ao validar login no banco: {e}")
                finally:
                    cursor.close()
                    conn.close()

            return redirect(url_for('index', erro_login='Credenciais inválidas.'))

    mobile = is_mobile(request)
    
    if mobile:
        resp = make_response(render_template('mobile/cover.html'))
    else:
        resp = make_response(render_template('cover.html'))
        
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    
    return resp

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/toggle-admin')
def toggle_admin():
    if session.get('perfil') == 'admin':
        session.pop('perfil', None)
    else:
        session['perfil'] = 'admin'
        session['permissoes'] = {'mod_free': True}
        
    return redirect(url_for('index'))

@app.route('/cadastrar_usuario', methods=['POST'])
def cadastrar_usuario():
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
            
            tabela_map = {
                'funcionario': 'funcionarios',
                'professor': 'funcionarios',
                'aluno': 'alunos'
            }
            
            tabela_alvo = tabela_map.get(perfil_form)
            base_id = None
            perfil_final = perfil_form
            
            if tabela_alvo:
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
                    if tabela_alvo == 'funcionarios':
                        perfil_final = existe[1]
                        
                except Exception as e:
                    print(f"Erro ao verificar existência na tabela {tabela_alvo}: {e}")
                    msg_erro = f"Não foi possível validar o cadastro de {perfil_form.capitalize()}. Verifique com o administrador."
                    return redirect(url_for('index', erro_cadastro=msg_erro))

            password_hash = generate_password_hash(senha)

            sql = """
                INSERT INTO usuarios (username, password_hash, perfil, status, nome_completo, senha_provisoria)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            valores = (username, password_hash, perfil_final, 'ativo', nome_completo, 0)
            cursor.execute(sql, valores)
            
            novo_usuario_id = cursor.lastrowid
            
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
            
    return redirect(url_for('index', show_login='true'))

@app.route('/recuperar_senha', methods=['POST'])
def recuperar_senha():
    perfil = request.form.get('perfil_recuperacao')
    username_recuperacao = request.form.get('username_recuperacao')
    
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            cursor.execute("SELECT id, username, nome_completo FROM usuarios WHERE username = %s LIMIT 1", (username_recuperacao,))
            user_exist = cursor.fetchone()
            
            if not user_exist:
                return redirect(url_for('index', erro_recuperacao="Usuário não encontrado ou sem acesso ao sistema."))
            
            usuario_id = user_exist[0]
            username = user_exist[1]
            nome_completo = user_exist[2]
            
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

            caracteres_seguros = "23456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz"
            senha_provisoria = ''.join(random.choice(caracteres_seguros) for i in range(8))
            password_hash = generate_password_hash(senha_provisoria)
            
            cursor.execute("UPDATE usuarios SET password_hash = %s, senha_provisoria = 1 WHERE username = %s", (password_hash, username))
            conn.commit()
            
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
    username = request.form.get('reset_user')
    nova_senha = request.form.get('nova_senha', '').strip()
    confirma_senha = request.form.get('confirma_senha', '').strip()
    
    if nova_senha != confirma_senha:
        return redirect(url_for('index', force_reset='true', reset_user=username, erro_reset="As senhas não conferem."))
        
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
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
    cpf = request.args.get('cpf')
    if not cpf:
        return jsonify({'encontrado': False})

    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
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
    return render_template('backoffice/cadastro_funcionario.html')

@app.route('/backoffice/funcionarios/salvar', methods=['POST'])
@requer_permissao('mod_cad_func')
def salvar_funcionario():
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
    
    if data_nascimento: 
        data_nascimento = data_nascimento.replace('-', '')
    else: 
        data_nascimento = None
        
    if data_inicio: 
        data_inicio = data_inicio.replace('-', '')
    else: 
        data_inicio = None
    
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
    
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            if funcionario_id:
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
            else:
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
    return render_template('backoffice/cadastro_professor.html')

@app.route('/api/valida_professor_funcionario', methods=['GET'])
def valida_professor_funcionario():
    cpf = request.args.get('cpf')
    if not cpf:
        return jsonify({'sucesso': False, 'msg': 'CPF não fornecido.'})

    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
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
            
            sql_prof = """
                SELECT id, nome_emergencia, telefone_emergencia, cref, modalidades, certificacoes
                FROM professores WHERE funcionario_id = %s LIMIT 1
            """
            cursor.execute(sql_prof, (func_id,))
            prof = cursor.fetchone()
            
            if prof:
                prof_id = prof[0]
                sql_certs = "SELECT id, arquivo_url, nome_original FROM professor_certificados WHERE professor_id = %s"
                cursor.execute(sql_certs, (prof_id,))
                certs_rows = cursor.fetchall()
                
                certificados_lista = [{'id': c[0], 'arquivo_url': c[1], 'nome_original': c[2]} for c in certs_rows]
                
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
    professor_id = request.form.get('professor_id')
    cpf = request.form.get('cpf')
    nome_emergencia = request.form.get('nome_emergencia')
    telefone_emergencia = request.form.get('telefone_emergencia')
    cref = request.form.get('cref')
    modalidades = request.form.get('modalidades')
    certificacoes = request.form.get('certificacoes')
    
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            cursor.execute("SELECT id, usuario_id FROM funcionarios WHERE cpf = %s LIMIT 1", (cpf,))
            func_data = cursor.fetchone()
            if not func_data:
                return redirect(url_for('novo_professor'))
                
            funcionario_id = func_data[0]
            usuario_id = func_data[1]
            
            if professor_id: 
                sql = """
                    UPDATE professores 
                    SET nome_emergencia=%s, telefone_emergencia=%s, cref=%s, 
                        modalidades=%s, certificacoes=%s
                    WHERE id=%s
                """
                valores = (nome_emergencia, telefone_emergencia, cref, modalidades, certificacoes, professor_id)
                cursor.execute(sql, valores)
            else: 
                sql = """
                    INSERT INTO professores (funcionario_id, usuario_id, nome_emergencia, telefone_emergencia, 
                                            cref, modalidades, certificacoes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                valores = (funcionario_id, usuario_id, nome_emergencia, telefone_emergencia, 
                           cref, modalidades, certificacoes)
                cursor.execute(sql, valores)
                professor_id = cursor.lastrowid
            
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
                
            conn.commit()
        except Exception as e:
            print(f"Erro ao salvar o professor no banco: {e}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
            
    return redirect(url_for('novo_professor'))

# ==============================================================================
# ROTAS DO CADASTRO DE ALUNOS
# ==============================================================================

@app.route('/backoffice/alunos/novo')
@requer_permissao('mod_cad_aluno')
def novo_aluno():
    return render_template('backoffice/cadastro_aluno.html')

@app.route('/api/alunos/buscar', methods=['GET'])
def buscar_aluno():
    termo = request.args.get('termo')
    if not termo:
        return jsonify({'encontrado': False, 'msg': 'Termo não fornecido.'})
    
    termo_limpo = re.sub(r'\D', '', termo)
    
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            sql_aluno = """
                SELECT id, usuario_id, responsavel_id, nome_completo, cpf, data_nascimento, 
                       sexo, email, telefone, foto_url, observacoes_medicas, 
                       exame_medico_data, exame_medico_validade 
                FROM alunos WHERE id = %s OR cpf = %s LIMIT 1
            """
            cursor.execute(sql_aluno, (termo, termo_limpo))
            aluno = cursor.fetchone()
            
            alunos_encontrados = []
            
            if aluno:
                alunos_encontrados.append(aluno)
            else:
                sql_resp = "SELECT id FROM responsaveis WHERE cpf = %s LIMIT 1"
                cursor.execute(sql_resp, (termo_limpo,))
                resp = cursor.fetchone()
                
                if resp:
                    resp_id = resp[0]
                    sql_alunos_resp = """
                        SELECT id, usuario_id, responsavel_id, nome_completo, cpf, data_nascimento, 
                               sexo, email, telefone, foto_url, observacoes_medicas, 
                               exame_medico_data, exame_medico_validade 
                        FROM alunos WHERE responsavel_id = %s
                    """
                    cursor.execute(sql_alunos_resp, (resp_id,))
                    alunos_encontrados = cursor.fetchall()
            
            if not alunos_encontrados:
                return jsonify({'encontrado': False, 'msg': 'Nenhum registro encontrado.'})
            
            if len(alunos_encontrados) > 1:
                lista_multiplos = []
                for a in alunos_encontrados:
                    lista_multiplos.append({
                        'id': a[0],
                        'nome_completo': a[3],
                        'data_nascimento': str(a[5]) if a[5] else '',
                        'cpf': a[4] or 'Não cadastrado'
                    })
                return jsonify({
                    'encontrado': True,
                    'multiplos': True,
                    'alunos': lista_multiplos
                })
            
            aluno = alunos_encontrados[0]
            aluno_id = aluno[0]
            resp_id = aluno[2]
            
            resp_data = None
            if resp_id:
                cursor.execute("SELECT id, nome_completo, cpf, telefone, cep, endereco, bairro, cidade, uf FROM responsaveis WHERE id = %s LIMIT 1", (resp_id,))
                r = cursor.fetchone()
                if r:
                    resp_data = {
                        'id': r[0], 'nome_completo': r[1], 'cpf': r[2], 'telefone': r[3],
                        'cep': r[4], 'endereco': r[5], 'bairro': r[6], 'cidade': r[7], 'uf': r[8]
                    }
                    
            cursor.execute("""
                SELECT c.nome_completo, c.telefone, c.tipo 
                FROM contatos c
                JOIN aluno_contatos ac ON c.id = ac.contato_id
                WHERE ac.aluno_id = %s
            """, (aluno_id,))
            contatos_rows = cursor.fetchall()
            contatos_lista = [{'nome_completo': row[0], 'telefone': row[1], 'tipo': row[2]} for row in contatos_rows]
            
            cursor.execute("""
                SELECT id, tipo_plano, forma_pagamento, parcelas, data_inicio, data_fim, dia_vencimento, taxa_matricula, status 
                FROM matriculas 
                WHERE aluno_id = %s AND status = 'Ativa' 
                ORDER BY id DESC LIMIT 1
            """, (aluno_id,))
            matricula_row = cursor.fetchone()
            
            matricula_data = None
            if matricula_row:
                mat_id = matricula_row[0]
                matricula_data = {
                    'id': mat_id,
                    'tipo_plano': matricula_row[1],
                    'forma_pagamento': matricula_row[2] or '',
                    'parcelas': matricula_row[3] or 1,
                    'data_inicio': str(matricula_row[4]) if matricula_row[4] else '',
                    'data_fim': str(matricula_row[5]) if matricula_row[5] else '',
                    'dia_vencimento': matricula_row[6],
                    'taxa_matricula': str(matricula_row[7]) if matricula_row[7] else '',
                    'status': matricula_row[8],
                    'grade': []
                }
                
                cursor.execute("""
                    SELECT modalidade, dias_semana, horario 
                    FROM matricula_grade 
                    WHERE matricula_id = %s
                """, (mat_id,))
                grade_rows = cursor.fetchall()
                for grow in grade_rows:
                    horario_str = str(grow[2]) if grow[2] else ''
                    if horario_str:
                        partes = horario_str.split(':')
                        if len(partes) >= 2:
                            horario_str = f"{int(partes[0]):02d}:{partes[1]}"
                        
                    matricula_data['grade'].append({
                        'modalidade': grow[0],
                        'dias_semana': grow[1],
                        'horario': horario_str
                    })
            
            return jsonify({
                'encontrado': True,
                'multiplos': False,
                'dados': {
                    'id': aluno[0],
                    'usuario_id': aluno[1],
                    'responsavel_id': aluno[2],
                    'nome_completo': aluno[3],
                    'cpf': aluno[4],
                    'data_nascimento': str(aluno[5]) if aluno[5] else '',
                    'sexo': aluno[6],
                    'email': aluno[7],
                    'telefone': aluno[8],
                    'foto_url': aluno[9],
                    'observacoes_medicas': aluno[10],
                    'exame_medico_data': str(aluno[11]) if aluno[11] else '',
                    'exame_medico_validade': str(aluno[12]) if aluno[12] else '',
                    'responsavel': resp_data,
                    'contatos': contatos_lista,
                    'matricula': matricula_data
                }
            })
        except Exception as e:
            print(f"Erro ao buscar aluno via API: {e}")
        finally:
            cursor.close()
            conn.close()
            
    return jsonify({'encontrado': False, 'msg': 'Erro de conexão com o banco.'})

@app.route('/backoffice/alunos/salvar', methods=['POST'])
@requer_permissao('mod_cad_aluno')
def salvar_aluno():
    aluno_id = request.form.get('aluno_id')
    nome_completo = request.form.get('nome_completo')
    
    cpf = request.form.get('cpf')
    if cpf: cpf = re.sub(r'\D', '', cpf)
        
    data_nascimento = request.form.get('data_nascimento')
    sexo = request.form.get('sexo')
    email = request.form.get('email')
    
    telefone = request.form.get('telefone')
    if telefone: telefone = re.sub(r'\D', '', telefone)
        
    observacoes_medicas = request.form.get('observacoes_medicas')
    exame_medico_data = request.form.get('exame_medico_data')
    exame_medico_validade = request.form.get('exame_medico_validade')
    
    if not data_nascimento: data_nascimento = None
    if not exame_medico_data: exame_medico_data = None
    if not exame_medico_validade: exame_medico_validade = None
    
    resp_id = request.form.get('responsavel_id')
    resp_nome = request.form.get('resp_nome')
    
    resp_cpf = request.form.get('resp_cpf')
    if resp_cpf: resp_cpf = re.sub(r'\D', '', resp_cpf)
        
    resp_telefone = request.form.get('resp_telefone')
    if resp_telefone: resp_telefone = re.sub(r'\D', '', resp_telefone)
        
    resp_cep = request.form.get('resp_cep')
    if resp_cep: resp_cep = re.sub(r'\D', '', resp_cep)
        
    resp_endereco = request.form.get('resp_endereco')
    resp_bairro = request.form.get('resp_bairro')
    resp_cidade = request.form.get('resp_cidade')
    resp_uf = request.form.get('resp_uf')
    
    foto_arquivo = request.files.get('foto_arquivo')
    foto_url = None
    if foto_arquivo and foto_arquivo.filename != '':
        upload_folder = os.path.join(app.root_path, 'static', 'uploads', 'alunos_fotos')
        os.makedirs(upload_folder, exist_ok=True)
        extensao = os.path.splitext(foto_arquivo.filename)[1]
        identificador = re.sub(r'\D', '', cpf) if cpf else str(int(time.time()))
        nome_seguro = secure_filename(f"aluno_{identificador}_{int(time.time())}{extensao}")
        caminho_fisico = os.path.join(upload_folder, nome_seguro)
        foto_arquivo.save(caminho_fisico)
        foto_url = f"/static/uploads/alunos_fotos/{nome_seguro}"
    
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            responsavel_id_final = None
            if resp_nome and resp_nome.strip() != '':
                if resp_id:
                    sql_resp_up = """
                        UPDATE responsaveis 
                        SET nome_completo=%s, cpf=%s, telefone=%s, cep=%s, endereco=%s, bairro=%s, cidade=%s, uf=%s
                        WHERE id=%s
                    """
                    cursor.execute(sql_resp_up, (resp_nome, resp_cpf, resp_telefone, resp_cep, resp_endereco, resp_bairro, resp_cidade, resp_uf, resp_id))
                    responsavel_id_final = resp_id
                else:
                    sql_resp_ins = """
                        INSERT INTO responsaveis (nome_completo, cpf, telefone, cep, endereco, bairro, cidade, uf)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(sql_resp_ins, (resp_nome, resp_cpf, resp_telefone, resp_cep, resp_endereco, resp_bairro, resp_cidade, resp_uf))
                    responsavel_id_final = cursor.lastrowid
            
            if aluno_id:
                if foto_url:
                    sql_aluno = """
                        UPDATE alunos 
                        SET responsavel_id=%s, nome_completo=%s, cpf=%s, data_nascimento=%s, sexo=%s, 
                            email=%s, telefone=%s, foto_url=%s, observacoes_medicas=%s, 
                            exame_medico_data=%s, exame_medico_validade=%s
                        WHERE id=%s
                    """
                    cursor.execute(sql_aluno, (responsavel_id_final, nome_completo, cpf, data_nascimento, sexo, email, telefone, foto_url, observacoes_medicas, exame_medico_data, exame_medico_validade, aluno_id))
                else:
                    sql_aluno = """
                        UPDATE alunos 
                        SET responsavel_id=%s, nome_completo=%s, cpf=%s, data_nascimento=%s, sexo=%s, 
                            email=%s, telefone=%s, observacoes_medicas=%s, 
                            exame_medico_data=%s, exame_medico_validade=%s
                        WHERE id=%s
                    """
                    cursor.execute(sql_aluno, (responsavel_id_final, nome_completo, cpf, data_nascimento, sexo, email, telefone, observacoes_medicas, exame_medico_data, exame_medico_validade, aluno_id))
            else:
                sql_aluno = """
                    INSERT INTO alunos (responsavel_id, nome_completo, cpf, data_nascimento, sexo, 
                                       email, telefone, foto_url, observacoes_medicas, 
                                       exame_medico_data, exame_medico_validade)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql_aluno, (responsavel_id_final, nome_completo, cpf, data_nascimento, sexo, email, telefone, foto_url, observacoes_medicas, exame_medico_data, exame_medico_validade))
                aluno_id = cursor.lastrowid
                
            cursor.execute("DELETE FROM aluno_contatos WHERE aluno_id = %s", (aluno_id,))
            
            nomes_contato = request.form.getlist('contato_nome[]')
            telefones_contato = request.form.getlist('contato_telefone[]')
            tipos_contato = request.form.getlist('contato_tipo[]')
            
            for i in range(len(nomes_contato)):
                c_nome = nomes_contato[i].strip()
                
                c_tel = telefones_contato[i].strip()
                if c_tel: c_tel = re.sub(r'\D', '', c_tel)
                
                c_tipo = tipos_contato[i].strip()
                
                if c_nome and c_tel:
                    cursor.execute("INSERT INTO contatos (nome_completo, telefone, tipo) VALUES (%s, %s, %s)", (c_nome, c_tel, c_tipo))
                    c_id = cursor.lastrowid
                    cursor.execute("INSERT INTO aluno_contatos (aluno_id, contato_id) VALUES (%s, %s)", (aluno_id, c_id))
                    
            conn.commit()
        except Exception as e:
            print(f"Erro ao salvar aluno no banco: {e}")
            conn.rollback()
            if request.headers.get('Accept') == 'application/json' or request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.path.endswith('/salvar') and request.method == 'POST':
                return jsonify({'sucesso': False, 'msg': f'Erro ao salvar aluno: {str(e)}'})
        finally:
            cursor.close()
            conn.close()
            
        is_ajax = request.headers.get('Accept') == 'application/json' or 'fetch' in str(request.headers.get('User-Agent', '')).lower() or request.headers.get('Sec-Fetch-Mode') == 'cors'
        return jsonify({
            'sucesso': True, 
            'msg': 'Aluno salvo com sucesso!',
            'id_aluno': aluno_id
        })
            
    return jsonify({'sucesso': False, 'msg': 'Erro de conexão com o banco de dados.'})

# ==============================================================================
# ROTAS DO CONTROLE DE ACESSOS E PERMISSÕES
# ==============================================================================

@app.route('/backoffice/permissoes')
@requer_permissao('mod_cad_perm')
def controles_de_acesso():
    return render_template('backoffice/permissoes.html')

@app.route('/api/permissoes/buscar', methods=['GET'])
def buscar_permissoes():
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
    dados = request.get_json()
    cargo = dados.get('cargo')
    permissoes = dados.get('permissoes')
    
    if not cargo or not permissoes:
        return jsonify({'sucesso': False, 'msg': 'Dados incompletos.'})
        
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            for modulo, valor in permissoes.items():
                cursor.execute("SELECT id FROM permissoes_cargo WHERE cargo = %s AND modulo = %s", (cargo, modulo))
                registro = cursor.fetchone()
                
                if registro:
                    sql_update = "UPDATE permissoes_cargo SET pode_acessar = %s WHERE id = %s"
                    cursor.execute(sql_update, (valor, registro[0]))
                else:
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

# ==============================================================================
# ROTAS DA TABELA DE PREÇOS
# ==============================================================================

@app.route('/backoffice/precos')
@requer_permissao('mod_precos')
def tabela_precos():
    return render_template('backoffice/tabela_precos.html')

@app.route('/api/precos/buscar', methods=['GET'])
def buscar_precos():
    modalidade = request.args.get('modalidade')
    if not modalidade:
        return jsonify({'sucesso': False, 'msg': 'Modalidade não informada.'})
        
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            sql = """
                SELECT frequencia_semanal, valor_mensal, valor_trimestral, valor_semestral, valor_anual 
                FROM tabela_precos 
                WHERE modalidade = %s
            """
            cursor.execute(sql, (modalidade,))
            rows = cursor.fetchall()
            
            precos = []
            for row in rows:
                precos.append({
                    'frequencia': row[0],
                    'mensal': str(row[1]),
                    'trimestral': str(row[2]),
                    'semestral': str(row[3]),
                    'anual': str(row[4])
                })
            
            return jsonify({'sucesso': True, 'precos': precos})
        except Exception as e:
            print(f"Erro ao buscar tabela de preços: {e}")
        finally:
            cursor.close()
            conn.close()
            
    return jsonify({'sucesso': False, 'msg': 'Erro de conexão com o banco.'})

@app.route('/backoffice/precos/salvar', methods=['POST'])
@requer_permissao('mod_precos')
def salvar_precos():
    modalidade = request.form.get('modalidade')
    
    if not modalidade:
        return redirect(url_for('tabela_precos'))
        
    frequencias = request.form.getlist('frequencia[]')
    mensais = request.form.getlist('mensal[]')
    trimestrais = request.form.getlist('trimestral[]')
    semestrais = request.form.getlist('semestral[]')
    anuais = request.form.getlist('anual[]')
    
    def limpar_moeda(valor_str):
        if not valor_str:
            return 0.00
        v = str(valor_str).replace('R$', '').strip()
        if ',' in v:
            v = v.replace('.', '').replace(',', '.')
        try:
            return float(v)
        except ValueError:
            return 0.00

    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            for i in range(len(frequencias)):
                freq = frequencias[i]
                v_mensal = limpar_moeda(mensais[i]) if i < len(mensais) else 0.00
                v_trimestral = limpar_moeda(trimestrais[i]) if i < len(trimestrais) else 0.00
                v_semestral = limpar_moeda(semestrais[i]) if i < len(semestrais) else 0.00
                v_anual = limpar_moeda(anuais[i]) if i < len(anuais) else 0.00
                
                sql = """
                    INSERT INTO tabela_precos (modalidade, frequencia_semanal, valor_mensal, valor_trimestral, valor_semestral, valor_anual)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE 
                        valor_mensal = VALUES(valor_mensal),
                        valor_trimestral = VALUES(valor_trimestral),
                        valor_semestral = VALUES(valor_semestral),
                        valor_anual = VALUES(valor_anual)
                """
                cursor.execute(sql, (modalidade, freq, v_mensal, v_trimestral, v_semestral, v_anual))
            
            conn.commit()
            print(f"Tabela de preços salva com sucesso para a modalidade: {modalidade}")
        except Exception as e:
            print(f"Erro ao salvar tabela de preços: {e}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
            
    return redirect(url_for('tabela_precos'))


# ==============================================================================
# ROTAS DE GESTÃO DE TURMAS (GRADE OFICIAL)
# ==============================================================================

@app.route('/backoffice/turmas/nova')
@requer_permissao('mod_cad_turma')
def nova_turma():
    return render_template('backoffice/cadastro_turma.html')

@app.route('/api/professores/por_modalidade', methods=['GET'])
def buscar_professores_por_modalidade():
    modalidade = request.args.get('modalidade')
    if not modalidade:
        return jsonify({'sucesso': False, 'msg': 'Modalidade não informada.'})
        
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            sql = """
                SELECT p.id, f.nome_completo 
                FROM professores p
                JOIN funcionarios f ON p.funcionario_id = f.id
                WHERE p.modalidades LIKE %s AND f.status = 'ativo'
            """
            
            parametro_busca = f"%{modalidade}%"
            cursor.execute(sql, (parametro_busca,))
            rows = cursor.fetchall()
            
            professores = [{'id': row[0], 'nome_completo': row[1]} for row in rows]
            
            return jsonify({'sucesso': True, 'professores': professores})
        except Exception as e:
            print(f"Erro ao buscar professores por modalidade: {e}")
        finally:
            cursor.close()
            conn.close()
            
    return jsonify({'sucesso': False, 'msg': 'Erro de conexão com o banco.'})

@app.route('/backoffice/turmas/salvar', methods=['POST'])
@requer_permissao('mod_cad_turma')
def salvar_turma():
    turma_id = request.form.get('turma_id')
    modalidade = request.form.get('modalidade')
    professor_id = request.form.get('professor_id')
    capacidade_maxima = request.form.get('capacidade_maxima')
    horario = request.form.get('horario')
    status = request.form.get('status')
    
    dias_selecionados = request.form.getlist('dias_semana[]')
    dias_str = "-".join(dias_selecionados) if dias_selecionados else ""
    
    if horario and len(horario) == 5:
        horario = f"{horario}:00"
        
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            if turma_id:
                sql = """
                    UPDATE turmas 
                    SET modalidade=%s, professor_id=%s, dias_semana=%s, 
                        horario=%s, capacidade_maxima=%s, status=%s
                    WHERE id=%s
                """
                valores = (modalidade, professor_id, dias_str, horario, capacidade_maxima, status, turma_id)
                cursor.execute(sql, valores)
            else:
                sql = """
                    INSERT INTO turmas (modalidade, professor_id, dias_semana, horario, capacidade_maxima, status)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                valores = (modalidade, professor_id, dias_str, horario, capacidade_maxima, status)
                cursor.execute(sql, valores)
                
            conn.commit()
            print(f"Turma de {modalidade} salva com sucesso!")
        except Exception as e:
            print(f"Erro ao salvar turma no banco: {e}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
            
    return redirect(url_for('nova_turma'))

# ==============================================================================
# ROTAS DO QUADRO DE VAGAS E LISTA DE ESPERA
# ==============================================================================

@app.route('/backoffice/vagas')
@requer_permissao('mod_grade')
def quadro_vagas():
    return render_template('backoffice/quadro_vagas.html')

@app.route('/api/turmas/buscar', methods=['GET'])
def api_buscar_turmas_vagas():
    dia_filtro = request.args.get('dia', '').strip()
    mod_filtro = request.args.get('modalidade', '').strip()
    
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            sql = """
                SELECT t.id, t.modalidade, t.dias_semana, t.horario, t.capacidade_maxima, f.nome_completo
                FROM turmas t
                JOIN professores p ON t.professor_id = p.id
                JOIN funcionarios f ON p.funcionario_id = f.id
                WHERE t.status = 'Ativa'
            """
            parametros = []
            
            if mod_filtro:
                sql += " AND t.modalidade = %s"
                parametros.append(mod_filtro)
                
            if dia_filtro:
                sql += " AND t.dias_semana LIKE %s"
                parametros.append(f"%{dia_filtro}%")
                
            cursor.execute(sql, tuple(parametros))
            turmas_rows = cursor.fetchall()
            
            lista_turmas = []
            for row in turmas_rows:
                turma_id = row[0]
                modalidade = row[1]
                dias_semana = row[2]
                horario_raw = str(row[3])
                capacidade = row[4]
                professor = row[5]
                
                horario = horario_raw[:5] if len(horario_raw) >= 5 else horario_raw
                
                sql_vagas = """
                    SELECT COUNT(mg.id) 
                    FROM matricula_grade mg
                    JOIN matriculas m ON mg.matricula_id = m.id
                    WHERE mg.modalidade = %s AND mg.dias_semana = %s AND mg.horario LIKE %s AND m.status = 'Ativa'
                """
                cursor.execute(sql_vagas, (modalidade, dias_semana, f"%{horario}%"))
                matriculados_count = cursor.fetchone()[0]
                
                vagas_livres = capacidade - matriculados_count
                if vagas_livres < 0: 
                    vagas_livres = 0
                
                lista_turmas.append({
                    'id': turma_id,
                    'modalidade': modalidade,
                    'dias_semana': dias_semana,
                    'horario': horario,
                    'capacidade': capacidade,
                    'matriculados': matriculados_count,
                    'vagas_livres': vagas_livres,
                    'lotada': vagas_livres == 0,
                    'professor': professor
                })
                
            return jsonify({'sucesso': True, 'turmas': lista_turmas})
        except Exception as e:
            print(f"Erro ao buscar turmas para o quadro de vagas: {e}")
        finally:
            cursor.close()
            conn.close()
            
    return jsonify({'sucesso': False, 'turmas': []})

@app.route('/api/lista_espera/salvar', methods=['POST'])
def salvar_lista_espera():
    turma_id = request.form.get('turma_id')
    nome_contato = request.form.get('nome_contato')
    telefone = request.form.get('telefone')
    email = request.form.get('email')
    observacao = request.form.get('observacao')
    
    if telefone:
        telefone = re.sub(r'\D', '', telefone)
        
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            sql = """
                INSERT INTO lista_espera (turma_id, nome_contato, telefone, email, observacao, status)
                VALUES (%s, %s, %s, %s, %s, 'Aguardando')
            """
            cursor.execute(sql, (turma_id, nome_contato, telefone, email, observacao))
            conn.commit()
            return jsonify({'sucesso': True, 'msg': 'Lead adicionado com sucesso à lista de espera!'})
        except Exception as e:
            print(f"Erro ao salvar lista de espera: {e}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
            
    return jsonify({'sucesso': False, 'msg': 'Erro interno ao salvar.'})

# ==============================================================================
# ROTAS DE MATRÍCULAS
# ==============================================================================

@app.route('/api/matriculas/validar_horario', methods=['POST'])
@requer_permissao('mod_matricula')
def validar_horario_matricula():
    dados = request.get_json()
    aluno_id = dados.get('aluno_id')
    modalidade_atual = dados.get('modalidade_atual')
    horarios = dados.get('horarios', [])

    if not aluno_id or not horarios:
        return jsonify({'conflito': False})

    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            for item in horarios:
                dia = item.get('dia')
                horario = item.get('horario')
                
                if len(horario) == 5:
                    horario_str = horario + ':00'
                else:
                    horario_str = horario

                sql = """
                    SELECT mg.modalidade 
                    FROM matricula_grade mg
                    JOIN matriculas m ON mg.matricula_id = m.id
                    WHERE m.aluno_id = %s AND m.status = 'Ativa' 
                      AND mg.modalidade != %s 
                      AND mg.dias_semana = %s AND mg.horario = %s
                    LIMIT 1
                """
                cursor.execute(sql, (aluno_id, modalidade_atual, dia, horario_str))
                row = cursor.fetchone()
                
                if row:
                    return jsonify({
                        'conflito': True,
                        'mensagem': f"O aluno já possui uma atividade ({row[0]}) agendada no banco de dados para {dia} às {horario}."
                    })
            return jsonify({'conflito': False})
        except Exception as e:
            print(f"Erro ao validar horários no banco: {e}")
        finally:
            cursor.close()
            conn.close()
            
    return jsonify({'conflito': False})

@app.route('/backoffice/matriculas/nova')
@requer_permissao('mod_matricula')
def nova_matricula():
    return render_template('backoffice/cadastro_matricula.html')

@app.route('/backoffice/matriculas/salvar', methods=['POST'])
@requer_permissao('mod_matricula')
def salvar_matricula():
    matricula_id = request.form.get('matricula_id')
    aluno_id = request.form.get('aluno_id')
    tipo_plano = request.form.get('tipo_plano')
    forma_pagamento = request.form.get('forma_pagamento')
    parcelas = request.form.get('parcelas')
    data_inicio = request.form.get('data_inicio')
    data_fim = request.form.get('data_fim')
    dia_vencimento = request.form.get('dia_vencimento')
    taxa_matricula_str = request.form.get('taxa_matricula')
    
    if not data_fim:
        data_fim = None
        
    if not parcelas or not str(parcelas).isdigit():
        parcelas = 1
    else:
        parcelas = int(parcelas)
        
    taxa_matricula = 0.00
    if taxa_matricula_str:
        taxa_limpa = taxa_matricula_str.replace('R$', '').strip()
        if ',' in taxa_limpa:
            taxa_limpa = taxa_limpa.replace('.', '').replace(',', '.')
        try:
            taxa_matricula = float(taxa_limpa)
        except ValueError:
            taxa_matricula = 0.00

    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            if matricula_id:
                sql_matricula = """
                    UPDATE matriculas 
                    SET tipo_plano=%s, forma_pagamento=%s, parcelas=%s, data_inicio=%s, data_fim=%s, dia_vencimento=%s, taxa_matricula=%s 
                    WHERE id=%s
                """
                cursor.execute(sql_matricula, (tipo_plano, forma_pagamento, parcelas, data_inicio, data_fim, dia_vencimento, taxa_matricula, matricula_id))
                cursor.execute("DELETE FROM matricula_grade WHERE matricula_id = %s", (matricula_id,))
            else:
                sql_matricula = """
                    INSERT INTO matriculas (aluno_id, tipo_plano, forma_pagamento, parcelas, data_inicio, data_fim, dia_vencimento, taxa_matricula, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql_matricula, (aluno_id, tipo_plano, forma_pagamento, parcelas, data_inicio, data_fim, dia_vencimento, taxa_matricula, 'Ativa'))
                matricula_id = cursor.lastrowid
            
            modalidades = request.form.getlist('grade_modalidade[]')
            dias = request.form.getlist('grade_dias[]')
            horarios = request.form.getlist('grade_horario[]')
            
            lista_grade_email = []
            
            for i in range(len(modalidades)):
                mod = modalidades[i]
                dia = dias[i] if i < len(dias) else ''
                horario = horarios[i] if i < len(horarios) else ''
                
                if mod and dia and horario:
                    partes = horario.split(':')
                    if len(partes) >= 2:
                        horario = f"{int(partes[0]):02d}:{partes[1]}"
                        
                    sql_grade = """
                        INSERT INTO matricula_grade (matricula_id, modalidade, dias_semana, horario)
                        VALUES (%s, %s, %s, %s)
                    """
                    cursor.execute(sql_grade, (matricula_id, mod, dia, horario))
                    lista_grade_email.append({'modalidade': mod, 'dias_semana': dia, 'horario': horario})
                    
            conn.commit()
            print(f"Matrícula {matricula_id} e grade salvas com sucesso para o Aluno {aluno_id}.")
            
            try:
                sql_aluno_email = """
                    SELECT a.nome_completo, a.email
                    FROM alunos a
                    WHERE a.id = %s LIMIT 1
                """
                cursor.execute(sql_aluno_email, (aluno_id,))
                aluno_row = cursor.fetchone()
                
                if aluno_row:
                    nome_aluno = aluno_row[0]
                    email_destino = aluno_row[1]
                    
                    if email_destino:
                        try:
                            data_inicio_formatada = datetime.strptime(data_inicio, '%Y-%m-%d').strftime('%d/%m/%Y')
                        except:
                            data_inicio_formatada = data_inicio
                            
                        html_corpo = render_template(
                            'emails/matricula_confirmada.html',
                            nome_aluno=nome_aluno,
                            tipo_plano=tipo_plano,
                            data_inicio=data_inicio_formatada,
                            grade=lista_grade_email
                        )
                        
                        enviou = enviar_email_html(
                            destinatario=email_destino,
                            assunto="Sua Matrícula no MyGym foi confirmada! 🏊‍♂️",
                            corpo_html=html_corpo
                        )
                        if enviou:
                            print(f"E-mail de confirmação enviado para {email_destino}")
            except Exception as e_email:
                print(f"Erro na rotina de envio de e-mail: {e_email}")
                
        except Exception as e:
            print(f"Erro ao salvar matrícula no banco: {e}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
            
    return redirect(url_for('nova_matricula'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)