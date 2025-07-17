import requests

# URL base de la API
base_url = "https://api.demo.matrizoms.com.ar"

# Endpoint para obtener el token de autenticación
auth_url = f"{base_url}/auth/getToken"

# Endpoint para obtener detalles del instrumento
instrument_detail_url = f"{base_url}/rest/instruments/detail"

# Credenciales de usuario
username = "api_provinciabursatil"
password = "5aRg80zD_"

# Encabezados de la solicitud
headers = {
    "X-Username": username,
    "X-Password": password,
    "Content-Type": "application/x-www-form-urlencoded"
}

# Realizar la solicitud POST para obtener el token
response = requests.post(auth_url, headers=headers)

# Verificar si la solicitud fue exitosa
if response.status_code == 200:
    # Extraer el token del encabezado de la respuesta
    token = response.headers.get("X-Auth-Token")
    if token:
        print("Autenticación exitosa. Token:", token)
    else:
        print("Error: No se encontró el token en los encabezados de la respuesta.")
else:
    print("Error en la autenticación:", response.status_code, response.text)


# Parámetros de la solicitud
params = {
    "marketId": "ROFX",
    "symbol": "MERV - XMEV - YPFD - 24hs"
}

# Encabezados de la solicitud
headers = {
    "X-Auth-Token": token,
    "Content-Type": "application/x-www-form-urlencoded"
}

# Realizar la solicitud GET para obtener detalles del instrumento
response = requests.get(instrument_detail_url, headers=headers, params=params)

# Verificar si la solicitud fue exitosa
if response.status_code == 200:
    try:
        # Decodificar el JSON de la respuesta
        instrument_details = response.json()
        print("Detalles del instrumento:", instrument_details)
    except requests.exceptions.JSONDecodeError:
        print("Error al decodificar el JSON de la respuesta.")
else:
    print("Error en la solicitud:", response.status_code, response.text)