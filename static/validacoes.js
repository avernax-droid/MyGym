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
// 07/08/26: Inclusão das funções de máscara de CEP e busca de endereço via API (ViaCEP).
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

// ==============================================================================
// FUNÇÕES DE CEP E INTEGRAÇÃO VIACEP
// ==============================================================================

function aplicarMascaraCEP(input) {
    let valor = input.value.replace(/\D/g, "");
    if (valor.length > 8) valor = valor.slice(0, 8);
    
    if (valor.length > 5) {
        valor = `${valor.slice(0, 5)}-${valor.slice(5)}`;
    }
    input.value = valor;
}

async function buscarEnderecoViaCEP(cep, mapaCampos) {
    const cepLimpo = cep.replace(/\D/g, '');
    
    if (cepLimpo.length !== 8) return; // Só busca se o CEP estiver completo

    try {
        const response = await fetch(`https://viacep.com.br/ws/${cepLimpo}/json/`);
        const data = await response.json();

        if (!data.erro) {
            if (mapaCampos.endereco && document.getElementById(mapaCampos.endereco)) {
                document.getElementById(mapaCampos.endereco).value = data.logradouro || '';
            }
            if (mapaCampos.bairro && document.getElementById(mapaCampos.bairro)) {
                document.getElementById(mapaCampos.bairro).value = data.bairro || '';
            }
            if (mapaCampos.cidade && document.getElementById(mapaCampos.cidade)) {
                document.getElementById(mapaCampos.cidade).value = data.localidade || '';
            }
            if (mapaCampos.uf && document.getElementById(mapaCampos.uf)) {
                document.getElementById(mapaCampos.uf).value = data.uf || '';
            }
        } else {
            console.warn("CEP não encontrado.");
        }
    } catch (error) {
        console.error("Erro ao buscar CEP na API ViaCEP:", error);
    }
}