import tkinter as tk
from tkinter import messagebox
import mysql.connector
from mysql.connector import Error
from tkinter import PhotoImage
from PIL import Image, ImageTk  # Este sirve para modificar la imagen de fondo
import datetime

# Conexión a la base de datos
def conectar():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='punto_de_venta',
            user='root',
            password='123456789'
        )
        if connection.is_connected():
            return connection
    except Error as e:
        messagebox.showerror("Error", f"Error al conectar a la base de datos: {e}")
        return None

# Registrar una venta
def registrar_venta(id_usuario, id_cliente, productos):
    try:
        connection = conectar()
        if connection:
            cursor = connection.cursor()

            # Calcular total
            total = 0
            for id_producto, cantidad in productos:
                cursor.execute("SELECT precio FROM productos WHERE id = %s", (id_producto,))
                precio = cursor.fetchone()
                if precio:
                    total += precio[0] * cantidad

            # Insertar en la tabla ventas
            query_venta = "INSERT INTO ventas (id_usuario, id_cliente, total) VALUES (%s, %s, %s)"
            cursor.execute(query_venta, (id_usuario, id_cliente, total))
            id_venta = cursor.lastrowid  # Obtener el ID de la venta recién creada

            # Insertar detalles de venta
            for id_producto, cantidad in productos:
                cursor.execute("SELECT precio FROM productos WHERE id = %s", (id_producto,))
                precio = cursor.fetchone()[0]
                query_detalle = """
                INSERT INTO detalles_venta (id_venta, id_producto, cantidad, precio_unitario)
                VALUES (%s, %s, %s, %s)
                """
                cursor.execute(query_detalle, (id_venta, id_producto, cantidad, precio))

                # Actualizar inventario
                query_inventario = "UPDATE productos SET cantidad_en_stock = cantidad_en_stock - %s WHERE id = %s"
                cursor.execute(query_inventario, (cantidad, id_producto))

            connection.commit()
            generar_ticket(id_venta, id_usuario, productos, total)
            messagebox.showinfo("Éxito", f"Venta registrada con éxito. Total: ${total:.2f}")
    except Error as e:
        messagebox.showerror("Error", f"Error al registrar la venta: {e}")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

# Generar ticket y guardarlo en un archivo de texto
def generar_ticket(id_venta, id_usuario, productos, total):
    try:
        connection = conectar()
        if connection:
            cursor = connection.cursor()

            # Obtener detalles del usuario
            cursor.execute("SELECT nombre FROM usuarios WHERE id = %s", (id_usuario,))
            cajero = cursor.fetchone()[0]

            # Formatear ticket
            ticket = "*" * 30 + "\n"
            ticket += " Taqueria Los Dos Plebes \n"
            ticket += f" Fecha y Hora: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} \n"
            ticket += f" Número de Ticket: {id_venta} \n"
            ticket += f" Cajero: {cajero} \n"
            ticket += "*" * 30 + "\n"
            ticket += " Productos Vendidos: \n"
            for id_producto, cantidad in productos:
                cursor.execute("SELECT nombre, precio FROM productos WHERE id = %s", (id_producto,))
                nombre_producto, precio = cursor.fetchone()
                ticket += f" {nombre_producto} - Cantidad: {cantidad} - Precio: ${precio:.2f} \n"
            ticket += "*" * 30 + "\n"
            ticket += f" Total a Pagar: ${total:.2f} \n"
            ticket += "*" * 30 + "\n"

            # Guardar el ticket en un archivo de texto
            with open(f'ticket_{id_venta}.txt', 'w') as file:
                file.write(ticket)

            # Notificar al usuario que se ha guardado el ticket
            messagebox.showinfo("Ticket Guardado", f"El ticket ha sido guardado como ticket_{id_venta}.txt")

    except Error as e:
        messagebox.showerror("Error", f"Error al generar el ticket: {e}")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

# Generar corte X (Ventas hasta el momento)
def generar_corte_x():
    try:
        connection = conectar()
        if connection:
            cursor = connection.cursor()

            query = """
            SELECT v.id, v.fecha_venta, u.nombre AS cajero, v.total
            FROM ventas v
            JOIN usuarios u ON v.id_usuario = u.id
            WHERE DATE(v.fecha_venta) = CURDATE()
            """
            cursor.execute(query)
            ventas = cursor.fetchall()

            report = "=== Corte X ===\n"
            total_dia = 0
            for venta in ventas:
                report += f"ID Venta: {venta[0]}, Fecha: {venta[1]}, Cajero: {venta[2]}, Total: ${venta[3]:.2f}\n"
                total_dia += venta[3]
            report += f"Total vendido hasta el momento: ${total_dia:.2f}"
            messagebox.showinfo("Corte X", report)
    except Error as e:
        messagebox.showerror("Error", f"Error al generar el corte X: {e}")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

