#! /usr/bin/env python

# This is a script to walk a directory structure and verify file integrity of
# each file it encounters.  On first run, it will open a directory, hash each
# file, and store the hashes in an md5sum compatible file in that directory.
# Subsequent runs will process new files in a similar way, but will also check
# existing files with the current hashes.  Any inconsistencies are reported.
#
# A similar project is http://snipplr.com/view/4023/ which I stumbled across and
# stole some ideas from, but I decided to finish this script instead of updating
# that one with the things I wanted.  That one has features this one doesn't,
# and this one has a little more error checking, script/cron/nagios
# friendly output, and 100% compatibility with `md5sum` output.

import hashlib
import logging as log
import optparse
import os
import re
import sys

md5line = re.compile(r"^(\\?)([0-9a-f]{32}) [\ \*](.*)$")


def process_directory(path, outfile):

    consistency = True  # Nothing bad found yet
    oldcwd = os.getcwd()

    for root, dirs, files in os.walk(path, onerror=log.error):

        os.chdir(root)
        log.info("Operating on %s" % root)

        updated = False  # We haven't detected any changes
        c_file = "%s/%s" % (root, outfile)

        new = {}
        existing = {}

        if os.path.isfile(c_file):
            log.debug("Found existing checksums for %s" % root)
            for hash, file in read_checksums(c_file):
                if os.path.isfile(file):
                    existing[file] = hash
                else:
                    updated = True
                    consistency = False
                    fullname = "%s/%s" % (root, file)
                    log.warning("Missing a file: %s (hash: %s)" % (fullname,
                                                                   hash))

        for file in sorted(files):
            if file == outfile:
                continue

            hash = calculate_hash(file)

            if file in existing:
                if not existing[file] == hash:
                    updated = True
                    consistency = False
                    fullname = "%s/%s" % (root, file)
                    msg = ("Inconsistent hashes detected for %s! Old: %s "
                           "New: %s" % (fullname, existing[file], hash))
                    log.warning(msg)
                    existing[file] = hash  # Will write the new hash to disk
            else:
                updated = True
                new[file] = hash

        new.update(existing)

        if updated:
            write_checksums(c_file, new)

    os.chdir(oldcwd)

    return consistency


def calculate_hash(file):

    md5 = hashlib.md5()
    try:
        with open(file, 'rb') as f:
            while True:
                chunk = f.read(32768)  # picked a number
                md5.update(chunk)
                if not chunk:
                    return md5.hexdigest()
    except IOError, e:
        log.error("Error opening %s: %s" % (file, e))


def read_checksums(file):

    try:
        with open(file, 'r') as f:
            for line in f:
                match = md5line.match(line)

                if not match:
                    msg = "Invalid syntax in checksum file.  Line: %s" % line
                    log.error(msg)
                    continue

                # If a line starts with \, the filename has escaped
                # characters. Python won't expect that so we strip them.
                if match.group(1):
                    name = (match.group(3).replace("\\\\", "\\")
                                          .replace("\\\n", "\n"))
                else:
                    name = match.group(3)


                yield match.group(2), name

    except IOError, e:
        log.error("Error reading checksums file %s: %s" % (file, e))


def write_checksums(file, results):

    if not results:
        return

    try:
        with open(file, 'w') as f:
            for name, hash in results.iteritems():
                line = ""

                # The md5sum utility will prefix a line with \ if it contains
                # certain characters.  We'll do the same here for compatibilty's
                # sake.  Read `info md5sum` for more info.
                if "\\" in name or "\n" in name:
                    name = (name.replace("\\", "\\\\")
                                .replace("\n", "\\\n"))
                    line = "\\"

                # Linux (and it's md5sum) don't care if a file is binary or not,
                # so I'm not going to care either.  If you care you'll need to:
                # 1) Determine if the file is binary (most tools scan the file
                #    for a null char)
                # 2) If the file is binary, change the second space in this
                #    string to an `*'
                line = "%s%s  %s\n" % (line, hash, name)

                f.write(line)

    except IOError, e:
        log.error("Error writing checksums file %s: %s" % (file, e))


if __name__ == "__main__":

    usage = "usage: %prog [options] path"
    parser = optparse.OptionParser(usage)

    parser.add_option("-o", "--outfile", default="checksums.txt",
                      help=("What should the name of the output file be?"
                            " [default: %default]"))
    parser.add_option("-v", "--verbose", action="count", dest="verbose",
                      help="Print more output (up to -v -v)")

    (options, args) = parser.parse_args()

    LOG_LEVEL = log.WARNING
    if options.verbose == 1:
        LOG_LEVEL = log.INFO
    elif options.verbose >=2:
        LOG_LEVEL = log.DEBUG

    log.basicConfig(level=LOG_LEVEL, format="%(levelname)s - %(message)s")

    if not len(args) == 1:
        log.critical("You need to specify the directory to process.")
        parser.print_usage()
        sys.exit(2)

    if not os.path.isdir(args[0]):
        log.critical("%s is not a directory" % args[0])
        sys.exit(2)

    # Returns false when inconsistencies are found
    if not process_directory(args[0], outfile=options.outfile):
        sys.exit(1)
