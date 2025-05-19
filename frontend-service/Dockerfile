FROM node:18-slim

WORKDIR /app

# Copiar archivos de configuración
COPY package*.json ./

# Instalar dependencias
RUN npm install

# Copiar el resto de los archivos
COPY . .

# Crear directorios necesarios si no existen
RUN mkdir -p static/css static/js static/images

# Establecer permisos
RUN chown -R node:node /app

# Cambiar al usuario node
USER node

EXPOSE 5005

CMD ["npm", "start"] 