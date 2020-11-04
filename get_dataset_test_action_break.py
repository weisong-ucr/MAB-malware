import os

list_file_1000 = os.listdir('data/malware_1000/')
list_file_1000_allgood = os.listdir('data/malware_1000_all_good/')

list_file = [x for x in list_file_1000 if x in list_file_1000_allgood][:50]
print(list_file)
os.system('mkdir data/malware_50_for_break_rate/')
os.system('rm data/malware_50_for_break_rate/*')
for f in list_file:
    os.system('cp data/malware_1000/%s data/malware_50_for_break_rate/%s' %(f, f))
