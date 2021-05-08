import os
import sys
import time
import hashlib

dict_rewriter_file_to_time = {}
dict_minimizer_file_to_time = {}

for folder in ['rewriter', 'minimizer']:
	folder_in = 'Z:\\share\\avast\\%s\\' %folder
	folder_out = 'C:\\Users\\wsong008\\Desktop\\share\\%s\\' %folder
	os.system('del /Q %s*' %(folder_in))
	os.system('del /Q %s*' %(folder_out))
os.system('del /Q Z:\\share\\avast\\tmp\\*')

def get_md5(path):
	if os.path.exists(path) == False:
		print('\n%s file does not exist' %(path))
		return 0
	hash_md5 = hashlib.md5()
	try:
		with open(path, 'rb') as f:
			content = f.read()
			hash_md5.update(content)
			md5 = hash_md5.hexdigest()
			#print('md5:', md5)
		return md5 
	except Exception as e:
		exc_type, exc_obj, exc_tb = sys.exc_info()
		fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
		#print('\n%s %s:%s cannot get md5' %(exc_type, fname, exc_tb.tb_lineno))
		return -1

def copy(folder, dict_file_to_time, idx, mod):
	folder_in = 'Z:\\share\\avast\\%s\\' %folder
	folder_out = 'C:\\Users\\wsong008\\Desktop\\share\\%s\\' %folder

	print('.', end='', flush=True)
	if idx >= 0:
		list_f = [x for x in os.listdir(folder_in) if x not in dict_file_to_time and int(x[:8], 16) % mod == idx]
	else:
		list_f = [x for x in os.listdir(folder_in) if x not in dict_file_to_time]

	for f in list_f:
		dict_file_to_time[f] = time.time()
		os.system('copy %s%s %s >NUL' %(folder_in, f, folder_out))

	files = list(dict_file_to_time.keys())
	for file in files:
		md5_ori = get_md5(folder_in + file)
		md5_copy = get_md5(folder_out + file)
		delete_all = False
		if md5_copy == 0 or md5_ori == 0:
			delete_all = True
		elif (md5_copy == -1 or md5_ori == -1):
			if time.time() - dict_file_to_time[file] < 300:
				print('\n%s cannot get md5, wait...' %file)
			else:
				print('\n%s overtime' %file)
				delete_all = True
		elif md5_ori != md5_copy:
			print('\nmd5 changed %s' %file)
			delete_all = True

		if delete_all == True:
			if os.path.exists('%s%s' %(folder_in, file)):
				os.system('del /Q %s%s' %(folder_in, file))
			if os.path.exists('%s%s' %(folder_out, file)):
				os.system('del /Q %s%s' %(folder_out, file))
			del dict_file_to_time[file]
			print('\ndel %s' %file, flush=True)

index = int(sys.argv[1])

while True:
	time.sleep(0.5)
	copy('rewriter', dict_rewriter_file_to_time, index, 4)
	copy('minimizer', dict_minimizer_file_to_time, index, 4)