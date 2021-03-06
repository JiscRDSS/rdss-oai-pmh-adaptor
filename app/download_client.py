import logging
import math
import os
import requests
import tempfile

from tqdm import tqdm


class DownloadClient(object):

    def download_file(self, url):
        # Create a temporary file object.
        temp_file = self._get_temp_file_name()

        # Get a handle on the description and file path for the temporary file.
        file_descriptor = temp_file[0]
        file_path = temp_file[1]

        # Download the file and if it was successful, return the file path.
        if self._do_download_file(url, file_descriptor, file_path):
            return file_path
        else:
            return None

    def _get_temp_file_name(self):
        # Generate a temporary file with the appropriate prefix and suffix.
        temp_file = tempfile.mkstemp(prefix='oai_pmh_adaptor-', suffix='.download')
        logging.info('Generated temporary file [%s]', temp_file)
        return temp_file

    def _do_download_file(self, url, target_file_descriptor, target_file_path):
        # Initialise the download by getting a handle on the response object.
        logging.info('Downloading URL [%s] to file [%s]', url, target_file_path)
        response = requests.get(url, stream=True)
        logging.info('Got HTTP response [%s] from URL [%s]', response, url)

        # EPrints currently returns 401 status codes for some files. We can ignore these for now,
        # we're only interested in successful downloads.
        if response.status_code == 200:

            # Execute the download, using tqdm to provide us with a progress bar for the download.
            total_size = int(response.headers.get('content-length', 0))
            wrote = 0
            with open(target_file_path, 'wb') as handle:
                for data in tqdm(
                        response.iter_content(1024),
                        total=math.ceil(total_size // 1024),
                        unit='KB'
                ):
                    wrote = wrote + len(data)
                    handle.write(data)
            logging.info(
                'Download complete, closing descriptor [%s] for [%s]',
                target_file_descriptor,
                target_file_path
            )
            os.close(target_file_descriptor)
            return True
        else:
            # We didn't get a 200 status code, close and delete the file and return false.
            logging.warning(
                'Received non-200 HTTP status code for URL [%s], cannot access target for download',
                url
            )
            logging.info('Deleting temporary file [%s]', target_file_path)
            os.close(target_file_descriptor)
            os.remove(target_file_path)
            return False
