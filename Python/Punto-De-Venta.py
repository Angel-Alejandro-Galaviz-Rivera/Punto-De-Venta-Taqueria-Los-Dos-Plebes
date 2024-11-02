# Librerias
import tkinter as tk
from tkinter import messagebox
import mysql.connector
from mysql.connector import Error
from tkinter import PhotoImage
import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import pandas as pd
from tkinter import simpledialog

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
    
# Variable global para controlar el estado de las ventas
ventas_permitidas = True

# Ventana para registrar ventas
def abrir_registrar_venta():
    ventana_venta = tk.Toplevel(root)
    ventana_venta.title("Registrar Venta")
    ventana_venta.configure(bg='#FF0000')  # Cambiado a rojo

    tk.Label(ventana_venta, text="ID del Cajero:", bg='#FF0000', font=("Arial", 12)).pack(pady=5)
    id_usuario_entry = tk.Entry(ventana_venta, font=("Arial", 12), bd=2, relief="groove")
    id_usuario_entry.pack(pady=5)

    tk.Label(ventana_venta, text="ID del Cliente (dejar vacío si es cliente general):", bg='#FF0000', font=("Arial", 12)).pack(pady=5)
    id_cliente_entry = tk.Entry(ventana_venta, font=("Arial", 12), bd=2, relief="groove")
    id_cliente_entry.pack(pady=5)

    # Listbox para seleccionar productos
    tk.Label(ventana_venta, text="Seleccione los productos:", bg='#FF0000', font=("Arial", 12)).pack(pady=5)
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

    tk.Label(ventana_venta, text="Ingrese la cantidad para cada producto (separados por comas):", bg='#FF0000', font=("Arial", 12)).pack(pady=5)
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

    tk.Button(ventana_venta, text="Registrar Venta", command=registrar_venta_gui, bg='#FF0000', fg='white', font=("Arial", 12), relief="raised", width=20).pack(pady=10)

# Función para registrar una venta
def registrar_venta(id_usuario, id_cliente, productos):
    global ventas_permitidas  # Hacer referencia a la variable global

    # Verificar si las ventas están permitidas
    if not ventas_permitidas:
        messagebox.showwarning("Advertencia", "No se pueden realizar ventas después de cerrar caja.")
        return

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

