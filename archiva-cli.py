import archiva
import argparse
import os
import json
import sys
import pprint


def instruction_is_valid(ins):
    """Returns if instruction ins is valid (simple check)"""
    return\
        ins != "i" or\
        not ins.startswith("versionsList:") or\
        not ins.startswith("downloadInfos:")


def instruction_execute(session, ins):
    """Executes instruction ins in session session"""

    def get_group_and_name(group_p_name):
        """Returns (package_group, package_name) from full string"""
        group_p_name_split = group_p_name.split(".")
        return\
            ".".join(group_p_name_split[:-1]),\
            group_p_name_split[-1]

    # for object responses
    pp = pprint.PrettyPrinter(indent=2)

    if ins.startswith("versionsList:"):
        # execute session.get_versions_list
        group_p_name = ins.split(":")[1]
        pp.pprint(session.get_versions_list(
            *get_group_and_name(group_p_name)))

    elif ins.startswith("downloadInfos:"):
        # execute session.get_download_infos
        _, group_p_name, version = ins.split(":")
        pp.pprint(session.get_download_infos(
            *get_group_and_name(group_p_name),
            version))

    elif ins.startswith("download:"):
        # execute package download
        _, group_p_name, version = ins.split(":")
        filename = session.download(
            *get_group_and_name(group_p_name),
            version)

        if filename:
            print(f"Output file: {filename}")
        else:
            print("No data.")

    else:
        # instruction not supported
        print(f"Invalid instruction: {ins}",
              file=sys.stderr)


def get_args():
    """See: python archive-cli.py -h"""

    parser = argparse.ArgumentParser()
    parser.add_argument("-V", "--verbose-level",
                        help="set verbose level: e(rror)|[w(arning)]|i(nfo)|s(uppress)",
                        choices=["e", "w", "i", "s"],
                        default="w")
    parser.add_argument("-H", "--host",
                        help="archiva host (should include protocol)",
                        required=True)
    parser.add_argument("-R", "--set-referer",
                        help="set Referer header (<host>)",
                        action="store_true")
    parser.add_argument("-u", "--user",
                        help="archiva user (default=guest), also taken from $ARCHIVA_USR",
                        default="guest")
    parser.add_argument("-p", "--password",
                        help="archiva password (default=), also taken from $ARCHIVA_PWD",
                        default="")
    parser.add_argument("-x", "--execute",
                        help="execute instruction (default=i(nteractive))",
                        default="i")

    args = parser.parse_args()

    # validate -x instruction
    if not instruction_is_valid(args.execute):
        print(f"Invalid instruction: {args.execute}",
              file=sys.stderr, end=", ")
        print(f"Must be one of:", file=sys.stderr)
        print(f"\t* i", file=sys.stderr)
        print(f"\t* versionsList:{{group}}.{{name}}",
              file=sys.stderr)
        print(f"\t* downloadInfos:{{group}}.{{name}}:{{version}}",
              file=sys.stderr)

    # options -u/-p have precedence over environment variables counterparts,
    # although env vars are encouraged
    if args.user == "guest":
        args.user = os.getenv("ARCHIVA_USR", "guest")
    if args.password == "":
        args.password = os.getenv("ARCHIVA_PWD", "")

    return args


def main():
    args = get_args()
    logger = archiva.Logger(args.verbose_level)

    try:
        # define session
        s = archiva.Session(args.host,
                            args.user, args.password,
                            set_referer=args.set_referer, logger=logger)

        # login
        with s:
            # interactive mode
            if args.execute == "i":
                while True:
                    ins = input("ins> ")
                    if ins == "q":
                        return
                    instruction_execute(s, ins)
            # single instruction
            else:
                instruction_execute(s, args.execute)
    except json.decoder.JSONDecodeError as e:
        logger.e(f"could not decode: {e.doc}")
    except archiva.ErrorResponse as e:
        logger.e(e)


if __name__ == "__main__":
    main()
