# Archiva Python

`archiva-python` is a minimal python3 interface for a subset of Apache Archiva's REST API.

## Roadmap

The following feature subset is planned to be supported:

- [x] Session support
  - [x] Login
  - [x] Logout
  - [x] `with` "RAII" support
- [x] versionsList
- [x] artifactDownloadInfos
- [ ] Download a package

## How to Install

Because this project is in its early stages,  you must clone this repo.

**Remember** to install `requirements.txt` packages:

```sh
(venv) $ pip install -r requirements.txt
```

## Usage

It can be used as a python library:

```python
import archiva

with archiva.Session("http://localhost:8080", "user", "pass", set_referer=True) as s:
  versions = s.get_versions_list("com.myorganization.division", "MyPackage")
  print(f"com.myorganization.division.MyPackage versions: {versions}")
```

And as a CLI tool:

```sh
(venv) $ python archiva-cli.py -h
usage: archiva-cli.py [-h] [-V {e,w,i,s}] -H HOST [-R] [-u USER] [-p PASSWORD]
                      [-x EXECUTE]

optional arguments:
  -h, --help            show this help message and exit
  -V {e,w,i,s}, --verbose-level {e,w,i,s}
                        set verbose level:
                        e(rror)|[w(arning)]|i(nfo)|s(uppress)
  -H HOST, --host HOST  archiva host (should include protocol)
  -R, --set-referer     set Referer header (<host>)
  -u USER, --user USER  archiva user (default=guest), also taken from
                        $ARCHIVA_USR
  -p PASSWORD, --password PASSWORD
                        archiva password (default=), also taken from
                        $ARCHIVA_PWD
  -x EXECUTE, --execute EXECUTE
                        execute instruction (default=i(nteractive))
```

Currently, `-x` supports:

- `versionsList:{packageGroup}.{packageName}`
- `downloadInfos:{packageGroup}.{packageName}:{packageVersion}`

Interactive mode (`[-x i]`) enters a loop asking for instructions over stdin. Supported instructions are the same as above, adding special command `q` to quit interactive mode.

**Example**

```sh
(venv) $ python archiva-cli.py -H http://localhost:8080 -R -x versionsList:com.organization.mydivision.MyPackage
{'versions': ['0.1.0']}
```



## Resources

Archiva API REST docs: [https://archiva.apache.org/docs/2.1.1/adminguide/webservices/rest.html](https://archiva.apache.org/docs/2.1.1/adminguide/webservices/rest.html).