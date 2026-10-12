// Guarda os itens escolhidos até o checkout terminar.
let pedido = [];
// Define a taxa fixa cobrada quando o cliente escolhe entrega.
const TAXA_ENTREGA = 5;

// Adiciona uma unidade de um produto ao carrinho.
function adicionarProduto(nome, preco) {

    alterarQuantidade(nome, preco, 1);
}

// Altera a quantidade de um item pelo ID do banco e depois redesenha o carrinho.
function alterarQuantidade(nome, preco, variacao, produtoId = null) {

    const produto = pedido.find(function (item) {
        return produtoId !== null ? item.id === produtoId : item.nome === nome;
    });

    if (produto) {
        produto.quantidade += variacao;
    } else if (variacao > 0) {
        pedido.push({
            nome: nome,
            preco: preco,
            id: produtoId,
            quantidade: variacao
        });
    }

    if (produto && produto.quantidade <= 0) {
        pedido.splice(pedido.indexOf(produto), 1);
    }

    atualizarPedido();
}


// Renderiza os itens do carrinho e mantém seus contadores e subtotal atualizados.

function atualizarPedido() {

    const listaPedido = document.getElementById("lista-pedido");

    const totalElemento = document.getElementById("total");


    // Limpa a lista atual

    listaPedido.innerHTML = "";

    document.querySelectorAll(".controle-quantidade span").forEach(function (contador) {
        contador.textContent = "0";
    });


    // Se não tiver produtos

    if (pedido.length === 0) {

        listaPedido.innerHTML =
            "<p>Nenhum produto adicionado.</p>";

        totalElemento.textContent = "0.00";

        return;
    }


    // Total da compra

    let total = 0;


    // Percorre os produtos

    pedido.forEach(function (produto, indice) {

        const item = document.createElement("p");

        const controle = [...document.querySelectorAll(".controle-quantidade")]
            .find(elemento => elemento.dataset.produto === produto.nome);
        const contador = controle && controle.querySelector("span");
        if (contador) contador.textContent = produto.quantidade;

        item.textContent =
            `${produto.quantidade}x ${produto.nome} - R$ ${(produto.preco * produto.quantidade).toFixed(2)}`;


        // Cria botão de excluir

        const botaoExcluir = document.createElement("button");

        botaoExcluir.textContent = "❌";


        // Quando clicar no botão

        botaoExcluir.onclick = function () {

            pedido.splice(indice, 1);

            atualizarPedido();
        };


        // Coloca o botão junto do produto

        item.appendChild(botaoExcluir);

        listaPedido.appendChild(item);


        // Soma o preço

        total += produto.preco * produto.quantidade;
    });


    // Mostra o total

    totalElemento.textContent = total.toFixed(2);
}


// Valida os dados de contato, o endereço de entrega e a forma de pagamento.
function validarEndereco() {

    const formulario = document.getElementById("endereco-entrega");
    const erro = document.getElementById("erro-pedido");
    const tipoPedido = document.querySelector("input[name='tipo-pedido']:checked");

    if (!tipoPedido) {
        erro.textContent = "Escolha entre retirada ou entrega.";
        erro.classList.add("visivel");
        return null;
    }

    const camposObrigatorios = [
        ...formulario.querySelectorAll(".dados-cliente input[required]")
    ];

    if (tipoPedido.value === "Entrega") {
        camposObrigatorios.push(
            ...formulario.querySelectorAll("#campos-entrega input[required]")
        );
    }
    let enderecoValido = true;

    camposObrigatorios.forEach(function (campo) {

        const preenchido = campo.value.trim() !== "";
        const cepValido = campo.name !== "cep" || /^[0-9]{5}-?[0-9]{3}$/.test(campo.value.trim());
        const cpfValido = campo.name !== "cpf" || validarCPF(campo.value);
        const telefoneValido = campo.name !== "telefone" || campo.value.replace(/\D/g, "").length >= 10;
        const campoValido = preenchido && cepValido && cpfValido && telefoneValido;

        campo.classList.toggle("invalido", !campoValido);

        if (!campoValido) {
            enderecoValido = false;
        }
    });

    if (!enderecoValido) {
        erro.textContent = tipoPedido.value === "Entrega"
            ? "Preencha o endereço, nome, telefone válido e CPF válido."
            : "Preencha nome, telefone válido e CPF válido.";
        erro.classList.add("visivel");
        return null;
    }

    const pagamento = formulario.querySelector("input[name='pagamento']:checked");
    const tipoMaquina = formulario.querySelector("input[name='tipo-maquina']:checked");

    if (!pagamento || (pagamento.value === "Na máquina" && !tipoMaquina)) {
        erro.textContent = pagamento && pagamento.value === "Na máquina"
            ? "Escolha débito, crédito ou Pix."
            : "Escolha uma forma de pagamento.";
        erro.classList.add("visivel");
        return null;
    }

    erro.textContent = "";
    erro.classList.remove("visivel");

    const dados = new FormData(formulario);

    return {
        tipoPedido: tipoPedido.value,
        rua: (dados.get("rua") || "").trim(),
        numero: (dados.get("numero") || "").trim(),
        bairro: (dados.get("bairro") || "").trim(),
        cidade: (dados.get("cidade") || "").trim(),
        cep: (dados.get("cep") || "").trim(),
        complemento: (dados.get("complemento") || "").trim(),
        nome: dados.get("nome").trim(),
        telefone: dados.get("telefone").trim(),
        cpf: dados.get("cpf").trim(),
        pagamento: pagamento.value,
        tipoMaquina: tipoMaquina ? tipoMaquina.value : ""
    };
}

