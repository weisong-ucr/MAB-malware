from utils import *
import random
import pefile
import mmap
import hashlib
import string
import sys

class Arm:
    def __init__(self, idx):
        self.idx = idx
        self.action = None
        self.content = None
        self.description = None
        self.list_reward = []
        self.n_play = 0

    def update_description(self):
        self.description = self.action

    def pull(self, sample):
        logger_rew.info('pull Arm %s (%d)' %(self.description, self.idx))
        sample.pull_count += 1
        return self.transfer(sample.current_exe_path, rewriter_output_folder)
    
    def transfer(self, input_path, output_folder=rewriter_output_folder, verbose=True):
        raise Exception ('Not Implemented')

    def estimated_probas(self):
        raise NotImplementedError

    def get_output_path(self, folder, input_path):
        #print(input_path)
        return folder + basename(input_path) + '.' + self.action

    def get_overlay_size(self, sample_path):
        file_size = os.path.getsize(sample_path)
        pe = self.try_parse_pe(sample_path)
        if pe == None:
            logger_rew.info('action fail, no change')
            return 0
        overlay_offset = pe.get_overlay_data_start_offset()
        overlay_size = 0
        if overlay_offset != None:
            overlay_size = file_size - overlay_offset
        return overlay_size

    def try_parse_pe(self, sample_path):
        try:
            pe = pefile.PE(sample_path)
            return pe
        except Exception as e:
            logger_rew.info('pefile parse fail')
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            logger_rew.error('%s %s:%s cannot parse pe' %(exc_type, fname, exc_tb.tb_lineno))

    def get_available_size_safe(self, pe, section_idx):
        target_section = pe.sections[section_idx]
    
        if section_idx < len(pe.sections) - 1:
            available_size = (pe.sections[section_idx+1].PointerToRawData - target_section.PointerToRawData) - target_section.Misc_VirtualSize
        else:           # the last section
            overlay_offset = pe.get_overlay_data_start_offset()
            if overlay_offset != None:      # pe has overlay data, the last section
                available_size = (overlay_offset - target_section.PointerToRawData) - target_section.Misc_VirtualSize
            else:       # no overlay data, the last section
                available_size = self.get_available_size(pe, section_idx)
    
        if available_size > 0x1000 or available_size < 0:
            available_size = 0
        return available_size

    def get_available_size(self, pe, section_idx):
        target_section = pe.sections[section_idx]
        available_size = target_section.SizeOfRawData - target_section.Misc_VirtualSize
        if available_size < 0:
            available_size = 0
        return available_size

    def print_section_names(self, pe):
        logger_rew.info(self.get_section_name_list(pe))

    def get_section_name_list(self, pe):
        return [str(section.Name.split(b'\0',1)[0]).split('\'')[1] for section in pe.sections]
        #return [section.Name.decode('utf8').rstrip('\0') for section in pe.sections]

    def zero_out_file_content(self, file_path, offset, segment_size):
        content = ('\x00'*(segment_size)).encode()
    
        fp_in = open(file_path, 'rb')
        file_content = fp_in.read()
        #logger_rew.info(len(file_content))
        fp_in.close()
    
        fp_out = open(file_path, 'wb')
        fp_out.write(file_content[:offset])
        fp_out.write(content)
        fp_out.write(file_content[offset + len(content):])
        fp_out.close()
    
    def align(self, val_to_align, alignment):
        return (int((val_to_align + alignment - 1) / alignment)) * alignment

