import json
from copy import deepcopy


class Models:
    def __init__(self, modelfile_path="./assets/models.json"):
        self.path = modelfile_path
        f = open(self.path)

        self.contents = json.load(f)["contents"]
        self.modelname_list = [content["model_name"] for content in self.contents]
        self.models = {}

        for i, n in enumerate(self.modelname_list):
            self.models[n] = self.contents[i]

    @staticmethod
    def remove_key_from_dict_list(data, key):
        new_data = []
        for item in data:
            if key in item:
                new_item = deepcopy(item)
                new_item.pop(key)
                new_data.append(new_item)
            else:
                new_data.append(item)

        return new_data


models = Models()
