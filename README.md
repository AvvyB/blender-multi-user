# MULTI-USER for blender

> Enable real-time collaborative workflow inside blender  

<img src="https://i.imgur.com/X0B7O1Q.gif" width=600>


:warning: Under development, use it at your own risks. Currently tested on Windows platform. :warning:

This tool aims to allow multiple users to work on the same scene over the network. Based on a Clients / Server architecture, the data-oriented replication schema replicate blender data-blocks across the wire.

## Quick installation

1. Download latest release [multi_user.zip](https://gitlab.com/slumber/multi-user/-/jobs/artifacts/master/download?job=build).
2. Run blender as administrator (dependencies installation).
3. Install last_version.zip from your addon preferences.

[Dependencies](#dependencies) will be automatically added to your blender python during installation.

## Usage

See the [documentation](https://multi-user.readthedocs.io/en/latest/) for details.

## Current development status

Currently, not all data-block are supported for replication over the wire. The following list summarizes the status for each ones.

| Name        | Status |                            Comment                            |
| ----------- | :----: | :-----------------------------------------------------------: |
| action      |   ❗    |                          Not stable                           |
| armature    |   ❗    |                          Not stable                           |
| camera      |   ✔️   |                                                               |
| collection  |   ✔️   |                                                               |
| curve       |   ✔️   |              Nurbs surface don't load correctly               |
| gpencil     |   ✔️   |                                                               |
| image       |   ❗    |                        Not stable yet                         |
| mesh        |   ✔️   |                                                               |
| material    |   ✔️   |                                                               |
| metaball    |   ✔️   |                                                               |
| object      |   ✔️   |                                                               |
| scene       |   ✔️   |                                                               |
| world       |   ✔️   |                                                               |
| lightprobes |   ✔️   |                                                               |
| particles   |   ❌    | [On-going](https://gitlab.com/slumber/multi-user/-/issues/24) |
| speakers    |   ❌    | [Planned](https://gitlab.com/slumber/multi-user/-/issues/65)  |
| vse         |   ❌    | [Planned](https://gitlab.com/slumber/multi-user/-/issues/45)  |
| physics     |   ❌    | [Planned](https://gitlab.com/slumber/multi-user/-/issues/45)  |
| libraries   |   ❗    |                            Partial                            |


### Performance issues

Since this addon is written in pure python for a research purpose, performances could be better from all perspective.
I'm working on it.

## Dependencies

| Dependencies | Version | Needed |
| ------------ | :-----: | -----: |
| Replication       | latest  |    yes |



## Contributing

See [contributing section](https://multi-user.readthedocs.io/en/latest/ways_to_contribute.html) of the documentation.

## Licensing

See [license](LICENSE)

