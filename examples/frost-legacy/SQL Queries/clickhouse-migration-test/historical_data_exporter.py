import json
import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta
from enum import Enum
from pathlib import Path
from threading import Lock

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import typer
from dotenv import load_dotenv

load_dotenv(
    dotenv_path=Path(__file__)
    .parent.joinpath(f".env.{os.getenv('ENV', 'dev')}")
    .absolute()
)

import boto3
from botocore.exceptions import ClientError
from database_helper import DatabaseHelper

session = boto3.Session()

s3 = session.client("s3")
app = typer.Typer()

logging.basicConfig()
logger = logging.getLogger("DataExporter")
logger.setLevel(logging.INFO)
ERRORS_LOCK = Lock()

# Create logs directory if it doesn't exist
Path("./logs").mkdir(exist_ok=True)

# Create file handler
file_handler = logging.FileHandler(
    f"./logs/data_exporter_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
)
file_handler.setLevel(logging.ERROR)

# Create formatter
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(file_handler)

BUCKET = "frost-sensor-data-cold-storage"

# Change this to whatever path you want as the prefix for the data
S3_PREFIX = "dev/exports/images-rmt"
if os.environ.get("ENV") == "prod":
    logger.info("Running in production environment, changing S3_PREFIX")
    S3_PREFIX = "prod/sql-server-exports"

# We could make these inputs to the script
START_DATE = date(2024, 1, 1).isoformat()
END_DATE = date.today().isoformat()


# transform funcs
def transform_transmissions(transmissions):
    transmissions["VendorDeviceID"] = transmissions.apply(
        lambda row: row["VendorReadingID"].split("_")[0], axis=1
    )
    transmissions["CaptureTimestampUTC"] = transmissions.apply(
        lambda row: row["VendorReadingID"].split("_")[1], axis=1
    )
    del transmissions["VendorReadingID"]


def transform_images(images):
    images["CameraVersion"] = images.apply(
        lambda row: (
            row["VendorImageID"].split("_")[0]
            if len(row["VendorImageID"].split("_")) == 3
            and row["VendorImageID"].split("_")[0][0] == "v"
            else ""
        ),
        axis=1,
    )

    images["VendorDeviceID"] = images.apply(
        lambda row: (
            row["VendorImageID"].split("_")[1]
            if len(row["VendorImageID"].split("_")) == 3
            and row["VendorImageID"].split("_")[1].startswith("e00fce")
            else ""
        ),
        axis=1,
    )

    images["CaptureTimestampUTC"] = images.apply(
        lambda row: _parse_capture_timestamp_utc(row["VendorImageID"]),
        axis=1,
    )

    images["ImageBucket"] = images.apply(
        lambda row: _parse_image_url(row["ImageUrl"])[0], axis=1
    )

    images["ImageFormat"] = images.apply(
        lambda row: _parse_image_url(row["ImageUrl"])[1], axis=1
    )

    images["AmbientLight"] = images.apply(
        lambda row: (
            int(row["AmbientLight"])
            if row["AmbientLight"] and row["AmbientLight"].isdigit()
            else 0
        ),
        axis=1,
    )

    images["Contrast"] = images.apply(
        lambda row: (
            int(row["Contrast"]) if row["Contrast"] and row["Contrast"].isdigit() else 0
        ),
        axis=1,
    )

    images["Brightness"] = images.apply(
        lambda row: (
            int(row["Brightness"])
            if row["Brightness"] and row["Brightness"].isdigit()
            else 0
        ),
        axis=1,
    )

    images["Exposure"] = images.apply(
        lambda row: (
            int(row["Exposure"]) if row["Exposure"] and row["Exposure"].isdigit() else 0
        ),
        axis=1,
    )

    images["ModelVersion"] = images.apply(
        lambda row: (row["ModelVersion"] if row["ModelVersion"] else ""),
        axis=1,
    )

    images["IsComplete"] = images.apply(
        lambda row: (row["IsComplete"] == 1),
        axis=1,
    )
    images["IsBurstImage"] = images.apply(
        lambda row: (row["IsBurstImage"] == 1),
        axis=1,
    )

    images["Version"] = images.apply(
        lambda row: (
            1 if row["IsComplete"] == 0 else 2 if row["ModelVersion"] == "" else 3
        ),
        axis=1,
    )

    images["CreatedDateTimeUTC"] = images.apply(
        lambda row: (row["CreateDateTimeUTC"]),
        axis=1,
    )
    del images["CreateDateTimeUTC"]

    images["CVAssessmentDateTimeUTC"] = images.apply(
        lambda row: (row["ModifiedDateTimeUTC"]) if row["ModifiedDateTimeUTC"] else "",
        axis=1,
    )

    images["ImageAssembledDateTimeUTC"] = images.apply(
        lambda row: (row["CreatedDateTimeUTC"]) if row["CreatedDateTimeUTC"] else "",
        axis=1,
    )

    cv_columns_to_default = [
        "NightClearPavement",
        "NightSnowing",
        "NightWetPavement",
        "NightSnowOnRoad",
        "NightPartialSnowOnRoad",
        "DaySnowing",
        "DayPartialSnowOnRoad",
        "DayClearPavement",
        "DayWetPavement",
        "DaySnowOnRoad",
        "Night",
        "Sunny",
        "Cloudy",
        "ClearPavement",
        "WetPavement",
        "SnowOnRoad",
        "PartialSnowOnRoad",
        "Snowing",
        "Raining",
        "IcedLens",
    ]

    for col in cv_columns_to_default:
        images[col] = images.apply(
            lambda row: (row[col] if row[col] else 0),
            axis=1,
        )


