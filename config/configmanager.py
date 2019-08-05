import configparser


class ExchConfManager:

    def __init__(self):
        self.configs = {}
        self.api_conf = configparser.ConfigParser()

        # Read config file on class init
        self.read_config()

    def read_config(self):
        self.api_conf.read('config/api.conf')
        for sec in self.api_conf.sections():
            self.configs.update({sec.lower(): {
                'api_key': self.api_conf.get(sec, 'api_key'),
                'api_secret': self.api_conf.get(sec, 'api_secret')
            }})

    def get_active_exchanges(self):
        self.read_config()
        return self.configs
