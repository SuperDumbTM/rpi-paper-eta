class RpcTable {
    /** @type {HTMLTableElement} */
    table;

    /** @type {Array<HTMLTableRowElement>} */
    #children;

    /** @type {Object<string, number>} */
    #breakpoints;

    /**
     * @returns {Array<string>}
     */
    get tableHeaders() {
        return [...this.table.querySelectorAll("tr:nth-child(1) th")]
            .map((node) => node.innerHTML);
    }

    /** @type {number} */
    #resizeTimeout;

    /**
     * 
     * @param {string} selector CSS selector
     * @param {Object} options 
     */
    constructor(selector, options = {}) {
        this.table = document.querySelector(selector);
        this.table.classList.add("rpc");

        this.#children = [];
        this.#breakpoints = options.breakpoints || {
            "collapse-xs": 576,
            "collapse-sm": 768,
            "collapse-md": 992,
            "collapse-lg": 1200,
            "collapse": Number.MAX_SAFE_INTEGER,
        }

        this.process();

        this.table.addEventListener("click", (event) => {
            if (![...event.target.classList].includes("rpc-toggler"))
                return

            let tr = event.target.closest("tr");
            if (tr.classList.contains("rpc-expanded")) {
                tr.nextSibling.remove()
            } else {
                tr.after(this.#children[tr.dataset.childIndex])
            }

            tr.classList.toggle("rpc-expanded")
        })
        window.addEventListener("resize", this.#handleResize.bind(this))
    }

    process() {
        this.#children = [];

        this.table.querySelectorAll("tbody tr:not(.child)").forEach((tr) => {
            let child = Object.assign(document.createElement("tr"), {
                classList: ["child"],
                colspan: "100%",
                innerHTML: `<td colspan=\"100%\"><ul data-row=\"${tr.rowIndex}\"></ul></td>`,
            });


            tr.querySelectorAll("td").forEach((td, i) => {
                if (![...td.classList].includes("rpc-hidden"))
                    return
                child.querySelector("td > ul").appendChild(this.#createChildLi(td))
            });

            tr.dataset.childIndex = this.#children.length;
            tr.dataset.row = tr.rowIndex;

            this.#children.push(child);
        })
        this.render();
    }

    render() {
        this.#toggleResponsiveClass();

        this.table.querySelectorAll("tbody tr:not(.child)").forEach((tr) => {
            let child = this.#children[tr.dataset.childIndex];

            /** @type {HTMLLIElement} */
            let childContainer = child.querySelector("tr > td > ul");

            for (let td of tr.cells) {
                if ([...td.classList].includes("rpc-hidden")
                    && !this.#inChild(child, tr.dataset.row, td.cellIndex)
                ) {
                    let index = childContainer.children.length;
                    while (true) {
                        if (index == 0) {
                            childContainer.prepend(this.#createChildLi(td));
                            break;
                        }

                        index--;
                        if (td.cellIndex > childContainer.children[index].dataset.column) {
                            childContainer.children[index].after(this.#createChildLi(td));
                            break;
                        }
                    }
                    continue;
                }

                if (![...td.classList].includes("rpc-hidden")
                    && this.#inChild(child, tr.dataset.row, td.cellIndex)
                ) {
                    for (let li of childContainer.getElementsByTagName("li")) {
                        if (li.dataset.column != td.cellIndex) {
                            continue;
                        }
                        // let rowIndex = parseInt(tr.dataset.row) + this.table.querySelectorAll(`tbody tr.rpc-expanded:nth-of-type(-n+${tr.rowIndex})`).length
                        // let span = li.querySelector("span.rpc-child-value");

                        // if (span.children.length > 0) {
                        //     this.table.rows[rowIndex].cells[li.dataset.column].append(...span.children);
                        // } else {
                        //     this.table.rows[rowIndex].cells[li.dataset.column].innerHTML = span.innerHTML;
                        // }
                        li.remove();
                    }
                    continue;
                }
            }

            tr.querySelector('td.rpc-toggler')?.classList.remove("rpc-toggler");
            if (childContainer.children.length > 0) {
                tr.classList.add("has-child")
                tr.querySelector('td:not(.rpc-hidden)').classList.add("rpc-toggler");
            } else {
                tr.classList.remove("has-child")
            }
        });
    }

    /**
     * @returns {Array<string>}
     */
    hiddenClasses() {
        return Object.keys(this.#breakpoints)
            .filter((k) => this.#breakpoints[k] >= window.innerWidth)
    }

    #toggleResponsiveClass() {
        this.table.querySelectorAll("thead > tr > th").forEach((th, i) => {
            let responsive = [...th.classList].filter(c => Object.keys(this.#breakpoints).includes)[0]

            this.table.querySelectorAll(`tbody tr:not(.child) td:nth-child(${i + 1})`).forEach((td) => {
                if (responsive)
                    td.classList.add(responsive)

                if (responsive && this.hiddenClasses().includes(responsive)) {
                    th.classList.add("rpc-hidden")
                    td.classList.add("rpc-hidden")
                } else {
                    th.classList.remove("rpc-hidden")
                    td.classList.remove("rpc-hidden")
                }
            });
        });
    }

    /**
     * 
     * @param {HTMLTableRowElement} child
     * @param {number} row 
     * @param {number} column
     * @returns {boolean}
     */
    #inChild(child, row, column) {
        let ul = child.querySelector("ul");
        for (let li of ul.getElementsByTagName("li")) {
            if (ul.dataset.row == row && li.dataset.column == column) {
                return true
            }
        }
        return false
    }

    /**
     * @param {HTMLTableCellElement} td
     * @returns {HTMLLIElement}
     */
    #createChildLi(td) {
        let li = document.createElement("li");
        li.dataset.column = td.cellIndex;

        li.appendChild(Object.assign(document.createElement("span"), {
            classList: ["rpc-child-title"],
            innerHTML: this.tableHeaders[td.cellIndex],
        }));

        li.appendChild(Object.assign(document.createElement("span"), {
            classList: ["rpc-child-value"],
        }));

        if (td.children.length > 0) {
            li.children[1].append(...td.children)
        } else {
            li.children[1].innerHTML = td.innerText
        }

        return li
    }

    #handleResize(window) {
        clearTimeout(this.#resizeTimeout);
        this.#resizeTimeout = setTimeout(this.render.bind(this), 0)
    }
}