def transform_sds_readings(sds_readings):
    pass


class ImportType(Enum):
    TRANSMISSIONS = "transmissions"
    IMAGES = "images"
    SDS = "sds"


query_mapping = {
    ImportType.TRANSMISSIONS: "GetTransmissionsDump.sql",
    ImportType.IMAGES: "images.sql",
    ImportType.SDS: "GetSDSDump.sql",
}


transform_mapping = {
    ImportType.TRANSMISSIONS: transform_transmissions,
    ImportType.IMAGES: transform_images,
    ImportType.SDS: transform_sds_readings,
}


# example usage: python historical_data_exporter.py export-to-s3 images --max-workers 4
@app.command()
def export_to_s3(
    import_type: ImportType,
    overwrite: bool = False,
    start_date: datetime = START_DATE,
    end_date: datetime = END_DATE,
    max_workers: int = 4,
):
    query_and_validate_async(
        import_type=import_type,
        export=True,
        overwrite=overwrite,
        validate=True,
        date_range=date_range(start_date, end_date),
        max_workers=max_workers,
    )


# example usage: python historical_data_exporter.py s3-validate images --max-workers 4
@app.command()
def s3_validate(
    import_type: ImportType,
    start_date: datetime = START_DATE,
    end_date: datetime = END_DATE,
    max_workers: int = 4,
):
    query_and_validate_async(
        import_type=import_type,
        export=False,
        overwrite=False,
        validate=True,
        date_range=date_range(start_date, end_date),
        max_workers=max_workers,
    )


def process_single_date(
    date_idx: datetime,
    import_type: ImportType,
    export: bool,
    overwrite: bool,
    validate: bool,
    template: str,
) -> dict:
    """Process a single date in a separate thread with its own database connection."""
    # IMPORTANT: DatabaseHelper has 'conn' as a class attribute, which would be
    # shared across all instances. We must create an instance attribute to shadow
    # the class attribute, ensuring each thread gets its own connection.
    db = DatabaseHelper()
    db.conn = None  # Creates instance attribute, shadows class attribute
    db.connect()  # Will now set the instance attribute, not class attribute
    db.cur.arraysize = 500000

    errors = {"missing_s3_file": [], "s3_file_mismatch": []}

    try:
        d = date_idx.date()
        s3_file_key = f"{S3_PREFIX}/{import_type.value}/{d}.parquet"
        file_exists = s3_file_exists(s3_file_key, BUCKET)

        if file_exists and not overwrite:
            logger.info(f"File {s3_file_key} already exists in S3, skipping export.")
            return errors

        logger.info(f"fetching data for {import_type.value} for date {d}")
        data = db.execute_fetchall(template, date_idx, date_idx + timedelta(days=1))
        df = pd.DataFrame(data)

        if (export and not file_exists) or (export and overwrite):
            # Transform the data before exporting to parquet
            transform_func = transform_mapping[import_type]
            transform_func(df)

            table = pa.Table.from_pandas(df)

            parquet_buffer = pa.BufferOutputStream()
            pq.write_table(table, parquet_buffer)
            logger.info(f"Uploading file to {BUCKET}://{s3_file_key}")
            # Upload the Parquet data to S3
            s3.put_object(
                Bucket=BUCKET,
                Key=s3_file_key,
                Body=parquet_buffer.getvalue().to_pybytes(),
                ContentType="application/x-parquet",
            )
            file_exists = True

        if validate:
            if not file_exists:
                logger.error(f"S3 file {s3_file_key} did not exist")
                errors["missing_s3_file"].append(f"s3://{BUCKET}/{s3_file_key}")
            else:
                rows_of_s3_file = get_number_of_rows_for_s3_parquet_file(
                    f"s3://{BUCKET}/{s3_file_key}"
                )
                # check that the data frame length (which comes from the db query) is equal to the length of the corresponding parquet file
                if len(df) == rows_of_s3_file:
                    logger.info(f"Validated file s3://{BUCKET}/{s3_file_key}")
                else:
                    logger.error(f"Invalid file s3://{BUCKET}/{s3_file_key}")
                    errors["s3_file_mismatch"].append(f"s3://{BUCKET}/{s3_file_key}")

    except Exception as e:
        logger.exception(f"Error processing date {d}: {e}")
        # Add to errors for this specific date
        errors["processing_error"] = [f"Date {d}: {str(e)}"]

    finally:
        # Clean up database connection
        if "db" in locals() and hasattr(db, "conn") and db.conn:
            try:
                db.conn.close()
            except:
                pass

    return errors


