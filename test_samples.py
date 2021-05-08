from utils import *
import random
import pefile
import mmap
import copy
import hashlib
from scipy.stats import beta
import pexpect
import string
#from manipulate2 import *
import json
import requests
from models import *
import time

MALCONV_MODEL_PATH = 'models/malconv/malconv.checkpoint'
model = MalConvModel( MALCONV_MODEL_PATH, thresh=0.5 )
#EMBER_2019_MODEL_PATH = 'models/ember_2019/ember_model.txt'
#model = EmberModel_2019( EMBER_2019_MODEL_PATH, thresh=0.8336 )

folder = '/root/MAB-malware/output_malconv/evasive/'

list_f = os.listdir(folder)
total = len(list_f)
evaded = detect = 0
for f in list_f:
    eva = model.is_evasive('%s%s' %(folder, f))
    if eva:
        evaded += 1
    else:
        detect += 1
    print('%d/%d/%d' %(evaded, detect, total))
print('######################')
