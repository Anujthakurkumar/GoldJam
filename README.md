<p align="center">
  <img src="assets/GoldJam.png" alt="GoldJam Logo" width="300">
</p>

<h1 align="center">GoldJam – WiFi Jamming Tool</h1>

<p align="center">
  <i>WiFi jamming and scanning utility built for Kali Linux using Python and Aircrack-ng</i>
</p>

<p align="center">
  <a href="https://github.com/GoldSkull-777/GoldJam/stargazers">
    <img src="https://img.shields.io/github/stars/GoldSkull-777/GoldJam?style=flat-square" />
  </a>
  <a href="https://github.com/GoldSkull-777/GoldJam/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/GoldSkull-777/GoldJam?style=flat-square" />
  </a>
</p>

---

## 📽️ Demo

![GoldJam Demo](assets/Gif.gif)

---

## ⚙️ Features

- 📡 Live WiFi scanning using `airodump-ng`
- 🎯 Real-time target selection
- 🔥 Deauthentication attacks using `aireplay-ng`
- 🖥️ Rich terminal UI with `rich`
- 🧹 Automatic interface recovery after attacks

---

## 📦 Requirements

- ✅ Kali Linux 2024 or newer
- ✅ Python 3.x
- ✅ `aircrack-ng` installed
- ✅ WiFi adapter with monitor mode & packet injection

---

## 🚀 Installation

```bash
git clone https://github.com/GoldSkull-777/GoldJam.git
cd GoldJam
chmod +x GoldJam.py
sudo python3 GoldJam.py
