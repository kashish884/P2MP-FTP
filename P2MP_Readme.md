
# Point-to-Multipoint File Transfer Protocol (P2MP-FTP)
P2MP-FTP - protocol that provides a FTP sophisticated service: transferring a file from one host (p2mp client) to multiple destinations (p2mp servers).
P2MP-FTP uses UDP to send packets from the sending host (p2mp client) to each of the destinations (p2mp servers) as different to the traditional FTP where TCP is used to ensure 
reliable data transmission of files from one sender to one receiver. In order to provide reliable data transfer service over UDP, P2MP-FTP utilizes the Stop-and-Wait automatic 
repeat request (ARQ). Hence, using the unreliable UDP protocol, P2MP-FTP implements a transport layer service such as reliable data transfer in user space.

The project consists of 2 (two) main programs: P2MP-FTP Client (Sender) program that runs on a single host, implements the sending side of the reliable Stop-and-Wait data transfer, 
and P2MP-FTP Server (Receiver) program that can run on multiple hosts, listens on the well-known port, and implements the receiving side of the Stop-and-Wait protocol. 


## Run P2MP-FTP Server (Receiver) program
To execute the P2MP-FTP Server (Receiver) program run:

```
python p2mpserver.py arg1 arg2 arg3
```

 where all 3 (three) arguments are required and specified as follows:
 *  arg1:
	Port number of the Server to which the Server is listening. The port number must be in the range of allowed ports `(1024, 65535]`. The firewall on the Servers must be disabled.
	
 *  arg2:
	Name of the file where the data will be written.
	
 *  arg3:
	Packet loss probability denoted as *p*. The value must be in the range of `0 <= p <= 1`.

*Example of the P2MP-FTP Server (Receiver) program execution:*
```
python p2mpserver.py 65450 testing.txt 0.5
```


## Run P2MP-FTP Client (Sender) program

install pip:
[get-pip.py file is present within the project folder]
python get-pip.py

python -m pip install requests

To execute the P2MP-FTP Client (Sender) program run:
```
python p2mpclient.py arg1 arg2 ... arg(i) arg(i+1) arg(i+2) arg(i+3)
```
where at least 4 (four) arguments are required and specified as follows:
 *	arg1, arg2, . . . , arg(i):
	Host name(s) or IPv4 address(es) of the Server(s). Can take any number of servers.
	
 *  arg(i+1):
	Port number of the Server(s) to which the Server(s) is listening. All Servers must listen on the same port number.The firewall on the Servers must be disabled.
	
 *  arg(i+2):
	Name of the file to be transmitted.
	
 *  arg(i+3):
	Maximum segment size (MSS) in bytes. MSS must be greater than the header size (8 bytes), but less than maximum allowed MSS value (2048 bytes).
    
*Example of the P2MP-FTP Client (Sender) program execution:*
```
python p2mpclient.py 152.46.17.179 152.46.17.182 152.46.17.192 65450 2mb.txt 1000
```


# Version
 - 1.0

#Authors
----
Kashish Singh, Sathwik Kalvakuntla

# License

  - All rights reserved by the owner and NC State University.
  - Usage of the code can be done post approval from the above.
