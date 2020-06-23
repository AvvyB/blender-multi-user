.. _internet-guide:

===================
Hosting on internet
===================

.. warning::
    Until now, those communications are not encrypted but are planned to be in a mid-term future (`Status <https://gitlab.com/slumber/multi-user/issues/62>`_).

This tutorial aims to guide you to host a collaborative Session on internet.
Hosting a session can be done is several ways:

- :ref:`host-blender`: hosting a session directly from the blender addon pannel.
- :ref:`host-dedicated`: hosting a session directly from the command line interface on a computer without blender.

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

Many different third party software like `ZEROTIER <https://www.zerotier.com/download/>`_ (Free) or `HAMACHI <https://vpn.net/>`_ (Free until 5 users) allow you to share your private network with other peole.
For the example I'm gonna use ZeroTier because its free and open soure.

1. Installation
^^^^^^^^^^^^^^^

Let's start by downloading and installing ZeroTier:
https://www.zerotier.com/download/

Once installed, launch it.

2. Network creation
^^^^^^^^^^^^^^^^^^^

Before trying to connect to any network we need to create one.
Only the host need to do this step.

To create a ZeroTier private network you need to register a ZeroTier account `on my.zerotier.com <https://my.zerotier.com/login>`_
(click on **login** then register on the bottom)

Once you account it activated, you can connect to `my.zerotier.com <https://my.zerotier.com/login>`_.
Head up to the **Network** section(highlighted in red in the image below).

.. figure:: img/hosting_guide_head_network.png
    :align: center
    :width: 400px

    ZeroTier user homepage

Hit 'Create a network'(see image below) and go to the network settings.

.. figure:: img/hosting_guide_create_network.png
    :align: center
    :width: 400px

    Network page

Now that the network is created, let's configure it.

In the Settings section(see image below), you can change the network name to what you want.
Make sure that the field **Access Control** is set to **PRIVATE**.

.. hint::
    If you set the Access Control to PUBLIC, anyone will be able to join without
    your confirmation.  Its easier to setup but less secure. 

.. figure:: img/hosting_guide_network_settings.png
    :align: center
    :width: 400px

    Network settings

That's all for the network setup !
Now let's connect everyone.

3. Network authorization
^^^^^^^^^^^^^^^^^^^^^^^^

Since your ZeroTier network is Private, you will need to authorize each new users
to connect to it.
For each user you want to add, do the following step:

1. Get the client **ZeroTier id** by right clicking on the ZeroTier tray icon and click on the `Node ID`, it will copy it.

.. figure:: img/hosting_guide_get_node.png
    :align: center
    :width: 400px

    Get the zerotier client id

2. Go to the network settings in the Member section and paste the Node ID into the Manualy Add Member field.

.. figure:: img/hosting_guide_add_node.png
    :align: center
    :width: 400px

    Add the client to network authorized users

4. Network connection
^^^^^^^^^^^^^^^^^^^^^

To connect to the ZeroTier network, start to copy the network id.

.. figure:: img/hosting_guide_get_id.png
    :align: center
    :width: 400px



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
    :width: 200px

    Port in host settings
In the picture below we have setup our port to **5555** so it will be:

* Commands: 5555 (**5555**)
* Subscriber: 5556 (**5555** +1)
* Publisher: 5557 (**5555** +2)
* TTL: 5558 (**5555** +3)

Those four ports needs to be accessible from the client otherwise it wont work at all !