# Mini plataforma CTF

Pequeña plataforma con 3 desafios ctfs para usarse de demostracion en la 2da prueba de la asignatura de `Ingenieria en DevOps`

## Dockerfile multi-stage

Imagen Docker creada a partir de una imagen de alpine linux `python:3.12-slim` usada en dos etapas:

| Etapa | Descripcion |
| ---- | ----------- |
| 1 | Descarga las dependencias necesarias en `/root/.local` |
| 2 | Marca los contenedores, determina el entorno del sistema interno del docker y el usuario que usara, hace un checkeo y expone el puerto 8080 para correr el proyecto. |

Cabe destacar que esta medida no es del todo necesaria cuando se trabaja con python debido a que no hay compilacion de por medio.

## Pruebas unitarias para casos criticos

| Alcance | Test | Condicion |
| ------- | ---- | --------- |
| Servicio | `test_health_ok` | Test de health comun respondiendo a un 200 |
| HTML | `test_index_sirve_html` | Test de index si responde con un HTML |
| SQLi | `test_sqli_login_normal_sin_flag` | Test del desafio de sqli para determinar si un login normal no da la flag |
| SQLi | `test_sqli_credenciales_invalidas` | Verifica que un login con contraseña incorrecta no autentica ni entrega flag |
| SQLi | `test_sqli_inyeccion_entrega_flag` | Comprueba que el bypass `' OR '1'='1' --` recupera la fila del admin y entrega la flag |
| SSTI | `test_ssti_evaluacion_aritmetica` | Confirma que `{{ 7*7 }}` se evalúa a `49` (hay SSTI) pero sin entregar flag |
| SSTI | `test_ssti_extrae_flag` | Verifica que `{{ config.SECRET_FLAG }}` extrae la flag del contexto de la plantilla |
| SSTI | `test_ssti_payload_invalido_devuelve_error` | Una plantilla mal formada devuelve error 400 sin romper el servicio |
| XSS | `test_xss_texto_plano_no_resuelve` | Un texto plano se refleja pero no resuelve el desafío (sin flag) |
| XSS | `test_xss_script_entrega_flag` | Un payload `<script>alert(1)</script>` es detectado y entrega la flag |
| XSS | `test_xss_img_onerror_entrega_flag` | Un payload `<img src=x onerror=alert(1)>` también resuelve el desafío |

## Dependabot activo + Snyk con bloqueo ante fallo de seguridad

Se añadieron ambas dependencias dentro del pipeline principal. A fin de obtener reportes sobre posibles problemas de seguridad en librerias externas.

### SNYK

```yaml
 security:
    name: Analisis de seguridad
    runs-on: ubuntu-latest
    needs: test
    steps:
      - name: Checkout del codigo
        uses: actions/checkout@v4

      - name: Snyk - analisis de dependencias
        uses: snyk/actions/python@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
        with:
          args: --file=requirements.txt --severity-threshold=high
```

### Dependabot

```yml
version: 2
updates:
  - package-ecosystem: "pip"      # cambiar según lenguaje (maven, npm...)
    directory: "/"
    schedule:
      interval: "weekly"
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
```

## Parametros de escalabilidad

Se limitaron los recursos utilizados por la maquina a manera tal que se puedan aumentar en caso de que la plataforma aumente de necesidades de recursos.

```yml
 deploy:
      replicas: 1
      resources:
        limits:                     # techo de recursos (evita que un contenedor acapare la maquina)
          cpus: "0.50"
          memory: 256M
        reservations:               # minimo garantizado
          cpus: "0.25"
          memory: 128M
```

## Despliegue automatico

El despliegue consta de varios pasos:

1. Si detecta un push, realiza un checkout del codigo
2. Levanta el servicio a traves del `docker-compose`
3. Se corre un script en bash al endpoint `/health` para verificar si esta arriba.
4. Registra el SHA de github para identificar el pipeline
5. Baja el contenedor a traves del `docker-compose`

```yml
  deploy:
    name: Deploy 
    runs-on: ubuntu-latest
    needs: [ test, build, security ]
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    steps:
      - name: Checkout del codigo
        uses: actions/checkout@v4

      - name: Levantar el servicio con Docker Compose
        run: docker compose up -d --build

      - name: Verificacion post-deploy (/health)
        run: | # Toma 10 intentos para probar el servicio, marcando como error si no responde
          for i in $(seq 1 10); do
            if curl --fail --silent http://localhost:8080/health; then
              echo "Servicio saludable"; exit 0
            fi
            echo "Esperando al servicio... ($i)"; sleep 3
          done
          echo "El servicio no respondio a tiempo"; exit 1

      - name: Registrar version desplegada (trazabilidad)
        run: echo "Desplegada imagen ${{ env.IMAGE_NAME }} con SHA ${{ github.sha }}"

      - name: Apagar el entorno
        if: always()
        run: docker compose down
```

## docker-compose

El `docker-compose` llama al contenedor creado a traves del `Dockerfile` y al puerto 8080, probando un health check verificando el estado de subida

```yml
services:
  app:
    build: .
    image: mini-ctf:latest
    container_name: mini-ctf
    ports:
      - "8080:8080"
    environment:
      - CTF_DB_PATH=/app/data/ctf.db
    volumes:
      - ctf-data:/app/data          # persiste la base de datos SQLite
    deploy:
      replicas: 1
      resources:
        limits:                     # techo de recursos (evita que un contenedor acapare la maquina)
          cpus: "0.50"
          memory: 256M
        reservations:               # minimo garantizado
          cpus: "0.25"
          memory: 128M
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')"]
      interval: 30s
      timeout: 3s
      retries: 3
      start_period: 5s
    restart: unless-stopped         # se reinicia solo si el contenedor cae

volumes:
  ctf-data:
```

## Declaracion de uso de IA

La IA fue usada dentro del proyecto en los siguientes aspectos:

- **Esqueleto principal de `pipeline.yml`**: Se uso para identificar la principal estructura que tendria el pipeline, basado en los ejemplos de la documentacion otorgada.

- **Microservicio**: Como el microservicio solo es para la demostracion del pipeline se creo una pagina web sencilla a traves del agente de IA claude-code.

- **Propuestas de tests**: Se uso para proponer principales pruebas criticas, se tomaron solo un par para simplificar.

- **Consultas concretas del Dockerfile**: Consultas sobre las etapas y las secciones concretas del Dockerfile.

## Reflexion individual

Daniel:

> Creo que esta evaluacion fue bastante valiosa, creo que me permitara dar un paso mas en mis proyectos, aplicando tecnicas para el trabajo eficiente y rapido en proyectos que requieren cierto nivel de sofisticadez de desarrollo. Como una vez le dije a mi profesor Gabriel Grobier: `"Me gusta eso de hacer una pega una vez, y luego no hacerla nunca mas"` (**Claro que en la practica no es asi, pero se entiende el mensaje**)
