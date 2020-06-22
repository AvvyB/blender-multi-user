.. _internet-guide:

===================
Hosting on internet
===================

.. warning::
    Until now, those communications are not encrypted but are planned to be in a mid-term future (`Status <https://gitlab.com/slumber/multi-user/issues/62>`_).

This tutorial aims to guide you to host a collaborative Session on internet.
Hosting a session can be done is several ways:

- :ref:`host-blender`: hosting a session directly from the blender addon pannel
- :ref:`host-dedicated`: using a the dedicated server from a command line interface

.. _host-blender:

-------------
From blender
-------------
By default your router doesn't allow anyone to share you connection.
In order grant server access to people from internet you have tow main option:

* The :ref:`connection-sharing`: the easiest way.
* The :ref:`port-forwarding`: this one is the most unsecure, if you have no networking knowledge, you should definitively go to :ref:`connection-sharing`.

.. _connection-sharing:

Using a connection sharing solution
-----------------------------------

1. Simple: use a third party software like `HAMACHI <https://vpn.net/>`_ (Free until 5 users) or `ZEROTIER <https://www.zerotier.com/download/>`_ to handle network sharing.

.. _port-forwarding:

Using port-forwarding
---------------------

2. **Not secure** but simple: Setup port forwarding for each ports (for example 5555,5556,5557 and 5558 in our case). You can follow this `guide <https://www.wikihow.com/Set-Up-Port-Forwarding-on-a-Router>`_ for example.
To know which port are used by the 

Once you have setup the network, you can run **HOST** in order to start the server. Then other users could join your session in the regular way.

.. _host-dedicated:

--------------------------
From the dedicated server
--------------------------

.. code-block:: bash

    docker run -it --rm \
        -p 5555-5560:5555-5560 \
        -e port=5555 \
        -e password=admin \
        -e timeout=1000 \
        registry.gitlab.com/slumber/multi-user/multi-user-server:0.0.3

.. _port-setup:

-----------------------
Port setup (optionnal) 
-----------------------

The multi-user network architecture is based on a clients-server model. The communication protocol use four ports to communicate with client:

* Commands: command transmission (such as **snapshots**, **change_rights**, etc.) [given port]
* Subscriber : pull data [Commands port + 1]
* Publisher : push data [Commands port + 2]
* TTL (time to leave) : used to ping each clients [Commands port + 3]

To know which ports will be used, you just have to read the port in your preference.

.. figure:: img/hosting_guide_port.png
    :align: center
    :alt: Port

    Port in host settings
In the picture below we have setup our port to **5555** so it will be:

* Commands: 5555 (**5555**)
* Subscriber: 5556 (**5555** +1)
* Publisher: 5557 (**5555** +2)
* TTL: 5558 (**5555** +3)

Those four ports needs to be accessible from the client otherwise it wont work at all !