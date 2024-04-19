import socket
import struct

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect the socket to the port where the server is listening
server_address = ("localhost", 10001)
print("connecting to " + str(server_address))
sock.connect(server_address)

try:

    # Send data
    message = struct.pack(
        ">iccffffffffffffffffiiiiiciiiiii",
        1,
        bytes("L", "utf-8"),
        bytes("E", "utf-8"),
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
        20,
        21,
        bytes("V", "utf-8"),
        22,
        23,
        24,
        25,
        26,
        27,
    )
    print("sending: " + str(message))
    sock.sendall(message)

    # Look for the response
    amount_received = 0
    amount_expected = 8

    while amount_received < amount_expected:
        data = sock.recv(16)
        amount_received += 1
        print(
            "received: "
            + str(struct.unpack(">f", data[0:4])[0])
            + ", "
            + str(struct.unpack(">i", data[4:8])[0])
        )

finally:
    print("closing socket")
    sock.close()