class ArmOA(Arm):
    def __init__(self, idx, content=None):
        super().__init__(idx)
        self.content = content
        if content and len(content) == 1:
            self.action = 'OA1'
        else:
            self.action = 'OA'
        self.update_description()

    def update_description(self):
        if self.content == None:
            self.description = 'OA+Rand'
        elif len(self.content) == 1:
            self.description = 'OA+1'
        else:
            self.description = 'OA+' + hashlib.md5(self.content).hexdigest()[:8]

    def set_content(self, content):
        self.content = content
        if len(content) == 1:
            self.action = 'OA1'
        self.update_description()

    def transfer(self, input_path, output_folder=rewriter_output_folder, verbose=True):
        if verbose == True:
            logger_rew.info('=== %s ===' %self.action)
        output_path = self.get_output_path(output_folder, input_path)

        os.system('cp -p %s %s' %(input_path, output_path))
        if self.content == None:
            if verbose == True:
                logger_rew.info('generating new random content')
            _, _, self.content = Utils.get_random_content()
        if verbose == True:
            logger_rew.info('using arm idx: %d, len content: %d' %(self.idx, len(self.content)))
        with open(output_path, 'ab') as f:
            f.write(self.content)
        
        # verify action changes
        old_overlay_size = self.get_overlay_size(input_path)
        new_overlay_size = self.get_overlay_size(output_path)

        if verbose == True:
            logger_rew.info('old overlay size: %d, new overlay size: %d' %(old_overlay_size, new_overlay_size))
        #if 'rewriter_output' in os.path.dirname(input_path):
        #    os.system('rm %s' %input_path)
        return output_path

class ArmRD(Arm):
    def __init__(self, idx):
        super().__init__(idx)
        self.action = 'RD'
        self.description = self.action

    def transfer(self, input_path, output_folder=rewriter_output_folder, verbose=True):
        if verbose == True:
            logger_rew.info('=== %s ===' %self.action)
        output_path = self.get_output_path(output_folder, input_path)

        pe = pefile.PE(input_path)
        segment_size = 0
        for d in pe.OPTIONAL_HEADER.DATA_DIRECTORY:
            if d.name == 'IMAGE_DIRECTORY_ENTRY_DEBUG':
                if verbose == True: 
                    logger_rew.info('%s\t%s\t%s' %(d.name, hex(d.VirtualAddress), hex(d.Size)))
                if d.Size > 0:
                    debug_directories = pe.parse_debug_directory(d.VirtualAddress, d.Size)
                    if debug_directories:
                        for debug_directory in debug_directories:
                            debug_type = debug_directory.struct.Type
                            if debug_type == 2:
                                file_offset = debug_directory.struct.PointerToRawData
                                segment_size = debug_directory.struct.SizeOfData
                    d.VirtualAddress = 0
                    d.Size = 0

        pe.write(output_path)

        if segment_size > 0:
            # set_bytes_at_offset doesn't take effect, zero out directly.
            self.zero_out_file_content(output_path, file_offset, segment_size)

        # verify action changes
        pe = self.try_parse_pe(output_path)
        if pe:
            for d in pe.OPTIONAL_HEADER.DATA_DIRECTORY:
                if d.name == 'IMAGE_DIRECTORY_ENTRY_DEBUG':
                    if verbose == True: 
                        logger_rew.info('%s\t%s\t%s' %(d.name, hex(d.VirtualAddress), hex(d.Size)))
        else:
            if verbose == True: 
                logger_rew.info('pefile cannot parse, restore original file')
            os.system('cp -p %s %s' %(input_path, output_path))

        #if 'rewriter_output' in os.path.dirname(input_path):
        #    os.system('rm %s' %input_path)
        return output_path

class ArmRC(Arm):
    def __init__(self, idx):
        super().__init__(idx)
        self.action = 'RC'
        self.description = self.action

    def transfer(self, input_path, output_folder=rewriter_output_folder, verbose=True):
        if verbose == True:
            logger_rew.info('=== %s ===' %self.action)
        output_path = self.get_output_path(output_folder, input_path)

        pe = pefile.PE(input_path)
        for d in pe.OPTIONAL_HEADER.DATA_DIRECTORY:
            if d.name == 'IMAGE_DIRECTORY_ENTRY_SECURITY':
                if verbose == True:
                    logger_rew.info('%s\t%s\t%s' %(d.name, hex(d.VirtualAddress), hex(d.Size)))
                if d.VirtualAddress > 0:
                    size_in_sig = pe.get_word_from_offset(d.VirtualAddress)
                    if size_in_sig == d.Size:
                        if verbose == True:
                            logger_rew.info('find certificate')
                        pe.set_bytes_at_offset(d.VirtualAddress, ('\x00'*(d.Size)).encode())
                        d.VirtualAddress = 0
                        d.Size = 0

        pe.write(output_path)

        # verify action change
        pe = self.try_parse_pe(output_path)
        if pe:
            for d in pe.OPTIONAL_HEADER.DATA_DIRECTORY:
                if d.name == 'IMAGE_DIRECTORY_ENTRY_SECURITY':
                    if verbose == True:
                        logger_rew.info('%s\t%s\t%s' %(d.name, hex(d.VirtualAddress), hex(d.Size)))
        else:
            if verbose == True:
                logger_rew.info('pefile cannot parse, restore original file')
            os.system('cp -p %s %s' %(input_path, output_path))
        
        #if 'rewriter_output' in os.path.dirname(input_path):
        #    os.system('rm %s' %input_path)
        return output_path

