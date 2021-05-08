import torch
import time
import requests
import torch.nn.functional as F
import lightgbm as lgb
import numpy as np
import subprocess
import json
from ember import predict_sample
from MalConv import MalConv
import sys

class MalConvModel(object):
    def __init__(self, model_path, thresh=0.5, name='malconv'): 
        self.model = MalConv(channels=256, window_size=512, embd_size=8).train()
        weights = torch.load(model_path,map_location='cpu')
        self.model.load_state_dict( weights['model_state_dict'])
        self.thresh = thresh
        self.__name__ = name

    def get_score(self, file_path):
        try:
            with open(file_path, 'rb') as fp:
                bytez = fp.read(2000000)        # read the first 2000000 bytes
                _inp = torch.from_numpy( np.frombuffer(bytez,dtype=np.uint8)[np.newaxis,:] )
                with torch.no_grad():
                    outputs = F.softmax( self.model(_inp), dim=-1)
                return outputs.detach().numpy()[0,1]
        except Exception as e:
            print(e)
        return 0.0 
    
    def is_evasive(self, file_path):
        score = self.get_score(file_path)
        #print(os.path.basename(file_path), score)
        return score < self.thresh

#class EmberModel_gym(object):      # model in gym-malware
#    # ember_threshold = 0.8336 # resulting in 1% FPR
#    def __init__(self, model_path, thresh=0.9, name='ember'):       # 0.9 or 0.8336
#        # load lightgbm model
#        self.local_model = joblib.load(model_path)
#        self.thresh = thresh
#        self.__name__ = 'ember'
#
#    def get_score(self, file_path):
#        with open(file_path, 'rb') as fp:
#            bytez = fp.read()
#            #return predict_sample(self.model, bytez) > self.thresh
#            features = feature_extractor.extract( bytez )
#            score = local_model.predict_proba( features.reshape(1,-1) )[0,-1]
#            return score
#    
#    def is_evasive(self, file_path):
#        score = self.get_score(file_path)
#        return score < self.thresh

class EmberModel_2019(object):       # model in MLSEC 2019
    def __init__(self, model_path, thresh=0.8336, name='ember'):
        # load lightgbm model
        self.model = lgb.Booster(model_file=model_path)
        self.thresh = thresh
        self.__name__ = 'ember'

    def get_score(self,file_path):
        with open(file_path, 'rb') as fp:
            bytez = fp.read()
            score = predict_sample(self.model, bytez)
            return score
    
    def is_evasive(self, file_path):
        score = self.get_score(file_path)
        return score < self.thresh

#class EmberModel_2020(object):      # model in MLSEC 2020
#    '''Implements predict(self, bytez)'''
#    def __init__(self,
#                 name: str = 'ember_MLSEC202H0',
#                 thresh=0.8336):
#        self.thresh = thresh
#        self.__name__ = name
#
#    def get_score(self, file_path):
#        with open(file_path, 'rb') as fp:
#            bytez = fp.read()
#            url = 'http://127.0.0.1:8080/'
#            timeout = 5
#            error_msg = None
#            res = None
#            start = time.time()
#            try:
#                res = self.get_raw_result(bytez, url, timeout)
#                score = res.json()['score']
#            except (requests.RequestException, KeyError, json.decoder.JSONDecodeError) as e:
#                score = 1.0  # timeout or other error results in malicious
#                error_msg = str(e)
#                if res:
#                    error_msg += f'-{res.text()}'
#            return score
#    
#    def is_evasive(self, file_path):
#        score = self.get_score(file_path)
#        return score < self.thresh
#    
#    def get_raw_result(self, bytez, url, timeout):
#        return requests.post(url, data=bytez, headers={'Content-Type': 'application/octet-stream'}, timeout=timeout)

class ClamAV(object):
    def is_evasive(self, file_path):
        res = subprocess.run(['clamdscan', '--fdpass', file_path], stdout=subprocess.PIPE)
        #print(res.stdout)
        if 'FOUND' in str(res.stdout):
            return False
        elif 'OK' in str(res.stdout):
            return True
        else:
            print('clamav error')
            exit()
