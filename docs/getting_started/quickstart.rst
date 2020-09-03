.. _quickstart:

===========
Quick start
===========

.. hint::
   *All session related settings are located under: `View3D -> Sidebar -> Multiuser panel`*

The multi-user is based on a session management system.
In this this guide you will quickly learn how to use the collaborative session system in three part:

- :ref:`how-to-host`
- :ref:`how-to-join`
- :ref:`how-to-manage`

.. _how-to-host:

How to host a session
=====================

The multi-user add-on rely on a Client-Server architecture. 
The server is the heart of the collaborative session, 
it will allow each users to communicate with each others.  
In simple terms, *Hosting a session* means *run a local server and connect the local client to it*. 
When I said **local server** I mean accessible from the LAN (Local Area Network). 

However sometime you will need to host a session over the internet, 
in this case I strongly recommand you to read the :ref:`internet-guide` tutorial.

.. _user-info:

-----------------------------
1. Fill your user information
-----------------------------

The **User Info** panel (See image below) allow you to constomize your online identity.

.. figure:: img/quickstart_user_info.png
   :align: center

   User info panel


Let's fill those tow field:

- **name**: your online name.
- **color**: a color used to represent you into other user workspace(see image below).


During online sessions, other users will see your selected object and camera hilghlited in your profile color.

.. _user-representation:

.. figure:: img/quickstart_user_representation.png
   :align: center

   User viewport representation

--------------------
2. Setup the network
--------------------

When the hosting process will start, the multi-user addon will lauch a local server instance.
In the nerwork panel select **HOST**.
The **Host sub-panel** (see image below) allow you to configure the server according to:

* **Port**: Port on wich the server is listening.
* **Start from**: The session initialisation method.

   * **current scenes**: Start with the current blendfile datas.
   * **an empty scene**: Clear a data and start over.
   
   .. danger::
      By starting from an empty, all of the blend data will be removed !
      Ensure to save your existing work before launching the session.

* **Admin password**: The session administration password.

.. figure:: img/quickstart_host.png 
   :align: center
   :alt: host menu

   Host network panel


.. note:: Additionnal configuration setting can be found in the :ref:`advanced` section.

Once everything is setup you can hit the **HOST** button to launch the session !

It will do two things:

* Start a local server 
* Connect you to it as an :ref:`admin`

During online session, various actions are available to you, go to :ref:`how-to-manage` section to 
learn more about them.

.. _how-to-join:

How to join a session
=====================

This section describe how join a launched session. 
Before starting make sure that you have access to the session ip and port.

-----------------------------
1. Fill your user information
-----------------------------

Follow the user-info_ section for this step.

----------------
2. Network setup
----------------

In the nerwork panel select **JOIN**.
The **join sub-panel** (see image below) allow you configure the client to join a
collaborative session.

.. figure:: img/quickstart_join.png
   :align: center
   :alt: Connect menu

   Connection panel

Fill those field with your information:

- **IP**: the host ip.
- **Port**: the host port.
- **Connect as admin**: connect you with **admin rights** (see :ref:`admin` ) to the session.

.. Maybe something more explicit here

.. note::
   Additionnal configuration setting can be found in the :ref:`advanced` section.

Once you've set every field, hit the button **CONNECT** to join the session !
When the :ref:`session-status` is **ONLINE** you are online and ready to start to collaborate.

.. note::
   On the **dedicated server** startup, the session status will get you to the **LOBBY** waiting a admin to start it.

   If the session status is set to **LOBBY** and you are a regular user, you need to wait that an admin launch it.
   If you are the admin, you just need to init the repository to start the session (see image below).

   .. figure:: img/quickstart_session_init.png
      :align: center

      Session initialisation for dedicated server

During online session, various actions are available to you, go to :ref:`how-to-manage` section to 
learn more about them.

.. _how-to-manage:

How to manage a session
=======================

The collaboration quality directly depend on the communication quality. This section describes
various tools made in an effort to ease the communication between the different session users.
Feel free to suggest any idea for communication tools `here <https://gitlab.com/slumber/multi-user/-/issues/75>`_ .

--------------------
Monitor online users
--------------------

One of the most vital tool is the **Online user panel**. It list all connected
users information's including yours such as :

* **Role** : if user is an admin or a regular user.
* **Location**: Where the user is actually working.
* **Frame**: When (in frame) the user working.
* **Ping**: user connection delay in milliseconds

.. figure:: img/quickstart_users.png
   :align: center

   Online user panel

By selecting a user in the list you'll have access to different user related **actions**.
Those operators allow you reach the selected user state in tow different dimensions: **SPACE** and **TIME**.

Snapping in space
----------------

The **CAMERA button** (Also called **snap view** operator) allow you to snap on 
the user viewpoint. To disable the snap, click back on the button. This action 
served different purposes such as easing the review process, working together on
wide world.

