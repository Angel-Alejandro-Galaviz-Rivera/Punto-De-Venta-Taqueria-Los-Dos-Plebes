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

-- Registros de productos
INSERT INTO productos (nombre, descripcion, precio, cantidad_en_stock, categoria, codigo_barras) VALUES 
('Taco de sirloin maíz', 'Taco de sirloin con tortilla maíz', 26, 23, 'tacos', '000001'),
('Taco de sirloin harina', 'Taco de sirloin con tortilla de harina', 26, 15, 'tacos', '000002'),
('Taco sirloin maíz con queso', 'Taco de sirloin con tortilla de maíz y queso', 32, 35, 'tacos', '000003'),
('Taco de sirloin harina con queso', 'Taco de sirloin con tortilla de harina y queso', 32, 12, 'tacos', '000004'),
('Quesadilla mixta de harina', 'Quesadilla con carne sirloin y trompo', 65, 9, 'quesadillas', '000005'),
('Quesadilla Maíz', 'Tortilla grande con queso y carne', 65, 31, 'quesadillas', '000006'),
('Vampiro', 'Tortilla tostada a las brasas con queso y carne', 50, 17, 'antojitos', '000007'),
('Pellizcada', 'Sope con asientos de puerco, queso y carne', 70, 6, 'antojitos', '000008'),
('Papa Asada especial', 'Con carne, acompañada de tortilla o galleta', 125, 25, 'papas', '000009'),
('Papa sencilla', 'Sin carne, acompañada de tortilla o galleta', 80, 7, 'papas', '000010'),
('Salchicha asada sencilla', 'Salchicha asada', 30, 19, 'salchichas', '000011'),
('Salchicha asada especial', 'Con queso y carne', 45, 4, 'salchichas', '000012'),
('Frijoles charros sencillos', 'Frijoles charros', 30, 33, 'frijoles', '000013'),
('Frijoles charros especiales', NULL, 40, 8, 'frijoles', '000014'),

-- Bebidas de 1 litro
('Litro Horchata', NULL, 50, 20, 'bebidas', '000015'),
('Litro Cebada', NULL, 50, 18, 'bebidas', '000016'),
('Litro Limón', NULL, 50, 15, 'bebidas', '000017'),
('Litro Jamaica', NULL, 50, 25, 'bebidas', '000018'),
('Litro Piña', NULL, 50, 19, 'bebidas', '000019'),

-- Bebidas de 600 ml
('600 ml Horchata', NULL, 30, 10, 'bebidas', '000020'),
('600 ml Cebada', NULL, 30, 12, 'bebidas', '000021'),
('600 ml Limón', NULL, 30, 8, 'bebidas', '000022'),
('600 ml Jamaica', NULL, 30, 15, 'bebidas', '000023'),
('600 ml Piña', NULL, 30, 11, 'bebidas', '000024'),

('Refresco', NULL, 30, 28, 'bebidas', '000025'),
('Agua natural', NULL, 20, 37, 'bebidas', '000026');

-- Registros de usuarios
INSERT INTO usuarios (nombre, correo, contrasena, rol) VALUES
('Juan Pérez', 'juan.perez@example.com', 'contrasena123', 'cajero'),
('Ana García', 'ana.garcia@example.com', 'contrasena456', 'cajero');