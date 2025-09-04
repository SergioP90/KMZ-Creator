# KMZ-Creator
**A CMD application to create and modify KMZ files easily. All KMZ files generated with this application can be opened directly in Google Earth.**

![Version](https://img.shields.io/badge/Version-1.0-blue)
![Windows](https://img.shields.io/badge/Windows-COMPATIBLE-brightgreen) 
![Linux](https://img.shields.io/badge/Linux-UNTESTED-yellow) 
![Mac](https://img.shields.io/badge/MAC-INCOMPATIBLE-red) 


---

## Features
Legend:  
🟢 - Implemented  
🟡 - Implemented, has exceptions  
🔴 - Not implemented

| **Feature**                     | **Status** |
|---------------------------------|-----------|
| Create new KMZ files             | 🟢        |
| Open existing KMZ                | 🟢        |
| List points                      | 🟢        |
| List other features              | 🔴        |
| Add Points in Lat Lon / UTM      | 🟢        |
| Add Points from a file           | 🟡        |
| Add lines / Routes               | 🔴        |
| Point manipulation               | 🟡        |
| Line manipulation                | 🔴        |
| Distance calculations            | 🟢        |
| Height data                      | 🔴        |
| Complex geometry                 | 🔴        |
| Folder structure manipulation    | 🔴        |
| UTM datum selection              | 🟡        |

---

## ⚠️ Exceptions on features
- **Add Points from a file**: Only supports `.txt` files with a specific configuration using UTM.  
- **Point manipulation**: Will not work properly on KMZ files not generated with this app.  
- **UTM datum selection**: Currently supports WGS84 (Default), NAD83, and ETRS89.  

---

## 🛠 Requirements
- Python 3.12.4 or higher  


---

## 💾 Installation

### From source
1. Download [Python 3.12.4 or higher](https://www.python.org/) if you don't have it yet
2. Download the zip and extract (or clone using Git)  
3. Run `pip install -r requirements.txt` on a terminal 
    - *A virtual enviroment is highly recommended*
4. Run `main.py`  

### From exe
1. Download the zip and extract  
2. Run `KMZ-Creator.exe`  

---

## 💡 Example Usages

### Create a new KMZ from a list of points
```bash
> create
> addlist my_placemarks.txt
> save my_kmz.kmz
```
