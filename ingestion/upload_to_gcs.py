import os
from pathlib import Path

from google.cloud import storage


def upload_to_gcs(
    local_path: str,
    bucket_name: str | None = None,
    destination_blob_prefix: str = "raw/stocks",
) -> str:
    if bucket_name is None:
        bucket_name = os.environ["GCS_BUCKET_NAME"]

    client = storage.Client()
    bucket = client.bucket(bucket_name)

    filename = Path(local_path).name
    blob_name = f"{destination_blob_prefix}/{filename}"
    blob = bucket.blob(blob_name)

    print(f"Uploading {local_path} to gs://{bucket_name}/{blob_name}")
    blob.upload_from_filename(local_path)
    gcs_uri = f"gs://{bucket_name}/{blob_name}"
    print(f"Upload complete: {gcs_uri}")

    return gcs_uri


def upload_directory_to_gcs(
    local_dir: str,
    bucket_name: str | None = None,
    destination_blob_prefix: str = "raw/stocks",
) -> list[str]:
    uris = []
    for path in sorted(Path(local_dir).glob("*.parquet")):
        uri = upload_to_gcs(str(path), bucket_name, destination_blob_prefix)
        uris.append(uri)
    return uris


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python upload_to_gcs.py <path_to_parquet>")
        sys.exit(1)
    upload_to_gcs(sys.argv[1])
