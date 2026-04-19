import React, { useState, useEffect } from 'react';
import { Button, Input, Card, Space, message, Typography, Row, Col, Alert, Tag } from 'antd';
import { ShoppingCartOutlined, DollarOutlined, SearchOutlined, DeleteOutlined, PlusOutlined, MinusOutlined } from '@ant-design/icons';
import axios from 'axios';

const { Title, Text } = Typography;

// Configuración de la API
const API_URL = process.env.NODE_ENV === 'production' 
  ? 'https://saint-killer-api.onrender.com' 
  : 'http://localhost:8000';

// Interfaces (Tipos de datos)
interface Producto {
  id: string;
  nombre: string;
  codigo_barras: string;
  precio_bs: number;
  precio_usd: number;
  stock: number;
  stock_minimo: number;
}

interface CarritoItem {
  producto: Producto;
  cantidad: number;
  moneda: 'BS' | 'USD';
}

function App() {
  const [productos, setProductos] = useState<Producto[]>([]);
  const [carrito, setCarrito] = useState<CarritoItem[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(false);
  const [monedaPago, setMonedaPago] = useState<'BS' | 'USD'>('BS');

  // Cargar productos al iniciar
  useEffect(() => {
    cargarProductos();
  }, []);

  const cargarProductos = async () => {
    try {
      const response = await axios.get(`${API_URL}/productos`);
      setProductos(response.data);
    } catch (error) {
      message.error('Error al cargar productos. ¿El servidor está corriendo?');
    }
  };

  const agregarAlCarrito = (producto: Producto, moneda: 'BS' | 'USD') => {
    if (producto.stock <= 0) {
      message.warning(`${producto.nombre} está agotado`);
      return;
    }

    const existente = carrito.find(item => item.producto.id === producto.id && item.moneda === moneda);
    
    if (existente) {
      if (existente.cantidad + 1 > producto.stock) {
        message.warning(`Solo quedan ${producto.stock} unidades`);
        return;
      }
      setCarrito(carrito.map(item =>
        item.producto.id === producto.id && item.moneda === moneda
          ? { ...item, cantidad: item.cantidad + 1 }
          : item
      ));
    } else {
      setCarrito([...carrito, { producto, cantidad: 1, moneda }]);
    }
    message.success(`${producto.nombre} agregado en ${moneda}`);
  };

  const actualizarCantidad = (productoId: string, moneda: 'BS' | 'USD', nuevaCantidad: number) => {
    if (nuevaCantidad <= 0) {
      setCarrito(carrito.filter(item => !(item.producto.id === productoId && item.moneda === moneda)));
      return;
    }
    
    const item = carrito.find(i => i.producto.id === productoId && i.moneda === moneda);
    if (item && nuevaCantidad > item.producto.stock) {
      message.warning(`Solo quedan ${item.producto.stock} unidades`);
      return;
    }
    
    setCarrito(carrito.map(item =>
      item.producto.id === productoId && item.moneda === moneda
        ? { ...item, cantidad: nuevaCantidad }
        : item
    ));
  };

  const calcularSubtotal = (moneda: 'BS' | 'USD') => {
    return carrito
      .filter(item => item.moneda === moneda)
      .reduce((sum, item) => sum + (item.cantidad * (moneda === 'BS' ? item.producto.precio_bs : item.producto.precio_usd)), 0);
  };

  const calcularIVA = (moneda: 'BS' | 'USD') => {
    return calcularSubtotal(moneda) * 0.16;
  };

  const calcularTotal = (moneda: 'BS' | 'USD') => {
    return calcularSubtotal(moneda) + calcularIVA(moneda);
  };

  const realizarVenta = async () => {
    if (carrito.length === 0) {
      message.warning('Carrito vacío');
      return;
    }

    setLoading(true);
    try {
      const items = carrito.map(item => ({
        producto_id: item.producto.id,
        cantidad: item.cantidad,
        precio_unitario_bs: item.producto.precio_bs,
        precio_unitario_usd: item.producto.precio_usd
      }));

      const venta = {
        id: '',
        fecha: new Date().toISOString(),
        items: items,
        subtotal_bs: calcularSubtotal('BS'),
        subtotal_usd: calcularSubtotal('USD'),
        impuesto_bs: calcularIVA('BS'),
        impuesto_usd: calcularIVA('USD'),
        total_bs: calcularTotal('BS'),
        total_usd: calcularTotal('USD'),
        metodo_pago: 'Efectivo',
        moneda_pago: monedaPago
      };

      await axios.post(`${API_URL}/ventas`, venta);
      message.success('¡Venta realizada con éxito!');
      setCarrito([]);
      await cargarProductos();
      
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Error al procesar venta');
    } finally {
      setLoading(false);
    }
  };

  const productosFiltrados = productos.filter(p =>
    p.nombre.toLowerCase().includes(searchTerm.toLowerCase()) ||
    p.codigo_barras.includes(searchTerm)
  );

  return (
    <div style={{ padding: '20px', background: '#f0f2f5', minHeight: '100vh' }}>
      <Title level={2} style={{ textAlign: 'center', marginBottom: '20px', color: '#1890ff' }}>
        🚀 Saint Killer - Punto de Venta Profesional
      </Title>

      <Row gutter={20}>
        {/* Columna izquierda: Productos */}
        <Col span={14}>
          <Card 
            title="Productos" 
            extra={
              <Input
                placeholder="Buscar por nombre o código de barras"
                prefix={<SearchOutlined />}
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                style={{ width: 250 }}
                allowClear
                autoFocus
              />
            }
          >
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '16px' }}>
              {productosFiltrados.map(producto => (
                <Card
                  key={producto.id}
                  size="small"
                  hoverable
                  style={{ 
                    borderLeft: producto.stock < producto.stock_minimo ? '4px solid red' : '4px solid #52c41a',
                    backgroundColor: producto.stock === 0 ? '#fafafa' : 'white'
                  }}
                >
                  <div style={{ textAlign: 'center' }}>
                    <Text strong>{producto.nombre}</Text>
                    <div>
                      <Tag color="blue">Bs {producto.precio_bs.toFixed(2)}</Tag>
                      <Tag color="green">${producto.precio_usd.toFixed(2)}</Tag>
                    </div>
                    <Text type={producto.stock < producto.stock_minimo ? "danger" : "secondary"}>
                      Stock: {producto.stock}
                    </Text>
                    <div style={{ marginTop: 10 }}>
                      <Space>
                        <Button 
                          size="small" 
                          type="primary" 
                          onClick={() => agregarAlCarrito(producto, 'BS')}
                          disabled={producto.stock === 0}
                        >
                          Bs
                        </Button>
                        <Button 
                          size="small" 
                          type="default" 
                          onClick={() => agregarAlCarrito(producto, 'USD')}
                          disabled={producto.stock === 0}
                        >
                          USD
                        </Button>
                      </Space>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </Card>
        </Col>

        {/* Columna derecha: Carrito */}
        <Col span={10}>
          <Card 
            title={
              <Space>
                <ShoppingCartOutlined />
                <span>Carrito de Compras</span>
              </Space>
            }
            extra={
              <Space>
                <Button 
                  type={monedaPago === 'BS' ? 'primary' : 'default'} 
                  size="small"
                  onClick={() => setMonedaPago('BS')}
                >
                  Pagar en Bs
                </Button>
                <Button 
                  type={monedaPago === 'USD' ? 'primary' : 'default'} 
                  size="small"
                  onClick={() => setMonedaPago('USD')}
                >
                  Pagar en USD
                </Button>
              </Space>
            }
          >
            {carrito.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
                <ShoppingCartOutlined style={{ fontSize: 48, marginBottom: 16 }} />
                <p>Carrito vacío</p>
              </div>
            ) : (
              <>
                {carrito.map((item, index) => (
                  <Card key={index} size="small" style={{ marginBottom: 8 }}>
                    <Row align="middle">
                      <Col span={12}>
                        <Text strong>{item.producto.nombre}</Text>
                        <div>
                          <Text type="secondary">
                            {item.moneda === 'BS' ? 'Bs ' : '$ '}
                            {(item.moneda === 'BS' ? item.producto.precio_bs : item.producto.precio_usd).toFixed(2)}
                          </Text>
                        </div>
                      </Col>
                      <Col span={8}>
                        <Space>
                          <Button 
                            size="small" 
                            icon={<MinusOutlined />} 
                            onClick={() => actualizarCantidad(item.producto.id, item.moneda, item.cantidad - 1)}
                          />
                          <Text strong>{item.cantidad}</Text>
                          <Button 
                            size="small" 
                            icon={<PlusOutlined />} 
                            onClick={() => actualizarCantidad(item.producto.id, item.moneda, item.cantidad + 1)}
                          />
                        </Space>
                      </Col>
                      <Col span={4}>
                        <Button 
                          danger 
                          size="small" 
                          icon={<DeleteOutlined />} 
                          onClick={() => actualizarCantidad(item.producto.id, item.moneda, 0)}
                        />
                      </Col>
                    </Row>
                  </Card>
                ))}
                
                <div style={{ marginTop: 16, borderTop: '1px solid #f0f0f0', paddingTop: 16 }}>
                  <div style={{ marginBottom: 8 }}>
                    <Row justify="space-between">
                      <Text>Subtotal ({monedaPago}):</Text>
                      <Text strong>
                        {monedaPago === 'BS' ? 'Bs ' : '$ '}
                        {(monedaPago === 'BS' ? calcularSubtotal('BS') : calcularSubtotal('USD')).toFixed(2)}
                      </Text>
                    </Row>
                    <Row justify="space-between">
                      <Text>IVA (16%):</Text>
                      <Text>
                        {monedaPago === 'BS' ? 'Bs ' : '$ '}
                        {(monedaPago === 'BS' ? calcularIVA('BS') : calcularIVA('USD')).toFixed(2)}
                      </Text>
                    </Row>
                    <Row justify="space-between" style={{ marginTop: 8 }}>
                      <Text strong style={{ fontSize: 18 }}>Total a pagar:</Text>
                      <Text strong style={{ fontSize: 24, color: '#52c41a' }}>
                        {monedaPago === 'BS' ? 'Bs ' : '$ '}
                        {(monedaPago === 'BS' ? calcularTotal('BS') : calcularTotal('USD')).toFixed(2)}
                      </Text>
                    </Row>
                  </div>
                  
                  <Button 
                    type="primary" 
                    size="large" 
                    block 
                    onClick={realizarVenta}
                    loading={loading}
                    icon={<DollarOutlined />}
                  >
                    Cobrar Venta
                  </Button>
                </div>
              </>
            )}
          </Card>
        </Col>
      </Row>

      {productos.some(p => p.stock <= p.stock_minimo) && (
        <Alert
          message="⚠️ Alerta de inventario"
          description="Hay productos con stock bajo. Revisa la lista para reabastecer."
          type="warning"
          showIcon
          closable
          style={{ marginTop: 20 }}
        />
      )}
    </div>
  );
}

export default App;
