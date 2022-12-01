import struct

def pack(json, file_path=None):
    '''Create a byte array containing JSON and a file.
    '''

    file_data = b''
    if file_path != None:
        with open(file_path, 'rb') as fh:
            file_data = fh.read()

    # Place file's size in the first four bytes,
    # then the encoded JSON,
    # then the file data.
    b_file_size = struct.pack('I', len(file_data))
    out_data = b_file_size + json.encode() + file_data

    return out_data

def unpack(data):
    '''Return the JSON and file data in a packed message.
    '''

    file_size = (struct.unpack('I', data[0:4]))[0]
    encoded_json = b''
    file_data = None
    if file_size == 0:
        encoded_json = data[4:]
    else:
        encoded_json = data[4:-(file_size)]
        file_data = data[-(file_size):]

    return (encoded_json.decode(), file_data)
