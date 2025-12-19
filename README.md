# UIC Senior Design Project 

### PCB Design Contributors:

Narain Vazquez  
Nico Gomez

### Repository Description:

This repository specifically holds the contents of the electrical portion of the Aeroguard Project, including the schematics for our PCB design, power distribution, and system integration.  

All included files are designed to work specifically with **KiCad**, and the project files created for this project can be found in the following directories:  

- `libraries_v4` – contains custom KiCad libraries created for the project.  
- `rpi-aeroguard-template_v4` – contains the KiCad project files and PCB templates for the Aeroguard design.

### Aeroguard Description & Demo:

The Aeroguard Project is a senior design initiative focused on developing an autonomous aerial monitoring system. The system runs on a Linux-based platform and leverages YOLOv9 for real-time detection of fires, smoke, and safety equipment protocol. Video is streamed over RTMP, and the system can trigger alerts using speakers and lights to notify personnel of hazards or protocol violations.

The video demo showcases our Aeroguard prototype board in action. It demonstrates the fire detection feature, which triggers the speaker alerting system (note: the video itself has no audio).

![Aeroguard Demo](aeroguard_demo.gif)
![Prototype Board](pcb_render.png)
![Image Detection](pcb_render.png)


### Raspberry Pi Compute Module 4 (CM4) Carrier Template
![Rendered example of RPi CM4 Carrier Template PCB](https://raw.githubusercontent.com/ShawnHymel/rpi-cm4-carrier-template/main/images/rpi-cm4-carrier-template-rendered.png)