def query_and_validate_async(
    import_type: ImportType,
    export: bool,
    overwrite: bool,
    validate: bool,
    date_range,
    max_workers: int = 4,
):
    """Asynchronously process multiple dates using ThreadPoolExecutor."""
    template = Path(__file__).parent.joinpath(query_mapping[import_type]).read_text()

    # Convert date_range to list for better progress tracking
    dates_to_process = list(date_range)
    total_dates = len(dates_to_process)

    logger.info(f"Processing {total_dates} dates with {max_workers} workers")

    # Aggregate errors from all threads
    all_errors = {"missing_s3_file": [], "s3_file_mismatch": [], "processing_error": []}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_date = {
            executor.submit(
                process_single_date,
                date_idx,
                import_type,
                export,
                overwrite,
                validate,
                template,
            ): date_idx
            for date_idx in dates_to_process
        }

        # Process completed tasks
        completed = 0
        for future in as_completed(future_to_date):
            date_idx = future_to_date[future]
            completed += 1

            try:
                errors = future.result()
                # Thread-safe error aggregation
                with ERRORS_LOCK:
                    for error_type, error_list in errors.items():
                        if error_type not in all_errors:
                            all_errors[error_type] = []
                        all_errors[error_type].extend(error_list)

                logger.info(
                    f"Completed {completed}/{total_dates} dates (Date: {date_idx.date()})"
                )

            except Exception as e:
                logger.exception(f"Task for date {date_idx.date()} failed: {e}")
                with ERRORS_LOCK:
                    if "processing_error" not in all_errors:
                        all_errors["processing_error"] = []
                    all_errors["processing_error"].append(
                        f"Date {date_idx.date()}: {str(e)}"
                    )

    # dump errors to a file for easier visibility
    with open(f"errors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
        json.dump(all_errors, f, indent=4)

    logger.info(
        f"Processing complete. Total errors: {sum(len(v) for v in all_errors.values())}"
    )


def s3_file_exists(s3_file_key: str, s3_bucket: str) -> bool:
    try:
        s3.head_object(Bucket=s3_bucket, Key=s3_file_key)
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            # The key does not exist.
            return False
        else:
            # Something else has gone wrong.
            raise


def get_number_of_rows_for_s3_parquet_file(s3_file_path: str) -> int:
    file = pq.ParquetFile(s3_file_path)
    return file.metadata.num_rows


def date_range(start_date, end_date):
    for n in reversed(range(int((end_date - start_date).days))):
        yield start_date + timedelta(n)


def _parse_image_url(image_url):
    if not image_url:
        return "", ""
    split_url = image_url.split("/")
    if image_url and (
        len(split_url) == 4 or (len(split_url) == 5 and "built_in_dev" == split_url[1])
    ):
        bucket = image_url.split("/")[0]
        image_format = image_url.split("/")[-1].split(".")[-1]
    elif "test" in image_url:
        return "", ""
    else:
        logger.error(
            f"Invalid image URL format: {image_url}. Expected format: s3://bucket/path/to/image.jpg or s3://bucket/built_in_dev/path/to/image.jpg"
        )
        bucket = ""
        image_format = ""
    return bucket, image_format


def _parse_capture_timestamp_utc(vendor_image_id):
    if not vendor_image_id:
        return ""
    if (
        vendor_image_id.startswith("v")
        and len(vendor_image_id.split("_")) == 3
        and re.match(r"^\d{1,10}$", vendor_image_id.split("_")[2])
    ):
        return int(vendor_image_id.split("_")[2])
    elif (
        vendor_image_id.startswith("v")
        and len(vendor_image_id.split("_")) == 3
        and "." in vendor_image_id.split("_")[-1]
    ):
        if not vendor_image_id.startswith("v5"):
            logger.error(
                f"Invalid VendorImageID format: {vendor_image_id}. Has a decimal point in timestamp."
            )

        return int(vendor_image_id.split("_")[2].split(".")[0])
    elif (
        not vendor_image_id.startswith("v")
        and len(vendor_image_id.split("_")) == 2
        and re.match(r"^\d{1,10}$", vendor_image_id.split("_")[1])
    ):
        # For non-versioned images, we assume the timestamp is in the format <device_id>_<timestamp>
        return int(vendor_image_id.split("_")[1])
    elif "test" in vendor_image_id:
        # For test images, we assume the timestamp is in the format v<version>_<device_id>_<timestamp>
        return 0
    else:
        logger.error(
            f"Invalid VendorImageID format: {vendor_image_id}. Expected format: v<version>_<device_id>_<timestamp>"
        )
        return 0


if __name__ == "__main__":
    app()
ˆ
