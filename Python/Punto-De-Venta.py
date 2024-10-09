import tkinter as tk
from tkinter import messagebox
import mysql.connector
from mysql.connector import Error

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
            messagebox.showinfo("Éxito", f"Venta registrada con éxito. Total: ${total:.2f}")
    except Error as e:
        messagebox.showerror("Error", f"Error al registrar la venta: {e}")
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

            # Aquí puedes agregar código para marcar el final del día, reiniciar totales, etc.
            # Por ejemplo, insertar un registro de cierre en una tabla de "cierres de caja".
            messagebox.showinfo("Corte Z", report)

            # Código adicional para reiniciar totales puede ir aquí.
            # Por ejemplo: cursor.execute("INSERT INTO cierres_caja (fecha, total) VALUES (CURDATE(), %s)", (total_dia,))
            # connection.commit()

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
    ventana_venta.configure(bg='#f2f2f2')

    tk.Label(ventana_venta, text="ID del Cajero:", bg='#f2f2f2').pack(pady=5)
    id_usuario_entry = tk.Entry(ventana_venta)
    id_usuario_entry.pack(pady=5)

    tk.Label(ventana_venta, text="ID del Cliente (dejar vacío si es cliente general):", bg='#f2f2f2').pack(pady=5)
    id_cliente_entry = tk.Entry(ventana_venta)
    id_cliente_entry.pack(pady=5)

    productos_entry = tk.Text(ventana_venta, height=5, width=40)
    productos_entry.pack(pady=10)
    tk.Label(ventana_venta, text="Ingrese los productos en el formato 'ID, Cantidad' por línea:", bg='#f2f2f2').pack(pady=5)

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

    tk.Button(ventana_venta, text="Registrar Venta", command=registrar_venta_gui, bg='#4CAF50', fg='white').pack(pady=10)

# Configuración de la ventana principal
root = tk.Tk()
root.title("Sistema de Punto de Venta")

# Estilo
root.configure(bg='#f2f2f2')
header = tk.Label(root, text="Sistema de Punto de Venta", font=("Arial", 24, "bold"), bg='#4CAF50', fg='white')
header.pack(pady=10, fill=tk.X)

# Frame para los botones
frame = tk.Frame(root, bg='#f2f2f2')
frame.pack(pady=20)

# Botones del menú
btn_registrar_venta = tk.Button(frame, text="Registrar Venta", command=abrir_registrar_venta, bg='#4CAF50', fg='white', font=("Arial", 14), width=20)
btn_registrar_venta.pack(pady=10)

btn_corte_x = tk.Button(frame, text="Generar Corte X", command=generar_corte_x, bg='#2196F3', fg='white', font=("Arial", 14), width=20)
btn_corte_x.pack(pady=10)

btn_corte_z = tk.Button(frame, text="Generar Corte Z", command=generar_corte_z, bg='#FF9800', fg='white', font=("Arial", 14), width=20)
btn_corte_z.pack(pady=10)

btn_salir = tk.Button(frame, text="Salir", command=root.quit, bg='#f44336', fg='white', font=("Arial", 14), width=20)
btn_salir.pack(pady=10)

# Ejecutar la interfaz gráfica
root.mainloop()
