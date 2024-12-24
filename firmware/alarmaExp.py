import functools
from threading import Thread
import pyaudio
import numpy as np
import tensorflow as tf
import yamnet as yamnet_model
import re
import librosa
import glob
import random
import wave
import time
import sys, os
import uuid

import subprocess

rc = subprocess.call("/home/carlimp/mic.sh")

interpreter = tf.lite.Interpreter(model_path="/home/carlimp/lite-model_yamnet_classification_tflite_1.tflite")
interpreter.allocate_tensors()
inputs = interpreter.get_input_details()
outputs = interpreter.get_output_details()

yamnet_classes = yamnet_model.class_names('/home/carlimp/yamnet_class_map.csv')


p = pyaudio.PyAudio()

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000


stream = p.open(format=pyaudio.paInt16,
                channels=1,
                rate=RATE,
                input=True,
                frames_per_buffer=15600)

dog = 'Dog'
bark = 'Bark'
bow = 'Bow-wow'


###### led
#import Jetson.GPIO as GPIO
 
# Pin Definition
#led_rojo = 7
 
# Set up the GPIO channel
#GPIO.setmode(GPIO.BOARD) 
#GPIO.setup(led_rojo, GPIO.OUT, initial=GPIO.LOW) 
 
#GPIO.output(led_rojo, GPIO.HIGH) 
#GPIO.output(led_rojo, GPIO.LOW)



def monitoreo():
    okgoogle = 0
    ladridosTotalDespuesDeEscucha = 0
    ladridosSeguidos = 0
    pausasTODO = 0
    pausaAUX = 0  
    ##VARIABLES AUDIO##
    dataParaGuardar = []
    ##VARIABLES TEXTO##
    bufferString = ''
    ###duracion de la prueba
    cuantoTiempo = time.time() + duracion
    #GPIO.output(led_rojo, GPIO.HIGH)
    #print('inicie')
    while cuantoTiempo >= time.time():
        #resultadoPrediccion = bark
        dataParaClasificar = stream.read(15600, exception_on_overflow=False)
        time.sleep(0.1)
        interpreter.set_tensor(inputs[0]['index'], np.reshape(librosa.util.buf_to_float(dataParaClasificar, n_bytes=2, dtype=np.int16), [1, -1]).astype('float32').flatten())
        interpreter.invoke()
        scores = interpreter.get_tensor(outputs[0]['index'])
        prediction = np.mean(scores, axis=0)
        top5_i = np.argsort(prediction)[::-1][:5]
        resultadoPrediccion = ''.join('  {:12s}: {:.3f}'.format(yamnet_classes[i], prediction[i])
                for i in top5_i)
        if (not re.search(bark, resultadoPrediccion) and not re.search(bow, resultadoPrediccion)) and okgoogle == 1:
            pausaAUX += 1
        if (re.search(bark, resultadoPrediccion) or re.search(bow, resultadoPrediccion)) and okgoogle == 1:
            print('ladrido despues de escucha')
            ladridosTotalDespuesDeEscucha += 1
            pausasTODO = 0
        if not re.search(bark, resultadoPrediccion) and not re.search(bow, resultadoPrediccion):
            ladridosSeguidos = 0
            pausasTODO += 1
            if pausasTODO == 15:
                    ladridosTotalDespuesDeEscucha = 0
                    ladridosSeguidos = 0
                    okgoogle = 0
                    pausasTODO = 0
        ########guardando 5 minutos atras##########
        #if functools.reduce(lambda count, l: count + len(l), dataParaGuardar, 0) < 160000:
        #    print('guardando')
        dataParaGuardar.append(dataParaClasificar)
        bufferString = bufferString + str(time.time())+ ' ' + resultadoPrediccion + '\n'
        ########eliminando ultimo segundo y registro por si se pasa de los 5 minutos###########
        #if functools.reduce(lambda count, l: count + len(l), dataParaGuardar, 0) > 160000:
        #    arrayBuffer = bufferString.split('\n')
        #    del arrayBuffer[0]
        #    bufferString = '\n'.join(arrayBuffer)
        #    del dataParaGuardar[0]
        if ladridosTotalDespuesDeEscucha == int(numeroDeLadridosParaActivarAlarma):
            #bufferString = bufferString + str(time.time())+ ' ' + resultadoPrediccion
            bufferString = bufferString + str(time.time())+ ' ' + '¡¡¡ALARMA ACTIVADA!!!' + '\n'
            print('¡¡¡ALARMA ACTIVADA!!!')
            ladridosTotalDespuesDeEscucha = 0
            ladridosSeguidos = 0
            okgoogle = 0
            pausaAUX = 0
            pausasTODO = 0
        if (re.search(bark, resultadoPrediccion) or re.search(bow, resultadoPrediccion)) and okgoogle == 0:
            pausasTODO = 0
            ladridosSeguidos += 1
            print('ladrido seguido')
        if ladridosSeguidos == int(numeroDeLadridosParaActivarEscucha):
            okgoogle = 1
            print('ESCUCHA ACTIVA INICIADA')
        if pausaAUX >= int(pausasPermitidas):
            print('ESCUCHA ACTIVA DESACTIVADA')
            ladridosTotalDespuesDeEscucha = 0
            pausaAUX = 0
            ladridosSeguidos = 0
            okgoogle = 0
            pausasTODO = 0  
        dataParaClasificar = None
    iduu = str(uuid.uuid4())
    with open('experimento jetson texto-' + nombrePrueba + '-' + str(time.time()) + '---'+ str(iduu) +'.txt', 'w') as f:
        f.write(bufferString)
        f.close()
    wf = wave.open('experimento jetson audio-' + nombrePrueba + '-' + str(time.time()) +'---'+str(iduu)+ '.wav', 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(dataParaGuardar))
    wf.close()
    #GPIO.output(led_rojo, GPIO.LOW)
    #GPIO.cleanup()

if __name__ == '__main__':
    numeroDeLadridosParaActivarAlarma = sys.argv[1]
    numeroDeLadridosParaActivarEscucha = sys.argv[2]
    duracion = int(sys.argv[3]) * 60
    pausasPermitidas = sys.argv[4]
    nombrePrueba = sys.argv[5]
    monitoreo()

    
