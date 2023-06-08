  //////////////////////////////////////////////////////////////////////////////////////////////////
  //bagian anchor
  #include <SPI.h>
  #include "DW1000Ranging.h"
  #include "DW1000.h"
  ///////untuk antena delay/////////////
  uint16_t Adelay_delta = 100;
  float this_anchor_target_distance = 0; //measured distance to anchor in m  
  // leftmost two bytes below will become the "short address"
  char anchor_addr[] = "84:00:5B:D5:A9:9A:E2:2A"; //#4
  
  char tag_addr[] = "84:00:5B:D5:A9:9A:E2:2A";
  float this_anchor_Adelay;
  //calibrated Antenna Delay setting for this anchor
  uint16_t Adelay = 16514;
  //16634
  //16580
  //16565
  // calibration distance
  //float dist_m = 1; //meters
   
  #define SPI_SCK 18
  #define SPI_MISO 19
  #define SPI_MOSI 23
  #define DW_CS 4
   
  // connection pins
  const uint8_t PIN_RST = 27; // reset pin
  const uint8_t PIN_IRQ = 34; // irq pin
  const uint8_t PIN_SS = 4;   // spi select pin
  ////////////////////////////////////////////////////////////////////////////////////////////////////////
  ///bagian mqtt
  #include <WiFi.h>
  #include <PubSubClient.h>
  #include <Wire.h>
  
  
  // Replace the next variables with your SSID/Password combination
  const char* ssid = ":33333";
  const char* password = "shiro neko";
  
  // Add your MQTT Broker IP address, example:
  const char* mqtt_server = "192.168.185.12";
  WiFiClient espClient;
  PubSubClient client(espClient);
  long lastMsg = 0;
  char msg[50];
  int value = 0;
  ///////////////////////reconect dan subs///////
  void reconnect(){
  // Loop until we're reconnected
  while (!client.connected()){
   if (WiFi.status() == WL_CONNECTED){
     Serial.println("Connected to WiFi");
   }
   else{
    Serial.println("Failed to connect to WiFi");
   }
   Serial.print("Attempting MQTT connection...");
  // Attempt to connect
    if (client.connected()) {
     Serial.println("connected");
      listsubscribe();
  
    }
    else{
     Serial.print("failed, rc=");
     Serial.print(client.state());
     Serial.println(" try again in 5 seconds");
  // Wait 5 seconds before retrying
     delay(5000);
    }  
   }
  }
  ///////////////////////////////////////////////////////
  ///////list state////////////////////////////////////
  bool modecalibrasidelayantena=false;
  bool modekalibrasiperhitunganruangan=false;
  bool tagmode=false;
  int urutan=1; 
  int urutansekarang=1;
  
  //////////////////////////////////
  void setup(){
    
    setup_wifi();//setup wifi
    client.setServer(mqtt_server, 1883);
    String clientId = "ESP32Client" + String(random(0xffff), HEX);
    client.connect(clientId.c_str());
    client.setCallback(callback);
    Serial.begin(115200);
    delay(1000); //wait for serial monitor to connect
    //init the configuration
    SPI.begin(SPI_SCK, SPI_MISO, SPI_MOSI);
    DW1000Ranging.initCommunication(PIN_RST, PIN_SS, PIN_IRQ); //Reset, CS, IRQ pin
    // set antenna delay for anchors only. Tag is default (16384)
    DW1000.setAntennaDelay(Adelay);
    
    DW1000Ranging.attachNewRange(newRange);
    DW1000Ranging.attachNewDevice(newDevice);
    DW1000Ranging.attachInactiveDevice(inactiveDevice);
//      DW1000Ranging.useRangeFilter(true);

    //start the module as an anchor, do not assign random short address
    DW1000Ranging.startAsAnchor(anchor_addr, DW1000.MODE_LONGDATA_RANGE_LOWPOWER, false);
    // DW1000Ranging.startAsAnchor(ANCHOR_ADD, DW1000.MODE_SHORTDATA_FAST_LOWPOWER);
    // DW1000Ranging.startAsAnchor(ANCHOR_ADD, DW1000.MODE_LONGDATA_FAST_LOWPOWER);
    // DW1000Ranging.startAsAnchor(ANCHOR_ADD, DW1000.MODE_SHORTDATA_FAST_ACCURACY);
    // DW1000Ranging.startAsAnchor(ANCHOR_ADD, DW1000.MODE_LONGDATA_FAST_ACCURACY);
    // DW1000Ranging.startAsAnchor(ANCHOR_ADD, DW1000.MODE_LONGDATA_RANGE_ACCURACY);
    listsubscribe();
  }
  ////////////////////////////////////////////////////////////
  void setup_wifi() {
    delay(10);
    // We start by connecting to a WiFi network
    Serial.print("Connecting to ");
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
      delay(500);
      Serial.print(".");
    }
    Serial.println("WiFi connected");
  }
  ////////////////////////////////////////////////////////
  void loop(){
    if (!client.connected()){
      reconnect();
    }
    else{
      DW1000Ranging.loop();
      client.loop();
  
    }
  }
  void newRange()
  {
   if(modecalibrasidelayantena==true){
    kalibrasiantena();
    }
   else if(modekalibrasiperhitunganruangan==true){
        kalibrasirumus();
    }
   else{  
  searchrange();
   }
  }
  //////////////////////edit jika pesan subscribe masuk//////////
  void callback(char* topic, byte* message, unsigned int length) {
    Serial.print("Message arrived on topic: ");
    Serial.print(topic);
    Serial.print(". Message: ");
    String messageTemp;
    for (int i = 0; i < length; i++) {
      Serial.print((char)message[i]);
      messageTemp += (char)message[i];
    }
    if(strcmp(topic,"esp32/calibrasijarak")==0){
      Serial.println("mode calibrasi");
      uint16_t Adelay_delta = 100;
      this_anchor_target_distance = 0;
      modecalibrasidelayantena=true;
      }
      if(strcmp(topic,"esp32/calibrasiantena2")==0){
      this_anchor_target_distance=messageTemp.toFloat();
          Serial.println(this_anchor_target_distance);
  
      } 
          if(strcmp(topic,"esp32/comunicateanchor")==0){
            const char* myCharArray = messageTemp.c_str();
            Serial.println(messageTemp);
            if(strcmp(myCharArray,"anchorantena2")==0){
        DW1000Ranging.startAsTag(tag_addr, DW1000.MODE_LONGDATA_RANGE_LOWPOWER, false);
            }
            else{
    DW1000Ranging.startAsAnchor(anchor_addr, DW1000.MODE_LONGDATA_RANGE_LOWPOWER, false);
  
              }
            modekalibrasiperhitunganruangan=true;
      } 
  }
  //////////////////////////////////////////////////////////////////////////////////////////////
  void newDevice(DW1000Device *device)
  {
    Serial.print("Device added: ");
    Serial.println(device->getShortAddress(), HEX);
  }
  void inactiveDevice(DW1000Device *device)
  {
    Serial.print("Delete inactive device: ");
    Serial.println(device->getShortAddress(), HEX);
  }
  /////////////////////////////////////////////////////////////////////////////////////////
  void searchrange(){
  #define NUMBER_OF_DISTANCES 1
    float dist = 0.0;
    for (int i = 0; i < NUMBER_OF_DISTANCES; i++) {
      dist += DW1000Ranging.getDistantDevice()->getRange();
    }
    dist = dist/NUMBER_OF_DISTANCES;
  //  if(dist>0){
  //  int val_int = (int) dist;  // compute the integer part of the float
  //  float val_float = (abs(dist) - abs(val_int)) * 100000;
  //  int val_fra = (int)(val_float * val_int);
        Serial.println(dist);
  //  sprintf(msg, "%d.%d", val_int, val_fra);
    sprintf(msg, "%.2f", dist); // Convert val to a char array with 2 decimal places
    client.publish("esp32/jarak2", msg);
    int delayTime = random(100, 701); // Generate a random number between 100 and 500
  delay(delayTime);
  //  }
    }
    /////////////////////////////////////////////
  void kalibrasiantena(){
       if(this_anchor_target_distance!= 0){
        static float last_delta = 0.0;
    Serial.print(DW1000Ranging.getDistantDevice()->getShortAddress(), DEC);
    float dist = 0;
        if(DW1000Ranging.getDistantDevice()->getRange()<10){
    for (int i = 0; i < 100; i++) {
      // get and average 100 measurements
      dist += DW1000Ranging.getDistantDevice()->getRange();
    }
    dist /= 100.0;
    Serial.print(",");
    Serial.print(dist); 
    if (Adelay_delta < 3) {
      Serial.print(", final Adelay ");
      Serial.println(this_anchor_Adelay);
      int val_int = (int) this_anchor_Adelay;  // compute the integer part of the float
  
  float val_float = (abs(this_anchor_Adelay) - abs(val_int)) * 100000;
  
  int val_fra = (int)val_float;
    sprintf (msg, "%d.%d", val_int, val_fra); //
    Serial.print("delay=");
    Serial.print(msg);
  
    modecalibrasidelayantena=false;
    }
   
    float this_delta = dist - this_anchor_target_distance;  //error in measured distance
   
    if ( this_delta * last_delta < 0.0) Adelay_delta = Adelay_delta / 2; //sign changed, reduce step size
      last_delta = this_delta;
    
    if (this_delta > 0.0 ) this_anchor_Adelay += Adelay_delta; //new trial Adelay
    else this_anchor_Adelay -= Adelay_delta;
    
    Serial.print(", Adelay = ");
    Serial.println (this_anchor_Adelay);
  //  DW1000Ranging.initCommunication(PIN_RST, PIN_SS, PIN_IRQ); //Reset, CS, IRQ pin
    DW1000.setAntennaDelay(this_anchor_Adelay);
      }}
      else{
  //      Serial.print("tunggu jarak anchor dengan tag");
        delay(100);
        }}
    /////////////////////////////////////////////
    void kalibrasirumus(){
  char buffer[6];
  itoa(DW1000Ranging.getDistantDevice()->getShortAddress(),buffer,10);
  String alamatachor = String(buffer);
  Serial.print(alamatachor);
    client.publish("log", buffer);
  //
  //  #define NUMBER_OF_DISTANCES 1
  //  float dist = 0.0;
  //  for (int i = 0; i < NUMBER_OF_DISTANCES; i++) {
  //    dist += DW1000Ranging.getDistantDevice()->getRange();
  //  }
  //  dist = dist/NUMBER_OF_DISTANCES;
  //  if(dist>0){
  //  int val_int = (int) dist;  // compute the integer part of the float
  //  float val_float = (abs(dist) - abs(val_int)) * 100000;
  //  int val_fra = (int)(val_float * val_int);
  //      Serial.println(dist);
  //  sprintf(msg, "%d.%d", val_int, val_fra);
  //  client.publish(buffer, msg);
  //    }
    }
    //////////////////////////////////////////////
    void listsubscribe(){
     client.subscribe("esp32/calibrasiantena2");
     client.subscribe("esp32/calibrasijarak");
     client.subscribe("esp32/comunicateanchor");
     client.subscribe("esp32/jarakcalibrasiantena2");
     }
   
