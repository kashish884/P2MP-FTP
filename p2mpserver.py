
# Import required Python libraries
from socket import *
from random import *
import sys
import os
from datetime import  datetime

# Initialization of constants
DATA_PACKET = 0b0101010101010101
LAST_DATA_PACKET = 0b0101010101010111
ACK = 0b1010101010101010
HEADER_SIZE = 8
MAX_MSS = 2048
USAGE = 'Argument validation issue        ' \


def rdt_receive():
    #Receives and handles data packets from the P2MP-FTP Client.
    #It receives the data packet, decides whether it needs to discard or process it based on probability value.
    
    server_socket = socket(AF_INET, SOCK_DGRAM)
    
    file_out = open(file_name, 'wb')                        #The wb indicates that the file is opened for writing in binary mode.
    start = datetime.now()
    print('\nStart time(s): ' + str(start))
    try:
        server_socket.bind(('', server_port))
        seq_number = 0
        print 'P2MP-FTP Server is initialized and listening ...'
        receive = True
        while receive:
            datagram, client_address = server_socket.recvfrom(MAX_MSS)
            random_number = random()                   # Discard (r <= p) & no other action taken in care or process received packet (r > p)
            header = datagram[:HEADER_SIZE]             # Process the data packet All bytes b4 or till 8 bytes are header field
            payload = datagram[HEADER_SIZE:]            # Process the data packet All bytes after 8 bytes are payload field
                
            rcv_seq_number = validation(header, payload, seq_number)    # Do validation on checksum, data indicator and sequence number
            if probability < random_number:
                
                
                
                if rcv_seq_number is not None and rcv_seq_number == seq_number:     # Received packet is in-sequence so Construct the ACK and send it back to the client
                    
                    ack_packet = ack_encapsulation(rcv_seq_number)
                    server_socket.sendto(ack_packet, client_address)            
                    
                    file_out.write(payload)                                 # Write payload to the file
                    
                    seq_number = seq_number + len(header) + len(payload)    # Compute next expected sequence number
                    if seq_number > 0xffffffff:
                        seq_number = seq_number - 0xffffffff
                    
                    if int(header[6:8].encode('hex'), 16) == LAST_DATA_PACKET:      # Check if this is the last packet in sequence
                        receive = False
                
                elif rcv_seq_number is not None:                                    # Received packet is out-of-sequence
                    
                    if rcv_seq_number < seq_number:                                 # Construct the ACK and send it back to the client
                        ack_packet = ack_encapsulation(rcv_seq_number)
                    else:
                        
                        ack_packet = ack_encapsulation(seq_number)                  # ACK for the last received in-sequence packet
                    server_socket.sendto(ack_packet, client_address)
            else:
                rcv_seq_number = validation(header, payload, seq_number)
                if rcv_seq_number is not None and rcv_seq_number == seq_number:
                    seq_number1 = seq_number
                    print 'Packet loss, sequence number = {}'.format(seq_number1)
                
        print 'Complete!'
        end = datetime.now()
        print('\nEnd time: ' + str(end))
        diff = end - start
        diff = diff.total_seconds()
        print('\nTotal time(s): ' + str(diff))
    except error, (value, message):
        print 'Exception while creating and binding RFC Server socket:'
        print message
    except KeyboardInterrupt:
        print 'Some keyboard interruption has been made! BYE'
    file_out.close()
    server_socket.close()
    del server_socket


def validation(header, payload, seq_number):                #Performs validation on the received packet
    rcv_seq_number = int(header[:4].encode('hex'), 16)
    rcv_checksum = int(header[4:6].encode('hex'), 16)
    rcv_indicator = int(header[6:8].encode('hex'), 16)
    
    
    checksum = rcv_seq_number & 0xffff                      # Split 32-bit sequence number into two 16-bit numbers
    rcv_seq_num_left_bits = rcv_seq_number >> 16            # Initialize checksum with right-most 16 bits of sequence number
    
    
    checksum = wrap_around(checksum, rcv_seq_num_left_bits)         # Add checksum with left-most 16 bits of sequence number, received
    checksum = wrap_around(checksum, rcv_checksum)
    checksum = wrap_around(checksum, DATA_PACKET)
    # Add received payload (file content) into checksum
    for i in range(0, len(payload), 2):
        try:
            word = ord(payload[i]) + (ord(payload[i + 1]) << 8)
        except IndexError:
            word = ord(payload[i]) + (0 << 8)
        checksum = wrap_around(checksum, word)
    try:
        assert rcv_indicator in [DATA_PACKET, LAST_DATA_PACKET], \
            'Packet dropped, not a data packet'
        assert checksum == 0xffff, \
            'Packet is corrupted, dropping it [checksum = {}]'.format(bin(checksum).lstrip('-0b').zfill(16))
    except AssertionError, _e:
        print _e
        return None
    try:
        assert seq_number == rcv_seq_number, \
            'Packet loss, sequence number = {}'.format(rcv_seq_number)
    except AssertionError, _e:
        print _e
    return rcv_seq_number


def wrap_around(a, b):          #Performs wrap around on two 16-bit words if overflow occurs.
    
    checksum = a + b
    return (checksum & 0xffff) + (checksum >> 16)


def ack_encapsulation(seq_number):      #Encapsulates data into ACK packet that will be sent to P2MP-FTP Client.
    
    seq_number_hex = hex(seq_number).lstrip('-0x').zfill(8)
    seq_number_hex = seq_number_hex.decode('hex')
    zero_field_hex = hex(0).lstrip('-0x').zfill(4)
    zero_field_hex = zero_field_hex.decode('hex')
    ack_indicator = hex(ACK).lstrip('-0x').zfill(4)
    ack_indicator = ack_indicator.decode('hex')
    return seq_number_hex + zero_field_hex + ack_indicator

# Validation of all arguments received from command line

try:
    
    assert len(sys.argv) == 4, 'Error: Wrong number of arguments...\n'
    assert sys.argv[1].isdigit(), \
        'Error: Port number of the Server provided to which server must ' \
        'listen: \'{}\' is not Integer type...\n'.format(sys.argv[1])
    server_port = int(sys.argv[1])
    assert 1024 < server_port <= 0xffff, \
        'Port number must be in rage of (1024, 65535]\n'
    file_name = sys.argv[2]
    assert not os.path.isfile(file_name), \
        'Exception: \'{}\' file already exists, consider giving ' \
        'different name or removing file...\n'.format(file_name)
    probability = float(sys.argv[3])
    assert 0 <= probability <= 1, \
        'Exception: Packet loss probability must be in range of [0, 1]\n'
    
    rdt_receive()               # Start listening on well-known port
except AssertionError, e:
    print e, USAGE
except ValueError, e:
    print e
    print 'Exception: Packet loss probability argument provided: \'{}\' is ' \
          'neither of Integer nor Float type, it must be integer or float in ' \
          'range of [0, 1]'.format(sys.argv[3])
