from opcua import Client, ua      

# connect
reader = Client("opc.tcp://10.129.4.73:4840")
reader.connect()
reader.load_type_definitions()

# connect
writer = Client("opc.tcp://10.129.4.73:4840")
writer.connect()
writer.load_type_definitions()

# toggle Livebit by subscription
class LivebitHandler(object):
    def datachange_notification(self, node, value, data):
        print("Livebit:", value)
        
        # use the OPC-UA variable Livebit2DuoMix when using a duo-mix, Livebit2machine when using a SMP
        Livebit2machine = writer.get_node("ns=4;s=|var|B-Fortis CC-Slim S04.Application.GVL_OPC.Livebit2DuoMix")
        #Livebit2machine = writer.get_node("ns=4;s=|var|B-Fortis CC-Slim S04.Application.GVL_OPC.Livebit2machine")
        
        Livebit2machine.set_value(ua.Variant(value, ua.VariantType.Boolean))

Livebit2extern = reader.get_node("ns=4;s=|var|B-Fortis CC-Slim S04.Application.GVL_OPC.Livebit2extern")
subHandler = LivebitHandler()
sub = reader.create_subscription(100, subHandler)
subscription = sub.subscribe_data_change(Livebit2extern)

# use keyboard to start and stop
from pynput.keyboard import Listener
Remote_start = writer.get_node("ns=4;s=|var|B-Fortis CC-Slim S04.Application.GVL_OPC.Remote_start")
ValueMixing = writer.get_node("ns=4;s=|var|B-Fortis CC-Slim S04.Application.GVL_OPC.set_value_mixingpump")
pump_value = 0
def on_press(key):  # The function that's called when a key is pressed
    global pump_value 
    try:
        match key.char:
            case 'p':
                pump_value = int(pump_value + 65535 / 100)
                if pump_value > 65535: pump_value = 65534 
                print(f"Faster: {int(pump_value * 100 / 65535)}%")
                ValueMixing.set_value(ua.Variant(pump_value, ua.VariantType.UInt16))
            case 'm':
                pump_value = int(pump_value - 65535 / 100)
                if pump_value < 0: pump_value = 0
                print(f"Slower: {int(pump_value * 100 / 65535)}%")
                ValueMixing.set_value(ua.Variant(pump_value, ua.VariantType.UInt16))
            case 's':
                print("Start")
                Remote_start.set_value(ua.Variant(True, ua.VariantType.Boolean))
            case 'h':
                print("Stop")
                Remote_start.set_value(ua.Variant(False, ua.VariantType.Boolean))
    except AttributeError:
        pass

def on_release(key):  # The function that's called when a key is released
    pass

with Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join() 