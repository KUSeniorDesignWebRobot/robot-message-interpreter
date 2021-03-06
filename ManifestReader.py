import threading
import json
import io
import logging

class ManifestReader(object):

    instance = None

    class __ManifestReader:

        def __init__(self, filepath):
            self.lock = threading.Lock()
            self.dict = {}
            self.importJson(filepath)
            # self.manifestJson = None

        def importJson(self,filepath):
            with open(filepath) as f:
                contents = f.read()
            self.manifestJson = json.loads(contents)

        def setVar(self,key,value):
            self.dict[key] = value

        def getVar(self,key):
            if key in self.dict.keys():
                return self.dict[key]
            else:
                return None

        def getManifestValue(self,key):
            if key in self.manifestJson.keys():
                return self.manifestJson[key]
            else:
                print("Key not in manifest!!")
                return None

        def getManifest(self):
            return self.manifestJson



    def __new__(cls, filepath = None):
        if not ManifestReader.instance:
            if filepath:
                ManifestReader.instance = ManifestReader.__ManifestReader(filepath = filepath)
            else:
                raise Exception("Manifest requires filepath on first time initialization")
        return ManifestReader.instance