class ArmCR(Arm):
    def __init__(self, idx):
        super().__init__(idx)
        self.action = 'CR'
        self.description = self.action

    def transfer(self, input_path, output_folder=rewriter_output_folder, verbose=True):
        if verbose == True:
            logger_rew.info('=== %s ===' %self.action)
        output_path = self.get_output_path(output_folder, input_path)

        cr_path = Utils.get_randomized_folder() + Utils.get_ori_name(output_path) + '.CR'
        if os.path.exists(cr_path) == True:
            os.system('cp -p %s %s' %(cr_path, output_path))
            if verbose == True:
                logger_rew.info('have CR file')
        else:
            if verbose == True:
                logger_rew.info('do not have CR file')
            os.system('cp -p %s %s' %(input_path, output_path))

        # verify action change
        pe = self.try_parse_pe(output_path)
        if pe == None:
            if verbose == True:
                logger_rew.info('pefile cannot parse, restore original file')
            os.system('cp -p %s %s' %(input_path, output_path))
        
        #if 'rewriter_output' in os.path.dirname(input_path):
        #    os.system('rm %s' %input_path)
        return output_path

class ArmBC(Arm):
    def __init__(self, idx):
        super().__init__(idx)
        self.action = 'BC'
        self.description = self.action

    def transfer(self, input_path, output_folder=rewriter_output_folder, verbose=True):
        if verbose == True:
            logger_rew.info('=== %s ===' %self.action)
        output_path = self.get_output_path(output_folder, input_path)
        pe = pefile.PE(input_path)
        checksum_before = pe.OPTIONAL_HEADER.CheckSum

        pe.OPTIONAL_HEADER.CheckSum = 0
        pe.write(output_path)

        # verify action changes
        pe = self.try_parse_pe(output_path)
        if pe:
            checksum_after = pe.OPTIONAL_HEADER.CheckSum
            if verbose == True:
                logger_rew.info('CheckSum: before %s, after %s' %(hex(checksum_before), hex(checksum_after)))
        else:
            if verbose == True:
                logger_rew.info('pefile cannot parse, restore original file')
            os.system('cp -p %s %s' %(input_path, output_path))

        #if 'rewriter_output' in os.path.dirname(input_path):
        #    os.system('rm %s' %input_path)
        return output_path

