let carrito = JSON.parse(localStorage.getItem("carrito"))
if (!carrito) {
    carrito = []
}
console.log(carrito);

const agregarProducto = (idProducto) => {
    let prod = carrito.find((prod) => prod.idProducto === idProducto.toString());
    if (prod) {
        prod.cantidad++;
        prod.cantidad = prod.cantidad.toString();
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
    actualizarCantidadDisplay(idProducto)
    actualizarTotal();
};

const quitarProducto = (idProducto) => {
    const existe = carrito.some(
        (prod) => {
            return prod.idProducto === idProducto.toString();
        }
    );
    if (existe) {
        let prod = carrito.find((prod) => prod.idProducto === idProducto.toString());
        if (+prod.cantidad > 1) {
            prod.cantidad--;
            prod.cantidad = prod.cantidad.toString();
        } else {
            carrito = carrito.filter((prod) => prod.idProducto !== idProducto.toString());
        }
        console.log(carrito);
        localStorage.setItem("carrito", JSON.stringify(carrito));
        actualizarCantidadDisplay(idProducto);
        actualizarTotal();
    }
};

function actualizarCantidadDisplay(idProducto) {
    const elementId = `prod-${idProducto}-cantidad`;
    let p = carrito.find((prod) => prod.idProducto === idProducto.toString());
    if (p) {
        document.getElementById(elementId).setAttribute("value", p.cantidad);
    } else {
        document.getElementById(elementId).setAttribute("value", "0");
    }
}

function actualizarTotal() {
    document.getElementById("carritoTotal").setAttribute("value", calcularTotal().toString());
}

function calcularTotal() {
    let totalCLP = 0;
    let totalUSD = 0;
    for (item of carrito) {
        let precioCantidad = item.cantidad * item.PrecioCLP;
        totalCLP = +totalCLP + precioCantidad;
    }
    console.log(totalCLP);
    return totalCLP;
}

document.addEventListener("DOMContentLoaded", () => {
    for (prod of carrito) {
        actualizarCantidadDisplay(+prod.idProducto)
    }
    actualizarTotal();
})

// let request = new XMLHttpRequest();
// request.open("GET", `/procesarPago`, true);
// request.send();
