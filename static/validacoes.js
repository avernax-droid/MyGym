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
// 12/08/26: Adição do comportamento Enter como Tab e Preview de Imagem de Upload.
// 14/08/26: Inclusão da função aplicarMascaraCPFOuMatricula para busca dinâmica de alunos.
// 14/08/26: Inclusão da função formatarMatriculaBlur para preenchimento de zeros à esquerda (ex: 0001).
// 17/08/26: Inclusão da função global monitorarAlteracoes para controle inteligente do botão Salvar.
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

function aplicarMascaraCPFOuMatricula(input) {
    let valor = input.value.replace(/\D/g, "");
    if (valor.length === 0) {
        input.value = "";
        return;
    }
    if (valor.length > 11) valor = valor.slice(0, 11);
    
    if (valor.length > 6) {
        if (valor.length > 9) {
            valor = `${valor.slice(0, 3)}.${valor.slice(3, 6)}.${valor.slice(6, 9)}-${valor.slice(9)}`;
        } else {
            valor = `${valor.slice(0, 3)}.${valor.slice(3, 6)}.${valor.slice(6)}`;
        }
    }
    
    input.value = valor;
}

function formatarMatriculaBlur(input) {
    let valor = input.value.replace(/\D/g, "");
    // Se for uma matrícula (até 6 dígitos), preenche com zeros à esquerda até ter no mínimo 4 dígitos
    if (valor.length > 0 && valor.length <= 6) {
        input.value = valor.padStart(4, '0');
    }
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
// FUNÇÕES DE MONITORAMENTO DE ESTADO (DIRTY FORM)
// ==============================================================================

/**
 * Monitora alterações em um formulário comparando-o com seu estado inicial.
 * @param {string} formId - O ID do formulário HTML.
 * @param {string} btnSalvarId - O ID do botão que será habilitado/desabilitado.
 * @param {function} fnFormularioValido - (Opcional) Função que retorna boolean verificando regras adicionais (ex: campos obrigatórios preenchidos).
 * @returns {function} - Retorna a função de checagem caso precise ser invocada manualmente.
 */
function monitorarAlteracoes(formId, btnSalvarId, fnFormularioValido = null) {
    const form = document.getElementById(formId);
    const btnSalvar = document.getElementById(btnSalvarId);
    
    if (!form || !btnSalvar) {
        console.warn(`monitorarAlteracoes: Elementos não encontrados (Form: ${formId}, Botão: ${btnSalvarId})`);
        return null;
    }

    // Função interna que serializa o formulário atual
    const capturarEstado = () => {
        const formData = new FormData(form);
        const estado = {};
        for (let [key, value] of formData.entries()) {
            if (!estado[key]) {
                estado[key] = [];
            }
            estado[key].push(value);
        }
        return JSON.stringify(estado);
    };

    // "Tira a foto" do estado assim que a função é iniciada (geralmente após a carga do banco)
    const estadoInicial = capturarEstado();

    const checarEstado = () => {
        const estadoAtual = capturarEstado();
        const formFoiAlterado = (estadoInicial !== estadoAtual);
        
        let camposValidos = true;
        if (typeof fnFormularioValido === 'function') {
            camposValidos = fnFormularioValido(); // Valida obrigatoriedades da tela específica
        }

        // Habilita o botão APENAS se houver alteração E os campos estiverem válidos
        btnSalvar.disabled = !(formFoiAlterado && camposValidos);
    };

    // Dispara a checagem sempre que um input disparar evento
    form.addEventListener('input', checarEstado);
    form.addEventListener('change', checarEstado);

    // Usa MutationObserver para pegar elementos ocultos ou gerados via JS dinamicamente (ex: inputs da grade)
    const observer = new MutationObserver(() => {
        checarEstado();
    });
    observer.observe(form, { childList: true, subtree: true });

    // Garante o estado correto do botão logo na primeira execução
    checarEstado();

    return checarEstado;
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
    
    if (cepLimpo.length !== 8) return;

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

// ==============================================================================
// COMPORTAMENTO GERAL DA INTERFACE (UI/UX)
// ==============================================================================

function configurarEnterComoTab() {
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            const elementoAtivo = document.activeElement;
            
            // Ignora se for textarea, botões normais ou de submit
            if (!elementoAtivo || 
                elementoAtivo.tagName.toLowerCase() === 'textarea' || 
                elementoAtivo.tagName.toLowerCase() === 'button' ||
                elementoAtivo.type === 'submit') {
                return;
            }

            e.preventDefault(); 

            // Busca os elementos focáveis visíveis no formulário ou contexto atual
            const form = elementoAtivo.closest('form') || document;
            const elementosFocaveis = Array.from(form.querySelectorAll('input:not([type="hidden"]):not([disabled]), select:not([disabled]), textarea:not([disabled]), button:not([disabled])'));
            
            const indexAtual = elementosFocaveis.indexOf(elementoAtivo);
            if (indexAtual > -1 && indexAtual < elementosFocaveis.length - 1) {
                let proximoIndex = indexAtual + 1;
                
                while (proximoIndex < elementosFocaveis.length) {
                    const proximoElemento = elementosFocaveis[proximoIndex];
                    if (proximoElemento.offsetWidth > 0 && proximoElemento.offsetHeight > 0) {
                        proximoElemento.focus();
                        break;
                    }
                    proximoIndex++;
                }
            }
        }
    });
}

function ativarPreviewImagem(inputElement, imgElement, placeholderElement) {
    if (!inputElement) return;
    
    inputElement.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(evt) {
                if (imgElement) {
                    imgElement.src = evt.target.result;
                    imgElement.style.display = 'block';
                }
                if (placeholderElement) {
                    placeholderElement.style.display = 'none';
                }
            }
            reader.readAsDataURL(file);
        } else {
            if (imgElement) {
                imgElement.src = '';
                imgElement.style.display = 'none';
            }
            if (placeholderElement) {
                placeholderElement.style.display = 'block';
            }
        }
    });
}