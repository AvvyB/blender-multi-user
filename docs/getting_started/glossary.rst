========
Glossary
========


.. glossary::

   .. _admin:
   
   administrator

      *A session administrator can manage users (kick) and have a write access on
      each datablock. He could also init a dedicated server repository.*

   .. _session-status:

   session status

      *Located in the title of the multi-user panel, the session status show 
      you the connection state.*

      .. figure:: img/quickstart_session_status.png
         :align: center

         Session status in panel title bar

      All possible state are listed here with their meaning:*

      +--------------------+---------------------------------------------------------------------------------------------+
      | State              | Description                                                                                 |
      +--------------------+---------------------------------------------------------------------------------------------+
      | WARMING UP DATA    | Commiting local data                                                                        |
      +--------------------+---------------------------------------------------------------------------------------------+
      | FETCHING           | Dowloading snapshot from the server                                                         |
      +--------------------+---------------------------------------------------------------------------------------------+
      | AUTHENTIFICATION   | Initial server authentication                                                               |
      +--------------------+---------------------------------------------------------------------------------------------+
      | ONLINE             | Connected to the session                                                                    |
      +--------------------+---------------------------------------------------------------------------------------------+
      | PUSHING            | Init the server repository by pushing ours                                                  |
      +--------------------+---------------------------------------------------------------------------------------------+
      | INIT               | Initial state                                                                               |
      +--------------------+---------------------------------------------------------------------------------------------+
      | QUITTING           | Exiting the session                                                                         |
      +--------------------+---------------------------------------------------------------------------------------------+
      | LAUNCHING SERVICES | Launching local services. Services are spetialized daemons running in the background. )     |
      +--------------------+---------------------------------------------------------------------------------------------+
      | LOBBY              | The lobby is a waiting state triggered when the server repository hasn't been initiated yet |
      |                    |                                                                                             |
      |                    | Once initialized, the server will automatically launch all client in the **LOBBY**.         |
      +--------------------+---------------------------------------------------------------------------------------------+


