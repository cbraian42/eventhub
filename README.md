# Integrantes

- Castro Braian
- Aramberri Juan Bautista
- Costa Tomas Agustin
- Mazza Joaquin
- Reale Milagros

# Eventhub

Deploy en: https://eventhub-k9g9.onrender.com/
Aplicación web para venta de entradas utilizada en la cursada 2025 de Ingeniería y Calidad de Software. UTN-FRLP

## Dependencias

- python 3
- Django
- sqlite
- playwright
- ruff

## Instalar dependencias

`pip install -r requirements.txt`

## Iniciar la Base de Datos

`python manage.py migrate`

### Crear usuario admin

`python manage.py createsuperuser`

### Llenar la base de datos

`python manage.py loaddata fixtures/events.json`

## Iniciar app

`python manage.py runserver`

## Crear la imagen en docker

`docker build -t eventhub-app .`

## Crea el contenedor de docker y te lo ejecuta en http://127.0.0.1:8000

`docker run --env-file .env -p 8000:8000 eventhub-app`
