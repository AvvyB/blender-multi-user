###############
User Interface
###############

Side Pannel
===========

.. toctree::
    :maxdepth: 1
 
    Introduction <server/introduction.rst>
    server/splash.rst

Presence
=========

Change users display 
--------------------

Presence is the multi-user module responsible for displaying user presence. During the session,
it draw users' related information in your viewport such as:

* Username
* User point of view
* User active mode
* User selection

.. figure:: img/quickstart_presence.png
   :align: center

   Presence show flags

The presence overlay panel (see image above) allows you to enable/disable 
various drawn parts via the following flags:

- **Show session status**: display the session status in the viewport 
   
   .. figure:: img/quickstart_status.png
      :align: center

   - **Text scale**: session status text size
   - **Vertical/Horizontal position**: session position in the viewport
   
- **Show selected objects**: display other users' current selections
- **Show users**: display users' current viewpoint 
- **Show different scenes**: display users working on other scenes