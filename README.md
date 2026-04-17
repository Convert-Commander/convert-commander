# Convert-Commander
![img1](https://github.com/Benzauber/convert-commander/blob/main/pictures/1.png?raw=true)

## What is Convert-Commander
Convert-Commander is an open-source solution that you can easily install on your own server. With Convert-Commander, you can convert files directly on your locally hosted server without uploading sensitive data to external servers. All conversions are handled securely and exclusively on your own system, ensuring your data remains protected and under your control. Install Convert-Commander via GitHub and enjoy the benefits of a secure and flexible file conversion solution tailored to your needs.


## Which file can you convert?

You can see this [here](filelist.md)

## I have tested with:
Ubuntu and Dabian
 
# Installation Convert-Commander

## Installation

1. **Clone Repository**
   
   First, clone the repository to your system:

   ```bash
   git clone https://github.com/Convert-Commander/convert-commander.git
   ```

### Installation Script
2. **Run Installation Script**
   
   Navigate to the cloned directory and execute the `install.sh` script:

   ```bash
   cd convert-commander
   ./install.sh
   ```

### Docker
2. **Docker (Web)**
   
   Navigate to the cloned directory.

   ```bash
   sudo docker build -t convert-commander .
   sudo docker run -d -p 9595:5000 --name convert-commander convert-commander

   ```
   ## Docker Hub

   ```bash
   docker run -d --name convert-commander -p 9595:5000 benzauber/convert-commander:latest
   ```
   The Web will then be running on http://YOUR_IP-ADDRES:9595

## Usage

After installation, the following commands are available:

* **Start**
  
  To start the service, run `ccommander`:

  ```bash
  ccommander web start
  ```

* **Stop**
  
  To stop the service, use:

  ```bash
  ccommander web stop
  ```

* **Check Status**
  
  To check the status of the service, use:

  ```bash
  ccommander web status
  ```
The Web will then be running on `http://0.0.0.0:9595`.

### Doesn't work?

If it doesn't work, try the following:

1. Make the `create-alias.sh` script executable:

   ```bash
   chmod +x create-alias.sh
   ```

2. Run the script:

   ```bash
   bash create-alias.sh
   ```

3. Source the `.bashrc` file to load the new aliases:

   ```bash
   source ~/.bashrc
   ```

After doing this, the `ccommander` command should be available and you can use the start, stop, and status commands as mentioned above.

### Make Update

* You make an update with this command:

  ```bash
  ccommander update
  ```
  Only works from version `1.1.0`

# API Documentation

## Starting the API



* **Start**
* To start the API, run the following command in the command line:
  ```bash
  ccommander api start
  ```

* **Stop**
  
  To stop the service, use:

  ```bash
  ccommander api stop
  ```

* **Check Status**
  
  To check the status of the service, use:

  ```bash
  ccommander api status
  ```

* **Generate token**
  
   To generate the token, use:

  ```bash
  ccommander api token
  ```

The API will then be running on `http://0.0.0.0:9596`.

## API Routes

### Upload and Convert a File

**Endpoint:** `/upload`  
**Method:** `POST`  
**Description:** Uploads a file and converts it to the specified format.

**Parameters:**
* `file`: The file to be uploaded
* `format`: The target format for conversion
* `X-API-Token`: The generated API token for authentication

**Example Request:**

```bash
curl -X POST -H "X-API-Token: <api_token>" -F "file=@/path/to/file.txt" -F "format=pdf" http://0.0.0.0:9596/upload
```

### Clear Folders

**Endpoint:** `/clear`  
**Method:** `POST`  
**Description:** Deletes all files in the upload and conversion folders.

**Parameters:**
* `X-API-Token`: The generated API token for authentication

**Example Request:**

```bash
curl -X POST -H "X-API-Token: <api_token>" http://0.0.0.0:9596/clear
```

## External Script File (sendapi.sh)

Here is an example script that uses the API functionality from the command line:

```bash
#!/bin/bash

FILE_PATH=$1
TARGET_FORMAT=$2
API_TOKEN="<api_token>"
API_URL="http://0.0.0.0:9596/upload"

if [ -z "$FILE_PATH" ] || [ -z "$TARGET_FORMAT" ] || [ -z "$API_TOKEN" ]; then
    echo "Usage: $0 <file_path> <target_format> <api_token>"
    exit 1
fi

if [ ! -f "$FILE_PATH" ]; then
    echo "File not found!"
    exit 1
fi

# Extract filename without path
FILENAME=$(basename "$FILE_PATH")
# Remove original file extension
FILENAME_WITHOUT_EXT="${FILENAME%.*}"
# Create new filename with target format extension
NEW_FILENAME="${FILENAME_WITHOUT_EXT}.${TARGET_FORMAT}"

# Send the file with the target format to the API, including the API token in the header
response_file=$(mktemp)
http_code=$(curl -s -w "%{http_code}" -o "$response_file" -X POST \
    -H "X-API-Token: $API_TOKEN" \
    -F "file=@$FILE_PATH" \
    -F "format=$TARGET_FORMAT" \
    $API_URL)

if [ $http_code -eq 200 ]; then
    # Save the API response to the new file
    mv "$response_file" "$NEW_FILENAME"
    echo "Conversion successful. The converted file has been saved as '$NEW_FILENAME'."
    rm -f "$response_file" # Remove the temporary file if not needed anymore
elif [ $http_code -eq 401 ]; then
    echo "Error: Invalid API token. Please check your token and try again."
    rm -f "$response_file"
else
    echo "Error during conversion. Server response (HTTP $http_code):"
    cat "$response_file"
    rm -f "$response_file"
fi
```

To use this script, save it as `sendapi.sh` and run it with the following parameters:

```bash
./sendapi.sh /path/to/file.txt pdf <api_token>
```

This script sends the file to the `/upload` API endpoint, converts it to the specified format, and saves the converted file in the current directory.

Additionally, the script also provides an endpoint `/clear` to delete all files in the upload and conversion folders. This can be called as follows:

```bash
./sendapi.sh "" "" <api_token>
```

Please replace `<api_token>` with the actual generated API token.

## Buy me a Coffee
[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/benzauber)

