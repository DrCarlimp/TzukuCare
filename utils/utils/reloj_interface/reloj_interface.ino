#include <Adafruit_GFX.h>
#include <Adafruit_PCD8544.h>

// Pines para el display Nokia 5110
#define PIN_SCLK 2  // Clock
#define PIN_DIN 3   // Data in
#define PIN_DC 4    // Data/Command
#define PIN_CS 5    // Chip select
#define PIN_RST 6   // Reset

// Crear el objeto del display
Adafruit_PCD8544 display = Adafruit_PCD8544(PIN_SCLK, PIN_DIN, PIN_DC, PIN_CS, PIN_RST);

void setup() {
  // Iniciar la comunicación serial
  Serial.begin(9600);

  // Iniciar el display Nokia 5110
  display.begin();
  display.setContrast(50); // Ajusta el contraste según sea necesario
  display.clearDisplay();
  display.display();

  // Mostrar mensaje inicial
  display.setTextSize(1);
  display.setTextColor(BLACK);
  display.setCursor(0, 0);
  display.println("Esperando hora...");
  display.display();
}

void loop() {
  // Verificar si hay datos disponibles en el puerto serial
  if (Serial.available() > 0) {
    // Leer la hora recibida
    String hora = Serial.readStringUntil('\n');

    // Limpiar el display
    display.clearDisplay();

    // Mostrar la hora en el display
    display.setTextSize(2); // Tamaño del texto
    display.setTextColor(BLACK);
    display.setCursor(0, 10); // Posición en el display
    display.println(hora);

    // Actualizar el contenido del display
    display.display();
  }
}
