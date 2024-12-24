import itertools
import functools
import pyaudio
import numpy as np
import tensorflow as tf
import yamnet as yamnet_model
import re
import librosa
import random
import wave
import time
import requests
import subprocess
import threading
import serial
import uuid
import datetime
import os

#os.system("./mic.sh")

dog = 'Dog'
bark = 'Ladrar, ladrido'
bow = 'Guau-guau, ladrido'

"""
La configuración inicial de la jetson se hace con las siguientes lineas

Lo primero es intentar abrir el archivo user_info.txt donde solo existen dos lineas, una con el id del usuario
que ha vinculado el dispositivo con él y la otra linea con el id del perro que ha registrado.

Ejemplo:
1
2

Así se ve el archivo donde el primer 1 presenta el id del usuario y la segunda linea (2) representa el id 2 del perro registrado
por el usuario.

"""
while True:
    try:
            with open("/home/carlimp/user_info.txt", 'r') as f:
                lineas = f.readlines()
                user_id = lineas[0].strip()
                dog_id = lineas[1].strip()
                f.close()
            usuario = {
                "user_id": int(f'{user_id}')
            }
            """
            Aquí el proceso estará detenido hasta que la request pueda bajar la configuración de la alarma,
            la condición es que el usuario debe registrar un perro y dar de alta una configuración de alarma para 
            posteriormente recuperar los 3 parámetros:
                lpe (ladridos para activar escucha)
                lpa (ladridos para activar alarma)
                pausas (pausas permitidas antes de resetear las variables que monitorean el patrón de ladridos)
            """
            while True:
                response = requests.get(
                    f'https://multimodal-ai-lab.cicese.mx/tzukucare/api/alarm/{dog_id}', json=usuario)
                if response.status_code == 200:
                    break
            lpe = response.json()['barking_listened']
            lpa = response.json()['barking_alarm']
            pausas = response.json()['pause_duration']
            break
    except: pass

def send_alert(environmental_sounds):
    """
    params:

    environmental_sounds: string => son los sonidos ambientales con mayor ocurrencia hasta la detección de la alerta    

    """
    data = { #data: dict => es un diccionario que se envia al servidor cuando una alerta es detectada. 
        "user_id": int(f'{user_id}'), #user_id que recuperamos desde la funcion al inicio del codigo donde leemos el archivo user_info.txt
        "location": "casa", #localización del dispositivo (para pruebas se usa el string "casa")
        "was_true": False, #un booleano que indica (y el usuario despues edita) si la alerta generada fue o no correcta
        "environmental_sounds": environmental_sounds #sonidos ambientales
    }
    response = requests.post(f'https://multimodal-ai-lab.cicese.mx/tzukucare/api/alert', json=data) #aqui hacemos el post al servidor para almacenar la alerta

def obtenerTop(top5):

    """
    params:

    top5: list => recibe una lista de lista que contiene los indices de todos los eventos guardados a lo largo de 5 minutos
    antes de una ocurriencia de alarma

    la funcion primero aplana la lista y despues cuenta en cada pocision, al final ordena por frecuencia los elementos de la lista
    y recupera el top 5 (indices) para despues obtener a que clase pertenece cada indice haciendo uso de nuestra variable "yamnet_classes"

    return: string del top 5 clases detectadas separadas con un salto de linea '\n'

    """

    lista_plana = list(itertools.chain.from_iterable(top5)) #Aplanamos la lista ya que recibimos una lista de listas
    top_5_elementos_palabras = []
    frecuencias = {}
    for elemento in lista_plana:
        if elemento in frecuencias:
            frecuencias[elemento] += 1
        else:
            frecuencias[elemento] = 1
    # Ordenar el diccionario por su valor en orden descendente
    ordenado_por_frecuencia = sorted(frecuencias.items(), key=lambda x: x[1], reverse=True)
    # Obtener los primeros 5 elementos del diccionario ordenado
    top_5_elementos = [elem[0] for elem in ordenado_por_frecuencia[:5]]
    for top in top_5_elementos:
        top_5_elementos_palabras.append(yamnet_classes[top])
    top_5_elementos_palabras = '\n'.join(top_5_elementos_palabras)
    return top_5_elementos_palabras

"""
Cargamos el interprete para nuestro modelo lite de YAMNet

ref. https://tfhub.dev/google/lite-model/yamnet/classification/tflite/1
"""
interpreter = tf.lite.Interpreter(
    model_path="/home/carlimp/lite-model_yamnet_classification_tflite_1.tflite")
interpreter.allocate_tensors()
inputs = interpreter.get_input_details()
outputs = interpreter.get_output_details()

yamnet_classes = yamnet_model.class_names('/home/carlimp/yamnet_class_map_es.csv')

