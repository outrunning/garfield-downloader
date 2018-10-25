#! /usr/bin/env python3
# Copyright (C) 2015 Filip Brozovic
# This code is published under the MIT License; see the LICENSE file for details.

import argparse
import datetime
import sys
import os
import urllib.request
import threading
from queue import Queue


class MyURLopener(urllib.request.FancyURLopener):
    def http_error_default(self, url, fp, errcode, errmsg, headers):
        urllib.request.URLopener.http_error_default(self, url, fp, errcode, errmsg, headers)


class DownloadThread(threading.Thread):
    total_comics = None

    def __init__(self, queue, out_directory, quiet):
        super(DownloadThread, self).__init__()
        self.queue = queue
        self.out_directory = out_directory
        self.quiet = quiet
        self.daemon = True

    def run(self):
        while True:
            if self.queue.qsize() == 0:
                return
            url = self.queue.get()
            downloaded_comics = self.total_comics - self.queue.qsize()
            if not self.quiet:
                if downloaded_comics != self.total_comics:
                    print('', end='\r')
                    
                print('[{0}/{1}] {2}'.format(str(self.total_comics - self.queue.qsize()), str(self.total_comics), 
                                             url.split('/')[-1]), end='')

            sys.stdout.flush()

            try:
                self.download_url(url)
            except Exception as e:
                print('Error: {0}'.format(e))
            self.queue.task_done()

    def download_url(self, url):
        name = url.split('/')[-1]

        destination = os.path.join(self.out_directory, name)
        if os.path.exists(destination):
            return

        try:
            MyURLopener().retrieve(url, destination)
        except IOError as e:
            print('Could not download file {0} ({1})'.format(destination, str(e)))


def parse_arguments():
    global args
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--start',
                        help='Date of first strip to be downloaded. If none is given, defaults to 19780619.',
                        metavar='YYYY[MM[DD]]')
    parser.add_argument('-e', '--end',
                        help='Date of last strip to be downloaded. If none is given, defaults to the current date.',
                        metavar='YYYY[MM[DD]]')
    parser.add_argument('-o', '--output', help='Output directory. This defaults to ./garfield.', metavar='DIR')
    parser.add_argument('-x', '--connections',
                        help='Number of connections to use when downloading files. '
                             'If none is given, this defaults to 4.',
                        type=int)
    parser.add_argument('-q', '--quiet', help='Do not output anything to the console', action='store_true')
    args = parser.parse_args()


def parse_date_argument(date):
    if len(date) == 4:
        return datetime.date(int(date), 1, 1)
    elif len(date) == 6:
        return datetime.date(int(date[0:4]), int(date[4:6]), 1)
    elif len(date) == 8:
        return datetime.date(int(date[0:4]), int(date[4:6]), int(date[6:8]))


def generate_download_list(start_date, end_date):
    url_list = []
    cur_date = start_date
    while cur_date != end_date + datetime.timedelta(1):
        url_list.append('https://d1ejxu6vysztl5.cloudfront.net/comics/usacres/{0}/usa{0}-{1}-{2}.gif'.format(str(cur_date.year),
                                                                                    str(cur_date.month).zfill(2),
                                                                                    str(cur_date.day).zfill(2)))
        cur_date = cur_date + datetime.timedelta(1)
    return url_list


def download_list(url_list, out_directory, num_threads, quiet):
    queue = Queue()
    for url in url_list:
        queue.put(url)

    DownloadThread.total_comics = len(url_list)

    for i in range(num_threads):
        t = DownloadThread(queue, out_directory, quiet)
        t.start()

    queue.join()


def main():
    parse_arguments()

    if args.start is None:
        start_date = datetime.date(1986, 3, 3)
    else:
        start_date = parse_date_argument(args.start)

    if args.end is None:
        end_date = datetime.date(1989, 5, 7)
    else:
        end_date = parse_date_argument(args.end)

    if args.output is None:
        out_directory = "./usacres"
    else:
        out_directory = args.output

    if args.connections is None:
        num_threads = 4
    else:
        num_threads = args.connections

    if not os.path.exists(out_directory):
        try:
            os.makedirs(out_directory)
        except IOError as e:
            print('Could not create output directory ({0})'.format(str(e)))

    url_list = generate_download_list(start_date, end_date)
    download_list(url_list, out_directory, num_threads, args.quiet)


if __name__ == '__main__':
    main()
