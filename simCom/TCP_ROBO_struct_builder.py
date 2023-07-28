import struct

bag = struct.pack('>fi',123.4567,1)
print(bag)
print(struct.unpack('>fi',bag))

x=input("")
print(x)