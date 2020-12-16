import os
import json
import logging
import tempfile

from .config_file_provider_interface import ConfigFileProviderInterface

logger = logging.getLogger(__name__)

class ConfigTempFileProvider(ConfigFileProviderInterface):
    def __init__(self, username, password, android_id, lang_code='en_US', lang='us'):
        try:
            credentials_json_struct = [
                {
                    "USERNAME": username,
                    "PASSWORD": password,
                    "ANDROID_ID": android_id,
                    "LANG_CODE": lang_code,
                    "LANG": lang
                }
            ]
            self.credentials_file = tempfile.NamedTemporaryFile(mode='w', delete=False, encoding="utf8")  
            json.dump(credentials_json_struct, self.credentials_file)
            self.credentials_file.close()
        
        except Exception as ex:
            logger.critical(f"Error during the download: {ex}")
            sys.exit(1) 
    
    def __del__(self):
        os.remove(self.credentials_file.name)                                

    def get_credendials_file_path(self): 
        return self.credentials_file.name 