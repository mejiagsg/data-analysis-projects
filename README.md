# Data Analysis Projects 📊

This repository contains projects related to data analysis, automation, and data processing. 

## 📌 Project: Sales Report Processing
The `procesar_reporte_ventas.py` script automates the extraction, transformation, and loading (ETL) of sales reports from Excel files into **Google Cloud Storage** and **BigQuery**.

### 🚀 Features:
- Uploads Excel sales reports to Google Cloud Storage.
- Processes and cleans the data before loading it into BigQuery.
- Handles data type conversions and error handling for smooth data ingestion.
- Logs all activities for monitoring and debugging.

### 🛠️ Technologies Used:
- **Python** (pandas, openpyxl, google-cloud-storage, google-cloud-bigquery)
- **Google Cloud Platform** (Storage, BigQuery)
- **ETL Pipeline** for data processing

### 📂 Files:
- `procesar_reporte_ventas.py` → Python script for automating sales data ingestion.
- `README.md` → Project documentation.

### 📌 How to Use:
1️⃣ **Clone the repository:**
   ```bash
   git clone https://github.com/mejiagsg/data-analysis-projects.git

2️⃣ **Install dependencies:**
   ```bash
   pip install pandas openpyxl google-cloud-storage google-cloud-bigquery

3️⃣ **Run the script:**
  ```bash
   python procesar_reporte_ventas.py
