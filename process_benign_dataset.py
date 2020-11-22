import pefile
import os
import sys
from utils import *

def main():
    EXE_PATH = Utils.get_benignware_folder()
    if os.path.exists(EXE_PATH) == False:
        print('benignware_path %s does not exist' %EXE_PATH)
        exit()
    CONTENT_PATH = 'data/benign_section_content/'
    if os.path.exists(CONTENT_PATH) == False:
        os.system('mkdir -p %s' %CONTENT_PATH)
    
    list_section_content = []
    
    list_exe = os.listdir(EXE_PATH)
    list_exe.sort()
    list_name = []
    for exe in list_exe:
        print(EXE_PATH + exe)
        try:
            pe = pefile.PE(EXE_PATH + '/' + exe)
            for section in pe.sections:
                PointerToRawData = section.PointerToRawData
                SizeOfRawData = section.SizeOfRawData
                Name = section.Name.split(b'\0',1)[0].decode('utf-8')
                list_name.append(Name)
                Characteristics = section.Characteristics
                output_path = CONTENT_PATH + exe + '|' + Name + '|' + str(SizeOfRawData)
                print(output_path, PointerToRawData, SizeOfRawData)
                with open(EXE_PATH + exe, 'rb') as fp_in:
                    fp_in.seek(PointerToRawData)
                    content = fp_in.read(SizeOfRawData)
                    with open(output_path, 'wb') as fp_out:
                        fp_out.write(content)
        except Exception as e:
            print(e)
    #with open('data/benign_section_names.txt', 'w') as fp:
    #    for name in list_name:
    #        fp.write('%s\n' %name)

if __name__ == '__main__':
    main()

