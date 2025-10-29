window.onload = () => {
    new QWebChannel(qt.webChannelTransport, (channel) => {
        const bridge = channel.objects.bridge;
        const info = document.getElementById("userInfo")
        const logoutBtn = document.getElementById("logoutBtn")
        const user = JSON.parse(localStorage.getItem("user"));
        const productList = document.querySelector(".product__list")
        info.innerText = user?.username || "Гость";

        logoutBtn.onclick = () => {
            localStorage.removeItem("user")
            bridge.change_page("auth", (res) => {})
        }

        bridge.get_products({}, (response) => {
            if (response.ok) {
                response.data.forEach((product) => {
                    productList.innerHTML += `
                        <li class="product__item">
                            <span>${product.category.title} | ${product.title}</span>
                            <div class="product__row">
                                <span>Описание:</span>
                                <span>${product.description}</span>
                            </div>
                            <div class="product__row">
                                <span>Производитель:</span>
                                <span>${product.producer}</span>
                            </div>
                            <div class="product__row">
                                <span>Поставщик:</span>
                                <span>${product.supplier}</span>
                            </div>
                            <div class="product__row">
                                <span>Цена:</span>
                                <span>${product.price}</span>
                            </div>
                            <div class="product__row">
                                <span>Единица измерения:</span>
                                <span>${product.measure}</span>
                            </div>
                            <div class="product__row">
                                <span>Количество на складе:</span>
                                <span>${product.quantity}</span>
                            </div>
                        </li>
                    `
                })
            }
        })
    })
}