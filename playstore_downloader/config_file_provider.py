from .config_file_provider_interface import ConfigFileProviderInterface

class ConfigFileProvider(ConfigFileProviderInterface):
    def __init__(self, credentials_file="credentials.json"):
        self.file_path = credentials_file

    def get_credendials_file_path(self):
        return self.file_path