p = pyaudio.PyAudio()

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000

stream = p.open(format=pyaudio.paInt16, #los datos de entrada del microfono pueden ser encontrados en el sig enlace. https://tfhub.dev/google/lite-model/yamnet/classification/tflite/1
                channels=1,
                rate=RATE,
                input=True,
                frames_per_buffer=15600)


def envioSerial():
    """
    funcion que devuelve una conexion serial para poder comunicarnos con nuestro display para enviar información visual
    """
    ser = serial.Serial(baudrate=9600, port='/dev/ttyUSB0')
    return ser

    
def hora(ser):
    """
    hora es una funcion que recibe una conexión serial a la que enviara cada minuto la hora del sistema,
    esto para que el reloj que se muestra en el display solo se actualice cada minuto
    """
    current_minute = -1
    while True:
        now = datetime.datetime.now()
        if now.minute != current_minute:
            current_minute = now.minute
            #print(now.strftime("%H:%M"))
            ser.write(now.strftime("%H:%M").encode())
        time.sleep(1)


def inferencia(ser):
    # VARIABLES ALARMA
    monitorearAlgoritmoAlarma = True
    okgoogle = 0
    ladridosTotalDespuesDeEscucha = 0
    ladridosSeguidos = 0
    pausasTODO = 0
    pausaAUX = 0
    ## VARIABLES AUDIO##
    dataParaGuardar = []
    m = ''
    dataParaGuardarDespuesDeAlarma = []
    ## VARIABLES TEXTO##
    bufferString = ''
    bufferStringDespuesDeAlarma = ''
    stringsTop5 = []
    ## INICIO DE CLASIFICACION Y EVALUACION DE ALARMA##
    while True:
        while monitorearAlgoritmoAlarma: #mientras no se registre una alerta vamos a recolectar datos y evaluar el patron de predicciones del modelo
            ## RECOLECTANDO MUESTRAS DEL MICROFONO##
            dataParaClasificar = stream.read(
                15600, exception_on_overflow=False)
            """
            las caracteristicas del tensor de entrada y tensor de salida se encuentran en https://tfhub.dev/google/lite-model/yamnet/classification/tflite/1
            """
            interpreter.set_tensor(inputs[0]['index'], np.reshape(librosa.util.buf_to_float(
                dataParaClasificar, n_bytes=2, dtype=np.int16), [1, -1]).astype('float32').flatten())
            interpreter.invoke()
            scores = interpreter.get_tensor(outputs[0]['index'])
            prediction = np.mean(scores, axis=0)
            top5_i = np.argsort(prediction)[::-1][:5]
            stringsTop5.append(top5_i)
            resultadoPrediccion = ''.join('  {:12s}: {:.3f}'.format(yamnet_classes[i], prediction[i])
                                for i in top5_i)
            #resultadoPrediccion = bark
            if (not re.search(bark, resultadoPrediccion) and not re.search(bow, resultadoPrediccion)) and okgoogle == 1:
                pausaAUX += 1
            if (re.search(bark, resultadoPrediccion) or re.search(bow, resultadoPrediccion)) and okgoogle == 1:
                print('ladrido despues de escucha')
                ladridosTotalDespuesDeEscucha += 1
                pausasTODO = 0
            if pausaAUX >= int(pausas):
                print('ESCUCHA ACTIVA DESACTIVADA')
                ladridosTotalDespuesDeEscucha = 0
                ladridosSeguidos = 0
                okgoogle = 0
                pausasTODO = 0
            if not re.search(bark, resultadoPrediccion) and not re.search(bow, resultadoPrediccion):
                ladridosSeguidos = 0
                pausasTODO += 1
                if pausasTODO == 15:
                    ladridosTotalDespuesDeEscucha = 0
                    ladridosSeguidos = 0
                    okgoogle = 0
                    pausasTODO = 0
            ######## guardando 5 minutos atras##########
            if functools.reduce(lambda count, l: count + len(l), dataParaGuardar, 0) < 9600000: #esta condicion evalua si la grabación sigue por debajo de los 5min
                print('guardando')
                dataParaGuardar.append(dataParaClasificar)
                bufferString = bufferString + \
                    str(time.time()) + ' ' + resultadoPrediccion + '\n'
            ####### eliminando ultimo segundo y registro por si se pasa de los 5 minutos###########
            if functools.reduce(lambda count, l: count + len(l), dataParaGuardar, 0) > 9600000:
                arrayBuffer = bufferString.split('\n')
                del arrayBuffer[0]
                bufferString = '\n'.join(arrayBuffer)
                del dataParaGuardar[0]
            # if len(bufferString.split('\n')) == 305:
            #    arrayBuffer = bufferString.split('\n')
            #    del arrayBuffer[0]
            #    bufferString = '\n'.join(arrayBuffer)
            if ladridosTotalDespuesDeEscucha == int(lpa):
                uid = str(uuid.uuid4())
                # bufferString = bufferString + str(time.time())+ ' ' + resultadoPrediccion
                print('¡¡¡ALARMA ACTIVADA!!!')
                ser.write(b'a ')
                with open('/home/carlimp/activaciones/ACTIVACION-ALARMA-' + uid + '-' + '.txt', 'w') as f:
                    f.write(bufferString)
                    f.close()
                send_alert(environmental_sounds=obtenerTop(stringsTop5))
                stringsTop5 = []
                wf = wave.open('/home/carlimp/activaciones/ACTIVACION-ALARMA-' + uid +
                               '-' + '.wav', 'wb')
                wf.setnchannels(1)
                wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
                wf.setframerate(RATE)
                wf.writeframes(b''.join(dataParaGuardar))
                wf.close()
                ladridosTotalDespuesDeEscucha = 0
                ladridosSeguidos = 0
                okgoogle = 0
                pausasTODO = 0
                monitorearAlgoritmoAlarma = False #cuando una alerta es detectada la variable monitorearAlgoritmoAlarma pasa a falso para no evaluar las predicciones
            if (re.search(bark, resultadoPrediccion) or re.search(bow, resultadoPrediccion)) and okgoogle == 0:
                pausasTODO = 0
                ladridosSeguidos += 1
                print('ladrido seguido')
            if ladridosSeguidos == int(lpe):
                okgoogle = 1
                enviado = False
                if not enviado:
                    ser.write(b'e ')
                    enviado = True
                print('ESCUCHA ACTIVA INICIADA')
        ## DESPUES DE ALARMA ESTO ES LO QUE SE GUARDA - 5 MIN DE AUDIO Y TEXTO##
        while not monitorearAlgoritmoAlarma: #esta parte es similar a la primera solo que no se evalua el patron de ladridos, sino que solo se graban los eventos posteriores a la alarma
            dataParaClasificar = stream.read(
                15600, exception_on_overflow=False)
            interpreter.set_tensor(inputs[0]['index'], np.reshape(librosa.util.buf_to_float(
                dataParaClasificar, n_bytes=2, dtype=np.int16), [1, -1]).astype('float32').flatten())
            interpreter.invoke()
            scores = interpreter.get_tensor(outputs[0]['index'])
            prediction = np.mean(scores, axis=0)
            top5_i = np.argsort(prediction)[::-1][:5]
            resultadoPrediccion = ''.join('  {:12s}: {:.3f}'.format(yamnet_classes[i], prediction[i])
                                          for i in top5_i)
            ######## guardando 5 minutos##########
            if functools.reduce(lambda count, l: count + len(l), dataParaGuardarDespuesDeAlarma, 0) < 160000:
                #print('guardando audio despues de alarma')
                #print('guardando texto despues de alarma')
                dataParaGuardarDespuesDeAlarma.append(dataParaClasificar)
                bufferStringDespuesDeAlarma = bufferStringDespuesDeAlarma + \
                    str(time.time()) + ' ' + resultadoPrediccion + '\n'
            if functools.reduce(lambda count, l: count + len(l), dataParaGuardarDespuesDeAlarma, 0) > 160000:
