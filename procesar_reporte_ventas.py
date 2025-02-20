import os
from google.cloud import storage, bigquery
import pandas as pd
import io
import logging

# ========================== CONFIGURACIÓN INICIAL ========================== #

# Configuración de logging para registrar el proceso en un archivo log
log_file = "procesamiento_tarea.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_file, mode='w', encoding='utf-8')]
)

# Configuración de credenciales para Google Cloud
SERVICE_ACCOUNT_FILE = "C:/Users/mejia/MisProyectos/Claves/valetdata-3dec9d3372ec.json"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = SERVICE_ACCOUNT_FILE

# Inicializar clientes de Google Cloud (Storage y BigQuery)
try:
    storage_client = storage.Client()
    bq_client = bigquery.Client()
    logging.info("Clientes de Google Cloud inicializados correctamente.")
except Exception as e:
    logging.error(f"Error al inicializar los clientes de Google Cloud: {e}")
    exit()

# Configuración del bucket y archivos
bucket_name = "gustavoaprende"
archivos = [
    "C:/Users/mejia/Downloads/datosaliaddo/Reporte_Venta_Detallado_2024.xlsx",
    "C:/Users/mejia/Downloads/datosaliaddo/Reporte_Venta_Detallado_2025.xlsx"
]

# ========================== FUNCIONES AUXILIARES ========================== #

# Función para subir un archivo a Google Cloud Storage
def subir_a_cloud_storage(local_path, bucket_name, blob_name):
    try:
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(local_path)

        if blob.exists():
            os.remove(local_path)
            logging.info(f"Archivo {local_path} subido exitosamente y eliminado localmente.")
        else:
            logging.warning(f"El archivo {local_path} no fue eliminado localmente porque la subida falló.")
    except Exception as e:
        logging.error(f"Error al subir el archivo a Cloud Storage: {e}")
        exit()

# Función para descargar un archivo desde Google Cloud Storage
def descargar_de_cloud_storage(bucket_name, blob_name):
    try:
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        data = blob.download_as_bytes()
        logging.info(f"Archivo descargado exitosamente desde {bucket_name}/{blob_name}.")
        return data
    except Exception as e:
        logging.error(f"Error al descargar el archivo desde Cloud Storage: {e}")
        exit()

# Función para procesar una hoja de Excel y formatear los datos
def procesar_hoja(data, table_id, sheet_name, skiprows=3):
    try:
        # Leer el archivo Excel en memoria
        df = pd.read_excel(io.BytesIO(data), sheet_name=sheet_name, skiprows=skiprows, engine="openpyxl", usecols=None)

        # Obtener estructura de la tabla en BigQuery
        table = bq_client.get_table(table_id)
        table_columns = [field.name for field in table.schema]

        # Asegurar que todas las columnas de BigQuery estén en el DataFrame
        df = df.reindex(columns=table_columns, fill_value="")

        # Normalizar formato de fechas
        date_columns = ["Fecha", "Fechadevenc", "Fecha_de_venc"]
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], dayfirst=True, errors="coerce").dt.strftime("%Y-%m-%d")

        # Convertir columnas numéricas
        float_columns = ["Valor_Unitario", "Costo_Unitario", "SubTotal", "Descuento", "Total", "Anticipo", "Saldo", "Retenciones"]
        int_columns = ["Cantidad"]

        for col in float_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(float)

        for col in int_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

        # Convertir "No_orden_de_compra" a STRING para evitar errores
        if "No_orden_de_compra" in df.columns:
            df["No_orden_de_compra"] = df["No_orden_de_compra"].astype(str)

        # Limpiar caracteres especiales como saltos de línea
        df.replace({"\n": " ", "\r": " "}, regex=True, inplace=True)

        # Eliminar filas completamente vacías
        df.dropna(how='all', inplace=True)

        # Exportar archivo para depuración
        debug_file = f"debug_{sheet_name}.csv"
        df.to_csv(debug_file, index=False)
        logging.info(f"Datos de la hoja '{sheet_name}' procesados correctamente y guardados en {debug_file} para revisión.")

        return df
    except Exception as e:
        logging.error(f"Error al procesar la hoja '{sheet_name}': {e}")
        return None

# Función para cargar datos en BigQuery
def cargar_a_bigquery(dataframe, table_id):
    try:
        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.CSV,
            skip_leading_rows=1,
            write_disposition="WRITE_APPEND"
        )

        temp_file = "temp.csv"
        dataframe.to_csv(temp_file, index=False, encoding='utf-8')

        with open(temp_file, "rb") as source_file:
            load_job = bq_client.load_table_from_file(source_file, table_id, job_config=job_config)
        load_job.result()
        logging.info(f"Datos cargados exitosamente en la tabla {table_id}.")

        os.remove(temp_file)
        logging.info(f"Archivo temporal {temp_file} eliminado.")
    except Exception as e:
        logging.error(f"Error al cargar datos en la tabla {table_id}: {e}")

# ========================== PROCESO PRINCIPAL ========================== #

for archivo in archivos:
    año = archivo[-9:-5]  # Extrae el año del nombre del archivo
    cloud_file_path = f"ReportesAliaddo/Reporte_Venta_Detallado_{año}.xlsx"

    subir_a_cloud_storage(archivo, bucket_name, cloud_file_path)
    data = descargar_de_cloud_storage(bucket_name, cloud_file_path)

    table_id_venta = "valetdata.AliaddoData.TblVenta"
    df_venta = procesar_hoja(data, table_id_venta, sheet_name='Reporte')
    if df_venta is not None:
        cargar_a_bigquery(df_venta, table_id_venta)

    table_id_detalle = "valetdata.AliaddoData.TblVentaDetalle"
    df_detalle = procesar_hoja(data, table_id_detalle, sheet_name='Reporte_Detalle')
    if df_detalle is not None:
        cargar_a_bigquery(df_detalle, table_id_detalle)

logging.info("Proceso completado.")