// Verifica os dígitos de controle do CPF antes de aceitar o formulário.
function validarCPF(cpf) {

    const numeros = cpf.replace(/\D/g, "");

    if (numeros.length !== 11 || /^([0-9])\1{10}$/.test(numeros)) {
        return false;
    }

    let soma = 0;

    for (let indice = 0; indice < 9; indice++) {
        soma += Number(numeros[indice]) * (10 - indice);
    }

    let primeiroDigito = (soma * 10) % 11;
    primeiroDigito = primeiroDigito === 10 ? 0 : primeiroDigito;

    if (primeiroDigito !== Number(numeros[9])) {
        return false;
    }

    soma = 0;

    for (let indice = 0; indice < 10; indice++) {
        soma += Number(numeros[indice]) * (11 - indice);
    }

    let segundoDigito = (soma * 10) % 11;
    segundoDigito = segundoDigito === 10 ? 0 : segundoDigito;

    return segundoDigito === Number(numeros[10]);
}

// Exibe endereço e taxa somente quando a pessoa escolher receber por entrega.
function configurarTipoPedido() {

    const opcoesTipoPedido = document.querySelectorAll("input[name='tipo-pedido']");
    const camposEntrega = document.getElementById("campos-entrega");
    const taxaEntrega = document.getElementById("taxa-entrega");

    opcoesTipoPedido.forEach(function (opcao) {
        opcao.addEventListener("change", function () {
            const entregaSelecionada = opcao.value === "Entrega" && opcao.checked;
            camposEntrega.classList.toggle("oculto", !entregaSelecionada);
            taxaEntrega.classList.toggle("visivel", entregaSelecionada);
        });
    });
}

// Exibe as opções da maquininha quando esse método de pagamento for selecionado.
function configurarPagamento() {

    const opcoesPagamento = document.querySelectorAll("input[name='pagamento']");
    const opcoesMaquina = document.getElementById("opcoes-maquina");
    const tiposMaquina = document.querySelectorAll("input[name='tipo-maquina']");

    opcoesPagamento.forEach(function (opcao) {
        opcao.addEventListener("change", function () {
            const maquinaSelecionada = opcao.value === "Na máquina" && opcao.checked;
            opcoesMaquina.classList.toggle("visivel", maquinaSelecionada);
            tiposMaquina.forEach(function (tipo) {
                tipo.required = maquinaSelecionada;
                if (!maquinaSelecionada) {
                    tipo.checked = false;
                }
            });
        });
    });
}

// Insere pontos e hífen no CPF enquanto a pessoa digita.
function configurarMascaraCPF() {

    const campoCPF = document.querySelector("input[name='cpf']");

    campoCPF.addEventListener("input", function () {
        const numeros = campoCPF.value.replace(/\D/g, "").slice(0, 11);

        campoCPF.value = numeros
            .replace(/(\d{3})(\d)/, "$1.$2")
            .replace(/(\d{3})(\d)/, "$1.$2")
            .replace(/(\d{3})(\d{1,2})$/, "$1-$2");
    });
}

// Ativa os comportamentos dos campos do formulário presentes na página.
configurarPagamento();
configurarTipoPedido();
configurarMascaraCPF();


