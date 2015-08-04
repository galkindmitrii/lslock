#!/usr/bin/python
"""
lslock - list locked files and PIDs that locked them.
Run with one positional argument with the path to look for lock files.
Path should be a folder and might have subfolders.
"""
from sys import exit
from os import path, stat, walk as os_walk
from argparse import ArgumentParser, ArgumentError


class ListLocks(object):
    """
    Class implementing the lslock functionality.
    """

    def __init__(self):
        """
        Class constructor.
        """
        self.inode_file_dict = {}  # dict for {inode: filename} pairs.

    def parse_arguments(self):
        """
        Parses user input, returns the directory to look for lock files.
        """
        parser = ArgumentParser(description='lslock - list locked files and '
                                            'PIDs for a given directory')
        parser.add_argument('directory', help='directory to list the locks '
                                              '(current by default)')
        try:
            args = parser.parse_args()
        except ArgumentError as exc:
            print "Argument Error: ", exc
            exit(2)

        return args.directory

    def find_all_lock_files(self, path_to_look):
        """
        Checks if given path exists and returns a list of all .lock files
        found there.
        """
        if not path.exists(path_to_look):
            print ("The given path %s cannot be found or unaccessible"
                   % path_to_look)
            exit(1)

        # list all files in the path_to_look and get the *.lock ones:
        lock_files = []
        for dir_path, _, files in os_walk(path_to_look):
            for a_file in [f for f in files if f.endswith(".lock")]:
                lock_files.append(path.join(dir_path, a_file))

        if not lock_files:
            print "No .lock files were found in the '%s'" % path_to_look
            exit(0)

        return lock_files

    def get_inode_for_lock(self, lock_file):
        """
        Checks if the given 'lock_file' exists and returns the its inode.
        """
        # check that file was not deleted meanwhile by the test script:
        if not path.exists(lock_file):
            print "The lock file '%s' cannot be found" % lock_file
            exit(1)

        try:
            inode = str(stat(lock_file).st_ino)  # gives inode as a string
        except OSError as exc:
            print ("An Error occured while getting the %s inode: %s"
                   % (lock_file, exc))
            exit(1)

        return inode

    def search_line_for_lock(self, line):
        """
        Searches the line for inodes of interest to find the respective PID.
        """
        unknown_inodes = self.inode_file_dict.keys()
        if not unknown_inodes:
            # exit when PIDs for all inodes/files were indentified
            exit(0)

        for inode in unknown_inodes:
            # look for inode surrounded by : and ' ' in the line:
            if "".join((':', inode, ' ')) in line:
                line = line.split()  # to get pid, that is 5th
                print self.inode_file_dict[inode], line[4]  # filepath, PID
                del self.inode_file_dict[inode]  # as it won't be used again

    def get_pids_for_inodes(self):
        """
        Parses the '/proc/locks' to find PIDs for inodes of interest.
        Processing is done by lines.
        """
        if not path.exists('/proc/locks'):  # if run on non-Linux
            print "The /proc/locks file cannot be found"
            exit(1)

        try:
            with open('/proc/locks', 'r') as all_locks_file:
                for line in all_locks_file:
                    self.search_line_for_lock(line)
        except (OSError, IOError) as exc:
            print "An Error occured while working with /proc/locks: %s" % exc
            exit(1)

    def list_locks(self):
        """
        Main function, an entry point for the lslock:
        First parse the given input with the directory path;
        Then find all the .lock files located in it and subdirs;
        Get inodes for all the locks;
        Finally get respective PIDs for those inodes.
        """
        # parse given argument - directory to work with:
        directory = self.parse_arguments()

        # find all .lock files in the directory:
        for lock_file in self.find_all_lock_files(directory):
            lock_file = path.join(directory, lock_file)  # path including dir
            inode = self.get_inode_for_lock(lock_file)
            # fill the dict {inode: path_to_file}
            self.inode_file_dict[inode] = lock_file

        # find PIDs for inodes and print results:
        print "Filename: PID:"
        self.get_pids_for_inodes()


if __name__ == '__main__':
    Lslock = ListLocks()
    Lslock.list_locks()
