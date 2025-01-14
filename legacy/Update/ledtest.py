import requests
import base64
import logging

# Logging setup
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%d/%m/%Y %H:%M:%S',
    handlers=[
        logging.FileHandler('auth_test.log', mode='a'),
        logging.StreamHandler()
    ]
)

# URL and authentication details
base_url = "http://192.168.10.230"
endpoint = "/armed"
url = f"{base_url}{endpoint}"
username = "SensePro"
password = "SensePro"

# Manually create the Basic Authentication header
auth_str = f"{username}:{password}"
b64_auth_str = base64.b64encode(auth_str.encode()).decode()

headers = {
    "Authorization": f"Basic {b64_auth_str}"
}

logging.info("Testing connectivity and authentication with manual header")

try:
    logging.debug(f"Sending request to {url} with user {username}")
    response = requests.get(url, headers=headers, allow_redirects=False)
    
    if response.status_code == 302:
        redirect_url = response.headers.get('Location')
        logging.debug(f"Redirected to {redirect_url}")
        
        if redirect_url:
            # Handle relative redirect
            if redirect_url.startswith('/'):
                redirect_url = base_url + redirect_url
            
            logging.debug(f"Following redirect to {redirect_url}")
            response = requests.get(redirect_url, headers=headers)
            
            if response.status_code == 200:
                logging.info(f"Successfully followed redirect to {redirect_url}")
                logging.info(f"Response: {response.text}")
            else:
                logging.error(f"Failed to send request after redirect. Status Code: {response.status_code}, Response: {response.text}")
        else:
            logging.error(f"No redirect location found in headers.")
    elif response.status_code == 200:
        logging.info(f"Successfully sent request to {url}")
        logging.info(f"Response: {response.text}")
    else:
        logging.error(f"Failed to send request. Status Code: {response.status_code}, Response: {response.text}")
except requests.ConnectionError:
    logging.error(f"Unable to communicate with device at {url}")
except Exception as e:
    logging.error(f"An error occurred: {e}")

# Test base URL directly with manual header
logging.info("Testing base URL connectivity with manual header")

try:
    logging.debug(f"Sending request to {base_url} with user {username}")
    response = requests.get(base_url, headers=headers, allow_redirects=True)
    
    if response.status_code == 200:
        logging.info(f"Successfully sent request to {base_url}")
        logging.info(f"Response: {response.text}")
    else:
        logging.error(f"Failed to send request to base URL. Status Code: {response.status_code}, Response: {response.text}")
except requests.ConnectionError:
    logging.error(f"Unable to communicate with device at {base_url}")
except Exception as e:
    logging.error(f"An error occurred: {e}")

