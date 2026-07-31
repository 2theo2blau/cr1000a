# CR1000A

Tools for working with the ASUS CR1000A router: unpacking firmware binaries and
decrypting/encrypting the router's configuration backup files so they can be
modified and reloaded onto the device through the "restore from backup" action
in the router's web UI.

## Repository contents

### `firmware/unpack.sh`

Bash script that carves apart a CR1000A firmware image. Given a source
firmware file it:

- Locates and extracts the SquashFS root filesystem (`root_fs.sqfs`).
- Finds the Flattened Device Tree (FDT) magic, carves out the `.dtb`, and
  converts it to a human readable `.dts` with `dtc`.
- Walks the FDT root, `images`, `configurations`, `security`, `trust`, and
  `brcm_rootfs_encrypt` nodes, dumping descriptions, identity strings,
  compatibility strings, security policy / anti-rollback data, and trust
  salts/encoded keys.
- Recursively extracts sub-images with `dumpimage` and converts any embedded
  DTBs to `.dts`.
- If a kernel image is present, decompresses the LZMA layer and extracts the
  embedded `IKCONFIG` gzip blob into `kconfig.conf`.

Dependencies: `ugrep`, `device-tree-compiler`, `coreutils`, `u-boot-tools`,
`gzip`, `xz-utils`. See the install line at the top of the script.

Usage:

```bash
bash firmware/unpack.sh <source_firmware_image>
```

### `config/cr1000a_config.py`

Python script that decrypts and encrypts the router's configuration backup
files (the `.cfg` files produced and consumed by the router's
"Backup / Restore" UI). The router stores these as an AES-256-CBC encrypted
tarball with a trailing IV. The script:

- Decrypts a backup `.cfg` into a directory of plaintext config files.
- Re-encrypts a directory of (potentially modified) config files back into a
  `.cfg` the router will accept.

The AES key and IV are recovered from values hardcoded in the firmware: a
"de-obfuscation" key is used to decrypt a small embedded blob
(`dot_encrypt_data`) which yields the real AES-256 key, and a hardcoded IV is
used both for that unwrap and for the config payload itself.

The script shells out to `openssl` for the AES operations and uses Python's
`tarfile` for packaging. Usage:

```bash
# decrypt a backup into a directory
python config/cr1000a_config.py -c decrypt -i <backup.cfg> [-o <output_dir>]

# re-encrypt a directory back into a backup the router will accept
python config/cr1000a_config.py -c encrypt -i <config_dir> [-o <output.cfg>]
```

### `config/original_configs/`

Decrypted configuration backups extracted from several stock firmware
versions, kept for reference. Each backup directory contains the plaintext
config files plus a `backup_md5` file.

## How modified configs get back onto the router

The router's backup format nominally includes an `backup_md5` file that is
supposed to be an MD5 digest of the backup contents, used to verify integrity
on restore. In practice the firmware contains a bug: it neither generates a
real MD5 nor verifies the digest on restore. `cr1000a_config.py` takes
advantage of this by writing a fixed, well-known (and incorrect) string into
`backup_md5` when re-encrypting. Because the router does not actually check
the hash, a modified config archive encrypted with the hardcoded key/IV is
accepted by the "restore from backup" flow and loaded onto the device.

## Disclaimer

Sensitive information from the router configurations, logs, and database dumps
in this repository has been redacted for security reasons so that the material
can be shared safely. Anything that could expose credentials, private keys,
personal data, or device-specific identifying material has been removed or
replaced before publication.