// Salva o cliente e o pedido na API e, em seguida, abre a mensagem do WhatsApp.
async function enviarWhatsApp() {
    if (pedido.length === 0) {
        alert("Adicione algum produto ao pedido.");
        return;
    }

    const endereco = validarEndereco();
    if (endereco === null) return;

    // Abre uma aba durante o clique para evitar que o navegador bloqueie o WhatsApp.
    const janela = window.open("about:blank", "_blank");
    const erro = document.getElementById("erro-pedido");
    const botao = document.querySelector(".whatsapp");
    botao.disabled = true;
    erro.textContent = "";
    erro.classList.remove("visivel");

    try {
        // Envia os dados de checkout; o servidor reconhece o cliente pelo telefone e salva tudo.
        const respostaPedido = await fetch("/pedidos", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                cliente_nome: endereco.nome,
                cliente_telefone: endereco.telefone,
                itens: pedido.map(item => ({ produto_id: item.id, quantidade: item.quantidade })),
                tipo_pedido: endereco.tipoPedido,
                rua: endereco.rua,
                numero: endereco.numero,
                bairro: endereco.bairro,
                cidade: endereco.cidade,
                cep: endereco.cep,
                complemento: endereco.complemento,
                cpf: endereco.cpf,
                pagamento: endereco.pagamento,
                tipo_maquina: endereco.tipoMaquina
            })
        });
        const resultadoPedido = await respostaPedido.json();
        if (!respostaPedido.ok) throw new Error(resultadoPedido.erro || "Não foi possível salvar o pedido.");

        // Monta a mensagem para o estabelecimento revisar e enviar pelo WhatsApp.
        const linhas = ["Olá! Gostaria de fazer um pedido:", ""];
        resultadoPedido.itens.forEach(item => {
            linhas.push(`${item.quantidade}x ${item.nome} - R$ ${item.total_item.toFixed(2)}`);
        });
        linhas.push(
            "",
            `Pedido #${resultadoPedido.pedido_id}`,
            `Cliente ID: ${resultadoPedido.cliente_id}`,
            `WhatsApp do cliente: ${resultadoPedido.telefone_cliente}`,
            `Pedidos anteriores na loja: ${resultadoPedido.pedidos_anteriores}`,
            `Este é o pedido nº ${resultadoPedido.numero_pedido_cliente} deste cliente`,
            `Subtotal: R$ ${resultadoPedido.subtotal.toFixed(2)}`
        );
        if (resultadoPedido.taxa_entrega > 0) {
            linhas.push(`Taxa de entrega: R$ ${resultadoPedido.taxa_entrega.toFixed(2)}`);
        }
        linhas.push(`Total: R$ ${resultadoPedido.total.toFixed(2)}`, "", `${endereco.tipoPedido}:`);
        if (endereco.tipoPedido === "Entrega") {
            linhas.push(`${endereco.rua}, ${endereco.numero}`, `${endereco.bairro} - ${endereco.cidade}`, `CEP: ${endereco.cep}`);
            if (endereco.complemento) linhas.push(`Complemento: ${endereco.complemento}`);
        }
        linhas.push("", `Cliente: ${endereco.nome}`, `Telefone: ${endereco.telefone}`, `CPF: ${endereco.cpf}`, `Pagamento: ${endereco.pagamento}`);
        if (endereco.tipoMaquina) linhas.push(`Tipo: ${endereco.tipoMaquina}`);

        // Número do WhatsApp do estabelecimento, com código do país e DDD, sem sinais.
        const telefoneLancheria = "5551992125860";
        const urlWhatsApp = `https://wa.me/${telefoneLancheria}?text=${encodeURIComponent(linhas.join("\n"))}`;
        if (janela) janela.location.href = urlWhatsApp;
        else window.location.href = urlWhatsApp;
    } catch (falha) {
        if (janela) janela.close();
        erro.textContent = `${falha.message} Confira se o Flask e o banco estão funcionando e tente novamente.`;
        console.error(falha);
    } finally {
        botao.disabled = false;
    }
}

