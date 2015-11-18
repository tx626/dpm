LOG_DEBUG = True
LOG_ERROR = True

DEBUG = True
SHOW_TIME = False

MONGO_PORT = 27017
FRONTEND_PORT = 9001
BACKEND_PORT = 9002
REPOSITORY_PORT = 9003
INSTALLER_PORT = 9004
ALLOCATOR_PORT = 9005
RECORDER_PORT = 9006

MANAGER_PORTS = [i for i in range(10001, 10002)]

# global info
#USER_DB = '192.168.10.128'                             #register user
RECORDER_DB = '192.168.10.129'                     #recorder/manager    statistics of macro information
USERDB_SERVERS = ['192.168.10.133', '192.168.10.134', '192.168.10.160', '192.168.10.161', '192.168.10.162', '192.168.10.163', '192.168.10.164', '192.168.10.165',
                  '192.168.10.166', '192.168.10.192', '192.168.10.193', '192.168.10.194', '192.168.10.195', '192.168.10.196', '192.168.10.197', '192.168.10.198']

#local info
APP_DB = '192.168.10.130'                               #install app
REPO_DB = '192.168.10.131'                            #upload app
ALLOC_DB = '192.168.10.132'                    #installer

FRONTEND_SERVERS = ['192.168.10.128', '192.168.10.129', '192.168.10.130', '192.168.10.131']
BACKEND_SERVERS = ['192.168.10.36', '192.168.10.37', '192.168.10.50', '192.168.10.51']
REPOSITORY_SERVERS = ['192.168.10.194', '192.168.10.195', '192.168.10.196', '192.168.10.197']
ALLOCATOR_SERVERS = ['192.168.10.165', '192.168.10.166', '192.168.10.192', '192.168.10.193']
RECORDER_SERVERS =  ['192.168.10.132', '192.168.10.133', '192.168.10.134', '192.168.10.160']
MANAGER_SERVERS = ['192.168.10.227', '192.168.10.228', '192.168.10.229', '192.168.10.230']

IFACE = 'eth0'
