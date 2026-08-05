// ==============================================================================
// PROJETO: MyGym
// MÓDULO: static/validacoes.js
// DATA DE CRIAÇÃO: 05/08/26
// TÍTULO: Central de Validações e Máscaras
// FUNÇÃO: Centralizar as regras matemáticas de validação (CPF, E-mail) e 
//         formatação visual (máscaras) para evitar duplicação de código no front-end.
//
// HISTÓRICO DE ALTERAÇÕES:
// 05/08/26: Criação do arquivo e migração das funções globais do cadastro.
// ==============================================================================

// --- FUNÇÕES DE MÁSCARA E LIMPEZA ---

function aplicarMascaraTelefone(input) {
    let valor = input.value.replace(/\D/g, "");
    if (valor.length === 0) return;
    if (valor.length > 11) valor = valor.slice(0, 11);
    
    if (valor.length > 6) {
        valor = `(${valor.slice(0, 2)}) ${valor.slice(2, 7)}-${valor.slice(7)}`;
    } else if (valor.length > 2) {
        valor = `(${valor.slice(0, 2)}) ${valor.slice(2)}`;
    } else if (valor.length > 0) {
        valor = `(${valor}`;
    }
    input.value = valor;
}

function aplicarMascaraCPF(input) {
    let valor = input.value.replace(/\D/g, "");
    if (valor.length === 0) return;
    if (valor.length > 11) valor = valor.slice(0, 11);
    
    if (valor.length > 9) {
        valor = `${valor.slice(0, 3)}.${valor.slice(3, 6)}.${valor.slice(6, 9)}-${valor.slice(9)}`;
    } else if (valor.length > 6) {
        valor = `${valor.slice(0, 3)}.${valor.slice(3, 6)}.${valor.slice(6)}`;
    } else if (valor.length > 3) {
        valor = `${valor.slice(0, 3)}.${valor.slice(3)}`;
    }
    input.value = valor;
}

function removerMascara(input) {
    input.value = input.value.replace(/\D/g, "");
}

// --- FUNÇÕES DE VALIDAÇÃO ---

function validarEmail(email) {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
}

function validarCPF(cpf) {
    cpf = cpf.replace(/\D/g, '');
    if (cpf.length !== 11 || /^(\d)\1{10}$/.test(cpf)) return false;
    
    let soma = 0, resto;
    for (let i = 1; i <= 9; i++) soma += parseInt(cpf.substring(i - 1, i)) * (11 - i);
    resto = (soma * 10) % 11;
    if ((resto === 10) || (resto === 11)) resto = 0;
    if (resto !== parseInt(cpf.substring(9, 10))) return false;
    
    soma = 0;
    for (let i = 1; i <= 10; i++) soma += parseInt(cpf.substring(i - 1, i)) * (12 - i);
    resto = (soma * 10) % 11;
    if ((resto === 10) || (resto === 11)) resto = 0;
    if (resto !== parseInt(cpf.substring(10, 11))) return false;
    
    return true;
}