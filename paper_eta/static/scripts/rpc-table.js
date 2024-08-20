class RpcTable {
    static get classes() {
        return [
            [576, ".collapse-xs"], [768, ".collapse-sm"], [992, ".collapse-md"], [1200, ".collapse-lg"]
        ];
    }

    /**
     * @returns {Array<string>}
     */
    static hiddenClasses() {
        return RpcTable.classes.filter((v) => v[0] >= window.screen.width).map((v) => v[1]);
    }

    constructor(selector) {
        this.table = document.querySelector(selector);
        this.table.classList.add("rpc");
        let cls = this;

        this.table.querySelectorAll(`tbody tr td:not(${RpcTable.classes.map((c) => c[1]).join(", ")})`).forEach((el) => {
            el.addEventListener("click", function (event) {
                let tr = el.closest("tr");
                if (tr.classList.contains("rpc-expanded")) {
                    el.closest("tbody").removeChild(tr.nextSibling)
                } else {
                    let newTr = document.createElement("tr");
                    newTr.innerHTML = `
                        <td colspan=${tr.querySelectorAll(`td:not(${RpcTable.hiddenClasses().join(",")})`).length}>123</td>
                    `;
                    tr.after(cls.generateChild(tr));
                }

                tr.classList.toggle("rpc-expanded")
            });

            return;
        })

        this.table.querySelectorAll("thead th").forEach((el, i) => {
            if (!el.classList.contains("collapse-sm"))
                return

            this.table.querySelectorAll(`tbody tr td:nth-child(${i + 1})`).forEach((el, i) => {
                el.classList.add("collapse-sm")
            });
        });

        window.addEventListener("resize", function (event) {
            cls.table.querySelectorAll("tbody tr").forEach((el) => {
                cls.generateChild(el)
            })
        })
    }

    /**
     * @param {HTMLElement} tr 
     * @returns {HTMLElement}
     */
    generateChild(tr) {
        const headers = [];
        document
            .querySelectorAll("table.rpc tr:nth-child(1) th")
            .forEach((el) => { headers.push(el.innerHTML) });

        const lis = [];
        tr.querySelectorAll("td")
            .forEach((td, i) => {
                if ([...td.classList].some((c) => "."+RpcTable.hiddenClasses().includes(c))) {
                    lis.push(`
                        <li>
                            <span class="rpc-child-title">${headers[i]}</span>
                            <span class="rpc-child-value">${td.innerHTML}</span>
                        </li>
                    `);
                }
            });
        
        if (!lis) {
            tr.classList.remove("has-child")
        }
        tr.classList.add("has-child")

        let newTr = document.createElement("tr");
        newTr.classList.add("child");
        newTr.innerHTML = `
            <td colspan=${headers.length - lis.length}>
                <ul>
                    ${lis.join("\n")}
                </ul>
            </td>
        `;
        return newTr;
    }
}