class ArmSP(Arm):
    def __init__(self, idx, section_idx=None, content=None):
        super().__init__(idx)
        #if section_idx != None and len(content) == 1:
        #    self.action = 'CP1'     # special case, only CP1 init with section_idx, SP1 only set_content
        #else:
        if content and len(content) == 1:
            self.action = 'SP1'
        else:
            self.action = 'SP'
        self.section_idx = section_idx
        self.content = content
        self.update_description()

    def update_description(self):
        if self.content == None:
            self.description = 'SP+Rand'
        elif len(self.content) == 1:
            self.description = 'SP+1'
        else:
            self.description = 'SP+' + hashlib.md5(self.content).hexdigest()[:8]

    def set_content(self, content):
        self.content = content
        if len(content) == 1:
            self.action = 'SP1'
        self.update_description()

    def transfer(self, input_path, output_folder=rewriter_output_folder, verbose=True):
        if verbose == True:
            logger_rew.info('=== %s ===' %self.action)
        output_path = self.get_output_path(output_folder, input_path)
        pe = pefile.PE(input_path)

        # find out all available_sections
        dict_idx_to_available_size = {}
        for idx, section in enumerate(pe.sections):
            available_size = self.get_available_size_safe(pe, idx)
            if available_size > 0:
                dict_idx_to_available_size[idx] = available_size
                
        if len(dict_idx_to_available_size) == 0:
            if verbose == True:
                logger_rew.info('no section has free space, return the original sample')
            os.system('cp -p %s %s' %(input_path, output_path))
            #if 'rewriter_output' in os.path.dirname(input_path):
            #    os.system('rm %s' %input_path)
            return output_path

        append_section_idx = self.section_idx
        # arm first use, or cannot be directly applied
        if append_section_idx == None or append_section_idx not in dict_idx_to_available_size.keys():
            append_section_idx = random.choice(list(dict_idx_to_available_size.keys()))

        available_size = dict_idx_to_available_size[append_section_idx]

        # arm first use, save for later use 
        if self.section_idx == None:
            self.section_idx = append_section_idx
        if self.content == None:
            _, _, self.content = Utils.get_random_content()

        append_content = self.content
        if len(append_content) != 1:            # if it's SP1, do not need to extend content
            while available_size > len(append_content):   # extend content
                append_content += self.content                    
            append_content = bytes(append_content[:available_size])

        target_section = pe.sections[append_section_idx]
        pe.set_bytes_at_offset(target_section.PointerToRawData + target_section.Misc_VirtualSize, append_content)
        if verbose == True:
            logger_rew.info('section_idx: %d, content lenth: %d' %(append_section_idx, len(append_content)))
        pe.write(output_path)

        # verify action changes
        pe = self.try_parse_pe(output_path)
        if pe == None:
            if verbose == True:
                logger_rew.info('pefile cannot parse, restore original file')
            os.system('cp -p %s %s' %(input_path, output_path))

        #if 'rewriter_output' in os.path.dirname(input_path):
        #    os.system('rm %s' %input_path)
        return output_path

class ArmCP1(Arm):     # todo
    def __init__(self, idx):
        super().__init__(idx)
        self.action = 'CP1'     # special case, only CP1 init with section_idx, SP1 only set_content
        self.description = 'CP+1'

    def transfer(self, input_path, output_folder=rewriter_output_folder, verbose=True):
        if verbose == True:
            logger_rew.info('=== %s ===' %self.action)
        output_path = self.get_output_path(output_folder, input_path)

        pe = pefile.PE(input_path)
        code_section_idx = None
        for section_idx, section in enumerate(pe.sections):
            #logger_min.info('%s: %d, %s' %(self.sname, section_idx, section.Name[:5].decode('utf-8')))
            #logger_min.info(len(section.Name[:5].decode('utf-8')))
            try:
                if section.Name[:5].decode('utf-8') == '.text':
                    available_size = self.get_available_size_safe(pe, section_idx)
                    if available_size > 0:
                        code_section_idx = section_idx
                        #logger_min.info('%s: find .text in section_idx %d' %(self.sname, code_section_idx))
                    else:
                        if verbose == True:
                            logger_rew.info('code section has free space')
                    break
            except Exception as e:
                #exc_type, exc_obj, exc_tb = sys.exc_info()
                #fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                #logger_rew.error('%s %s:%s cannot parse pe' %(exc_type, fname, exc_tb.tb_lineno))
                logger_rew.error('decode section name fail')
        if code_section_idx != None:
            target_section = pe.sections[code_section_idx]
            pe.set_bytes_at_offset(target_section.PointerToRawData + target_section.Misc_VirtualSize, bytes([1]))
            pe.write(output_path)
    
            # verify action changes
            pe = self.try_parse_pe(output_path)
            if pe == None:
                if verbose == True:
                    logger_rew.info('pefile cannot parse, restore original file')
                os.system('cp -p %s %s' %(input_path, output_path))
        else:
            #logger_min.info('%s: cannot find code section' %self.sname)
            os.system('cp -p %s %s' %(input_path, output_path))

        #if 'rewriter_output' in os.path.dirname(input_path):
        #    os.system('rm %s' %input_path)
        return output_path

