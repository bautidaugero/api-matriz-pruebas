# API Matriz - Primary Trading Client

Una aplicación Flask para interactuar con la API de Primary Trading.

## Características

- Consulta de detalles de instrumentos financieros
- Interfaz web intuitiva
- Cliente para market data en tiempo real

## Instalación

1. Clona el repositorio:
```bash
git clone https://github.com/TU-USUARIO/api-matriz.git
cd api-matriz
```

2. Crea un entorno virtual:
```bash
python -m venv venv
venv\Scripts\activate
```

3. Instala las dependencias:
```bash
pip install -r requirements.txt
```

## Uso

1. Ejecuta la aplicación:
```bash
python app.py
```

2. Abre tu navegador en:
- `http://127.0.0.1:5000/` - Página principal
- `http://127.0.0.1:5000/market_data` - Market data

## Estructura del proyecto

```
├── app.py                 # Aplicación principal Flask
├── primary_trading_client.py  # Cliente de la API
├── requirements.txt       # Dependencias
├── templates/
│   ├── index.html        # Página principal
│   └── market_data.html  # Página de market data
└── README.md
```