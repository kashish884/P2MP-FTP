
# Import required Python libraries
from socket import *
import sys
import os
import requests
import time
from datetime import  datetime

# Initialization of constants
DATA_PACKET = 0b0101010101010101
LAST_DATA_PACKET = 0b0101010101010111
ACK = 0b1010101010101010
HEADER_SIZE = 8
MAX_MSS = 2048
ACK_SIZE = 8

USAGE = 'Argument validation issue        ' \


def rdt_send():

    seq_number = 0
    bytes_sent = 0
    
    file_size = os.stat(file_name).st_size
    file_in = open(file_name, 'rb')
    payload = file_in.read(mss - HEADER_SIZE)
    try:
        while payload:
            if seq_number > 0xffffffff:
                seq_number = seq_number - 0xffffffff
            # Get the checksum and header
            checksum = get_checksum(seq_number, payload)
            if bytes_sent + len(payload) < file_size:
                bytes_sent = bytes_sent + len(payload)
                header = get_header(seq_number, checksum)
            else:
                header = get_header(seq_number, checksum,
                                    indicator=LAST_DATA_PACKET)
            # Continuously re-transmit the same datagram until all P2MP-FTP Servers correctly ACKed it
            while rdt_send_datagram(header + payload, seq_number):
                pass
            # Get header field for the next packet
            payload = file_in.read(mss - HEADER_SIZE)
            seq_number = seq_number + mss
    except KeyboardInterrupt:
        pass
    file_in.close()


def get_checksum(seq_number, payload):

    # Split 32-bit sequence number into two 16-bit numbers
    # Initialize checksum with right-most 16 bits of sequence number
    checksum = seq_number & 0xffff
    seq_num_left_bits = seq_number >> 16
    # Add checksum with left-most 16 bits of sequence number and data packet
    # indicator
    checksum = wrap_around(checksum, seq_num_left_bits)
    checksum = wrap_around(checksum, DATA_PACKET)
    # Include payload (file content) into checksum
    for i in range(0, len(payload), 2):
        try:
            word = ord(payload[i]) + (ord(payload[i+1]) << 8)
        except IndexError:
            word = ord(payload[i]) + (0 << 8)
        checksum = wrap_around(checksum, word)
    return ~checksum & 0xffff


def wrap_around(a, b):

    checksum = a + b
    return (checksum & 0xffff) + (checksum >> 16)


def get_header(seq_number, checksum, indicator=DATA_PACKET):

    seq_number_hex = hex(seq_number).lstrip('-0x').zfill(8).decode('hex')
    checksum_hex = hex(checksum).lstrip('-0x').zfill(4).decode('hex')
    indicator_hex = hex(indicator).lstrip('-0x').zfill(4).decode('hex')
    return seq_number_hex + checksum_hex + indicator_hex


def rdt_send_datagram(datagram, seq_number):
    
    retransmit = False
    client_socket = socket(AF_INET, SOCK_DGRAM)
    client_socket.settimeout(timeout_interval)
    try:
        # Send datagram to P2MP-FTP Servers yet did not receive this datagram
        # using new UDP socket
        for name, host in dict_hosts.iteritems():
            # No need to retransmit datagram if server has already received it
            if host.ack != seq_number:
                host.ack_response = False
                retransmit = True
                client_socket.sendto(datagram, (name, server_port))
        # Read ACKs until whether all P2MP-FTP Servers ACKed this datagram or
        # timeout is triggered
        while not all_responses_received():
            ack_packet, (server_ip, port) = client_socket.recvfrom(ACK_SIZE)
            extract_server_ack(seq_number, ack_packet, server_ip)
    except timeout:
        seq_number = seq_number
        print 'Timeout, sequence number = {}'.format(seq_number)
    client_socket.close()

    del client_socket
    return retransmit


def extract_server_ack(seq_number, ack_packet, server_ip):

    try:
        dict_hosts[server_ip].ack_response = True
        # Extract received ACKed sequence number, zero field and ACK indicator
        rcv_ack = int(ack_packet[:4].encode('hex'), 16)
        rcv_zero_field = int(ack_packet[4:6].encode('hex'), 16)
        rcv_ack_indicator = int(ack_packet[6:8].encode('hex'), 16)
        # Verify whether this server responded with an ACK and in-sequence ACK
        assert rcv_ack_indicator == ACK
        assert rcv_zero_field == 0
        assert rcv_ack == seq_number
        dict_hosts[server_ip].ack = seq_number
    except (AssertionError, KeyError, TypeError):
        return


def all_responses_received():

    for name, host in dict_hosts.iteritems():
        if not host.ack_response:
            return False
    return True


class Host:

    def __init__(self, name):
        #Initiates Host object with default attributes
        self.name = name
        self.ack = None
        self.ack_response = False


# Initialize dictionary of host objects
dict_hosts = {}
timeout_interval = 0
start = datetime.now()
try:
    # Validation of all arguments received from command line
    assert len(sys.argv) >= 5, 'Error: Wrong number of arguments...\n'
    assert sys.argv[-1].isdigit(), \
        'Error: Maximum Segment Size (MSS) provided: \'{}\' is not Integer ' \
        'type...\n'.format(sys.argv[-1])
    assert sys.argv[-3].isdigit(), \
        'Error: Port number of the Server(s) provided: \'{}\' is not Integer ' \
        'type...\n'.format(sys.argv[-3])
    mss = int(sys.argv[-1])
    server_port = int(sys.argv[-3])
    assert mss > HEADER_SIZE, \
        'Exception: Maximum Segment Size (MSS) provided: \'{}\' <= 8 bytes ' \
        'is not enough to encapsulate the payload into the ' \
        'segment...\n'.format(sys.argv[-1])
    assert MAX_MSS >= mss, \
        'Exception: Maximum Segment Size (MSS) provided: \'{}\' exceeds ' \
        'possible MSS value of 2048 bytes (consider smaller value for ' \
        'MMS)...'.format(sys.argv[-1])
    assert 1024 < server_port <= 0xffff, \
        'Port number must be in rage of (1024, 65535]\n'
    file_name = sys.argv[-2]
    assert os.path.isfile(file_name), \
        'Error: \'{}\' no such file...\n'.format(file_name)
    for h in range(1, len(sys.argv) - 3):
        # Create host object with the name, ACK response packet and ACK
        # sequence number. Store object into the dictionary of hosts
        if sys.argv[h] == 'localhost':
            hostname = '127.0.0.1'
        else:
            hostname = sys.argv[h]
        _host = Host(hostname)
        dict_hosts[hostname] = _host
        # Determine RTT to this host and adjust timeout accordingly
        start_time = time.time()
        try:
            http_request = requests.get('http://{}'.format(hostname))
            rtt = http_request.elapsed.total_seconds()
            
        except requests.exceptions.RequestException:
            rtt = time.time() - start_time
        if rtt > timeout_interval:
            timeout_interval = rtt
        print 'RTT = {0}'.format(rtt)    
    # Start transferring data to P2MP-FTP Servers
    rdt_send()
except AssertionError, e:
    print e, USAGE
except ValueError, e:
    print e
end = datetime.now()
diff = end - start
diff = diff.total_seconds()
print('\nTotal time(s): ' + str(diff))
print('\n')
