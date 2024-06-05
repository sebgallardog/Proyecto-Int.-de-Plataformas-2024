let carrito = JSON.parse(localStorage.getItem("carrito"))
if (!carrito) {
    carrito = []
};
console.log(carrito);

const agregarProducto = (idProducto) => {
    const existe = carrito.some(
        (prod) => {
            return prod.idProducto == idProducto;
        }
    );
    if (existe) {
        const prod = carrito.map((prod) => {
            if (prod.idProducto == idProducto) {
                prod.cantidad++;
            }
        });
    } else {
        let columns = ["Categoria", "Marca", "PrecioCLP", "PrecioUSD", "Producto", "Stock", "idProducto"];
        let item = {}
        const prodtable = document.getElementById(`prod-${idProducto}`);
        columns.forEach((col) => {
            let prodtd = prodtable.getElementsByClassName(col);
            item[col] = prodtd[0].innerHTML;
        })
        item["cantidad"] = "1";
        carrito.push(item);
    }
    console.log(carrito);
    localStorage.setItem("carrito", JSON.stringify(carrito));
};