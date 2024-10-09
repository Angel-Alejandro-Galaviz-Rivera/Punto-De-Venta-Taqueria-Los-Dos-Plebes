CREATE DATABASE Punto_De_Venta;
USE Punto_De_Venta;

-- Tabla de usuarios (no necesita cambios)
CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    correo VARCHAR(100) NOT NULL UNIQUE,
    contrasena VARCHAR(255) NOT NULL,
    rol ENUM('admin', 'cajero') NOT NULL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de productos (no necesita cambios)
CREATE TABLE productos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    precio DECIMAL(10, 2) NOT NULL,
    cantidad_en_stock INT DEFAULT 0,
    categoria VARCHAR(50),
    codigo_barras VARCHAR(50) UNIQUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de clientes (no necesita cambios)
CREATE TABLE clientes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    correo VARCHAR(100) UNIQUE,
    telefono VARCHAR(20),
    direccion TEXT,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de ventas
CREATE TABLE ventas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT,  -- El cajero que realiza la venta
    id_cliente INT,  -- El cliente (puede ser NULL si es cliente general)
    total DECIMAL(10, 2) NOT NULL,
    fecha_venta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- Fecha y hora de la venta
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id),
    FOREIGN KEY (id_cliente) REFERENCES clientes(id) ON DELETE SET NULL
);

-- Tabla de detalles de venta
CREATE TABLE detalles_venta (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_venta INT,  -- Relacionada con la tabla de ventas
    id_producto INT,  -- Relacionada con la tabla de productos
    cantidad INT NOT NULL,  -- Cantidad de producto vendido
    precio_unitario DECIMAL(10, 2) NOT NULL,  -- Precio del producto en ese momento
    subtotal DECIMAL(10, 2) AS (cantidad * precio_unitario),  -- Subtotal (calculado)
    FOREIGN KEY (id_venta) REFERENCES ventas(id) ON DELETE CASCADE,
    FOREIGN KEY (id_producto) REFERENCES productos(id) ON DELETE RESTRICT
);

-- Tabla de inventario
CREATE TABLE inventario (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_producto INT,
    cantidad_cambiada INT NOT NULL,  -- Cantidad cambiada (puede ser negativo si es venta)
    motivo ENUM('venta', 'compra', 'ajuste') NOT NULL,  -- Motivo del cambio
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- Fecha del cambio
    FOREIGN KEY (id_producto) REFERENCES productos(id)
);

-- Tabla de cortes (opcional, para registrar cortes Z)
CREATE TABLE cortes_z (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT,  -- Usuario que realiza el corte
    total DECIMAL(10, 2) NOT NULL,  -- Total acumulado en el corte
    fecha_corte TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- Fecha y hora del corte
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id)
);
