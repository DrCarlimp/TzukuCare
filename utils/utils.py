import serial
from datetime import datetime
import time

def enviar_hora(port="/dev/ttyUSB0", baudrate=9600):
    """
    Envía la hora actual al Arduino Nano a través del puerto serial.

    :param port: Puerto serial al que está conectado el Arduino (por defecto: /dev/ttyUSB0).
    :param baudrate: Velocidad de comunicación serial (por defecto: 9600).
    """
    try:
        # Configurar la conexión serial
        with serial.Serial(port, baudrate, timeout=1) as ser:
            print(f"Conectado al puerto {port} a {baudrate} bps")
            while True:
                # Obtener la hora actual
                hora_actual = datetime.now().strftime("%H:%M:%S")

                # Enviar la hora al Arduino
                ser.write(hora_actual.encode('utf-8'))
                print(f"Hora enviada: {hora_actual}")

                # Pausar por un segundo
                time.sleep(1)

    except serial.SerialException as e:
        print(f"Error al acceder al puerto serial: {e}")
    except KeyboardInterrupt:
        print("Programa terminado por el usuario.")

if __name__ == "__main__":
    # Llama a la función para enviar la hora
    enviar_hora()
