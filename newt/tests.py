"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".
"""

from django.test import TestCase
from django.conf import settings
import socket
import requests
import os

newt_base_url = "http://127.0.0.1:8000/api"

class BasicTests(TestCase):
    def test_root(self):
        """
        test basic root URI
        """
        r = requests.get(newt_base_url)
        self.assertEquals(r.status_code, 200)

        json_response = r.json()
        self.assertEquals(json_response['status'], "OK")
        self.assertEquals(json_response['status_code'], 200)
        self.assertEquals(json_response['error'], "")
        self.assertTrue(json_response['output']['version'], settings.NEWT_VERSION)

        self.assertEquals(r.status_code, 200)
        self.assertEquals(r.headers['content-type'], 'application/json')



    def test_error(self):
        r = requests.post(newt_base_url)
        self.assertEquals(r.status_code, 501)

        json_response = r.json()
        self.assertEquals(json_response['status'], "ERROR")
        # self.assertEquals(r.headers['content-type'], 'application/json')

class StatusTests(TestCase):
    def test_all(self):
        r = requests.get(newt_base_url+'/status')
        self.assertEquals(r.status_code, 200)

        json_response = r.json()
        self.assertEquals(json_response['status'], "OK")

        self.assertEquals(json_response['output'][0]['status'], 'up')

    def test_one(self):
        system = settings.NEWT_CONFIG['SYSTEMS'][0]['NAME']
        r = requests.get('%s/status/%s' % (newt_base_url, system))
        self.assertEquals(r.status_code, 200)

        json_response = r.json()
        self.assertEquals(json_response['status'], "OK")

        self.assertEquals(json_response['output']['status'], 'up')

class CommandTests(TestCase):
    def test_root(self):
        r = requests.get(newt_base_url+'/command')
        self.assertEquals(r.status_code, 200)
        json_response = r.json()
        self.assertEquals(json_response['status'], "OK")
        self.assertIn('localhost', json_response['output'])

    def test_command(self):
        r = requests.post(newt_base_url+'/command/localhost', {'command': '/bin/hostname'})
        self.assertEquals(r.status_code, 200)
        json_response = r.json()
        self.assertEquals(json_response['status'], "OK")

        hostname = socket.gethostname()
        self.assertEquals(hostname, json_response['output']['stdout'].strip())


    def test_command_with_args(self):
        # Run ls in / which should always have "usr"
        r = requests.post(newt_base_url+'/command/localhost', {'command': '/bin/ls -l /'})
        self.assertEquals(r.status_code, 200)
        json_response = r.json()
        self.assertEquals(json_response['status'], "OK")
        self.assertIn('usr', json_response['output']['stdout'])
        self.assertIn('drw', json_response['output']['stdout'])




class FileTests(TestCase):
    def test_root(self):
        r = requests.get(newt_base_url+'/file')
        self.assertEquals(r.status_code, 200)
        json_response = r.json()
        self.assertEquals(json_response['status'], "OK")
        self.assertIn('localhost', json_response['output'])
        
    def test_getdir(self):
        file_list = os.listdir("/")
        # Add . and .. to listdir results
        file_list = file_list + ['.', '..']
        file_list.sort()
        self.assertTrue(len(file_list)>0)
        
        r = requests.get(newt_base_url+'/file/localhost/')
        self.assertEquals(r.status_code, 200)

        json_response = r.json()
        self.assertEquals(json_response['status'], "OK")
        
        self.assertEquals(len(json_response['output']), len(file_list))
        newt_file_list = [ str(line['name']) for line in json_response['output'] ]
        newt_file_list.sort()
        
        self.maxDiff = None
        self.assertEquals(newt_file_list, file_list)
        
    def test_getfile(self):
        # TODO: Use namedtmpfile instead
        tmpfile = "/tmp/tmp_newt.txt"
        with open(tmpfile, 'w') as f:
            f.write('hello newt')
            
        r = requests.get(newt_base_url+'/file/localhost/tmp/tmp_newt.txt?download=true')
        self.assertEquals(r.status_code, 200)
        
        self.assertEquals(r.content, 'hello newt')
        os.remove(tmpfile)

class AuthTests(TestCase):
    payload = { 'username': "testuser", 'password': "test1pass" }
    def setUp(self):
        self.session = requests.Session()

    def test_login(self):
        session = self.session
        # Should not be logged in
        r = session.get(newt_base_url + "/auth")
        self.assertEquals(r.status_code, 200)
        json_response = r.json()
        self.assertEquals(json_response['output']['auth'], False)
        
        # Should be logged in
        r = session.post(newt_base_url + "/auth", data=self.payload)
        self.assertEquals(r.status_code, 200)
        json_response = r.json()
        self.assertEquals(json_response['output']['auth'], True)
        self.assertEquals(json_response['output']['username'], self.payload['username'])

        # Loggen in session should return user info
        r = session.get(newt_base_url + "/auth")
        self.assertEquals(r.status_code, 200)
        json_response = r.json()
        self.assertEquals(json_response['output']['auth'], True)
        self.assertEquals(json_response['output']['username'], self.payload['username'])


    def test_logout(self):
        session = self.session

        # Should be logged in
        r = session.post(newt_base_url + "/auth", data=self.payload)
        self.assertEquals(r.status_code, 200)
        json_response = r.json()
        self.assertEquals(json_response['output']['auth'], True)
        self.assertEquals(json_response['output']['username'], self.payload['username'])

        r = session.delete(newt_base_url + "/auth")
        self.assertEquals(r.status_code, 200)
        json_response = r.json()
        self.assertEquals(json_response['output']['auth'], False)

        r = session.get(newt_base_url + "/auth")
        self.assertEquals(r.status_code, 200)
        json_response = r.json()
        self.assertEquals(json_response['output']['auth'], False)
