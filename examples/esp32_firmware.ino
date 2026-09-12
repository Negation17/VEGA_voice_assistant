/*
 * VEGA AI Voice Assistant - ESP32 Microphone PCM Streamer
 *
 * Samples audio from an I2S digital microphone (e.g. INMP441) at 16kHz mono 16-bit
 * and streams raw PCM audio bytes to the VEGA /chat_pcm endpoint over WiFi.
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <driver/i2s.h>

const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* vegaServer = "http://192.168.1.100:8000/chat_pcm";

#define I2S_WS 15
#define I2S_SD 32
#define I2S_SCK 14
#define I2S_PORT I2S_NUM_0

#define SAMPLE_RATE 16000
#define RECORD_TIME_SEC 3
#define BUFFER_SIZE (SAMPLE_RATE * 2 * RECORD_TIME_SEC) // 16-bit = 2 bytes per sample

uint8_t pcmBuffer[BUFFER_SIZE];

void setupI2S() {
  i2s_config_t i2s_config = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
    .sample_rate = SAMPLE_RATE,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = I2S_COMM_FORMAT_STAND_I2S,
    .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
    .dma_buf_count = 4,
    .dma_buf_len = 1024,
    .use_apll = false
  };

  i2s_pin_config_t pin_config = {
    .bck_io_num = I2S_SCK,
    .ws_io_num = I2S_WS,
    .data_out_num = I2S_PIN_NO_CHANGE,
    .data_in_num = I2S_SD
  };

  i2s_driver_install(I2S_PORT, &i2s_config, 0, NULL);
  i2s_set_pin(I2S_PORT, &pin_config);
}

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi Connected!");
  setupI2S();
  Serial.println("VEGA ESP32 Ready. Press Enter in Serial to record and send PCM.");
}

void loop() {
  if (Serial.available()) {
    Serial.readStringUntil('\n');
    Serial.println("Recording 3 seconds of 16kHz PCM audio...");

    size_t bytesRead = 0;
    i2s_read(I2S_PORT, pcmBuffer, BUFFER_SIZE, &bytesRead, portMAX_DELAY);
    Serial.printf("Recorded %d bytes. Sending to VEGA /chat_pcm...\n", bytesRead);

    HTTPClient http;
    http.begin(vegaServer);
    http.addHeader("Content-Type", "application/octet-stream");

    int httpCode = http.POST(pcmBuffer, bytesRead);
    if (httpCode > 0) {
      String response = http.getString();
      Serial.printf("VEGA Response [%d]: %s\n", httpCode, response.c_str());
    } else {
      Serial.printf("HTTP Error: %s\n", http.errorToString(httpCode).c_str());
    }
    http.end();
  }
}
