#      backend.py
#      
#      Copyright (C) 2015 Xiao-Fang Huang <huangxfbnu@163.com>,  Xu Tian <tianxu@iscas.ac.cn>
#      
#      This program is free software; you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation; either version 2 of the License, or
#      (at your option) any later version.
#      
#      This program is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#      GNU General Public License for more details.
#      
#      You should have received a copy of the GNU General Public License
#      along with this program; if not, write to the Free Software
#      Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#      MA 02110-1301, USA.

import os
import json
import uuid
from lib.user import User
from threading import Lock
from hash_ring import HashRing
from lib.util import localhost, get_uid
from lib.log import log_debug, log_err
from lib.sandbox import Sandbox, OP_SCAN
from component.rpcclient import RPCClient
from component.rpcserver import RPCServer
from conf.config import BACKEND_PORT, REPOSITORY_PORT, ALLOCATOR_PORT, INSTALLER_PORT, RECORDER_PORT, REPOSITORY_SERVERS, ALLOCATOR_SERVERS, RECORDER_SERVERS, SHOW_TIME, DEBUG, CATEGORIES

LOCK_MAX = 1024
CACHE_MAX = 4096

if SHOW_TIME:
    from datetime import datetime

class Backend(RPCServer):
    def __init__(self, addr, port):
        RPCServer.__init__(self, addr, port, user=User())
        self._sandbox = Sandbox()
        locks = []
        for _ in range(LOCK_MAX):
            locks.append(Lock())
        self._locks = HashRing(locks)
        self._cache = {}
        if DEBUG:
            self._register_cnt = 0
            self._login_cnt = 0
            self._upload_cnt = 0
            self._install_cnt = 0
    
    def _load(self, buf):
        return json.loads(buf)
    
    def _get_lock(self, user):
        uid = get_uid(user)
        return self._locks.get_node(uid)
    
    def _get_allocator(self, uid):
        ring = HashRing(ALLOCATOR_SERVERS)
        server = ring.get_node(uid)
        return server
    
    def _get_repo(self, package):
        ring = HashRing(REPOSITORY_SERVERS)
        server = ring.get_node(package)
        return server
    
    def _get_recorder(self, package):
        ring = HashRing(RECORDER_SERVERS)
        server = ring.get_node(package)
        return server
    
    def _update(self, uid, category, package, title, description):
        addr = self._get_recorder(package)
        rpcclient = RPCClient(addr, RECORDER_PORT)
        return rpcclient.request('upload', uid=uid, category=category, package=package, title=title, description=description)
    
    def _check_category(self, category):
        res = CATEGORIES
        if res.has_key(category):
            return res.get(category)
        else:
            return str(len(res))
    
    def upload(self, uid, package, version, buf, typ):
        log_debug('Backend', 'start to upload')
        try:
            if SHOW_TIME:
                start_time = datetime.utcnow()
            addr = self._get_repo(package)
            rpcclient = RPCClient(addr, REPOSITORY_PORT)
            res = rpcclient.request('upload', uid=uid, package=package, version=version, buf=buf)
            if SHOW_TIME:
                log_debug('Backend', 'upload, upload package to repo, time=%d sec' % (datetime.utcnow() - start_time).seconds)
                start_time = datetime.utcnow()
            if not res:
                log_err('Backend', 'failed to upload to repo')
                return
            cat, title, desc = self._sandbox.evaluate(OP_SCAN, buf)
            if not cat or not title or not desc:
                log_err('Backend', 'invalid package')
                return
            cat = self._check_category(cat)
            if not cat:
                log_err('Backend', 'invalid category')
                return
            if SHOW_TIME:
                log_debug('Backend', 'upload, analyze yaml, time=%d sec' % (datetime.utcnow() - start_time).seconds)
                start_time = datetime.utcnow()
            if DEBUG:
                self._upload_cnt += 1
                log_debug('Backend', 'upload, count=%d' % self._upload_cnt)
            #return self._update(uid, cat, package, title, desc)
            res = self._update(uid, cat, package, title, desc)
            if SHOW_TIME:
                log_debug('Backend', 'upload, update recorder, time=%d sec' % (datetime.utcnow() - start_time).seconds)
            return res
        finally:
            pass
        #except:
        #    log_err('Backend', 'failed to upload')
    
    def _get_installer(self, uid):
        log_debug('Backend', 'start to get instsaller addr')
        try:
            cache = self._cache
            addr = cache.get(uid)
            if addr:
                return addr
            else:
                address = self._get_allocator(uid)
                rpcclient = RPCClient(address, ALLOCATOR_PORT)
                addr = rpcclient.request('get_installer', uid=uid)
                if len(cache) >= CACHE_MAX:
                    cache.popitem()
                cache.update({uid:addr})
                return addr
        except:
            log_err('Backend', 'failed to get instsaller addr')
    
    
    def install(self, uid, package, version, typ):
        log_debug('Backend', 'start to install')
        try:
            if SHOW_TIME:
                start_time = datetime.utcnow()
            addr = self._get_installer(uid)
            rpcclient = RPCClient(addr, INSTALLER_PORT)
            res = rpcclient.request('install', uid=uid, package=package, version=version, typ=typ)
            if not res:
                log_err('Backend', 'failed to install')
                return
            addr = self._get_recorder(package)
            rpcclient = RPCClient(addr, RECORDER_PORT)
            info = rpcclient.request('install', package=package)
            if SHOW_TIME:
                log_debug('Backend', 'install, time=%d sec' % (datetime.utcnow() - start_time).seconds)
            if DEBUG:
                self._install_cnt += 1
                log_debug('Backend', 'install, count=%d' % self._install_cnt)
            if not info:
                log_err('Backend', 'failed to install, invalid update install table')
                return
            return info
        except:
            log_err('Backend', 'failed to install')
    
    def uninstall(self, uid, package, typ):
        log_debug('Backend', 'start to uninstall')
        addr = self._get_installer(uid)
        rpcclient = RPCClient(addr, INSTALLER_PORT)
        res = rpcclient.request('uninstall', uid=uid, package=package, typ=typ)
        if not res:
            log_err('Backend', 'failed to uninstall')
            return
        return res
        
    def get_name(self, uid):
        log_debug('Backend', 'start to get name, uid=%s' % str(uid))
        return self.user.get_name(uid)
    
    def get_installed_packages(self, uid, typ):
        log_debug('Backend', 'start to get installed packages')
        addr = self._get_installer(uid)
        rpcclient = RPCClient(addr, INSTALLER_PORT)
        return rpcclient.request('get_packages', uid=uid, typ=typ)
    
    def has_package(self, uid, package, typ):
        log_debug('Backend', 'has_package, package=%s' % str(package))
        addr = self._get_installer(uid)
        rpcclient = RPCClient(addr, INSTALLER_PORT)
        return rpcclient.request('has_package', uid=uid, package=package, typ=typ)
    
    def _alloc_installer(self, uid):
        log_debug('Backend', 'alloc_installer->uid=%s' % str(uid))
        addr = self._get_allocator(uid)
        rpcclient = RPCClient(addr, ALLOCATOR_PORT)
        if  rpcclient.request('alloc_installer', uid=uid):
            return True
        else:
            log_err('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!  Backend', 'failed to allocate installer')
            return False
    
    def register(self, user, pwd, email):
        log_debug('Backend', 'register starts')
        lock = self._get_lock(user)
        lock.acquire()
        try:
            if SHOW_TIME:
                start_time = datetime.utcnow()
            uid = self.user.add(user, pwd, email)
            if not uid:
                log_err('Backend', 'failed to register, invalid register table')
                return False
            info= self._alloc_installer(uid)
            if SHOW_TIME:
                log_debug('Backend', 'register, time=%d sec' % (datetime.utcnow() - start_time).seconds)
            if info:
                if DEBUG:
                    self._register_cnt += 1
                    log_debug('Backend', 'register, count=%d' % self._register_cnt)
                return True
            else:
                self.user.remove(user)
                log_err('@@@@@@@@ Backend', 'failed to register, invalid alloc installer table')
                return False
        finally:
            lock.release()
    
    def login(self, user, pwd):
        log_debug('Backend', 'start to login')
        if SHOW_TIME:
            start_time = datetime.utcnow()
        password = self.user.get_password(user)
        if SHOW_TIME:
            log_debug('Backend', 'login, time=%d sec' % (datetime.utcnow() - start_time).seconds)
        if pwd == password:
            if DEBUG:
                self._login_cnt += 1
                log_debug('Backend', 'login, count=%d' % self._login_cnt)
            return self.user.get_public_key(user)
        else:
            log_err('Backend', 'failed to login, invalid login password')
            return (None, None)

def main():
    backend = Backend(localhost(), BACKEND_PORT)
    backend.run()