# Generar corte Z (Ventas del día y cierre)
def generar_corte_z():
    try:
        connection = conectar()
        if connection:
            cursor = connection.cursor()

            query = """
            SELECT v.id, v.fecha_venta, u.nombre AS cajero, v.total
            FROM ventas v
            JOIN usuarios u ON v.id_usuario = u.id
            WHERE DATE(v.fecha_venta) = CURDATE()
            """
            cursor.execute(query)
            ventas = cursor.fetchall()

            report = "=== Corte Z ===\n"
            total_dia = 0
            for venta in ventas:
                report += f"ID Venta: {venta[0]}, Fecha: {venta[1]}, Cajero: {venta[2]}, Total: ${venta[3]:.2f}\n"
                total_dia += venta[3]
            report += f"Total vendido en el día (Corte Z): ${total_dia:.2f}\n"
            messagebox.showinfo("Corte Z", report)

    except Error as e:
        messagebox.showerror("Error", f"Error al generar el corte Z: {e}")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

# Ventana para registrar ventas
def abrir_registrar_venta():
    ventana_venta = tk.Toplevel(root)
    ventana_venta.title("Registrar Venta")
    ventana_venta.configure(bg='#f0f8ff')

    tk.Label(ventana_venta, text="ID del Cajero:", bg='#f0f8ff', font=("Arial", 12)).pack(pady=5)
    id_usuario_entry = tk.Entry(ventana_venta, font=("Arial", 12), bd=2, relief="groove")
    id_usuario_entry.pack(pady=5)

    tk.Label(ventana_venta, text="ID del Cliente (dejar vacío si es cliente general):", bg='#f0f8ff', font=("Arial", 12)).pack(pady=5)
    id_cliente_entry = tk.Entry(ventana_venta, font=("Arial", 12), bd=2, relief="groove")
    id_cliente_entry.pack(pady=5)

    productos_entry = tk.Text(ventana_venta, height=5, width=40, font=("Arial", 12), bd=2, relief="groove")
    productos_entry.pack(pady=10)
    tk.Label(ventana_venta, text="Ingrese los productos en el formato 'ID, Cantidad' por línea:", bg='#f0f8ff', font=("Arial", 12)).pack(pady=5)

    def registrar_venta_gui():
        id_usuario = id_usuario_entry.get()
        id_cliente = id_cliente_entry.get() or None
        productos = []
        
        for line in productos_entry.get("1.0", tk.END).strip().splitlines():
            if line:
                id_producto, cantidad = map(int, line.split(","))
                productos.append((id_producto, cantidad))

        registrar_venta(int(id_usuario), id_cliente, productos)
        ventana_venta.destroy()

    tk.Button(ventana_venta, text="Registrar Venta", command=registrar_venta_gui, bg='#FFD700', fg='black', font=("Arial", 12), relief="raised", width=20).pack(pady=10)

# Configuración de la ventana principal
root = tk.Tk()
root.title("Sistema de Punto de Venta")

# Imagen de fondo
imagen_fondo = Image.open("Fondo Blanco.jpg")
imagen_fondo = imagen_fondo.resize((1600, 1050), Image.LANCZOS)
imagen_fondo_tk = ImageTk.PhotoImage(imagen_fondo)
fondo_label = tk.Label(root, image=imagen_fondo_tk)
fondo_label.place(x=0, y=0, relwidth=1, relheight=1)

# Logo
logo_img = Image.open("logo.png")
logo_img = logo_img.resize((200, 200), Image.LANCZOS)
logo_tk = ImageTk.PhotoImage(logo_img)
logo_label = tk.Label(root, image=logo_tk, bg="#FFFFFF")
logo_label.place(x=670, y=255)


# Botones principales
tk.Button(root, text="Registrar Venta", command=abrir_registrar_venta, bg='#FFD700', fg='black', font=("Arial", 16), relief="raised", width=20).pack(pady=10)
tk.Button(root, text="Corte X", command=generar_corte_x, bg='#FFD700', fg='black', font=("Arial", 16), relief="raised", width=20).pack(pady=10)
tk.Button(root, text="Corte Z", command=generar_corte_z, bg='#FFD700', fg='black', font=("Arial", 16), relief="raised", width=20).pack(pady=10)

root.mainloop()