// Relaciona cada produto do banco com sua descrição, categoria e imagem do cardápio.
const detalhesProdutos = {
    "x-burger": ["Hambúrgueres", "Hambúrguer da casa.", "xbacon.jpg"],
    "x-bacon": ["Hambúrgueres", "Pão, hambúrguer, queijo, bacon e molho especial.", "xbacon.jpg"],
    "x-salada": ["Hambúrgueres", "Pão, hambúrguer, queijo, alface, tomate e molho.", "xsalada.jpg"],
    "x-tudo": ["Hambúrgueres", "Hambúrguer, queijo, bacon, ovo, presunto e salada.", "xtudo.jpg"],
    "batata frita": ["Porções", "Porção de batata frita crocante.", "batata_simples.jpg"],
    "batata frita c/ cheddar": ["Porções", "Batata frita com queijo cheddar e bacon.", "batata_cheddar.png"],
    "coca-cola 2l": ["Bebidas", "Coca-Cola 2 litros.", "coca_cola_2l.jpg"],
    "coca-cola 2l zero": ["Bebidas", "Coca-Cola 2 litros zero.", "coca_cola_2l_zero.jpg"],
    "coca-cola 350ml": ["Bebidas", "Coca-Cola 350 ml.", "coca_cola_350ml.jpg"],
    "guaraná antartica 2l": ["Bebidas", "Guaraná Antarctica 2 litros.", "guarana_antartica_2l.jpg"],
    "fruki guaraná 2l": ["Bebidas", "Fruki Guaraná 2 litros.", "fruki_guaraná_2l.png"],
    "fruki guaraná 350 ml": ["Bebidas", "Fruki Guaraná 350 ml.", "fruki_350ml.png"]
};

// Padroniza o nome antes de procurar seus detalhes no catálogo local.
function chaveProduto(nome) {
    return nome.trim().toLocaleLowerCase("pt-BR");
}

// Busca o catálogo da API e monta os cartões com IDs e preços atuais do banco.
async function carregarProdutos() {
    const secoes = [...document.querySelectorAll("main > .categoria")];
    const secoesPorNome = new Map(secoes.map(secao => [
        secao.querySelector("h2").textContent.replace(/^\S+\s*/, "").trim(), secao
    ]));

    try {
        const resposta = await fetch("/produtos");
        if (!resposta.ok) throw new Error("Não foi possível consultar os produtos.");
        const produtos = await resposta.json();
        secoes.forEach(secao => secao.querySelectorAll(".produto").forEach(card => card.remove()));

        produtos.forEach(produto => {
            // Produtos novos sem texto editorial também aparecem, agrupados em "Outros".
            let detalhes = detalhesProdutos[chaveProduto(produto.nome)];
            if (!detalhes) detalhes = ["Outros", "Produto do cardápio.", "logo lancheria.png"];
            let secao = secoesPorNome.get(detalhes[0]);
            if (!secao) {
                secao = document.createElement("section");
                secao.className = "categoria";
                const titulo = document.createElement("h2");
                titulo.textContent = "🍽️ Outros";
                secao.appendChild(titulo);
                document.querySelector("main").insertBefore(secao, document.querySelector(".adicionar-pedido"));
                secoesPorNome.set(detalhes[0], secao);
            }

            const card = document.createElement("article");
            card.className = "produto";
            const conteudo = document.createElement("div");
            const nome = document.createElement("h3");
            nome.textContent = produto.nome;
            const descricao = document.createElement("p");
            descricao.textContent = detalhes[1];
            const imagem = document.createElement("img");
            imagem.src = `img_proj_cardápio/${detalhes[2]}`;
            imagem.alt = produto.nome;
            const preco = document.createElement("strong");
            preco.textContent = `R$ ${Number(produto.preco).toFixed(2).replace(".", ",")}`;
            conteudo.append(nome, descricao, imagem, preco);

            const controles = document.createElement("div");
            controles.className = "controle-quantidade";
            controles.dataset.produto = produto.nome;
            const menos = document.createElement("button");
            menos.type = "button";
            menos.className = "botao-quantidade botao-quantidade--menos";
            menos.textContent = "−";
            menos.setAttribute("aria-label", `Diminuir ${produto.nome}`);
            const quantidade = document.createElement("span");
            quantidade.textContent = "0";
            const mais = document.createElement("button");
            mais.type = "button";
            mais.className = "botao-quantidade";
            mais.textContent = "+";
            mais.setAttribute("aria-label", `Adicionar ${produto.nome}`);
            menos.addEventListener("click", () => alterarQuantidade(produto.nome, Number(produto.preco), -1, produto.id));
            mais.addEventListener("click", () => alterarQuantidade(produto.nome, Number(produto.preco), 1, produto.id));
            controles.append(menos, quantidade, mais);
            card.append(conteudo, controles);
            secao.appendChild(card);
        });

        if (produtos.length === 0) {
            const aviso = document.createElement("p");
            aviso.textContent = "Nenhum produto cadastrado no banco ainda.";
            secoes[0].appendChild(aviso);
        }
    } catch (erro) {
        const aviso = document.createElement("p");
        aviso.className = "erro-endereco visivel";
        aviso.textContent = "Não foi possível carregar o cardápio. Confira se o Flask e o banco estão ligados.";
        secoes[0].appendChild(aviso);
        console.error(erro);
    }
}

carregarProdutos();

