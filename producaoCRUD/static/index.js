function abrirPopup() {
    document.getElementById('overlay').style.display = 'flex';
}

function fecharPopup() {
    document.getElementById('overlay').style.display = 'none';
}

function enviarDados() {
    const nome = document.getElementById('nome').value;
    const senha = document.getElementById('password').value;

    if (nome.trim() === '' || senha.trim() === '') {
        alert('Preencha todos os campos!');
        return false;  // impede submit
    }

    alert(`Diretório ${nome} criado!`);
    fecharPopup();
    return true; // permite submit
}


// Pop-up individual dos diretórios


function fechardir(id) {
    document.getElementById(`diretorio-overlay-${id}`).style.display = 'none';
}

function verificar(id) {
    const senha = document.getElementById(`password_verificacao-${id}`).value;

    if (senha.trim() === "") {  
        alert("Digite a senha!");
        return;
    }

    alert(`Diretório ${id} verificado com sucesso!`);
    fechardir(id);
}

document.addEventListener("click", function(e) {
    const btn = e.target.closest(".menu-btn");
    const menus = document.querySelectorAll(".menu-opcoes");

    // Fecha todos os menus antes de abrir outro
    menus.forEach(m => m.style.display = "none");

    // Se clicou no botão, abre o menu
    if (btn) {
        const menu = btn.nextElementSibling;
        menu.style.display = "block";
    }
});
