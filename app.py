from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
import uuid
import requests
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# SQLAlchemy para PostgreSQL
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# ==================== CONFIGURACIÓN ====================
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:saintkiller123@localhost:5432/saintkiller_db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ==================== MODELOS DE BASE DE DATOS ====================

class ProductoDB(Base):
    __tablename__ = "productos"
    
    id = Column(String, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    codigo_barras = Column(String, unique=True, index=True)
    precio_bs = Column(Float, nullable=False)
    precio_usd = Column(Float, nullable=False)
    stock = Column(Integer, default=0)
    stock_minimo = Column(Integer, default=5)
    created_at = Column(DateTime, default=datetime.utcnow)

class VentaDB(Base):
    __tablename__ = "ventas"
    
    id = Column(String, primary_key=True, index=True)
    fecha = Column(DateTime, default=datetime.utcnow)
    items = Column(JSON, nullable=False)
    subtotal_bs = Column(Float, default=0)
    subtotal_usd = Column(Float, default=0)
    impuesto_bs = Column(Float, default=0)
    impuesto_usd = Column(Float, default=0)
    total_bs = Column(Float, default=0)
    total_usd = Column(Float, default=0)
    metodo_pago = Column(String, nullable=False)
    moneda_pago = Column(String, nullable=False)

# Crear tablas
Base.metadata.create_all(bind=engine)

# ==================== MODELOS PYDANTIC ====================

class Producto(BaseModel):
    id: str
    nombre: str
    codigo_barras: str
    precio_bs: float
    precio_usd: float
    stock: int
    stock_minimo: int = 5

class VentaItem(BaseModel):
    producto_id: str
    cantidad: int
    precio_unitario_bs: float
    precio_unitario_usd: float

class Venta(BaseModel):
    id: str
    fecha: datetime
    items: List[VentaItem]
    subtotal_bs: float
    subtotal_usd: float
    impuesto_bs: float
    impuesto_usd: float
    total_bs: float
    total_usd: float
    metodo_pago: str
    moneda_pago: str

# ==================== DEPENDENCIAS ====================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==================== FASTAPI APP ====================

app = FastAPI(
    title="Saint Killer API",
    description="La herramienta administrativa que revolucionará Maracaibo",
    version="4.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== ENDPOINTS ====================

@app.on_event("startup")
def init_db():
    """Inicializar la base de datos con productos por defecto"""
    db = SessionLocal()
    
    if db.query(ProductoDB).count() == 0:
        productos_iniciales = [
            ProductoDB(id="1", nombre="Harina PAN 1kg", codigo_barras="000123456789", precio_bs=25.00, precio_usd=3.50, stock=100, stock_minimo=10),
            ProductoDB(id="2", nombre="Coca-Cola 1.5L", codigo_barras="000987654321", precio_bs=15.00, precio_usd=2.00, stock=50, stock_minimo=8),
            ProductoDB(id="3", nombre="Queso Blanco 500g", codigo_barras="000456789123", precio_bs=35.00, precio_usd=5.00, stock=30, stock_minimo=5),
            ProductoDB(id="4", nombre="Café Marrón 250g", codigo_barras="000789123456", precio_bs=28.00, precio_usd=4.00, stock=45, stock_minimo=10),
            ProductoDB(id="5", nombre="Azúcar Blanco 1kg", codigo_barras="000321654987", precio_bs=12.00, precio_usd=1.70, stock=80, stock_minimo=15),
            ProductoDB(id="6", nombre="Pastelito de Pollo", codigo_barras="000111222333", precio_bs=18.00, precio_usd=2.50, stock=200, stock_minimo=30),
            ProductoDB(id="7", nombre="Cerveza Polar 355ml", codigo_barras="000444555666", precio_bs=10.00, precio_usd=1.40, stock=500, stock_minimo=50),
            ProductoDB(id="8", nombre="Arepa Reina Pepiada", codigo_barras="000777888999", precio_bs=22.00, precio_usd=3.00, stock=150, stock_minimo=25),
            ProductoDB(id="9", nombre="Tequeños (6 unidades)", codigo_barras="000111222444", precio_bs=15.00, precio_usd=2.10, stock=120, stock_minimo=20),
            ProductoDB(id="10", nombre="Papitas PL 40g", codigo_barras="000555666777", precio_bs=5.00, precio_usd=0.70, stock=300, stock_minimo=40),
        ]
        for producto in productos_iniciales:
            db.add(producto)
        db.commit()
    
    db.close()

@app.get("/")
def raiz():
    return {
        "mensaje": "¡Saint Killer API - Versión 4.0 con PostgreSQL!",
        "status": "online",
        "version": "4.0.0",
        "creadora": "La que va a revolucionar Maracaibo",
        "base_datos": "PostgreSQL"
    }

@app.get("/productos")
def obtener_productos(db: Session = Depends(get_db)):
    productos = db.query(ProductoDB).all()
    return productos

@app.get("/productos/{producto_id}")
def obtener_producto(producto_id: str, db: Session = Depends(get_db)):
    producto = db.query(ProductoDB).filter(ProductoDB.id == producto_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return producto

@app.get("/productos/buscar/codigo/{codigo_barras}")
def buscar_por_codigo(codigo_barras: str, db: Session = Depends(get_db)):
    producto = db.query(ProductoDB).filter(ProductoDB.codigo_barras == codigo_barras).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return producto

@app.get("/inventario/bajo-stock")
def productos_bajo_stock(db: Session = Depends(get_db)):
    bajo_stock = db.query(ProductoDB).filter(ProductoDB.stock <= ProductoDB.stock_minimo).all()
    return {
        "total": len(bajo_stock),
        "productos": bajo_stock
    }

@app.post("/ventas")
def registrar_venta(venta: Venta, db: Session = Depends(get_db)):
    for item in venta.items:
        producto = db.query(ProductoDB).filter(ProductoDB.id == item.producto_id).first()
        if not producto:
            raise HTTPException(status_code=404, detail=f"Producto {item.producto_id} no existe")
        
        if producto.stock < item.cantidad:
            raise HTTPException(status_code=400, detail=f"Stock insuficiente de {producto.nombre}")
        
        producto.stock -= item.cantidad
    
    venta.id = str(uuid.uuid4())
    venta.fecha = datetime.now()
    
    venta.subtotal_bs = sum(item.cantidad * item.precio_unitario_bs for item in venta.items)
    venta.subtotal_usd = sum(item.cantidad * item.precio_unitario_usd for item in venta.items)
    venta.impuesto_bs = venta.subtotal_bs * 0.16
    venta.impuesto_usd = venta.subtotal_usd * 0.16
    venta.total_bs = venta.subtotal_bs + venta.impuesto_bs
    venta.total_usd = venta.subtotal_usd + venta.impuesto_usd
    
    nueva_venta = VentaDB(
        id=venta.id,
        fecha=venta.fecha,
        items=[item.dict() for item in venta.items],
        subtotal_bs=venta.subtotal_bs,
        subtotal_usd=venta.subtotal_usd,
        impuesto_bs=venta.impuesto_bs,
        impuesto_usd=venta.impuesto_usd,
        total_bs=venta.total_bs,
        total_usd=venta.total_usd,
        metodo_pago=venta.metodo_pago,
        moneda_pago=venta.moneda_pago
    )
    
    db.add(nueva_venta)
    db.commit()
    
    alertas = []
    for item in venta.items:
        producto = db.query(ProductoDB).filter(ProductoDB.id == item.producto_id).first()
        if producto.stock <= producto.stock_minimo:
            alertas.append({
                "producto": producto.nombre,
                "stock_actual": producto.stock,
                "stock_minimo": producto.stock_minimo
            })
    
    return {
        "mensaje": "¡Venta registrada exitosamente!",
        "venta_id": venta.id,
        "fecha": venta.fecha,
        "total_bs": venta.total_bs,
        "total_usd": venta.total_usd,
        "alertas_inventario": alertas
    }

@app.get("/ventas")
def obtener_ventas(db: Session = Depends(get_db)):
    ventas = db.query(VentaDB).order_by(VentaDB.fecha.desc()).all()
    return ventas

@app.get("/ventas/{venta_id}")
def obtener_venta(venta_id: str, db: Session = Depends(get_db)):
    venta = db.query(VentaDB).filter(VentaDB.id == venta_id).first()
    if not venta:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    return venta

@app.get("/reporte/diario")
def reporte_diario(db: Session = Depends(get_db)):
    hoy = datetime.now().date()
    ventas_hoy = db.query(VentaDB).filter(VentaDB.fecha >= hoy).all()
    
    total_bs_dia = sum(v.total_bs for v in ventas_hoy)
    total_usd_dia = sum(v.total_usd for v in ventas_hoy)
    
    resumen_pagos = {}
    for venta in ventas_hoy:
        metodo = venta.metodo_pago
        if metodo not in resumen_pagos:
            resumen_pagos[metodo] = {"cantidad": 0, "total_bs": 0, "total_usd": 0}
        resumen_pagos[metodo]["cantidad"] += 1
        resumen_pagos[metodo]["total_bs"] += venta.total_bs
        resumen_pagos[metodo]["total_usd"] += venta.total_usd
    
    return {
        "fecha": hoy.isoformat(),
        "total_ventas": len(ventas_hoy),
        "total_bs": total_bs_dia,
        "total_usd": total_usd_dia,
        "resumen_pagos": resumen_pagos,
        "ventas": ventas_hoy
    }

@app.get("/tasa-dolar")
def obtener_tasa_dolar():
    resultado = {
        "binance": None,
        "bcv": None,
        "fecha_actualizacion": datetime.now().isoformat(),
        "activa": False
    }
    
    try:
        url_binance = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
        payload = {
            "asset": "USDT",
            "fiat": "VES",
            "tradeType": "BUY",
            "page": 1,
            "rows": 5,
            "payTypes": []
        }
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(url_binance, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == "000000" and data.get("data"):
                precios = [float(adv["adv"]["price"]) for adv in data["data"]]
                if precios:
                    resultado["binance"] = {
                        "promedio": round(sum(precios) / len(precios), 2),
                        "minimo": round(min(precios), 2),
                        "maximo": round(max(precios), 2),
                        "fuente": "Binance P2P - Mercado real",
                        "nota": "Precio promedio de compra de USDT en Bolívares"
                    }
                    resultado["activa"] = True
    except Exception as e:
        print(f"Error en Binance: {e}")
    
    try:
        url_bcv_api = "https://pydolarve.org/api/v1/dollar?page=bcv"
        response = requests.get(url_bcv_api, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "price" in data and data["price"]:
                tasa_bcv = float(data["price"])
                resultado["bcv"] = {
                    "tasa": tasa_bcv,
                    "fuente": "Banco Central de Venezuela (BCV)",
                    "nota": "Tasa oficial del BCV"
                }
    except Exception as e:
        print(f"Error en BCV API: {e}")
        resultado["bcv"] = {
            "tasa": 481.21,
            "fuente": "BCV (valor referencial)",
            "nota": "Tasa del BCV del 18/04/2026"
        }
    
    if resultado["binance"]:
        tasa_activa = resultado["binance"]["promedio"]
        fuente_activa = "Binance P2P (Mercado real)"
    elif resultado["bcv"]:
        tasa_activa = resultado["bcv"]["tasa"]
        fuente_activa = "BCV Oficial"
    else:
        tasa_activa = 481.21
        fuente_activa = "Sistema (respaldo)"
    
    return {
        "tasa_activa": tasa_activa,
        "fuente_activa": fuente_activa,
        "detalles": resultado,
        "fecha_actualizacion": datetime.now().isoformat(),
        "mensaje": f"✅ BCV: {resultado['bcv']['tasa'] if resultado['bcv'] else 'N/A'} Bs/USD | Binance: {resultado['binance']['promedio'] if resultado['binance'] else 'N/A'} Bs/USD"
    }

@app.get("/estadisticas")
def estadisticas(db: Session = Depends(get_db)):
    total_ventas = db.query(VentaDB).count()
    total_bs = sum(v.total_bs for v in db.query(VentaDB).all())
    total_usd = sum(v.total_usd for v in db.query(VentaDB).all())
    
    return {
        "total_ventas": total_ventas,
        "total_facturado_bs": total_bs,
        "total_facturado_usd": total_usd,
        "inventario_total": sum(p.stock for p in db.query(ProductoDB).all()),
        "base_datos": "PostgreSQL"
    }

@app.get("/health")
def salud():
    return {"estado": "saludable", "timestamp": datetime.now().isoformat()}

@app.get("/mensaje-para-francisco")
def mensaje():
    return {
        "mensaje": "Francisco, esto es el DÍA 4 y ya tengo:",
        "caracteristicas": [
            "✅ Base de datos PostgreSQL (datos guardados para siempre)",
            "✅ 10 productos típicos de Maracaibo",
            "✅ Múltiples monedas (Bs y USD)",
            "✅ Tasa del dólar desde Binance P2P y BCV",
            "✅ Los datos NO se pierden cuando apago el servidor",
            "✅ El que ríe último, ríe mejor."
        ],
        "dias_para_el_demo": 3
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)