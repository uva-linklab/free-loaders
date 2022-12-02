import struct

def pack(json, additional_data):
    '''Create a byte array containing JSON and some data.
    '''

    # Place file's size in the first four bytes,
    # then the encoded JSON,
    # then the file data.
    b_file_size = struct.pack('I', len(additional_data))
    out_data = b_file_size + json.encode() + additional_data

    return out_data

def unpack(data):
    '''Return the JSON and file data in a packed message.
    '''

    additional_size = (struct.unpack('I', data[0:4]))[0]
    encoded_json = b''
    additional_data = None
    if additional_size == 0:
        encoded_json = data[4:]
    else:
        encoded_json = data[4:-(additional_size)]
        additional_data = data[-(additional_size):]

    return (encoded_json.decode(), additional_data)
