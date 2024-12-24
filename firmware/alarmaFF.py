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

os.system("./mic.sh")

dog = 'Dog'
bark = 'Ladrar, ladrido'
bow = 'Guau-guau, ladrido'

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
    data = {
        "user_id": int(f'{user_id}'),
        "location": "casa",
        "was_true": False,
        "environmental_sounds": environmental_sounds
    }
    response = requests.post(f'https://multimodal-ai-lab.cicese.mx/tzukucare/api/alert', json=data)

def obtenerTop(top5):
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

stream = p.open(format=pyaudio.paInt16,
                channels=1,
                rate=RATE,
                input=True,
                frames_per_buffer=15600)

print(lpa, lpe, pausas)
def envioSerial():
    ser = serial.Serial(baudrate=9600, port='/dev/ttyS0')
    return ser

    
def hora(ser):
    current_minute = -1
    while True:
        now = datetime.datetime.now()
        if now.minute != current_minute:
            current_minute = now.minute
            #print(now.strftime("%H:%M"))
            ser.write(now.strftime("%H:%M").encode())
        time.sleep(1)


def inferencia():
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
        while monitorearAlgoritmoAlarma:
            ## RECOLECTANDO MUESTRAS DEL MICROFONO##
            dataParaClasificar = stream.read(
                15600, exception_on_overflow=False)
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
            if functools.reduce(lambda count, l: count + len(l), dataParaGuardar, 0) < 160000:
                print('guardando')
                dataParaGuardar.append(dataParaClasificar)
                bufferString = bufferString + \
                    str(time.time()) + ' ' + resultadoPrediccion + '\n'
            ####### eliminando ultimo segundo y registro por si se pasa de los 5 minutos###########
            if functools.reduce(lambda count, l: count + len(l), dataParaGuardar, 0) > 160000:
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
                monitorearAlgoritmoAlarma = False
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
        while not monitorearAlgoritmoAlarma:
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
    ser = envioSerial()
    t1 = threading.Thread(target=inferencia)
    t1.start()
    #t2 = threading.Thread(target=hora, args=(ser,))
    #t2.start()
    t1.join()
    #t2.join()

