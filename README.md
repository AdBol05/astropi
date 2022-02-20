# Laborky.cz
![image](https://user-images.githubusercontent.com/98588523/152417709-2008e586-28c6-4f2a-9e84-af8307ac01b9.png)
Developed at Laborky.cz

# Astropi
                   ESA Payload                 Powered by Raspberry Pi 

                %%%%%%%%%%%%%%%%               .%.%.%.%.      .%.%.%.%.
            %%%%%%%%%%%%%%%%%%%%%%%%          % \\\\\\\\\    ///////// %
         %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%        % \\\\  \\\\////  //// %
       %%%%%%%%%%%%%%%%%%%%%%@@@@@@@%%%%        % \\\\\\     /////// %
     %%%%%%%%%%%%%%%%%%%@@@@@@@@@@@@@@@%        % @@@  @@@@@@  @@@ %
    %%%%%%%%%%%%%%%%%@@@@@@%%%%%%%%@@@@@%      % @@              @@ %
    %%%%%%%@@@@%%%%%%@@@@@@%%%%%%%%%@@@@@    .%    @@@@@@  @@@@@@    %.
    %%%%%%@@@@@@%%%%%@@@@@%%@@@@@@@@@@@@@   % @@@ @@@@@@@  @@@@@@@ @@@ %
    %%%%%%%@@@@%%%%%%@@@@@@%%%%%%%%%%%%%%   % @@   @@@@      @@@@   @@ %
     %%%%%%%%%%%%%%%%%@@@@@@%%%%%%%%%%%%     %          @@@@          %
      %%%%%%%%%%%%%%%%%%@@@@@@%%%%%%%%%       % @@@@   @@@@@@   @@@@ %
       %%%%%%%%%%%%%%%%%%%@@@@@@@@@@@@         % @@@@@  @@@@  @@@@@ %
        %%%%%%%%%%%%%%%%%%%%%%%@@@@@@           '%% @@        @@ %%'
           %%%%%%%%%%%%%%%%%%%%%%%                 '%%. @@@@ .%%'
               %%%%%%%%%%%%%%%%                        '%%%%'


Astropi life in space experiment repository

# ISS_environment
Measuring changes in life environment of ISS caused by human presence using temperature, humidity, pressure and pir sensors.

Required libraries: csv, sense_hat, pathlib, datetime, time, RPi.GPIO
(should be included in Flight OS)

# Particle_detection
Detecting particles using raspberry pi HQ camera. Deleting empty images and saving only images with a particle detected.

Required libraries: csv, sense_hat, pathlib, datetime, time, picamera, orbit, skyfield.api, PIL, pycoral, os
(should be included in Flight OS)

# Deceleration
Measuring chages in speed of ISS caused by Earth’s magfnetic field.

# Lightning detection
Detects spikes in magnetic field caused by storms an Earth and tries to photograp Blue jets, red sprites and ELVES
![250px-Upperatmoslight1](https://user-images.githubusercontent.com/98588523/154854886-024aa0d7-b9f0-4820-b4e0-ee78c8081846.jpg)

# Coral
Retrained model used for Particle detection

                  project filestructure: /label.txt                  //label file for classes detrmination
                                         /particle.tflite            //retrained model used for classification
                                         /data.csv                   //data output file
                                         /main.py                    //main script
                                         /particle_{counter}.jpg     //outputted images classified as particle images
                                         
                  training filestructure: /Downloads/Coral/classify.py     //classification test script
                                          /Downloads/Coral/train.py        //training script
                                          /Downloads/Coral/models          //models for training
                                          /Documents/coral/train/blank     //training images {class: "blank"}
                                          /Documents/coral/train/particle  //training images {class: "particle"}
