# MULTI-USER for blender

> Enable real-time collaborative workflow inside blender  

<img src="https://i.imgur.com/X0B7O1Q.gif" width=600>


:warning: Under development, use it at your own risks. Currently tested on Windows platform. :warning:

This tool aims to allow multiple users to work on the same scene over the network. Based on a Clients / Server architecture, the data-oriented replication schema replicate blender data-blocks across the wire.

## Quick installation

1. Download [latest build](https://gitlab.com/slumber/multi-user/-/jobs/artifacts/develop/download?job=build) or [stable build](https://gitlab.com/slumber/multi-user/-/jobs/artifacts/master/download?job=build).
2. Install last_version.zip from your addon preferences.

[Dependencies](#dependencies) will be automatically added to your blender python during installation.

## Usage

See the [documentation](https://slumber.gitlab.io/multi-user/index.html) for details.

## Troubleshooting

See the [troubleshooting guide](https://slumber.gitlab.io/multi-user/getting_started/troubleshooting.html) for tips on the most common issues.

## Current development status

Currently, not all data-block are supported for replication over the wire. The following list summarizes the status for each ones.

| Name           | Status |                                 Comment                                 |
| -------------- | :----: | :---------------------------------------------------------------------: |
| action         |   ✔️    |                                                                         |
| camera         |   ✔️    |                                                                         |
| collection     |   ✔️    |                                                                         |
| gpencil        |   ✔️    |                                                                         |
| gpencil3        |   ✔️    |                                                                         |
| image          |   ✔️    |                                                                         |
| mesh           |   ✔️    |                                                                         |
| material       |   ✔️    |                                                                         |
| node_groups    |   ✔️    |                        Material & Geometry only                         |
| geometry nodes |   ✔️    |                                                                         |
| metaball       |   ✔️    |                                                                         |
| object         |   ✔️    |                                                                         |
| texts          |   ✔️    |                                                                         |
| scene          |   ✔️    |                                                                         |
| world          |   ✔️    |                                                                         |
| volumes        |   ✔️    |                                                                         |
| lightprobes    |   ✔️    |                                                                         |
| physics        |   ✔️    |                                                                         |
| textures       |   ✔️    |                                                                         |
| curve          |   ❗    |                      Nurbs surfaces not supported                       |
| armature       |   ❗    |          Only for Mesh. [Planned for GPencil](https://gitlab.com/slumber/multi-user/-/issues/161). Not stable yet           |
| particles      |   ❗    |                        The cache isn't syncing.                         |
| speakers       |   ❗    |      [Partial](https://gitlab.com/slumber/multi-user/-/issues/65)       |
| vse            |   ❗    |                     Mask and Clip not supported yet                     |
| libraries      |   ❌    |                                                                         |
| nla            |   ❌    |                                                                         |
| compositing    |   ❌    | [Planned for v0.5.0](https://gitlab.com/slumber/multi-user/-/issues/46) |



### Performance issues

Since this addon is written in pure python for a research purpose, performances could be better from all perspective.
I'm working on it.

## Dependencies

| Dependencies | Version | Needed |
| ------------ | :-----: | -----: |
| Replication  | latest  |    yes |



## Contributing

See [contributing section](https://slumber.gitlab.io/multi-user/ways_to_contribute.html) of the documentation.

Feel free to [join the discord server](https://discord.gg/aBPvGws) to chat, seek help and contribute.

## Licensing

See [license](LICENSE)

