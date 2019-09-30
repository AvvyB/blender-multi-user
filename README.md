# Multi-user blender addon

> Enable real-time collaborative workflow inside blender  

:warning: Under development, use it at your own risks. Currently tested on Windows platform. :warning:


This tool aims to allow multiple users to work on the same scene over the network. Based on a Clients / Server architecture, the data-oriented replication schema replicate blender datablocks across the wire.

## Installation

1. Download lastest release here.
2. Install last_version.zip from your addon preferences

## Usage

Settings are under: `View3D -> Sidebar -> Multiuser`

### Before starting

#### 1. User

![settings](medias/user.png)

- **name**: username.
- **color**: color used to represent the user into other user workspaces.

#### 2. Network

:warning: If you host a session over internet, special network configuration is needed :warning:
 
| Host                                         | Join                           |
| :------------------------------------------- | :----------------------------- |
| asd                                          |
| ![host_panel](medias/host.png)               | ![join_panel](medias/join.png) |
| Start empty: Cleanup the file before hosting | IP: host ip                    |
|                                              | Port: host port                |

#### 2.1 Advanced

![properties](medias/properties.png)

**Right strategy** (only host) enable you to choose between a strict and a relaxed pattern:

- **Strict**: Host is the king, by default the host own each properties, only him can grant modification rights.
- **Common**: Each properties are under common rights by default, on selection, a property is only modifiable by the owner.
  
_On each strategy, when a user is the owner he can choose to pass his rights to somemone else._

**Propertie frequency gird** allow to set a custom replication frequency for each type of datablock

### In-session

#### Connected users

![users](medias/users.png)

This pannel displays all connected users, including you. The **camera button** allow you to focus on a user.

#### Properties outliner

![properties](medias/properties_in_session.png)

## Current development statut

Actually, not all datablock are supported for replication over the wire. The following list summarizes the status for each ones.

| Name       |       Statut       |  Comment   |
| ---------- | :----------------: | :--------: |
| action     |        :x:         |    WIP     |
| armature   |        :x:         |    WIP     |
| camera     | :white_check_mark: |            |
| collection | :white_check_mark: |            |
| curve      | :white_check_mark: | Not tested |
| gpencil    | :white_check_mark: |            |
| image      | :white_check_mark: | Local only |
| mesh       | :white_check_mark: |            |
| material   | :white_check_mark: |            |
| metaball   |        :x:         |            |
| object     | :white_check_mark: |            |
| scene      | :white_check_mark: |            |
| world      | :white_check_mark: |            |

### Performance issues

Since this addon is writen in pure python for a prototyping purpose, perfomance could be better from all perspective. Soon I will start to port the multi-user addon concept to a blender branch.

## Dependencies

| Dependencies | Version | Needed |
| ------------ | :-----: | -----: |
| ZeroMQ       | latest  |    yes |
| msgpack      | latest  |    yes |
| PyYAML       | latest  |    yes |


## Contributing

1. Fork it (<https://gitlab.com/yourname/yourproject/fork>)
2. Create your feature branch (`git checkout -b feature/fooBar`)
3. Commit your changes (`git commit -am 'Add some fooBar'`)
4. Push to the branch (`git push origin feature/fooBar`)
5. Create a new Pull Request

