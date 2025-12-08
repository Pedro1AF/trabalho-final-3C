function abrirPopup() {
    document.getElementById('overlay').style.display = 'flex';
}

function fecharPopup() {
    document.getElementById('overlay').style.display = 'none';
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