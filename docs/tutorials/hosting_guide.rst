================
Advanced hosting
================

This tutorial aims to guide you to host a collaborative Session on internet.

.. note::
    This tutorial will change soon with the new dedicated server. 


The multi-user network architecture is based on a clients-server model. The communication protocol use four ports to communicate with client:

* Commands: command transmission (such as **snapshots**, **change_rights**, etc.)
* Subscriber: pull data
* Publisher: push data 
* TTL (time to leave): used to ping each clients

To know which ports will be used, you just have to read the port in your preference.

.. image:: img/hosting_guide_port.png
    :align: center
    :alt: Port

In the picture below we have setup our port to **5555** so it will be:

* Commands: 5555 (**5555** +0)
* Subscriber: 5556 (**5555** +1)
* Publisher: 5557 (**5555** +2)
* TTL: 5558 (**5555** +3)

Now that we know which port are needed to communicate we need to allow other computer to communicate with our one. 
By default your router shall block those ports. In order grant server access to people from internet you have multiple options:

1. Simple: use a third party software like `HAMACHI <https://vpn.net/>`_ (Free until 5 users) or `ZEROTIER <https://www.zerotier.com/download/>`_ to handle network sharing.

2. Harder: Setup a VPN server and allow distant user to connect to your VPN.

3. **Not secure** but simple: Setup port forwarding for each ports (for example 5555,5556,5557 and 5558 in our case). You can follow this `guide <https://www.wikihow.com/Set-Up-Port-Forwarding-on-a-Router>`_ for example.

Once you have setup the network, you can run **HOST** in order to start the server. Then other users could join your session in the regular way.




