# Quadruped AI

![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)
![Box2D](https://img.shields.io/badge/Box-2.3.10-red.svg)
![Pygame](https://img.shields.io/badge/Pygame-2.6.1-red.svg)

![License](https://img.shields.io/badge/license-MIT-green.svg)  
![Contributions](https://img.shields.io/badge/contributions-welcome-orange.svg)  

<p align="center">
  <img src="img/logo.png" alt="logo">
</p>


## 📝 Project Description 
This project is a try to understand how to use box2D with pygame. 🦊🦊🦊

To do so, I construct an AI able to control a quadruped, a fox with real physics, muscles, a world and a pretty low-poly design.

To learn data visualisation, I used Power BI to analyse in details !

🚨The project is not **finish** !🚨

---

## ⚙️ Features  

Constructed : 
- Real physique with muscles, interation with **box2D** library.
- A good-looking with pygame🦊.
- An algorithm to select the best choreography.

Project for the futur :
- A genetic algorithm
- PPO algorithm
- Add some commentary for each .py on the top for a better understanding of my code for AI (and me 🫠)


## Example Outputs

We can control the quadruped, the view (We can see clearly the parallax and the different mode - textured, skeleton and overlay) :
<p align="center">
  <img src="img/Gif-human-controled.gif" alt="Example Outputs : Human controlled">
</p>

Here is the algorithm that select just the best choreography :
<p align="center">
  <img src="img/Gif-select-choregraphy.gif" alt="Example Outputs : Select best choreography">
</p>

I'm currently working on other algorithm such as genetic neural network, PPO...

---

## ⚙️ How it works

Here it is juste a selection of the best choreography and adjusting time in consequence.



## 🗺️ Schema

![Overview](powerBI/img.png)

<details>
<summary>📸 See more data analyse</summary>

![Capture 1](powerBI/img_1.png)
![Capture 2](powerBI/img_2.png)
![Capture 3](powerBI/img_3.png)

</details>

---

## 📂 Repository structure  
```bash
├── test1_physique.py
├── test2_physique.py
│
├── LICENSE
├── README.md
```

---

## 💻 Run it on Your PC  
Clone the repository and install dependencies:  
```bash
git clone https://github.com/Thibault-GAREL/test_box2D_pygame.git
cd test_box2D_pygame

python -m venv .venv #if you don't have a virtual environnement
source .venv/bin/activate   # Linux / macOS
.venv\Scripts\activate      # Windows

pip install box2D pygame

python test1_physique.py # Or the .py you want
```
---

## 📖 Inspiration / Sources  
I code it without any help 😆 !

Code created by me 😎, Thibault GAREL - [Github](https://github.com/Thibault-GAREL)