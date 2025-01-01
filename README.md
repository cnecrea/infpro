![logo](https://github.com/user-attachments/assets/4bef00a2-ff4b-4494-9d8a-ed3740671c04)


# Cutremur România (INFP) - Integrare pentru Home Assistant 🏠🇷🇴

Această integrare pentru Home Assistant oferă **doi senzori** care monitorizează datele seismice din România, folosind informațiile oficiale de la **Institutul Național pentru Fizica Pământului (INFP)**. Integrarea este configurabilă prin interfața UI și permite personalizarea orașului monitorizat și a intervalului de actualizare. 🚀

## 🌟 Caracteristici

### Senzor `Cutremur`:
- **🔍 Monitorizare Generală**:
  - Urmărește datele generale despre ultimul cutremur detectat.
- **📊 Atribute disponibile**:
  - **ID Eveniment**: ID-ul evenimentului seismic.
  - **Magnitudine (ML)**: Magnitudinea pe scara locală.
  - **Magnitudinea Momentului (Mw)**: Puterea reală a cutremurului.
  - **Ora locală**: Ora locală a evenimentului.
  - **Coordonate**: Latitudine și longitudine ale epicentrului.
  - **Adâncime (km)**: Adâncimea epicentrului.
  - **Zonă**: Zona epicentrului.
  - **Intensitate**: Intensitatea percepută.
  - **Alerta**: Indică dacă evenimentul este nou.

### Senzor `Date analiză`:
- **🔍 Monitorizare Impact Oraș**:
  - Afișează date detaliate despre impactul cutremurului asupra unui oraș specific.
- **📊 Atribute disponibile**:
  - **Oraș**: Orașul monitorizat.
  - **Județ**: Județul în care se află orașul.
  - **Distanță (km)**: Distanța față de epicentru.
  - **Accelerația maximă a solului (PGA)**: Mișcarea maximă a solului (procent din accelerația gravitațională).
  - **Viteza maximă a solului (PGV)**: Mișcarea maximă a solului în cm/s.
  - **Intensitate**: Gradul perceput al cutremurului.
  - **Intensitate accelerației**: Intensitatea resimțită a accelerației solului în orașul monitorizat.

---

## ⚙️ Configurare

### 🛠️ Interfața UI:
1. Instalează integrarea prin HACS sau manual (vezi detaliile de mai jos). 
2. Adaugă integrarea din meniul **Setări > Dispozitive și Servicii > Adaugă Integrare**.
3. Specifică intervalul de actualizare (în secunde, între `10` și `3600`).
4. Alege un oraș din lista disponibilă pentru monitorizare.

---

## 🚀 Instalare

### 💡 Instalare prin HACS:
1. Adaugă [depozitul personalizat](https://github.com/cnecrea/infpro) în HACS. 🛠️
2. Caută integrarea **Cutremur România (INFP)** și instaleaz-o. ✅
3. Repornește Home Assistant și configurează integrarea. 🔄

### ✋ Instalare manuală:
1. Clonează sau descarcă [depozitul GitHub](https://github.com/cnecrea/infpro). 📂
2. Copiază folderul `custom_components/infpro` în directorul `custom_components` al Home Assistant. 🗂️
3. Repornește Home Assistant și configurează integrarea. 🔧

---

## ✨ Exemple de utilizare

### 🔔 Automatizare bazată pe Magnitudine:
Creează o automatizare pentru a primi notificări atunci când magnitudinea unui cutremur depășește un anumit prag.

```yaml
alias: Notificare Cutremur
description: Notificare dacă magnitudinea depășește 4.5 și alerta este "Da"
trigger:
  - platform: state
    entity_id: sensor.cutremur
    attribute: "Alerta"
    to: "Da"
condition:
  - condition: numeric_state
    entity_id: sensor.cutremur
    attribute: Magnitudine (ML)
    above: 4.5
action:
  - service: notify.mobile_app_your_phone
    data:
      title: "Cutremur Detectat! 🌋"
      message: "Un cutremur cu magnitudinea {{ states('sensor.cutremur') }} a fost detectat."
mode: single
```

### 🔍 Card pentru Dashboard:
Afișează informații despre cutremure și impactul asupra unui oraș pe interfața Home Assistant.

```yaml
type: entities
title: Monitorizare Cutremure
entities:
  - entity: sensor.cutremur
    name: Ultimul Cutremur
  - entity: sensor.date_analiza
    name: Date analiză
```

---

## 🧑‍💻 Contribuții

Contribuțiile sunt binevenite! Simte-te liber să trimiți un pull request sau să raportezi probleme [aici](https://github.com/cnecrea/infpro/issues).

---

## 🌟 Suport
Dacă îți place această integrare, oferă-i un ⭐ pe [GitHub](https://github.com/cnecrea/infpro/)! 😊
