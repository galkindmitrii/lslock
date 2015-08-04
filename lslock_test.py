#!/usr/bin/python
"""
A test application for the lslock.
Creates a defined amount of processes that create locks.
"""
from sys import exit
from time import sleep
from os import path, makedirs, remove
from random import choice
from string import lowercase as str_lowercase
from multiprocessing import Process
from fcntl import flock, LOCK_EX, LOCK_UN

NUM_TEST_PROCS_TO_LAUNCH = 5


class LocksGenerator(object):
    """
    Class implementing lslock-test.
    """

    def __init__(self):
        """
        Class constructor.
        """
        self.files_to_remove = []
        self.procs_to_terminate = []

    def create_lock_file(self, file_name):
        """
        Creats a 'file_name' and lock it.
        """
        try:
            test_file = open(file_name, 'w')
            flock(test_file, LOCK_EX)  # exclusive/write
            while True:
                sleep(1)  # simply sleep
        except (OSError, IOError):
            exit(1)
        finally:
            flock(test_file, LOCK_UN)  # unlock
            if not test_file.closed:
                test_file.close()

    def perform_cleanup(self):
        """
        Terminates spawned processes;
        Removes files created by those processes.
        """
        for process in self.procs_to_terminate:
            if process.is_alive():
                process.terminate()

        for created_file in self.files_to_remove:
            if path.exists(created_file):
                remove(created_file)

    def spawn_processes_to_lock(self):
        """
        Creates defined amount of test processes where each
        creates a file and lock it.
        """
        print "Spawning %d test processes" % NUM_TEST_PROCS_TO_LAUNCH
        for _ in xrange(NUM_TEST_PROCS_TO_LAUNCH):
            # make up the name and path:
            random_file_name = "".join(choice(str_lowercase) for _ in range(20))
            full_file_name = "".join(("/tmp/lslock-test/", random_file_name, ".lock"))
            self.files_to_remove.append(full_file_name)

            # start a new process that creates, locks the file:
            Locking_process = Process(target=self.create_lock_file,
                                      args=(full_file_name,))
            Locking_process.start()
            self.procs_to_terminate.append(Locking_process)

    def generate_lock_files(self):
        """
        Main function:
        Checks if /tmp/lslock-test exists and creates if not;
        Spawns test processes that create own flocks.
        """
        try:
            if not path.exists('/tmp/lslock-test'):
                # tempfile lib migth be a better option here
                makedirs('/tmp/lslock-test')
            self.spawn_processes_to_lock()
            sleep(600)  # wait 10 mins or untill keyboard interrupted
        except OSError as exc:
            print "An Error occured while creating a /tmp/lslock-test ", exc
            exit(1)
        except KeyboardInterrupt:
            print "Exiting..."
        finally:
            self.perform_cleanup()


if __name__ == '__main__':
    Locks_gen = LocksGenerator()
    Locks_gen.generate_lock_files()
