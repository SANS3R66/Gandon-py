# половина кода любезно спизженно из https://github.com/0BuRner/corona-archiver

import struct
import os
import sys
import subprocess

class GanDecryptor:
    _MAGIC_NUMBER_HEADER_CAR = b'\x72\x61\x63\x01'
    _MAGIC_NUMBER_HEADER_GAN = b'\x67\x6E\x61\x01'
    _MAGIC_NUMBER_INDEX = 1
    _MAGIC_NUMBER_DATA = 2
    _MAGIC_NUMBER_END = b'\xFF\xFF\xFF\xFF'

    def __init__(self, input_file, output_dir, decompile):
        self.input_file = input_file
        self.output_dir = output_dir
        self.key_bytes = "7f13a9cf-2f55-4898-8294-b6b0655d59f1".encode('utf-8')
        self.key_length = len(self.key_bytes) # 36 должен быть по идеи
        self.file_size = os.path.getsize(input_file)
        self.index = {}
        self.is_gan = False
        self.byte_index = 0
        self.decompile = decompile

        if not os.path.isdir(self.output_dir):
            os.makedirs(self.output_dir)

    """
        v25 = a7f13a9cf2f5548[v23 + 2 + -36 * (v24 / 0x24)];
        ++v24;
        v22[v23] = *((_BYTE *)v21 + v23) ^ v25;
        ++v23;
    """
    def decrypt_content(self, data, size):
        content = bytearray()
        for i in range(size):
            byte_val = data[i]
            counter = i + 2
            key_index = (counter - 36 * (counter // 36)) % self.key_length
            key_byte = self.key_bytes[key_index]
            decrypted_byte = byte_val ^ key_byte
            content.append(decrypted_byte)
        return bytes(content)

    def read_padding(self, length, section_type):
        padding_length = (4 - (length % 4)) % 4 if section_type == 'data' else (4 - (length % 4)) % 4 if length % 4 != 0 else 0
        self.infile.read(padding_length)
        self.byte_index += padding_length

    def process(self):
        with open(self.input_file, 'rb') as self.infile:
            header = self.infile.read(16)
            if len(header) < 16:
                raise EOFError("чета файл короткий")
            self.byte_index += 16
            magic_number, revision, data_offset_start, index_length = struct.unpack('<4sIII', header)

            if magic_number == self._MAGIC_NUMBER_HEADER_GAN:
                self.is_gan = True
            elif magic_number != self._MAGIC_NUMBER_HEADER_CAR:
                raise ValueError(f"магическое число не то")
            if revision != 1:
                print(f"[WARNING] revision {revision} не 1, другая версия архива???")

            for _ in range(index_length):
                entry = self.infile.read(12)
                if len(entry) < 12:
                    raise EOFError("index секция короткая слишком")
                entry_type, data_offset, filename_length = struct.unpack('<III', entry)
                self.byte_index += 12
                if entry_type != self._MAGIC_NUMBER_INDEX:
                    raise ValueError(f"неверный entry_type: {entry_type}")

                filename_bytes = self.infile.read(filename_length + 1)
                if len(filename_bytes) < filename_length + 1:
                    raise EOFError("неполное имя файла в секции index")
                filename = filename_bytes[:-1].decode('utf-8', errors='replace')
                self.index[data_offset] = filename
                self.byte_index += filename_length + 1

                self.read_padding(filename_length + 1, 'index')

            while self.byte_index < self.file_size:
                entry_type_bytes = self.infile.read(4)
                if len(entry_type_bytes) < 4:
                    if entry_type_bytes == b'':
                        print("[DEBUG] конец файла")
                        break
                    raise EOFError(f"неполная запись данных, прочитано {len(entry_type_bytes)} байт")
                self.byte_index += 4

                if entry_type_bytes == self._MAGIC_NUMBER_END:
                    self.infile.read(4)
                    self.byte_index += 4
                    break
                elif entry_type_bytes == struct.pack('<I', self._MAGIC_NUMBER_DATA):
                    next_offset_bytes = self.infile.read(4)
                    file_size_bytes = self.infile.read(4)
                    if len(next_offset_bytes) < 4 or len(file_size_bytes) < 4:
                        raise EOFError("мало данных")
                    next_offset, file_size = struct.unpack('<II', next_offset_bytes + file_size_bytes)
                    self.byte_index += 8

                    if file_size > self.file_size - self.byte_index:
                        raise ValueError(f"file_size ({file_size}) превышает байты ({self.file_size - self.byte_index})")

                    file_content = self.infile.read(file_size)
                    if len(file_content) < file_size:
                        raise EOFError("неполный file_content")
                    self.byte_index += file_size

                    offset = self.byte_index - file_size - 12
                    filename = self.index.get(offset, f"file-{offset}.extracted")

                    if self.is_gan: # самый сок
                        print(f"[+] дешифруется {filename}")
                        file_content = self.decrypt_content(file_content, file_size)

                    # сохраняем байткод чтобы можно было ручками декомпильнуть
                    with open(os.path.join(self.output_dir, filename), 'wb') as outfile:
                        outfile.write(file_content)

                    # декомпилируем если надо
                    if self.decompile:
                        print(f"[+] декомпилируется {filename}")
                        process = subprocess.run(['java', '-jar', 'unluac.jar', os.path.join(self.output_dir, filename)], capture_output=True, text=True, check=True)
                        with open(os.path.join(self.output_dir, filename + '.lua'), 'wb') as outfile:
                            outfile.write(process.stdout.encode('utf-8'))

                    self.read_padding(file_size, 'data')
                else:
                    raise ValueError(f"неизвестный entry_type: {entry_type_bytes.hex()} на {self.byte_index - 4}")

def gan_decrypt(input_file, output_dir, decompile):
    try:
        decryptor = GanDecryptor(input_file, output_dir, decompile)
        decryptor.process()
        print(f"[+] архив '{input_file}' успешно дешифрован в '{output_dir}'")
    except FileNotFoundError:
        print(f"[-] нет файла '{input_file}' еблойд")
    except EOFError as e:
        print(f"[-] ошибка: {e}")
    except ValueError as e:
        print(f"[-] ошибка: {e}")
    except Exception as e:
        print(f"[-] еще хуже ошибка: {e}")
