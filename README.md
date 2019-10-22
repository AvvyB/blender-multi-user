# MULTI-USER for blender

> Enable real-time collaborative workflow inside blender  

![demo](https://i.imgur.com/X0B7O1Q.gif)


:warning: Under development, use it at your own risks. Currently tested on Windows platform. :warning:

This tool aims to allow multiple users to work on the same scene over the network. Based on a Clients / Server architecture, the data-oriented replication schema replicate blender data-blocks across the wire.

## Installation

1. Download latest release [multi_user.zip](/uploads/8aef79c7cf5b1d9606dc58307fd9ad8b/multi_user.zip).
2. Run blender as administrator (dependencies installation).
3. Install last_version.zip from your addon preferences.

[Dependencies](#dependencies) will be automatically added to your blender python during installation.

## Usage

See [how to](https://gitlab.com/slumber/multi-user/wikis/User/Quickstart) section.

## Current development status

Currently, not all data-block are supported for replication over the wire. The following list summarizes the status for each ones.

| Name       |       Status       |    Comment     |
| ---------- | :----------------: | :------------: |
| action     |        :x:         |      WIP       |
| armature   |        :x:         |      WIP       |
| camera     | :white_check_mark: |                |
| collection | :white_check_mark: |                |
| curve      | :white_check_mark: |   Not tested   |
| gpencil    | :white_check_mark: |                |
| image      |   :exclamation:    | Not stable yet |
| mesh       | :white_check_mark: |                |
| material   | :white_check_mark: |                |
| metaball   |        :x:         |                |
| object     | :white_check_mark: |                |
| scene      | :white_check_mark: |                |
| world      | :white_check_mark: |                |

### Performance issues

Since this addon is written in pure python for a prototyping purpose, performances could be better from all perspective. 
I'm working on it.

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

## Licensing

See [license](LICENSE)