class ArmSR(Arm):
    def __init__(self, idx, mutate_one_byte=None):
        super().__init__(idx)
        self.mutate_one_byte = mutate_one_byte
        self.action = 'SR'
        self.section_idx = None
        self.new_name = None
        self.old_name = None
        self.update_description()

    def update_description(self):
        if self.mutate_one_byte:
            self.action = 'SR1'
            self.description = 'SR+1'
        elif self.new_name == None:
            self.description = 'SR+Rand'
        else:
            self.description = 'SR+' + hashlib.md5((str(self.section_idx) + self.new_name).encode()).hexdigest()[:8]

    def randomly_change_one_byte(self, old_name):
        if len(old_name) == 0:
            return random.choice(string.ascii_lowercase)
        new_name = old_name
        new_name_list = list(old_name)
        while(new_name == old_name):
            name_idx = random.randint(0, len(list(old_name))-1)
            new_name_list[name_idx] = random.choice(string.ascii_lowercase)
            new_name = ''.join(new_name_list)
        return new_name

    def mutate_section_name_one_byte(self):
        self.new_name = self.randomly_change_one_byte(self.old_name)
        self.action = 'SR1'
        self.description = 'SR+1'

    def transfer(self, input_path, output_folder=rewriter_output_folder, verbose=True):
        if verbose == True:
            logger_rew.info('=== %s ===' %self.action)
        output_path = self.get_output_path(output_folder, input_path)

        pe = pefile.PE(input_path)
        list_section_name = self.get_section_name_list(pe)
        if len(list_section_name) == 0:
            os.system('cp -p %s %s' %(input_path, output_path))
            return output_path

        if verbose == True:
            self.print_section_names(pe)

        if self.new_name == None and self.old_name == None and self.section_idx == None:
            # arm first use
            section_idx = random.choice(range(len(list_section_name)))
            old_name = list_section_name[section_idx]
            if self.description == 'SR+1':    # if SR1, change one byte
                new_name = self.randomly_change_one_byte(old_name)
            else:                       # if SR, randomly_select_new_name
                new_name = old_name
                while new_name == old_name:
                    new_name, _, _ = Utils.get_random_content()
            if verbose == True:
                logger_rew.info('old_name: %s, new_name: %s' %(old_name, new_name))

            # save for reuse later is succ
            self.new_name = new_name
            self.section_idx = section_idx
            self.old_name = old_name
        else:
            # reuse succ arm
            new_name = self.new_name
            if self.old_name in list_section_name:
                section_idx = list_section_name.index(self.old_name)
            elif self.section_idx >= len(list_section_name):
                section_idx = random.choice(range(len(list_section_name)))
            else:
                section_idx = self.section_idx

        pe.sections[section_idx].Name = new_name.encode()
        pe.write(output_path)

        # verify action changes
        pe = self.try_parse_pe(output_path)
        if pe:
            if verbose == True:
                self.print_section_names(pe)
        else:
            if verbose == True:
                logger_rew.info('pefile cannot parse, restore original file')
            os.system('cp -p %s %s' %(input_path, output_path))

        #if 'rewriter_output' in os.path.dirname(input_path):
        #    os.system('rm %s' %input_path)
        return output_path

