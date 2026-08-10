# Script Python que gera uma tabela pronta
# com os modulos python, html e js contidos na pasta corrente
#
# para executar: python extrai_funcoes.py > modulos.txt

import re
from pathlib import Path

PASTAS_IGNORADAS = {'venv', '__pycache__', '.git', 'node_modules', 'static/images', 'static/uploads'}

def extrai_cabecalho_py(conteudo):
    padrao = re.compile(
        r'# ={10,}.*?'
        r'# PROJETO:\s*(.+?)\n'
        r'# MÓDULO:\s*(.+?)\n'
        r'# DATA.*?\n'
        r'# TÍTULO:\s*(.+?)\n'
        r'# FUNÇÃO:\s*(.+?)(?=\n#\s*(?:HISTÓRICO|={10,})|\n[^#]|\Z)',
        re.DOTALL
    )
    match = padrao.search(conteudo)
    if match:
        projeto, modulo, titulo, funcao = match.groups()
        funcao = re.sub(r'\n#\s*', ' ', funcao).strip()
        return modulo, titulo, funcao
    return None

def extrai_cabecalho_jinja(conteudo):
    padrao = re.compile(
        r'\{#\s*'
        r'={10,}.*?'
        r'PROJETO:\s*(.+?)\n\s*'
        r'MÓDULO:\s*(.+?)\n\s*'
        r'DATA.*?\n\s*'
        r'TÍTULO:\s*(.+?)\n\s*'
        r'FUNÇÃO:\s*(.+?)(?=\n\s*(?:HISTÓRICO|={10,})|\n\s*#\}|\Z)',
        re.DOTALL
    )
    match = padrao.search(conteudo)
    if match:
        projeto, modulo, titulo, funcao = match.groups()
        funcao = re.sub(r'\n\s*', ' ', funcao).strip()
        return modulo, titulo, funcao
    return None

def extrai_cabecalho_js(conteudo):
    # Padrão de regex adaptado para o formato de comentário do JavaScript (//)
    padrao = re.compile(
        r'// ={10,}.*?'
        r'// PROJETO:\s*(.+?)\n'
        r'// MÓDULO:\s*(.+?)\n'
        r'// DATA.*?\n'
        r'// TÍTULO:\s*(.+?)\n'
        r'// FUNÇÃO:\s*(.+?)(?=\n//\s*(?:HISTÓRICO|={10,})|\n[^/]|\Z)',
        re.DOTALL
    )
    match = padrao.search(conteudo)
    if match:
        projeto, modulo, titulo, funcao = match.groups()
        # Remove as quebras de linha e as barras de comentário do meio do texto da função
        funcao = re.sub(r'\n//\s*', ' ', funcao).strip()
        return modulo, titulo, funcao
    return None

def main():
    print(f"{'ARQUIVO':<40} | {'TÍTULO':<45} | FUNÇÃO")
    print('-' * 160)

    for arquivo in Path('.').rglob('*'):
        if any(p in arquivo.parts for p in PASTAS_IGNORADAS):
            continue
            
        # Adicionado '.js' na lista de extensões verificadas
        if arquivo.suffix not in ['.py', '.html', '.js']:
            continue
            
        try:
            conteudo = arquivo.read_text(encoding='utf-8')
            dados = None
            
            if arquivo.suffix == '.py':
                dados = extrai_cabecalho_py(conteudo)
            elif arquivo.suffix == '.html':
                dados = extrai_cabecalho_jinja(conteudo)
            elif arquivo.suffix == '.js':
                dados = extrai_cabecalho_js(conteudo)
                
            if dados:
                modulo, titulo, funcao = dados
                caminho_relativo = str(arquivo)
                print(f"{caminho_relativo:<40} | {titulo:<45} | {funcao}")
        except Exception:
            pass

if __name__ == '__main__':
    main()