# Función para confirmar y cerrar la caja
def confirmar_cierre_caja():
    respuesta = messagebox.askyesno("Confirmar Cierre", "¿Estás seguro de que deseas cerrar la caja?")
    if respuesta:
        generar_corte_z()

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

            # Agregar logo al PDF (especifica la ruta correcta de tu logo)
            logo_path = "logo.png"  # Cambia esto a la ubicación de tu logo
            c.drawImage(logo_path, 100, height - 150, width=200, height=100)  # Ajusta el tamaño y posición según sea necesario

            # Estilo del ticket
            c.setFont("Helvetica-Bold", 16)
            c.drawString(100, height - 270, "Taqueria Los Dos Plebes")
            c.setFont("Helvetica", 10)

            # Línea separadora
            c.line(50, height - 280, width - 50, height - 280)

            c.drawString(100, height - 300, f"Fecha y Hora: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            c.drawString(100, height - 320, f"Número de Ticket: {id_venta}")
            c.drawString(100, height - 340, f"Cajero: {cajero}")

            # Línea separadora
            c.line(50, height - 350, width - 50, height - 350)
            c.drawString(100, height - 370, "Productos Vendidos:")
            c.line(50, height - 380, width - 50, height - 380)  # Línea horizontal

            # Añadir productos al PDF
            y_position = height - 400
            for id_producto, cantidad in productos:
                cursor.execute("SELECT nombre, precio FROM productos WHERE id = %s", (id_producto,))
                nombre_producto, precio = cursor.fetchone()
                c.drawString(100, y_position, f"{nombre_producto} - Cantidad: {cantidad} - Precio: ${precio:.2f}")
                y_position -= 20  # Espacio entre líneas

            # Línea final y total
            c.line(50, y_position, width - 50, y_position)  # Línea horizontal para el total
            y_position -= 10  # Espacio para el total
            c.setFont("Helvetica-Bold", 12)
            c.drawString(100, y_position, f"Total a Pagar: ${total:.2f}")
            c.setFont("Helvetica", 10)

            # Otra línea separadora
            c.line(50, y_position - 20, width - 50, y_position - 20)

            # Nota legal sobre la retención de tickets
            c.drawString(100, y_position - 40, "Nota: Este ticket es un comprobante de compra.")
            c.drawString(100, y_position - 60, "Guarde este ticket para futuras reclamaciones.")

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

            mostrar_corte_x(report)  # Llama a la función de ventana personalizada
    except Error as e:
        messagebox.showerror("Error", f"Error al generar el corte X: {e}")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

def mostrar_corte_x(report):
    # Crear una ventana personalizada
    ventana_corte = tk.Toplevel(root)
    ventana_corte.title("Corte X")
    ventana_corte.configure(bg='#FF0000')  # Color de fondo rojo

    # Etiqueta para mostrar el reporte
    label = tk.Label(ventana_corte, text=report, bg='#FF0000', fg='white', font=("Arial", 12))
    label.pack(padx=20, pady=20)

    # Botón para cerrar con color blanco y texto rojo
    tk.Button(ventana_corte, text="Cerrar", command=ventana_corte.destroy, bg='white', fg='#FF0000', font=("Arial", 12)).pack(pady=10)

# Generar corte Z (Ventas del día y cierre)
def generar_corte_z():
    global ventas_permitidas  # Hacer referencia a la variable global

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

            # Bloquear ventas al generar el corte Z
            ventas_permitidas = False

            mostrar_corte_z(report)  # Llama a la función de ventana personalizada

    except Error as e:
        messagebox.showerror("Error", f"Error al generar el corte Z: {e}")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

# Mostrar el corte Z
def mostrar_corte_z(report):
    # Crear una ventana personalizada
    ventana_corte = tk.Toplevel(root)
    ventana_corte.title("Corte Z")
    ventana_corte.configure(bg='#FF0000')  # Color de fondo rojo

    # Etiqueta para mostrar el reporte
    label = tk.Label(ventana_corte, text=report, bg='#FF0000', fg='white', font=("Arial", 12))
    label.pack(padx=20, pady=20)

    # Botón para cerrar con color blanco y texto rojo
    tk.Button(ventana_corte, text="Cerrar", command=ventana_corte.destroy, bg='white', fg='#FF0000', font=("Arial", 12)).pack(pady=10)

# Función para abrir la caja nuevamente
def abrir_caja():
    global ventas_permitidas  # Hacer referencia a la variable global
    respuesta = messagebox.askyesno("Confirmar Apertura", "¿Estás seguro de que deseas abrir la caja para realizar ventas?")
    if respuesta:
        ventas_permitidas = True
        messagebox.showinfo("Apertura de Caja", "La caja se ha abierto y las ventas están permitidas.")

# Consultar el inventario
def consultar_inventario():
    def buscar_producto_por_codigo_barras():
        codigo_barras = codigo_barras_entry.get()
        try:
            connection = conectar()
            if connection:
                cursor = connection.cursor()

                # Consultar producto por código de barras
                cursor.execute("SELECT nombre, cantidad_en_stock FROM productos WHERE codigo_barras = %s", (codigo_barras,))
                producto = cursor.fetchone()

                # Limpiar el Text widget antes de mostrar el resultado
                inventario_text.config(state=tk.NORMAL)
                inventario_text.delete(1.0, tk.END)

                if producto:
                    nombre, cantidad = producto
                    inventario_text.insert(tk.END, f"{nombre}: {cantidad}\n")
                else:
                    inventario_text.insert(tk.END, "Producto no encontrado.\n")

                inventario_text.config(state=tk.DISABLED)  # Deshabilitar la edición del Text widget

        except Error as e:
            messagebox.showerror("Error", f"Error al buscar el producto: {e}")
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()

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
            ventana_inventario.configure(bg='#FF0000')  # Color de fondo rojo

            # Crear una etiqueta para el título
            tk.Label(ventana_inventario, text="Inventario Actual", font=("Arial", 16, "bold"), bg='#FF0000', fg='white').pack(pady=10)

            # Crear un campo de entrada para el código de barras
            tk.Label(ventana_inventario, text="Buscar por Código de Barras:", font=("Arial", 12), bg='#FF0000', fg='white').pack(pady=5)
            codigo_barras_entry = tk.Entry(ventana_inventario, font=("Arial", 12))
            codigo_barras_entry.pack(pady=5)

            # Botón para buscar el producto con color blanco y texto rojo
            buscar_button = tk.Button(ventana_inventario, text="Buscar Producto", font=("Arial", 12), command=buscar_producto_por_codigo_barras, bg='white', fg='#FF0000')
            buscar_button.pack(pady=10)

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

# Generar reporte ventas
def generar_reporte_ventas():
    # Pedir al usuario que ingrese una fecha
    fecha = simpledialog.askstring("Fecha de Ventas", "Ingrese la fecha (YYYY-MM-DD):")
    if not fecha:
        return  # Salir si no se ingresa una fecha

    try:
        connection = conectar()
        if connection:
            cursor = connection.cursor()

            # Consultar ventas para la fecha ingresada
            query = """
            SELECT v.id, v.fecha_venta, u.nombre AS cajero, v.total
            FROM ventas v
            JOIN usuarios u ON v.id_usuario = u.id
            WHERE DATE(v.fecha_venta) = %s
            """
            cursor.execute(query, (fecha,))
            ventas = cursor.fetchall()

            # Verificar si hay ventas
            if not ventas:
                messagebox.showinfo("Reporte de Ventas", "No se encontraron ventas para la fecha proporcionada.")
                return

            # Crear un DataFrame de pandas
            df = pd.DataFrame(ventas, columns=["ID Venta", "Fecha Venta", "Cajero", "Total"])

            # Guardar el DataFrame en un archivo Excel
            nombre_archivo = f"reporte_ventas_{fecha}.xlsx"
            df.to_excel(nombre_archivo, index=False)

            messagebox.showinfo("Éxito", f"Reporte de ventas guardado como {nombre_archivo}.")
    except Error as e:
        messagebox.showerror("Error", f"Error al generar el reporte de ventas: {e}")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

# Agregar producto
def agregar_producto():
    def guardar_producto():
        nombre = nombre_entry.get()
        descripcion = descripcion_entry.get()
        precio = precio_entry.get()
        cantidad_en_stock = cantidad_entry.get()
        categoria = categoria_entry.get()
        codigo_barras = codigo_barras_entry.get()

        try:
            connection = conectar()
            if connection:
                cursor = connection.cursor()

                # Insertar el nuevo producto en la base de datos
                query = """
                INSERT INTO productos (nombre, descripcion, precio, cantidad_en_stock, categoria, codigo_barras)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                cursor.execute(query, (nombre, descripcion, float(precio), int(cantidad_en_stock), categoria, codigo_barras))
                connection.commit()

                messagebox.showinfo("Éxito", "Producto agregado con éxito.")
                ventana_agregar.destroy()  # Cerrar la ventana después de guardar
        except Error as e:
            messagebox.showerror("Error", f"Error al agregar el producto: {e}")
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()

    # Crear una ventana para agregar un nuevo producto
    ventana_agregar = tk.Toplevel(root)
    ventana_agregar.title("Agregar Producto")
    ventana_agregar.configure(bg='#f0f8ff')

    tk.Label(ventana_agregar, text="Nombre:", bg='#f0f8ff', font=("Arial", 12)).pack(pady=5)
    nombre_entry = tk.Entry(ventana_agregar, font=("Arial", 12), bd=2, relief="groove")
    nombre_entry.pack(pady=5)

    tk.Label(ventana_agregar, text="Descripción:", bg='#f0f8ff', font=("Arial", 12)).pack(pady=5)
    descripcion_entry = tk.Entry(ventana_agregar, font=("Arial", 12), bd=2, relief="groove")
    descripcion_entry.pack(pady=5)

    tk.Label(ventana_agregar, text="Precio:", bg='#f0f8ff', font=("Arial", 12)).pack(pady=5)
    precio_entry = tk.Entry(ventana_agregar, font=("Arial", 12), bd=2, relief="groove")
    precio_entry.pack(pady=5)

    tk.Label(ventana_agregar, text="Cantidad en Stock:", bg='#f0f8ff', font=("Arial", 12)).pack(pady=5)
    cantidad_entry = tk.Entry(ventana_agregar, font=("Arial", 12), bd=2, relief="groove")
    cantidad_entry.pack(pady=5)

    tk.Label(ventana_agregar, text="Categoría:", bg='#f0f8ff', font=("Arial", 12)).pack(pady=5)
    categoria_entry = tk.Entry(ventana_agregar, font=("Arial", 12), bd=2, relief="groove")
    categoria_entry.pack(pady=5)

    tk.Label(ventana_agregar, text="Código de Barras:", bg='#f0f8ff', font=("Arial", 12)).pack(pady=5)
    codigo_barras_entry = tk.Entry(ventana_agregar, font=("Arial", 12), bd=2, relief="groove")
    codigo_barras_entry.pack(pady=5)

    tk.Button(ventana_agregar, text="Guardar Producto", command=guardar_producto, bg='#FF5733', fg='white', font=("Arial", 12)).pack(pady=10)

# Configuración de la ventana principal
root = tk.Tk()
root.title("Sistema de Punto de Venta")

# Establecer la imagen de fondo
background_image = PhotoImage(file="Fondo.png")
background_label = tk.Label(root, image=background_image)
background_label.place(x=0, y=0, relwidth=1, relheight=1)

# Estilo
root.configure(bg='#f0f8ff')  # Color de fondo de la ventana principal
header = tk.Label(root, text="Taqueria los dos plebes", font=("Arial", 24, "bold"), bg='#FF0000', fg='white')  # Cambiar a rojo
header.pack(pady=20)

# Logo
logo = PhotoImage(file="logo.png")
logo = logo.subsample(4, 4)  # Reducir el tamaño del logo
logo_label = tk.Label(root, image=logo, bg='#f0f8ff')
logo_label.pack(pady=10)

# Botones de opciones 
tk.Button(root, text="Abrir Caja", command=abrir_caja, bg='#FF0000', fg='white', font=("Arial", 12), relief="raised", width=20).pack(pady=10)  # Rojo
tk.Button(root, text="Registrar Venta", command=abrir_registrar_venta, bg='#FF0000', fg='white', font=("Arial", 12), relief="raised", width=20).pack(pady=10)  # Rojo
tk.Button(root, text="Agregar Producto", command=agregar_producto, bg='#FF0000', fg='white', font=("Arial", 12), relief="raised", width=20).pack(pady=10)
tk.Button(root, text="Consultar Inventario", command=consultar_inventario, bg='#FF0000', fg='white', font=("Arial", 12), relief="raised", width=20).pack(pady=10)  # Rojo
tk.Button(root, text="Generar Reporte de Ventas", command=generar_reporte_ventas, bg='#FF0000', fg='white', font=("Arial", 12), relief="raised", width=20).pack(pady=10)  # Rojo
tk.Button(root, text="Generar Corte X", command=generar_corte_x, bg='#FF0000', fg='white', font=("Arial", 12), relief="raised", width=20).pack(pady=10)  # Rojo
tk.Button(root, text="Generar Corte Z", command=confirmar_cierre_caja, bg='#FF0000', fg='white', font=("Arial", 12), relief="raised", width=20).pack(pady=10)  # Rojo
tk.Button(root, text="Salir", command=root.quit, bg='#FF0000', fg='white', font=("Arial", 12), relief="raised", width=20).pack(pady=10)  # Rojo

# Iniciar la ventana principal
root.mainloop()