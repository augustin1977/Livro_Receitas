function getCookie(nome) {
    let cookieValue = null;

    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");

        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();

            if (cookie.substring(0, nome.length + 1) === (nome + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(nome.length + 1));
                break;
            }
        }
    }

    return cookieValue;
}

document.addEventListener("DOMContentLoaded", function() {
    document.querySelectorAll(".btn-favorito").forEach(function(botao) {
        botao.addEventListener("click", function() {
            const receitaId = this.dataset.receitaId;
            const icone = this.querySelector("i");

            fetch(`/receita/favoritar/${receitaId}/`, {
                method: "POST",
                headers: {
                    "X-CSRFToken": getCookie("csrftoken"),
                    "X-Requested-With": "XMLHttpRequest"
                }
            })
            .then(response => response.json())
            .then(data => {
                if (!data.sucesso) {
                    alert(data.erro || "Erro ao favoritar receita.");
                    return;
                }

                if (data.favoritada) {
                    icone.classList.remove("bi-star", "text-secondary");
                    icone.classList.add("bi-star-fill", "text-warning");
                } else {
                    icone.classList.remove("bi-star-fill", "text-warning");
                    icone.classList.add("bi-star", "text-secondary");
                }
            })
            .catch(error => {
                console.error("Erro:", error);
                alert("Erro ao comunicar com o servidor.");
            });
        });
    });
});