.. hint::
   If the target user is localized on another scene, the **snap view** operator will send you to his scene. 

.. figure:: img/quickstart_snap_view.gif
   :align: center

   Snap view in action

Snapping in time
---------------

The **CLOCK button** (Also called **snap time** operator) allow you to snap on 
the user time (current frame). To disable the snap, click back on the button. 
This action is built to help various actors to work on the same temporality 
(for instance multiple animators).

.. figure:: img/quickstart_snap_time.gif
   :align: center

   Snap time in action


Kick a user
-----------

.. warning:: Only available for :ref:`admin` !


The **CROSS button** (Also called **kick** operator) allow the admin to kick the selected user. On the target user side, the session will properly disconnect.


Change users display 
--------------------

Presence is the multi-user module responsible for users display. During the session,
it draw users related information in your viewport such as:

* Username
* User point of view
* User selection

.. figure:: img/quickstart_presence.png
   :align: center

   Presence show flags

The presence overlay panel (see image above) allow you to enable/disable 
various drawn parts via the following flags:

- **Show selected objects**: display other users current selection
- **Show users**: display users current viewpoint 
- **Show different scenes**: display users working on other scenes

-----------
Manage data
-----------

In order to understand replication data managment, a quick introduction to the multi-user data workflow is required.
First thing to know: until now, the addon rely on a data-based replication. In simple words, it means that it replicate
user's action results. 
To replicate datablocks between clients the multi-user rely on what tends to be a distributed architecture:

- The server store the "master" version of the work.
- Each client have a local version of the work.

When an artist modified something in the scene, here is what is happening in the background:

1. Modified data are **COMMITTED** to the local repository.
2. Once committed locally, they are **PUSHED** to the server
3. As soon as the server is getting updates, they are stored locally and pushed to every other clients

At the top of this data management system, a right management system prevent 
multiple users from modifying same data at same time. A datablock may belong to
a connected user or be under :ref:`common-right<**COMMON**>` rights. 

.. note::
   In a near future, the right management system will support roles to allow multiple users to 
   work on different aspect of the same datablock.

The Repository panel (see image below) allow you to monitor, change datablock states and right manually.

.. figure:: img/quickstart_properties.png
   :align: center

   Repository panel

The **show only owned** flag allow you to see which datablocks you are currently modifying.

.. warning::
   If you are editing a datablock not listed with this fag enabled, it means that you do
   not have right granted to modify it. So it won't be updated to other client ! 

Here is a quick list of available actions: 

+---------------------------------------+-------------------+------------------------------------------------------------------------------------+
| icon                                  | Action            | Description                                                                        |
+=======================================+===================+====================================================================================+
| .. image:: img/quickstart_push.png    |  **Push**         | push data-block to other clients                                                   |
+---------------------------------------+-------------------+------------------------------------------------------------------------------------+
| .. image:: img/quickstart_pull.png    | **Pull**          | pull last version into blender                                                     |
+---------------------------------------+-------------------+------------------------------------------------------------------------------------+
| .. image:: img/quickstart_refresh.png | **Reset**         | Reset local change to the server version                                           |
+---------------------------------------+-------------------+------------------------------------------------------------------------------------+
| .. image:: img/quickstart_unlock.png  | **Lock/Unlock**   | If locked, does nothing. If unlocked, grant modification rights to another user.   |
+---------------------------------------+-------------------+------------------------------------------------------------------------------------+
| .. image:: img/quickstart_remove.png  |  **Delete**       | Remove the data-block from network replication                                     |
+---------------------------------------+-------------------+------------------------------------------------------------------------------------+

.. _advanced:

Advanced configuration
======================

This section contains optional settings to configure the session behavior.

.. figure:: img/quickstart_advanced.png
   :align: center

   Advanced configuration panel

.. rubric:: Network panel

**IPC Port** is the port used for Inter Process Communication. This port is used 
by the multi-users subprocesses to communicate with each others. If different instances
of the multi-user are using the same IPC port it will create conflict !

.. note::
   You only need to modify it if you need to launch multiple clients from the same
   computer(or if you try to host and join on the same computer). You should just enter a different
   **IPC port** for each blender instance.

**Timeout (in milliseconds)** is the maximum ping authorized before auto-disconnecting.
You should only increase it if you have a bad connection.

.. rubric:: Replication panel

**Synchronize render settings** (only host) enable replication of EEVEE and CYCLES render settings to match render between clients.

**Update method** allow you to change how replication update are triggered. Until now two update methode are implemented:

- **Default**: Use external threads to monitor datablocks changes, slower and less accurate.
- **Despgraph ⚠️**: Use the blender dependency graph to trigger updates. Faster but experimental and unstable !

**Properties frequency gird** allow to set a custom replication frequency for each type of data-block:

- **Refresh**: pushed data update rate (in second)
- **Apply**: pulled data update rate (in second)

.. note:: Per-data type settings will soon be revamped for simplification purposes

