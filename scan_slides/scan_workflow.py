from multiprocessing import Process, Queue
import time
import sys
import os
import subprocess
import re
import gpiozero.pins
import argparse
from control_projector import Projector

PK_CMD = './pktriggercord-cli'


def get_pictures(queue, picture_path, picture_nums):
    # start pktriggercord and get picutres in raw format
    cmd = [PK_CMD, '--dangerous',
           '-o', picture_path, '-F', str(picture_nums),
           '--file_format', 'DNG'
           ]

    p = subprocess.Popen(cmd,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)

    shot_re = re.compile('.*Taking picture (\d+)/(\d+).*')
    for line in iter(p.stdout.readline, b''):
        line = line.rstrip().decode()
        print('>>> ' + line)
        result = re.match(shot_re, line)
        if result:
            queue.put((result.group(1), result.group(2)))

    queue.put(('stop', 'stop'))


def convert_picture_to_jpeg():
    # wait until next picture file appears or pktriggercord has finished,
    # then convert picture to jpeg
    pass


def reorder_pictures(picture_dir, picutre_temp_name, picture_name,
                     picture_nums, step, force):
    out_i = 0
    picture_list = range(0, picture_nums)
    if step == 'backward':
        picture_list = reversed(picture_list)

    for i in picture_list:
        in_i = i

        in_i_str = "-%04d.dng" % in_i
        out_i_str = "-%04d.dng" % out_i

        source_file = os.path.join(picture_dir, picutre_temp_name + in_i_str)
        target_file = os.path.join(picture_dir, picture_name + out_i_str)
        if not os.path.isfile(target_file):
            print("rename", source_file, "to", target_file)
            os.rename(source_file, target_file)
        elif force:
            print('replace existing file', target_file)
            os.remove(target_file)
            os.rename(source_file, target_file)
        else:
            print('file', target_file, 'exists!. New scan stored as',
                  source_file)
        out_i += 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--directory', help='Directory to store scans',
                        metavar='DIR',
                        required=True)
    parser.add_argument('-o', '--output_file',
                        help='Pattern for file names of scans',
                        metavar='FILE',
                        required=True)
    parser.add_argument('-s', '--step',
                        help='Direction of projector steps [forward/backward' +
                        '], default: forward',
                        default='forward')
    parser.add_argument('-n', type=int,
                        default=50,
                        help='Number of scans, default: 50')
    parser.add_argument('--force', '-f', action="store_true",
                        help='Overwrite existing files')
    args = parser.parse_args()

    if args.step != 'forward' and args.step != 'backward':
        raise argparse.ArgumentError(
            'step direction has to be one of: forward/backward')

    projector = Projector('raspberrypi')

    queue = Queue()

    picture_dir = args.directory
    picutre_temp_name = '__scan__temp'
    picture_name = args.output_file
    picture_nums = args.n

    os.makedirs(picture_dir, exist_ok=True)
    picture_path = os.path.join(picture_dir, picutre_temp_name)

    pktrigger = Process(target=get_pictures,
                        args=(queue, picture_path, picture_nums)
                        )
    pktrigger.daemon = True
    pktrigger.start()

    while True:
        msg = queue.get()
        print(msg)
        if msg[0] == 'stop':
            break
        else:
            time.sleep(0.5)
            print('<<<< took image')
            projector.forward()

    pktrigger.join()

    reorder_pictures(picture_dir, picutre_temp_name, picture_name,
                     picture_nums, args.step, args.force)
