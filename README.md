# MULTI-USER for blender

> Enable real-time collaborative workflow inside blender  

:warning: Under development, use it at your own risks. Currently tested on Windows platform. :warning:


This tool aims to allow multiple users to work on the same scene over the network. Based on a Clients / Server architecture, the data-oriented replication schema replicate blender datablocks across the wire.

## Installation

1. Download lastest release [here](/uploads/324f7d5dc4b18bb922168264809340d8/multi-user.zip).
2. Install last_version.zip from your addon preferences

## Usage

See [how to](https://gitlab.com/slumber/multi-user/wikis/User/Quickstart) section.

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
| JsonDiff     | latest  |    yes |


## Contributing

1. Fork it (<https://gitlab.com/yourname/yourproject/fork>)
2. Create your feature branch (`git checkout -b feature/fooBar`)
3. Commit your changes (`git commit -am 'Add some fooBar'`)
4. Push to the branch (`git push origin feature/fooBar`)
5. Create a new Pull Request

## Licencing

See [licence](LICENSE)


