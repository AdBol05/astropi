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

# Coral
Retrained model used for Particle detection

                  project filestructure: /label.txt                  //label file for classes detrmination
                                         /model/particle.tflite      //retrained model used for classification
                                         /image                      //images directory (images are removed, when classified as blank)
                                         /data.csv                   //data output file
                                         /main.py                    //main script
                                         
                  training filestructure: /Downloads/Coral/classify.py     //classification test script
                                          /Downloads/Coral/train.py        //training script
                                          /Downloads/Coral/models          //models for training
                                          /Documents/coral/train/blank     //training images {class: "blank"}
                                          /Documents/coral/train/particle  //training images {class: "particle"}
