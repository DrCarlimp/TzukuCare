# README - TZUKU Care

## Descripción del Proyecto

**TZUKU Care** es un sistema de monitoreo complementario para perros de asistencia, diseñado para mejorar la calidad de vida de personas con condiciones que dificultan llevar una vida plena. Este sistema combina la capacidad sensorial de los perros de asistencia con tecnologías avanzadas de monitoreo y análisis de sonido, ofreciendo una solución no invasiva basada en computación en el borde.

### Características principales:
- **Detección de patrones de ladridos:** Identifica ladridos específicos de perros entrenados para activar alarmas.
- **Privacidad y comodidad:** Diseñado para no interferir con los usuarios o los perros.
- **Procesamiento local:** Elimina la dependencia de una conexión a Internet.
- **Aplicación personalizable:** Permite configurar las notificaciones y el monitoreo de ubicación.

## Responsables

- **Equipo de Desarrollo:**
  - Carlos Alberto Aguilar Lazcano
  - Claudia Angélica Rivera Romero
  - Edwin Raúl Abrego Ulloa
  - Marco Adame
  - Humberto Pérez Espinosa

- **Instituciones Participantes:**
  - Centro de Investigación Científica y de Educación Superior de Ensenada, Unidad Académica Tepic (CICESE-UAT)
  - Instituto Nacional de Astrofísica, Óptica y Electrónica (INAOE)
  - Universidad Autónoma de Tlaxcala

- **Responsables Técnicos:**
  - Dr. Ismael Edrein Espinosa Curiel - [ecuriel@cicese.edu.mx](mailto:ecuriel@cicese.edu.mx)
  - Dr. Humberto Pérez Espinosa - [humbertop@inaoep.mx](mailto:humbertop@inaoep.mx)

- **Página web:** [https://tzuku.cicese.mx/](https://tzuku.cicese.mx/)

## Instalación y Configuración Inicial

### Requisitos previos:
- Tarjeta Nvidia Jetson Nano (2GB)
- Tarjeta microSD con mínimo 16GB
- Acceso a Internet para configuración inicial

### Pasos para Configurar:
1. **Preparación de la tarjeta microSD:**
   - Descarga el sistema operativo desde la página oficial de Nvidia.
   - Usa `Etcher` para grabar la imagen en la tarjeta microSD.
   - Inserta la tarjeta en la Jetson Nano y realiza la configuración inicial.

2. **Preparación del modelo YAMNet:**
   - Descarga el modelo desde TensorFlow Hub.
   - Instala las dependencias necesarias usando `pip install`.

3. **Configuración del Firmware:**
   - Carga los scripts en Python para la gestión de datos y la comunicación entre componentes.
   - Configura los dispositivos como Arduino Nano y la pantalla LCD Nokia 5110 según el esquema provisto.

### Ejecución del Sistema
- **Modo Básico:** Ejecuta el script `alarmaExp.py` desde la terminal, configurando los parámetros necesarios.
- **Modo Avanzado:** Ejecuta el script `alarmaVF.py` para integración con API remota y monitoreo avanzado.

## Documentación

### Objetivos del Proyecto:
1. Implementar un sistema embebido para ejecutar modelos de machine learning localmente.
2. Diseñar un algoritmo que clasifique sonidos en tiempo real.
3. Evaluar el sistema en entornos controlados y reales.

### Diseño del Prototipo:
- Unidad de procesamiento: Nvidia Jetson Nano (2GB)
- Modelo de análisis: YAMNet
- Carcasa: Impresión 3D en PLA
- Componentes adicionales: Arduino Nano y pantalla LCD Nokia 5110

### Recursos Adicionales:
- **Scripts de Utilidades:**
  - `Alarm_plotter.ipynb`: Visualiza los eventos de activación.
  - `Alarms_events_detector.ipynb`: Simula configuraciones del algoritmo de detección.

## Contacto

Para consultas o soporte técnico, contacta a:
- **CICESE-UAT:** 311-129-5930, ext. 28607
- **INAOE:** 222-266-3100, ext. 8321

