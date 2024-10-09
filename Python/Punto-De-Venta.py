import mysql.connector
from mysql.connector import Error

# Conexión a la base de datos
def conectar():
    try:
        connection = mysql.connector.connect(
            host='localhost',  # Cambia esto si usas otro host
            database='punto_de_venta',  # Nombre de tu base de datos
            user='root',  # Cambia al usuario de tu base de datos
            password='123456789'  # Cambia a la contraseña de tu base de datos
        )
        if connection.is_connected():
            print("Conexión exitosa a la base de datos")
            return connection
    except Error as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None

# Función para insertar un producto en la base de datos
def insertar_producto(nombre, descripcion, precio, cantidad, categoria, codigo_barras):
    try:
        connection = conectar()
        if connection:
            cursor = connection.cursor()
            query = """
            INSERT INTO productos (nombre, descripcion, precio, cantidad_en_stock, categoria, codigo_barras)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            data = (nombre, descripcion, precio, cantidad, categoria, codigo_barras)
            cursor.execute(query, data)
            connection.commit()
            print(f"Producto {nombre} insertado exitosamente.")
    except Error as e:
        print(f"Error al insertar producto: {e}")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

# Función para listar productos
def listar_productos():
    try:
        connection = conectar()
        if connection:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM productos")
            resultados = cursor.fetchall()
            print("Listado de productos:")
            for producto in resultados:
                print(producto)
    except Error as e:
        print(f"Error al listar productos: {e}")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

# Función para actualizar el stock de un producto
def actualizar_stock(id_producto, nueva_cantidad):
    try:
        connection = conectar()
        if connection:
            cursor = connection.cursor()
            query = "UPDATE productos SET cantidad_en_stock = %s WHERE id = %s"
            data = (nueva_cantidad, id_producto)
            cursor.execute(query, data)
            connection.commit()
            print(f"Producto con ID {id_producto} actualizado exitosamente.")
    except Error as e:
        print(f"Error al actualizar stock: {e}")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

# Función para eliminar un producto
def eliminar_producto(id_producto):
    try:
        connection = conectar()
        if connection:
            cursor = connection.cursor()
            query = "DELETE FROM productos WHERE id = %s"
            cursor.execute(query, (id_producto,))
            connection.commit()
            print(f"Producto con ID {id_producto} eliminado exitosamente.")
    except Error as e:
        print(f"Error al eliminar producto: {e}")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

# Menú principal
def menu():
    while True:
        print("\n=== Menú Punto de Venta ===")
        print("1. Insertar producto")
        print("2. Listar productos")
        print("3. Actualizar stock")
        print("4. Eliminar producto")
        print("5. Salir")
        
        opcion = input("Elige una opción: ")

        if opcion == '1':
            nombre = input("Nombre del producto: ")
            descripcion = input("Descripción del producto: ")
            precio = float(input("Precio del producto: "))
            cantidad = int(input("Cantidad en stock: "))
            categoria = input("Categoría del producto: ")
            codigo_barras = input("Código de barras: ")
            insertar_producto(nombre, descripcion, precio, cantidad, categoria, codigo_barras)
        elif opcion == '2':
            listar_productos()
        elif opcion == '3':
            id_producto = int(input("ID del producto a actualizar: "))
            nueva_cantidad = int(input("Nueva cantidad en stock: "))
            actualizar_stock(id_producto, nueva_cantidad)
        elif opcion == '4':
            id_producto = int(input("ID del producto a eliminar: "))
            eliminar_producto(id_producto)
        elif opcion == '5':
            print("Saliendo del sistema...")
            break
        else:
            print("Opción no válida. Inténtalo de nuevo.")

# Ejecutar el menú
if __name__ == '__main__':
    menu()
