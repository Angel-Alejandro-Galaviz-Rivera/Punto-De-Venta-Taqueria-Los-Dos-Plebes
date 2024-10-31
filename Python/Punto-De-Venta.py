import tkinter as tk
from tkinter import messagebox
import mysql.connector
from mysql.connector import Error
from tkinter import PhotoImage
import datetime

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Conexión a la base de datos
def conectar():
    try:    
        connection = mysql.connector.connect(
            host='localhost',
            database='punto_de_venta',
            user='root',
            password='Root'
        )
        if connection.is_connected():
            return connection
    except Error as e:
        messagebox.showerror("Error", f"Error al conectar a la base de datos: {e}")
        return None

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

    # Listbox para seleccionar productos
    tk.Label(ventana_venta, text="Seleccione los productos:", bg='#f0f8ff', font=("Arial", 12)).pack(pady=5)
    productos_listbox = tk.Listbox(ventana_venta, height=10, width=50, font=("Arial", 12), bd=2, relief="groove", selectmode=tk.MULTIPLE)
    productos_listbox.pack(pady=10)

    # Llenar el Listbox con productos de la base de datos
    try:
        connection = conectar()
        if connection:
            cursor = connection.cursor()
            cursor.execute("SELECT id, nombre FROM productos")
            productos = cursor.fetchall()
            for producto in productos:
                productos_listbox.insert(tk.END, f"{producto[0]} - {producto[1]}")
    except Error as e:
        messagebox.showerror("Error", f"Error al cargar productos: {e}")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

    tk.Label(ventana_venta, text="Ingrese la cantidad para cada producto (separados por comas):", bg='#f0f8ff', font=("Arial", 12)).pack(pady=5)
    cantidades_entry = tk.Entry(ventana_venta, font=("Arial", 12), bd=2, relief="groove")
    cantidades_entry.pack(pady=5)

    def registrar_venta_gui():
        id_usuario = id_usuario_entry.get()
        id_cliente = id_cliente_entry.get() or None
        
        # Obtener productos seleccionados
        productos_seleccionados = productos_listbox.curselection()
        productos = []

        # Verificar que se han seleccionado productos
        if not productos_seleccionados:
            messagebox.showwarning("Advertencia", "Debe seleccionar al menos un producto.")
            return
        
        # Obtener cantidades
        cantidades = cantidades_entry.get().split(",")
        if len(cantidades) != len(productos_seleccionados):
            messagebox.showwarning("Advertencia", "El número de cantidades debe coincidir con el número de productos seleccionados.")
            return

        for index in productos_seleccionados:
            # Obtener el ID del producto seleccionado
            producto_info = productos_listbox.get(index)
            id_producto = int(producto_info.split(" - ")[0])  # Obtener solo el ID
            try:
                cantidad = int(cantidades[index].strip())  # Obtener la cantidad correspondiente
                productos.append((id_producto, cantidad))
            except ValueError:
                messagebox.showwarning("Advertencia", f"La cantidad para el producto '{producto_info}' no es válida.")
                return

        registrar_venta(int(id_usuario), id_cliente, productos)
        ventana_venta.destroy()

    tk.Button(ventana_venta, text="Registrar Venta", command=registrar_venta_gui, bg='#4CAF50', fg='white', font=("Arial", 12), relief="raised", width=20).pack(pady=10)


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

