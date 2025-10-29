window.onload = () => {
    new QWebChannel(qt.webChannelTransport, (channel) => {
        const bridge = channel.objects.bridge;
        const noAuthBtn = document.getElementById("noAuthBtn")
        const errors = Object.fromEntries(
            Array.from(document.querySelectorAll(".error")).map((error) => {
                return [error.parentNode.querySelector("input").getAttribute("name"), error]
            })
        )

        function authenticate(data) {
            bridge.auth_request(data, (response) => {
                if (!response.ok) {
                    response.errors.forEach((error) => {
                        errors[error.ctx.field].innerText = "*" + error.msg;
                    })
                } else {
                    localStorage.setItem("user", JSON.stringify(response.data))
                    bridge.change_page("products", (res) => {})
                }
            });
        }

        noAuthBtn.onclick = (event) => {
            event.preventDefault();
            bridge.change_page("products", (res) => {})
        }

        document.auth.onsubmit = (event) => {
            event.preventDefault();
            Object.entries(errors).forEach(([_, error]) => {
                error.innerText = "";
            })
            const form = new FormData(event.target);
            const data = Object.fromEntries(form.entries());
            authenticate(data);
        }
    });
}