#                #print('audio guardado')
#                #print('texto guardado')
                wf = wave.open('/home/carlimp/activaciones/DESPUES-DE-ACTIVAR-ALARMA-' +
                               uid + '-' + '.wav', 'wb')
                wf.setnchannels(1)
                wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
                wf.setframerate(RATE)
                wf.writeframes(b''.join(dataParaGuardarDespuesDeAlarma))
                wf.close()
                with open('/home/carlimp/activaciones/DESPUES-DE-ACTIVAR-ALARMA-' + uid + '-' + '.txt', 'w') as f:
                    f.write(bufferStringDespuesDeAlarma)
                    f.close()
                monitorearAlgoritmoAlarma = True
                #sys.exit()
                dataParaGuardar = []
                dataParaGuardarDespuesDeAlarma = []
            enviado = False
    stream.stop_stream()
    stream.close()
    p.terminate()


if __name__ == '__main__':
    """
    lo primero es recuperar una conexión serial y pasarla como argumento a nuestras funcion de inferencia y reloj,
    se utilizan hilos porque comparten el mismo espacio en memoria, por lo que pueden utilizar la misma conexión serial sin conflicto
    """
    ser = envioSerial()
    t1 = threading.Thread(target=inferencia, args=(ser,))
    t1.start()
    t2 = threading.Thread(target=hora, args=(ser,))
    t2.start()
    t1.join()
    t2.join()

