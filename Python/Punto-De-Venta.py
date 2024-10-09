import mysql.connector
from mysql.connector import Error
from datetime import datetime

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
        print(f"Error al conectar a la base de datos: {e}")
        return None

# Registrar una venta
def registrar_venta(id_usuario, id_cliente, productos):
    """
    id_usuario: ID del cajero que está realizando la venta
    id_cliente: ID del cliente (puede ser NULL si es una venta sin cliente registrado)
    productos: Lista de tuplas con productos [(id_producto, cantidad), ...]
    """
    try:
        connection = conectar()
        if connection:
            cursor = connection.cursor()
            
            # Calcular total
            total = 0
            for id_producto, cantidad in productos:
                cursor.execute("SELECT precio FROM productos WHERE id = %s", (id_producto,))
                precio = cursor.fetchone()[0]
                total += precio * cantidad

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
            print(f"Venta registrada con éxito. Total: ${total}")
    except Error as e:
        print(f"Error al registrar la venta: {e}")
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
            
            print("=== Corte X ===")
            total_dia = 0
            for venta in ventas:
                print(f"ID Venta: {venta[0]}, Fecha: {venta[1]}, Cajero: {venta[2]}, Total: ${venta[3]}")
                total_dia += venta[3]
            print(f"Total vendido en el día (Corte X): ${total_dia}")
    except Error as e:
        print(f"Error al generar el corte X: {e}")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

# Generar corte Z (Ventas del día y reinicio)
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
            
            print("=== Corte Z ===")
            total_dia = 0
            for venta in ventas:
                print(f"ID Venta: {venta[0]}, Fecha: {venta[1]}, Cajero: {venta[2]}, Total: ${venta[3]}")
                total_dia += venta[3]
            print(f"Total vendido en el día (Corte Z): ${total_dia}")
            
            # Aquí puedes agregar código para marcar el final del día, reiniciar totales, etc.
            # Por ejemplo, podrías insertar un registro de cierre en una tabla de "cierres de caja".
    except Error as e:
        print(f"Error al generar el corte Z: {e}")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

# Menú principal del sistema
def menu():
    while True:
        print("\n=== Menú Punto de Venta ===")
        print("1. Registrar una venta")
        print("2. Generar corte X")
        print("3. Generar corte Z")
        print("4. Salir")
        
        opcion = input("Elige una opción: ")

        if opcion == '1':
            id_usuario = int(input("ID del cajero: "))
            id_cliente = input("ID del cliente (o presiona Enter si es cliente general): ")
            if not id_cliente:
                id_cliente = None

            productos = []
            while True:
                id_producto = int(input("ID del producto (0 para terminar): "))
                if id_producto == 0:
                    break
                cantidad = int(input("Cantidad: "))
                productos.append((id_producto, cantidad))

            registrar_venta(id_usuario, id_cliente, productos)

        elif opcion == '2':
            generar_corte_x()

        elif opcion == '3':
            generar_corte_z()

        elif opcion == '4':
            print("Saliendo del sistema...")
            break

        else:
            print("Opción no válida. Inténtalo de nuevo.")

# Ejecutar el menú
if __name__ == '__main__':
    menu()
