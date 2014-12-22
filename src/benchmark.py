import time, sys


class BenchMark(object):
    def __init__(self):
        self.start = 0
        self.end = 0
        self.spinner=0
    
    def toggleOn(self, msg):
        self.start = time.time()
        print msg,
        print '\b'*3,
        sys.stdout.flush()
        self.spinner = self._spinning_cursor()
        
    def add(self, delay):
        sys.stdout.write(self.spinner.next())
        sys.stdout.flush()
        time.sleep(delay)
        sys.stdout.write('\b')
        sys.stdout.flush()
        
    def toggleOff(self, msg):
        self.end = time.time()
        print msg + ' completed in %s' %(self.end-self.start) 
        
    def _spinning_cursor(self):
        while True:
            for cursor in '|/-\\':
                yield cursor