# Barber Manager SVC

## Descripción General

Barber Manager SVC es una plataforma de gestión para barberías basada en microservicios. Permite la administración de citas, barberos, productos y usuarios, integrando un frontend moderno y un sistema de autenticación robusto. El sistema está preparado para despliegue en Kubernetes, con observabilidad y gestión de tráfico gracias a Istio y Kiali.

---

## Arquitectura

El sistema está compuesto por los siguientes microservicios:

- **Frontend**: Aplicación Node.js/Express que sirve la interfaz web.
- **API Gateway**: Orquesta las peticiones entre el frontend y los microservicios internos.
- **Auth Service**: Servicio de autenticación y gestión de usuarios.
- **Appointments Service**: Gestión de citas.
- **Barbers Service**: Gestión de barberos.
- **Products Service**: Gestión de productos.
- **Bases de datos MySQL**: Una base de datos por microservicio de backend.

Todos los servicios se comunican a través de HTTP y están orquestados en Kubernetes. El tráfico externo entra por el Ingress Gateway de Istio.

### Diagrama de Arquitectura

```mermaid
graph TD
    FE[Frontend (Node.js)]
    GW[API Gateway]
    AUTH[Auth Service]
    APPT[Appointments Service]
    BARBERS[Barbers Service]
    PRODUCTS[Products Service]
    DBAUTH[(MySQL Auth)]
    DBAPPT[(MySQL Appointments)]
    DBBARBERS[(MySQL Barbers)]
    DBPRODUCTS[(MySQL Products)]
    ISTIO[Istio]
    KIALI[Kiali]
    PROM[Prometheus]

    FE -->|HTTP| GW
    GW -->|HTTP| AUTH
    GW -->|HTTP| APPT
    GW -->|HTTP| BARBERS
    GW -->|HTTP| PRODUCTS
    AUTH -->|SQL| DBAUTH
    APPT -->|SQL| DBAPPT
    BARBERS -->|SQL| DBBARBERS
    PRODUCTS -->|SQL| DBPRODUCTS
    FE --> ISTIO
    GW --> ISTIO
    AUTH --> ISTIO
    APPT --> ISTIO
    BARBERS --> ISTIO
    PRODUCTS --> ISTIO
    ISTIO --> PROM
    ISTIO --> KIALI
```

---

## Tecnologías Utilizadas

- **Node.js / Express**: Frontend web.
- **Python / Flask**: Microservicios backend.
- **MySQL**: Almacenamiento de datos.
- **Docker**: Contenerización de servicios.
- **Kubernetes**: Orquestación de contenedores.
- **Istio**: Malla de servicios para gestión de tráfico, seguridad y observabilidad.
- **Kiali**: Visualización y gestión de la malla de servicios.
- **Prometheus**: Monitorización y recolección de métricas.

---

## Despliegue

### 1. Construcción de Imágenes

```bash
eval $(minikube docker-env)
docker build -t frontend-service:latest ./frontend-service
docker build -t api-gateway:latest ./api-gateway
docker build -t auth-service:latest ./auth-service
docker build -t appointments-service:latest ./appointments-service
docker build -t barbers-service:latest ./barbers-service
docker build -t products-service:latest ./products-service
```

### 2. Despliegue en Kubernetes

```bash
kubectl apply -f k8s/
```

### 3. Acceso a la Aplicación

- Ejecuta:
  ```bash
  minikube tunnel
  ```
- Obtén la IP del Ingress Gateway de Istio:
  ```bash
  kubectl get svc istio-ingressgateway -n istio-system
  ```
- Accede desde el navegador a `http://<IP_DEL_GATEWAY>/`

### 4. Monitorización

- Kiali:
  ```bash
  minikube service kiali -n istio-system
  ```
- Prometheus:
  ```bash
  minikube service prometheus -n istio-system
  ```

---

## Observabilidad y Seguridad

- Todo el tráfico entre servicios es gestionado y monitorizado por Istio.
- Kiali permite visualizar el tráfico, latencias y errores entre microservicios.
- Prometheus recolecta métricas de la malla de servicios.

---

## Estructura de Carpetas

```
barber_manager_svc/
├── api-gateway/
├── appointments-service/
├── auth-service/
├── barbers-service/
├── frontend-service/
├── products-service/
├── k8s/
└── ...
```

---

## Contacto y Créditos

Creado por el equipo:

Brandon Chavez
Juan Pablo Martinez 
Gerardo Gabriel Mercado .

---

## Pasos para Descargar y Levantar el Proyecto

### 1. Clonar el repositorio

```bash
git clone <URL_DEL_REPOSITORIO>
cd barber_manager_svc/barber_manager_svc
```

### 2. Instalar y configurar Minikube, Istio, Kiali y Prometheus

- Instala [Minikube](https://minikube.sigs.k8s.io/docs/start/)
- Instala [Istio](https://istio.io/latest/docs/setup/getting-started/)
- Instala los addons de Kiali y Prometheus:

```bash
istioctl install --set profile=demo -y
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.20/samples/addons/kiali.yaml
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.20/samples/addons/prometheus.yaml
```

### 3. Etiquetar el namespace para Istio (opcional pero recomendado)

```bash
kubectl label namespace barber istio-injection=enabled --overwrite
```

### 4. Construir las imágenes Docker

```bash
eval $(minikube docker-env)
docker build -t frontend-service:latest ./frontend-service
docker build -t api-gateway:latest ./api-gateway
docker build -t auth-service:latest ./auth-service
docker build -t appointments-service:latest ./appointments-service
docker build -t barbers-service:latest ./barbers-service
docker build -t products-service:latest ./products-service
```

### 5. Desplegar los recursos de Kubernetes

```bash
kubectl apply -f k8s/
```

### 6. Verificar el estado de los pods

```bash
kubectl get pods -n barber
```

### 7. Exponer el Ingress Gateway de Istio

```bash
minikube tunnel
```

### 8. Obtener la IP del Ingress Gateway

```bash
kubectl get svc istio-ingressgateway -n istio-system
```

### 9. Acceder a la aplicación

- Abre tu navegador en: `http://<IP_DEL_GATEWAY>/`

### 10. Acceder a Kiali y Prometheus

- Kiali:
  ```bash
  minikube service kiali -n istio-system
  ```
- Prometheus:
  ```bash
  minikube service prometheus -n istio-system
  ``` 