# Generar ticket y guardarlo en un archivo PDF
def generar_ticket(id_venta, id_usuario, productos, total):
    try:
        connection = conectar()
        if connection:
            cursor = connection.cursor()

            # Obtener detalles del usuario
            cursor.execute("SELECT nombre FROM usuarios WHERE id = %s", (id_usuario,))
            cajero = cursor.fetchone()[0]

            # Crear el archivo PDF
            pdf_file_name = f'ticket_{id_venta}.pdf'
            c = canvas.Canvas(pdf_file_name, pagesize=letter)
            width, height = letter

            # Formatear ticket en PDF
            c.drawString(100, height - 50, "Taqueria Los Dos Plebes")
            c.drawString(100, height - 80, f"Fecha y Hora: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            c.drawString(100, height - 100, f"Número de Ticket: {id_venta}")
            c.drawString(100, height - 120, f"Cajero: {cajero}")
            c.drawString(100, height - 150, "Productos Vendidos:")

            # Añadir productos al PDF
            y_position = height - 180
            for id_producto, cantidad in productos:
                cursor.execute("SELECT nombre, precio FROM productos WHERE id = %s", (id_producto,))
                nombre_producto, precio = cursor.fetchone()
                c.drawString(100, y_position, f"{nombre_producto} - Cantidad: {cantidad} - Precio: ${precio:.2f}")
                y_position -= 20  # Espacio entre líneas

            c.drawString(100, y_position, f"Total a Pagar: ${total:.2f}")
            c.save()  # Guardar el PDF

            # Notificar al usuario que se ha guardado el ticket
            messagebox.showinfo("Ticket Guardado", f"El ticket ha sido guardado como {pdf_file_name}")

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

# Consultar el inventario
def consultar_inventario():
    try:
        connection = conectar()
        if connection:
            cursor = connection.cursor()

            # Obtener todos los productos y sus cantidades en stock
            cursor.execute("SELECT nombre, cantidad_en_stock FROM productos")
            inventario = cursor.fetchall()

            # Crear una nueva ventana para mostrar el inventario
            ventana_inventario = tk.Toplevel(root)
            ventana_inventario.title("Consultar Inventario")
            ventana_inventario.configure(bg='#f0f8ff')

            # Crear una etiqueta para el título
            tk.Label(ventana_inventario, text="Inventario Actual", font=("Arial", 16, "bold"), bg='#f0f8ff').pack(pady=10)

            # Mostrar el inventario en un Text widget
            inventario_text = tk.Text(ventana_inventario, height=15, width=50, font=("Arial", 12), bd=2, relief="groove")
            inventario_text.pack(pady=10)

            # Agregar los productos al Text widget
            for nombre, cantidad in inventario:
                inventario_text.insert(tk.END, f"{nombre}: {cantidad}\n")

            inventario_text.config(state=tk.DISABLED)  # Deshabilitar la edición del Text widget

    except Error as e:
        messagebox.showerror("Error", f"Error al consultar el inventario: {e}")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

# Configuración de la ventana principal
root = tk.Tk()
root.title("Sistema de Punto de Venta")

# Establecer la imagen de fondo
background_image = PhotoImage(file="Fondo.png")
background_label = tk.Label(root, image=background_image)
background_label.place(x=0, y=0, relwidth=1, relheight=1)

# Estilo
root.configure(bg='#f0f8ff')
header = tk.Label(root, text="Sistema de Punto de Venta", font=("Arial", 24, "bold"), bg='#4CAF50', fg='white')
header.pack(pady=20)

# Logo
logo = PhotoImage(file="logo.png")
logo = logo.subsample(4, 4)  # Reducir el tamaño del logo
logo_label = tk.Label(root, image=logo, bg='#f0f8ff')
logo_label.pack(pady=10)

# Botones de opciones
tk.Button(root, text="Registrar Venta", command=abrir_registrar_venta, bg='#4CAF50', fg='white', font=("Arial", 12), relief="raised", width=20).pack(pady=10)
tk.Button(root, text="Generar Corte X", command=generar_corte_x, bg='#2196F3', fg='white', font=("Arial", 12), relief="raised", width=20).pack(pady=10)
tk.Button(root, text="Generar Corte Z", command=generar_corte_z, bg='#F44336', fg='white', font=("Arial", 12), relief="raised", width=20).pack(pady=10)
tk.Button(root, text="Consultar Inventario", command=consultar_inventario, bg='#FFC107', fg='black', font=("Arial", 12), relief="raised", width=20).pack(pady=10)  # New button for inventory

# Botón de salir
tk.Button(root, text="Salir", command=root.quit, bg='#FF5733', fg='white', font=("Arial", 12), relief="raised", width=20).pack(pady=10)

# Iniciar la ventana principal
root.mainloop()