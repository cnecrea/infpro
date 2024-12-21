# Cutremur România (INFP) - Integrare pentru Home Assistant 🏠🇷🇴

Această integrare pentru Home Assistant oferă un senzor care monitorizează datele seismice din România, folosind informațiile oficiale de la **Institutul Național pentru Fizica Pământului (INFP)**. Integrarea este configurabilă prin interfața UI și permite personalizarea intervalului de actualizare. 🚀

## 🌟 Caracteristici

- **🔍 Monitorizare Cutremure**: 
  - Monitorizează ultimul cutremur detectat în România.

- **🔍 Monitorizare Cutremure**: 
  - Monitorizează ultimul cutremur detectat în România.

- **📊 Atribute disponibile**:
  - **ID**: ID-ul evenimentului seismic.
  - **Magnitudine (ML)**: Magnitudinea pe scara locală.
  - **Magnitudinea Momentului (Mw)**: Puterea reală a cutremurului.
  - **Ora (UTC)**: Ora în format UTC.
  - **Ora locală**: Ora locală a evenimentului.
  - **Coordonate**: Latitudine și longitudine ale epicentrului.
  - **Adâncime (km)**: Adâncimea epicentrului.
  - **Zonă**: Zona epicentrului.
  - **Intensitate**: Intensitatea percepută.
  - **Alerta**: Da/Nu (folosește atribut pentru automatizări)

---

## ⚙️ Configurare

### 🛠️ Interfața UI:
1. Instalează integrarea prin HACS sau manual (vezi detaliile de mai jos). 
2. Adaugă integrarea din meniul **Setări > Dispozitive și Servicii > Adaugă Integrare**.
3. Specifică intervalul de actualizare (în secunde, între `10` și `3600`).

### ⏱️ Intervalul de actualizare:
- Poate fi configurat din interfața UI.
- Toate configurările sunt salvate într-un fișier JSON local specific integrării.

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
description: Notificare dacă magnitudinea depășește 4.5
trigger:
  - platform: numeric_state
    entity_id: sensor.cutremur
    above: 4.5
action:
  - service: notify.mobile_app_your_phone
    data:
      title: "Cutremur Detectat! 🌋"
      message: "Un cutremur cu magnitudinea {{ states('sensor.cutremur') }} a fost detectat."
mode: single
```
## 🧑‍💻 Contribuții

Contribuțiile sunt binevenite! Simte-te liber să trimiți un pull request sau să raportezi probleme [aici](https://github.com/cnecrea/infpro/issues).

## 🌟 Suport
- Dacă îți place această integrare, oferă-i un ⭐ pe [GitHub](https://github.com/cnecrea/infpro/)! 😊