class ArmSA(Arm):
    def __init__(self, idx, content=None):
        super().__init__(idx)
        self.content = content
        if content and len(content) == 1:
            self.action = 'SA1'
        else:
            self.action = 'SA'
        self.section_name = None

        self.description = None
        self.update_description()
    
    def set_content(self, content):
        self.content = content
        if len(content) == 1:
            self.action = 'SA1'
        self.update_description()

    def update_description(self):
        if self.content == None:
            self.description = 'SA+Rand'
        elif len(self.content) == 1:
            self.description = 'SA+1'
        else:
            self.description = 'SA+' + hashlib.md5(self.content).hexdigest()[:8]

    def transfer(self, input_path, output_folder=rewriter_output_folder, verbose=True):
        if verbose == True:
            logger_rew.info('=== %s ===' %self.action)
        output_path = self.get_output_path(output_folder, input_path)

        pe = pefile.PE(input_path)
        if verbose == True:
            self.print_section_names(pe)
    
        if self.content == None:
            # SA first use
            self.section_name, _, self.content = Utils.get_random_content()
        if self.section_name == None:
            # SA1 first use
            self.section_name, _, _ = Utils.get_random_content()

        number_of_section = pe.FILE_HEADER.NumberOfSections
        last_section = number_of_section - 1
        file_alignment = pe.OPTIONAL_HEADER.FileAlignment
        section_alignment = pe.OPTIONAL_HEADER.SectionAlignment
        if last_section >= len(pe.sections):
            os.system('cp -p %s %s' %(input_path, output_path))
            #if 'rewriter_output' in os.path.dirname(input_path):
            #    os.system('rm %s' %input_path)
            return output_path
        new_section_header_offset = (pe.sections[number_of_section - 1].get_file_offset() + 40)
        next_header_space_content_sum = pe.get_qword_from_offset(new_section_header_offset) + \
                pe.get_qword_from_offset(new_section_header_offset + 8) + \
                pe.get_qword_from_offset(new_section_header_offset + 16) + \
                pe.get_qword_from_offset(new_section_header_offset + 24) + \
                pe.get_qword_from_offset(new_section_header_offset + 32)
        first_section_offset = pe.sections[0].PointerToRawData
        next_header_space_size = first_section_offset - new_section_header_offset
        if next_header_space_size < 40:
            if verbose == True:
                logger_rew.info('no free space to add a new header before the fist section')
            os.system('cp -p %s %s' %(input_path, output_path))
            #if 'rewriter_output' in os.path.dirname(input_path):
            #    os.system('rm %s' %input_path)
            return output_path
        if next_header_space_content_sum != 0:
            if verbose == True:
                logger_rew.info('exist hidden header or data, such as VB header')
            os.system('cp -p %s %s' %(input_path, output_path))
            #if 'rewriter_output' in os.path.dirname(input_path):
            #    os.system('rm %s' %input_path)
            return output_path
    
        file_size = os.path.getsize(input_path)
    
        #alignment = True
        #if alignment == False:
        #    raw_size = 1
        #else:
        raw_size = self.align(len(self.content), file_alignment)
        virtual_size = self.align(len(self.content), section_alignment)
    
        raw_offset = file_size
        #raw_offset = self.align(file_size, file_alignment)
    
        #log('1. Resize the PE file')
        os.system('cp -p %s %s' %(input_path, output_path))
        pe = pefile.PE(output_path)
        original_size = os.path.getsize(output_path)
        fd = open(output_path, 'a+b')
        map = mmap.mmap(fd.fileno(), 0, access=mmap.ACCESS_WRITE)
        map.resize(original_size + raw_size)
        map.close()
        fd.close()
    
        pe = pefile.PE(output_path)
        virtual_offset = self.align((pe.sections[last_section].VirtualAddress +
                            pe.sections[last_section].Misc_VirtualSize),
                            section_alignment)
    
        characteristics = 0xE0000020
        self.section_name = self.section_name + ('\x00' * (8-len(self.section_name)))
    
        #log('2. Add the New Section Header')
        hex(pe.get_qword_from_offset(new_section_header_offset))
        pe.set_bytes_at_offset(new_section_header_offset, self.section_name.encode())
        pe.set_dword_at_offset(new_section_header_offset + 8, virtual_size)
        pe.set_dword_at_offset(new_section_header_offset + 12, virtual_offset)
        pe.set_dword_at_offset(new_section_header_offset + 16, raw_size)
        pe.set_dword_at_offset(new_section_header_offset + 20, raw_offset)
        pe.set_bytes_at_offset(new_section_header_offset + 24, (12 * '\x00').encode())
        pe.set_dword_at_offset(new_section_header_offset + 36, characteristics)
    
        #log('3. Modify the Main Headers')
        pe.FILE_HEADER.NumberOfSections += 1
        pe.OPTIONAL_HEADER.SizeOfImage = virtual_size + virtual_offset
        #pe.write(output_path)
    
        #log('4. Add content for the New Section')
        pe.set_bytes_at_offset(raw_offset, self.content)
        try:
            pe.write(output_path)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            logger_rew.error('%s %s:%s pe.write fail' %(exc_type, fname, exc_tb.tb_lineno))
            os.system('cp -p %s %s' %(input_path, output_path))
        
        # verify action changes
        pe = self.try_parse_pe(output_path)
        if pe:
            if verbose == True:
                self.print_section_names(pe)
                logger_rew.info('new section len: %d' %len(self.content))
        else:
            if verbose == True:
                logger_rew.info('pefile cannot parse, restore original file')
            os.system('cp -p %s %s' %(input_path, output_path))
        
        #if 'rewriter_output' in os.path.dirname(input_path):
        #    os.system('rm %s' %input_path)
        return output_path
