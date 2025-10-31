window.onload = () => {
    new QWebChannel(qt.webChannelTransport, (channel) => {
        const bridge = channel.objects.bridge;
        const info = document.getElementById("userInfo")
        const logoutBtn = document.getElementById("logoutBtn")
        const user = JSON.parse(localStorage.getItem("user"));
        const productList = document.querySelector(".product__list")
        info.innerText = user?.username || "Гость";
        const searchData = Object.fromEntries((new FormData(document.searchForm)).entries());
        var timeout;

        logoutBtn.onclick = () => {
            localStorage.removeItem("user")
            bridge.change_page("auth", (res) => {})
        }

        function formatSearchData() {
            searchData["q"] = document.searchForm.q.value || null;
            searchData["min_price"] = document.searchForm.min_price.value || 0;
            searchData["max_price"] = document.searchForm.max_price.value || 'inf';
            get_products()
        }

        document.searchForm.q.oninput = (ev) => {
            if (timeout) clearTimeout(timeout);
            timeout = setTimeout(formatSearchData, 50);
        }

        document.searchForm.min_price.oninput = (ev) => {
            if (timeout) clearTimeout(timeout);
            timeout = setTimeout(formatSearchData, 50);
        }

        document.searchForm.max_price.oninput = (ev) => {
            if (timeout) clearTimeout(timeout);
            timeout = setTimeout(formatSearchData, 50);
        }

        function get_products() {
            bridge.get_products(searchData, (response) => {
                console.log(response)
                if (response.ok) {
                    productList.innerHTML = "";
                    response.data.forEach((product) => {
                        productList.innerHTML += `
                            <li class="product__item">
                                <img src="${product.image_url}" class="product__image"/>
                                <div class="product__info">
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
                                        ${
                                            !product.corrected_price ? (
                                                `<span>${product.price} руб.</span>`
                                            ) : (
                                                `<s>${product.price} руб.</s>`
                                            )
                                        }
                                        ${product.corrected_price ? `<span>${product.corrected_price} руб.</span>` : ''}
                                    </div>
                                    <div class="product__row">
                                        <span>Единица измерения:</span>
                                        <span>${product.measure}</span>
                                    </div>
                                    <div class="product__row">
                                        <span>Количество на складе:</span>
                                        <span>${product.quantity}</span>
                                    </div>
                                </div>
                                ${product.discount ? `<span class="product__discount">${product.discount}%</span>` : ''}
                            </li>
                        `
                    })
                }
            })
        }

        formatSearchData()
    })
}