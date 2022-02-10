# Laborky.cz
![image](https://user-images.githubusercontent.com/98588523/152417709-2008e586-28c6-4f2a-9e84-af8307ac01b9.png)
Developed at Laborky.cz

# astropi
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
