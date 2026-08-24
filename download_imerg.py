import os
import time
import requests
from urllib.parse import urlparse
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ============================================================
# SETTINGS
# ============================================================

LINKS_FILE = "links.txt"
OUTPUT_DIR = "imerg_2024"

# Windows Earthdata credentials file
NETRC_FILE = os.path.expanduser("~/_netrc")

# NASA Earthdata authentication server
EARTHDATA_HOST = "urs.earthdata.nasa.gov"

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# CHECK EARTHDATA CREDENTIALS
# ============================================================

if not os.path.exists(NETRC_FILE):
    print("\nERROR: NASA Earthdata credentials not found.")
    print()
    print("Create this file:")
    print(NETRC_FILE)
    print()
    print("It should contain:")
    print("machine urs.earthdata.nasa.gov")
    print("login YOUR_EARTHDATA_USERNAME")
    print("password YOUR_EARTHDATA_PASSWORD")
    print()
    print("Then run this script again.")
    print()

    raise SystemExit(1)

# Tell Python requests exactly which netrc file to use
os.environ["NETRC"] = NETRC_FILE

print("NASA Earthdata credentials file found:")
print(NETRC_FILE)


# ============================================================
# READ LINKS
# ============================================================

if not os.path.exists(LINKS_FILE):
    print(f"\nERROR: {LINKS_FILE} was not found.")
    print("Make sure links.txt is in the same folder as this script.")
    raise SystemExit(1)

with open(LINKS_FILE, "r", encoding="utf-8") as f:
    urls = [line.strip() for line in f if line.strip()]

# Only keep NetCDF rainfall files
urls = [url for url in urls if ".nc4" in url.lower()]

print()
print(f"Found {len(urls)} NetCDF files.")


# ============================================================
# CREATE SESSION
# ============================================================

session = requests.Session()

# Allow requests to use the NETRC credentials
session.trust_env = True

# Retry temporary server/network errors
retry_strategy = Retry(
    total=5,
    backoff_factor=2,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"]
)

adapter = HTTPAdapter(max_retries=retry_strategy)

session.mount("https://", adapter)
session.mount("http://", adapter)

# Browser-like headers
session.headers.update({
    "User-Agent": "JG-IMERG-Downloader/1.0",
    "Accept": "*/*"
})


# ============================================================
# TEST EARTHDATA CONNECTION
# ============================================================

print()
print("Testing NASA Earthdata authentication...")

test_url = urls[0]

try:

    test_response = session.get(
        test_url,
        stream=True,
        allow_redirects=True,
        timeout=60
    )

    print("Authentication test status:", test_response.status_code)

    if test_response.status_code == 401:
        print()
        print("ERROR: NASA Earthdata authentication failed.")
        print()
        print("Possible causes:")
        print("1. Wrong Earthdata username/password")
        print("2. _netrc file is incorrect")
        print("3. GES DISC application has not been authorized")
        print("4. Earthdata account needs to be verified")
        print()
        print("Check your Earthdata account and GES DISC authorization.")
        print()

        test_response.close()
        raise SystemExit(1)

    elif test_response.status_code == 403:
        print()
        print("ERROR: NASA returned 403 Forbidden.")
        print("Your Earthdata account may not be authorized for GES DISC.")
        print()

        test_response.close()
        raise SystemExit(1)

    elif test_response.status_code >= 400:
        print()
        print("ERROR: NASA returned HTTP", test_response.status_code)
        print()
        test_response.close()
        raise SystemExit(1)

    else:
        print("Earthdata authentication appears to be working.")

    test_response.close()

except requests.exceptions.RequestException as e:

    print()
    print("ERROR while testing Earthdata:")
    print(e)
    print()

    raise SystemExit(1)


# ============================================================
# DOWNLOAD
# ============================================================

successful = 0
skipped = 0
failed = 0

failed_urls = []

print()
print("================================")
print("STARTING IMERG DOWNLOAD")
print("================================")


