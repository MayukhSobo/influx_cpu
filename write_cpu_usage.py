# System modules
from Queue import Queue # for data structure holding thread data
from threading import Thread # thread library for creating thread
from datetime import datetime # for datetime , currently not used
from influxdb import InfluxDBClient # influxdb python agent
import psutil  # for the cpu usage
import time # for sleep()

class DBClinet(object):
	db_created_already = False # for checking if db is already created
	db = None # the database object common for all the object
	def __init__(self, host, port, user, passcode, dbname):
		self.host = host
		self.port = port
		self.user = user
		self.passcode = passcode
		self.dbName = dbname
		#self.client = None

	def create(self):
		if not DBClinet.db_created_already:
			DBClinet.db = InfluxDBClient(self.host, self.port, self.user, self.passcode, self.dbName)
			#print("Create database: " + self.dbName)
    			DBClinet.db.create_database(self.dbName)
			#print("Create a retention policy")
 	   		#DBClient.db.create_retention_policy('awesome_policy', '3d', 3, default=True)
			DBClinet.db_created_already = True

    	def write(self, json_data):
		DBClinet.db.write_points(json_data)



cpu_queue = Queue()
db = InfluxDBClient('localhost', 8086, 'root', 'mayukhsobo', 'python_cpu')

#template_json = "\"measurement\": \"cpu\", \"time\" : \"{t}\", \"cpu_usage\": {cu}"
json_data = [{'fields': {'cpu_usage': 0.0}, 'tags': {'host': 'DigitalOcean', 'region': 'india'}, 'measurement': 'cpu'}]

def worker1(q):
    """
	This is the first worker function which is
	used to return the cpu usage. This method uses
	psutil module to calculate the CPU usage using
	the method psutil.cpu_percent(). Please visit
	the documentation for more info in psutils.

	Note: sleep(10) is being used with the value of
	10 seconds. This is a nasty way of synchronising
	but however it gets our job done because influxdata_python
	agent is pusing the CPU usage at every 10 seconds. Race conditions 
	never seem to occur because data is put before the data is get
	and it gets 10 seconds to preempt the CPU and hopefully the control
	always jumps to pushing the data part thus preventing race conditions.
	For much more assured preemption we should use mutex locks.

	:param cpu_queue: This is the queue where all the
					  cpu percents are being stored.
					  We are using queue because, once
					  the data is pushed, we may not need
					  that again. It is a global data structure
	:return: None:
	"""
    while True:
        data = q.get()
        #json_data = template_json.format(t=data[0], cu=data[1])
        c = DBClinet('localhost', 8086, 'root', 'mayukhsobo', 'python_cpu')
        c.create()
	json_data[0]['fields']['cpu_usage'] = data[1] # populate the cpu usage in json body
        c.write(json_data)
	#db.write_points(json_data)
	#print json_data
        time.sleep(10)
	del c  # may be not necessary
        q.task_done()

# here is the main thread
influxWriter = Thread(target=worker1, args=(cpu_queue,))
influxWriter.setDaemon(True)
influxWriter.start()

while True:
	now = datetime.now()
	t = str(now.hour) + ":" + str(now.minute) + ":" + str(now.second)
	cpu_queue.put([t, psutil.cpu_percent(interval=1.0)]) # data is put here in the queue
	cpu_queue.join()
