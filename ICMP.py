from socket import *
import os
import sys
import struct
import time
import select
import binascii

ICMP_ECHO_REQUEST = 8

def checksum(str_):
    # In this function we make the checksum of our packet
    str_ = bytearray(str_)
    csum = 0
    countTo = (len(str_) // 2) * 2

    for count in range(0, countTo, 2):
        thisVal = str_[count + 1] * 256 + str_[count]
        csum = csum + thisVal
        csum = csum & 0xffffffff

    if countTo < len(str_):
        csum = csum + str_[-1]
        csum = csum & 0xffffffff

    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer
    
    
def receiveOnePing(mySocket, ID, timeout, destAddr):
    timeLeft = timeout
    while 1:
        startedSelect = time.time()
        whatReady = select.select([mySocket], [], [], timeLeft)
        howLongInSelect = (time.time() - startedSelect)
        if whatReady[0] == []: # Timeout
            return "Request timed out."
        timeReceived = time.time()
        recPacket, addr = mySocket.recvfrom(1024)
#Fill in start
        
        #Fetch the ICMP header from the IP packet
        icmpHeader = recPacket[20:28]

        # Unpack the ICMP header
        icmpType = struct.unpack("bbHHh", icmpHeader)[0]
        code = struct.unpack("bbHHh", icmpHeader)[1]
        myChecksum = struct.unpack("bbHHh", icmpHeader)[2]
        packetID = struct.unpack("bbHHh", icmpHeader)[3]
        sequence = struct.unpack("bbHHh", icmpHeader)[4]



        if icmpType != 8 and packetID == ID:
            bytesInDouble = struct.calcsize("d")
            timeSent = struct.unpack("d", recPacket[28:28 + bytesInDouble])[0]
            return timeReceived - timeSent

        # prints error message depending on the code
        if icmpType == 3:
            if code == 0:
                return "Network Unreachable"
            elif code == 1:
                return "Host Unreachable"
            elif code == 2:
                return "Protocol Unreachable"
            elif code == 3:
                return "Port Unreachable"
            elif code == 4:
                return "Fragmentation Needed"
            elif code == 5:
                return "Source Route Failed"
            elif code == 6:
                return "Destination Network Unknown"
            elif code == 7:
                return "Destination Host Unknown"
            elif code == 8:
                return "Source Host Isolated"
            elif code == 9:
                return "Communication with Destination Network is Administratively Prohibited"
            elif code == 10:
                return "Communication with Destination Host is Administratively Prohibited"
            elif code == 11:
                return "Destination Network Unreachable for Type of Service"
            elif code == 12:
                return "Destination Host Unreachable for Type of Service"
            elif code == 13:
                return "Communication Administratively Prohibited"
            elif code == 14:
                return "Host Precedence Violation"
            elif code == 15:
                return "Precedence cutoff in effect"


#Fill in end
        
        
        timeLeft = timeLeft - howLongInSelect
        if timeLeft <= 0:
            return "Request timed out."

def sendOnePing(mySocket, destAddr, ID):
    # Header is type (8), code (8), checksum (16), id (16), sequence (16)
    myChecksum = 0
    # Make a dummy header with a 0 checksum
    
    # struct -- Interpret strings as packed binary data
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    data = struct.pack("d", time.time())
    # Calculate the checksum on the data and the dummy header.
    myChecksum = checksum(header + data)

    # Get the right checksum, and put in the header
    if sys.platform == 'darwin':
        # Convert 16-bit integers from host to network byte order
        myChecksum = htons(myChecksum) & 0xffff
    else:
        myChecksum = htons(myChecksum)
    
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    packet = header + data
    mySocket.sendto(packet, (destAddr, 1)) # AF_INET address must be tuple, not str
    # Both LISTS and TUPLES consist of a number of objects
    # which can be referenced by their position number within the object.


def doOnePing(destAddr, timeout):
    icmp = getprotobyname("icmp")
    # SOCK_RAW is a powerful socket type. For more details: http://sockraw.org/papers/sock_raw

#Fill in start
    
    #create socket
    my_socket = socket(AF_INET, SOCK_RAW, icmp)

#Fill in end
   
    myID = os.getpid() & 0xFFFF # Return the current process i
    
#Fill in start
    
    #send a single ping using the socket, dst addr and ID
    sendOnePing(my_socket, destAddr, myID)

    #add delay using timeout
    delay = receiveOnePing(my_socket, myID, timeout, destAddr)

    #close socket
    my_socket.close()

#Fill in end
    

    return delay
    
    
def ping(host, timeout=1):
    # timeout=1 means: If one second goes by without a reply from the server,
    # the client assumes that either the client's ping or the server's pong is lost
    total = 0
    sent = 0
    received = 0
    minrtt = float('inf')
    maxrtt = float('-inf')
    lost_packet = 0
    
    dest = gethostbyname(host)
    print("Pinging " + dest + " using Python:")
    print("")
    
    # Send ping requests to a server separated by approximately one second
    for i in range(5) :
        sent += 1
        delay = doOnePing(dest, timeout)
        if isinstance(delay, str):              # Request timed out
            lost_packet += 1
        else:
            total += delay * 1000
            minrtt = min(minrtt, delay* 1000) 
            maxrtt = max(maxrtt, delay* 1000) 
            received += 1  # successful response               

        print(delay)
        time.sleep(1)# one second
    
    packetloss_rate = (lost_packet / (received + lost_packet)) * 100
    print("\nPing statistics:")
    print(f"    Packets: Sent = {sent}, Received = {received}, Packet Loss = {lost_packet} ({packetloss_rate:.2f}%)")
    if received != 0:
        print(f"RTT:")
        print(f"    Minimum = {minrtt:.2f}ms, Maximum = {maxrtt:.2f}ms, Average = {total / sent:.2f}ms")
    return delay

print("Pinging to localhost...")
ping("127.0.0.1")

print("Pinging to Canada...")
ping("ca.gov")

print("Pinging to Qatar...")
ping("104.122.143.234")

print("Pinging to Hong Kong...")
ping("www.carousell.com.hk")
