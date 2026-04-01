#!/usr/bin/env python3

from subprocess import Popen, PIPE, run
import sys
from getopt import getopt
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
import subprocess
import json



def setup_logging(log_file=None):
    try:
        opts, args = getopt(sys.argv[1:], "l:", ["logfile="])
        for opt, arg in opts:
            if opt in ("-l", "--logfile"):
                log_file = arg
    except:
        pass

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger


class ppingPerf:
    def __init__(self, dstHost=None, dstPort=None, testtype="http", outputType="json"):
        self.logger = setup_logging()
        self.filePath = None
        self.dstHost = dstHost
        self.dstPort = dstPort
        self.testtype = testtype
        self.outputType = outputType
        self.datetime = None
        self.latencyMean = None
        self.latencyMin = None
        self.latencyMax = None

    def run(self):
        if len(sys.argv) < 2 and self.dstHost is None: 
            self.logger.error("Usage: pping.py -t <testtype> -a <address> -p <port> -j <jsonfile>")
            sys.exit(1)
        try:
            opts, args = getopt(sys.argv[1:], "t:a:p:j:", ["testtype=", "address=", "port=", "jsonfile="])
        except:
            self.logger.error("Usage: pping.py -t <testtype> -a <address> -p <port> -j <jsonfile>")
            sys.exit(1)

        for opt, arg in opts:
            if opt in ("-t", "--testtype"):
                self.testtype = str(arg)
            elif opt in ("-a", "--address"):
                self.dstHost = str(arg)
            elif opt in ("-p", "--port"):
                self.dstPort = int(arg)
            elif opt in ("-j", "--jsonfile"):
                self.filePath = str(arg)

        if not self.testtype or not self.dstHost:
            self.logger.error("Usage: pping.py -t <testtype> -a <address> -p <port> -j <jsonfile>")
            sys.exit(1)
        now = datetime.now()
        self.datetime = now.strftime("%Y-%m-%d %H:%M:%S")
        self.dropped = 0
        self.latencyMean = 0.0
            
        if self.testtype in ['http', 'quic', 'tls', 'icmp']:
            self.logger.info("Running test: %s" % self.testtype)
            command = ["pping", self.testtype, self.dstHost]
            result = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, _ = result.communicate()
            output = stdout
            results = self.parseHTTP(output)
        elif self.testtype == 'tcp':
            self.logger.info("Running TCP test: %s" % self.testtype)
            command = ["pping", self.testtype, self.dstHost, str(self.dstPort)]
            result = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, _ = result.communicate()
            output = stdout
            results = self.parseHTTP(output)
        else:
            self.logger.error("Invalid testtype: %s" % results.testtype)
            sys.exit(1)
        if self.outputType == "json":    
            self.writeJSON()
        return results

    def writeJSON(self) -> None:
        if not self.filePath:
            self.filePath = "pping-%s-results.log" % self.testtype
        try:
            with open(self.filePath, 'w') as f:
                self.logger.debug(str(self))
                j = json.dumps(asdict(self), sort_keys=True, indent=4)
                f.write(j)
        except Exception as e:
            self.logger.error("Error writing to file: %s" % e)
            sys.exit(1)

    def parseHTTP(self, result: str) -> None: 
        import re
        latency = None
        dropped = None
        for line in result.splitlines():
            if "avg" in line:
                r = re.search(r'min \= (\d*) ms, max \= (\d*) ms, avg \= (\d*) ms', line)
                self.latencyMean = r.group(3)
                self.latencyMin = r.group(1)
                self.latencyMax = r.group(2)
            if "sent" in line:
                d = str(line.split(',')[2])
                d = d.strip()
                d = d.split('=')[1]
                self.dropped = int(d.split('(')[0])
        self.logger.info("LatencyMean: %s, LatencyMin: %s, LatencyMax: %s Dropped: %s" % (self.latencyMean, self.latencyMin, self.latencyMax, self.dropped))

    def parseLimited(self, result: str) -> None:
        import re
        for line in result.splitlines():
            if "avg" in line:
                self.logger.debug("Found AVG")
                r = re.search(r'min \= (\d*) ms, max \= (\d*) ms, avg \= (\d*) ms', line)
                self.latencyMean = r.group(3)
                self.latencyMin = r.group(1)
                self.latencyMax = r.group(2)
            if "sent" in line:
                self.logger.debug("Found Sent")
                d = str(line.split(',')[2])
                d = d.strip()
                d = d.split('=')[1]
                self.dropped = int(d.split('(')[0])
        self.logger.info("LatencyMean: %s, LatencyMin: %s, LatencyMax: %s Dropped: %s" % (self.latencyMean, self.latencyMin, self.latencyMax, self.dropped))
if __name__ == '__main__':
    log_file = None
   
    r = ppingPerf()
    r.run()