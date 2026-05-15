# 🌍 Zagazig Remote Sensing Analytics

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Node](https://img.shields.io/badge/node-v16%2B-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)

A Full-Stack AI-powered Web and Mobile Application for Hyperspectral Land Cover Classification. This platform provides an end-to-end pipeline covering ENVI data ingestion, feature extraction, Random Forest classification, and dynamic reporting of area statistics and validation metrics.

Developed under the supervision of **Dr. Azhar Ahmed** & **Eng. Assem Ibrahim** at the Electronics & Communication Department, Zagazig University.

---

## ✨ Features

*   **🗂️ ENVI Data Ingestion:** Upload `.hdr` and raw binary datasets seamlessly via a chunked upload processor, engineered locally to handle massive remote sensing data streams without memory crashes.
*   **🧠 Advanced ML Pipeline:** Uses a pre-trained Random Forest model for classifying hyperspectral imagery across versatile geographical regions (e.g., Nile Delta, Ismailia).
*   **📊 Dynamic Classification Dashboard:** Automatically calculates, evaluates, and dynamically displays comprehensive metrics using `scikit-learn` in a clean Glassmorphism UI:
    *   Area Statistics (km² and Scene Percentage)
    *   Overall Accuracy (OA) & Kappa Coefficient
    *   F1-Scores per Class (Water, Vegetation, Urban, Desert)
*   **📱 Cross-Platform Setup:** Ready for native Android compilation leveraging the **Capacitor** build system (`android/` project structure included).
*   **🐳 Production-Ready Deployment:** Supplied with a fully automated `Dockerfile`, `docker-compose.yml`, Nginx configurations, and Shell scripts to streamline server environments.

## 🏗️ Architecture & Tech Stack

*   **Frontend:** HTML5, CSS3, Vanilla JavaScript, Capacitor (Android Port)
*   **Backend:** Node.js, Express.js, Multer (Chunked File Assemblies)
*   **Machine Learning:** Python 3, `scikit-learn`, `numpy`, `spectral` (ENVI IO), `joblib`, `matplotlib`
*   **Infrastructure:** Docker, Nginx, Certbot (SSL), Bash Scripting

## ⚙️ Algorithms & Methodology

1.  **10-band ENVI Feature Extraction:** The input pipeline builds a 10-band feature cube utilizing native spectral bands complemented numerically by Spectral Indices (NDVI, NDWI, NDBI).
2.  **Preprocessing Safeguards:** Handles `.hdr` metadata parsing anomalies, isolates `NaN`/no-data values, dynamically masks shapes, and mitigates scaler crashes.
3.  **Model Transferability Strategy:** The Random Forest algorithm is calibrated geographically to accommodate domain shifts when generalized across different regions.
4.  **Ground-Truth ROI Validation:** Computes classification matrices pixel-by-pixel against locally embedded annotations (`Labeled_ROIs.csv`).

## 🚀 Getting Started

### Prerequisites
*   [Node.js](https://nodejs.org/) (v16.x or higher)
*   [Python](https://www.python.org/) (3.8 or higher)
*   *(Optional)* Docker & docker-compose

### Local Installation

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/MoNabawy-2003/Remote-Sensing-ML.git
    cd Remote-Sensing-ML
    ```

2.  **Backend Setup (Node.js)**
    ```bash
    npm install
    ```

3.  **AI Model Setup (Python)**
    ```bash
    pip install -r requirements.txt
    ```
    > Ensure that your pre-trained `model.pkl` and `scaler.pkl` are located within the `ai_model/` directory alongside `Labeled_ROIs.csv`.

4.  **Run the Server**
    ```bash
    node server.js
    ```

5.  **Access the Dashboard**
    Open your browser and navigate to: [http://localhost:3000](http://localhost:3000)

### Docker Deployment

To run the entire platform in isolated containers:
```bash
docker-compose up --build -d
```

## 👥 Project Team

*   **Ahmed Shawadfi** – Analog IC Engineer
*   **Ahmed Sabry** – Cloud & Full-Stack Engineer
*   **Mohamed Ayman Nabawi** – Cloud & DevOps Engineer
*   **Ibrahem Mohamed** – Network & Cloud Engineer
*   **Abdullah Reda** – Digital IC Engineer
*   **Mohamed Wagih** – Cyber Security Engineer
*   **Mariem Omar** – Telecommunication Engineer

---
*Disclaimer: This project was built for academic purposes as part of the Remote Sensing curriculum at Zagazig University.*
