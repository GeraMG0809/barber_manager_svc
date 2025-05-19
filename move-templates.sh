#!/bin/bash

# Crear directorios necesarios en el frontend-service
mkdir -p app/frontend-service/templates
mkdir -p app/frontend-service/static

# Mover plantillas
cp templates/* app/frontend-service/templates/

# Mover archivos estáticos
cp -r static/* app/frontend-service/static/

echo "Archivos movidos exitosamente" 