from net_components import RCFClient
import time
client = RCFClient()

client.connect("127.0.0.1",5555)


try:
    while True:
        client.set('key', 1)
        # Distribute as key-value message
        time.sleep(1)
except KeyboardInterrupt:
    pass