for i, url in enumerate(urls, start=1):

    filename = os.path.basename(urlparse(url).path)

    output_path = os.path.join(
        OUTPUT_DIR,
        filename
    )

    print()
    print("--------------------------------")
    print(f"Downloading {i}/{len(urls)}")
    print(filename)
    print("--------------------------------")

    # --------------------------------------------------------
    # SKIP ALREADY DOWNLOADED FILE
    # --------------------------------------------------------

    if os.path.exists(output_path):

        file_size = os.path.getsize(output_path)

        if file_size > 0:

            print("Already exists - skipping.")
            print(f"Size: {file_size / (1024 * 1024):.2f} MB")

            skipped += 1
            continue


    # --------------------------------------------------------
    # TEMPORARY FILE
    # --------------------------------------------------------

    temp_path = output_path + ".part"

    try:

        print("Connecting to NASA GES DISC...")

        response = session.get(
            url,
            stream=True,
            allow_redirects=True,
            timeout=(30, 300)
        )

        # ----------------------------------------------------
        # AUTHENTICATION ERRORS
        # ----------------------------------------------------

        if response.status_code == 401:

            print()
            print("ERROR 401: Unauthorized")
            print()
            print("NASA Earthdata rejected the authentication.")
            print("Check your _netrc credentials and GES DISC authorization.")

            response.close()

            failed += 1
            failed_urls.append(url)

            continue

        if response.status_code == 403:

            print()
            print("ERROR 403: Forbidden")
            print("Your account may not have permission for this dataset.")

            response.close()

            failed += 1
            failed_urls.append(url)

            continue

        response.raise_for_status()


        # ----------------------------------------------------
        # CHECK CONTENT TYPE
        # ----------------------------------------------------

        content_type = response.headers.get(
            "Content-Type",
            ""
        ).lower()

        print("Content-Type:", content_type)

        # ----------------------------------------------------
        # DOWNLOAD
        # ----------------------------------------------------

        total_size = response.headers.get(
            "Content-Length"
        )

        if total_size:
            total_size = int(total_size)

            print(
                f"File size: "
                f"{total_size / (1024 * 1024):.2f} MB"
            )

        else:
            total_size = None
            print("File size: unknown")


        downloaded = 0
        start_time = time.time()

        with open(temp_path, "wb") as f:

            for chunk in response.iter_content(
                chunk_size=1024 * 1024
            ):

                if not chunk:
                    continue

                f.write(chunk)

                downloaded += len(chunk)

                # --------------------------------------------
                # PROGRESS
                # --------------------------------------------

                if total_size:

                    percentage = (
                        downloaded / total_size
                    ) * 100

                    elapsed = time.time() - start_time

                    if elapsed > 0:

                        speed = (
                            downloaded / elapsed
                        ) / (1024 * 1024)

                    else:

                        speed = 0

                    print(
                        f"\rProgress: "
                        f"{percentage:6.2f}% | "
                        f"{downloaded / (1024 * 1024):.2f} MB | "
                        f"{speed:.2f} MB/s",
                        end=""
                    )

        response.close()

        print()

        # ----------------------------------------------------
        # VERIFY DOWNLOAD
        # ----------------------------------------------------

        if not os.path.exists(temp_path):

            print("ERROR: Downloaded file does not exist.")

            failed += 1
            failed_urls.append(url)

            continue


        file_size = os.path.getsize(temp_path)

        if file_size == 0:

            print("ERROR: Downloaded file is empty.")

            os.remove(temp_path)

            failed += 1
            failed_urls.append(url)

            continue


        # ----------------------------------------------------
        # RENAME TEMP FILE
        # ----------------------------------------------------

        os.replace(
            temp_path,
            output_path
        )

        print(
            f"Downloaded successfully "
            f"({file_size / (1024 * 1024):.2f} MB)"
        )

        successful += 1


    except requests.exceptions.RequestException as e:

        print()
        print("NETWORK ERROR:")
        print(e)

        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass

        failed += 1
        failed_urls.append(url)

    except Exception as e:

        print()
        print("ERROR:")
        print(e)

        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass

        failed += 1
        failed_urls.append(url)


# ============================================================
# SAVE FAILED URLS
# ============================================================

if failed_urls:

    failed_file = "failed_downloads.txt"

    with open(
        failed_file,
        "w",
        encoding="utf-8"
    ) as f:

        for url in failed_urls:
            f.write(url + "\n")

    print()
    print(f"Failed URLs saved to: {failed_file}")


# ============================================================
# FINAL SUMMARY
# ============================================================

print()
print("================================")
print("DOWNLOAD COMPLETE")
print("================================")

print(f"Total files : {len(urls)}")
print(f"Downloaded  : {successful}")
print(f"Skipped     : {skipped}")
print(f"Failed      : {failed}")

print()
print(f"Output folder:")
print(os.path.abspath(OUTPUT_DIR))
print("================================")