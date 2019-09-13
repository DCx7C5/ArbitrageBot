import json

from botlib.data_logs import orders_json, jobs_json, txs_json
from botlib.bot_log import daemon_logger


class save:
    """Json file backup management"""
    def __init__(self, func):
        self.func = func
        if "job" in self.func.__name__:
            self.save_file = jobs_json
        elif "order" in self.func.__name__:
            self.save_file = orders_json
        elif 'transaction' in self.func.__name__:
            self.save_file = txs_json
        else:
            raise Exception("Unknown save_type: Must be 'job' or 'order' or 'transaction'")

    def __call__(self, *args, **kwargs):
        values = self.func(*args, **kwargs)
        self.update_json_file(values)
        daemon_logger.debug(f'{self.save_file} updated!')
        return values

    def update_json_file(self, new_data):
        data = self.__load_json_from_file()
        if data:
            for nd in new_data:
                if nd not in data:
                    data.append(nd)
            self.__write_json_to_file(data)
        else:
            self.__write_json_to_file(new_data)

    def __load_json_from_file(self):
        with open(self.save_file, 'r') as f:
            data = json.load(f)
        return data

    def __write_json_to_file(self, data):
        with open(self.save_file, 'w') as f:
            json.dump(data, f)
        return True
