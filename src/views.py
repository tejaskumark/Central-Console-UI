from logging import raiseExceptions
import time
import json
import sqlite3
from pathlib import Path

from requests import status_codes
from . import app
from flask import jsonify, render_template
from flask import request  # import main Flask class and request object
from src.mlogger import logger
import requests


dbFile = "/app/host.db"


@app.route("/about")
def about():
    return "Central Serial Console"


@app.route("/", methods=["GET"])
def index():
    try:
        return render_template("index.html")
    except Exception as e:
        logger.exception(e)
        return "Template Not Found", 404


@app.route("/get/hosts/list", methods=["GET"])
def gethostslist():
    try:
        r = getdbdata("SELECT * FROM hosts;")
        hostslist = [dict(row) for row in r]
        return json.dumps(hostslist)
    except Exception as e:
        logger.exception(e)
        return {'error': str(e)}, 500


@app.route("/get/console/ports", methods=["GET"])
def getconsoleports():
    try:
        allports = {}
        errorhost = []
        r = getdbdata("SELECT * FROM hosts;")
        hostslist = [dict(row) for row in r]
        for index in range(len(hostslist)):
            hostnametulple = hostslist[index]["hostname"] + \
                ":" + hostslist[index]["port"]
            hostdesc = hostslist[index]["location"]
            allports[hostnametulple] = []
            url = "http://" + hostnametulple + "/get/config"
            try:
                resp = requests.get(url, timeout=3)
                jsnresp = resp.json()
                for index in range(len(jsnresp["Ports"])):
                    jsnresp["Ports"][index]["Logs"] = "http://" + hostnametulple + \
                        "/logs/" + jsnresp["Ports"][index]["Name"].split("/")[-1] + ".txt"
                    jsnresp["Ports"][index]["Terminal"] = "http://" + hostnametulple + \
                        "/port?portname=" + jsnresp["Ports"][index]["Name"]
                    jsnresp["Ports"][index]["Description"] = hostdesc
                    allports[hostnametulple].append(jsnresp["Ports"][index])
            except requests.ConnectionError:
                host = hostnametulple + "(" + hostdesc + ")"
                errorhost.append(host)
            except Exception:
                host = hostnametulple + "(" + hostdesc + ")"
                errorhost.append(host)
        if len(errorhost) == 0:
            return json.dumps(allports)
        else:
            allports["errorhost"] = errorhost
            return json.dumps(allports), 206
    except Exception as e:
        logger.exception(e)
        return {'error': str(e)}, 500


@app.route("/edit/console/port", methods=["POST"])
def editconsoleport():
    content = request.json
    try:
        host = content["existinghostname"].split("&")[0]
        existingport = content["existinghostname"].split("&")[1]
        data = {}
        data["baudrate"] = content["baudrate"]
        data["newname"] = content["newname"]
        data["description"] = content["description"]
    except KeyError as e:
        logger.exception(e)
        return {'error': 'Expected key value data not present.'}, 400
    try:
        url = "http://" + host + "/edit?portname=" + existingport
        resp = requests.post(url, json=data)
        if resp.status_code == 200:
            return "", resp.status_code
        else:
            return json.dumps(resp.json()), resp.status_code
    except Exception as e:
        logger.exception(e)
        return {'error': str(e)}, 500


@app.route("/add/console/port", methods=["POST"])
def addconsoleport():
    content = request.json
    try:
        host = content["hosttuple"]
        data = {}
        data["baudrate"] = content["baudrate"]
        data["newname"] = content["newname"]
        data["description"] = content["description"]
    except KeyError as e:
        logger.exception(e)
        return {'error': 'Expected key value data not present.'}, 400
    try:
        url = "http://" + host + "/add"
        resp = requests.post(url, json=data)
        if resp.status_code == 200:

            return "", resp.status_code
        else:
            logger.info
            return resp.content.decode("utf-8"), resp.status_code
    except Exception as e:
        logger.exception(e)
        return {'error': str(e)}, 500


@app.route("/delete/console/port", methods=["DELETE"])
def deleteconsoleport():
    content = request.json
    try:
        host = content["hosttuple"].split("&")[0]
        consoleport = content["hosttuple"].split("&")[1]
    except KeyError as e:
        logger.exception(e)
        return {'error': 'Expected key value data not present.'}, 400
    try:
        url = "http://" + host + "/delete?portname=" + consoleport
        resp = requests.delete(url)
        if resp.status_code == 200:
            return "", resp.status_code
        else:
            return json.dumps(resp.json()), resp.status_code
    except Exception as e:
        logger.exception(e)
        return {'error': str(e)}, 500


@app.route("/stop/console/port", methods=["POST"])
def stopconsoleport():
    content = request.json
    try:
        host = content["hostname"]
        port = content["port"]
    except KeyError as e:
        logger.exception(e)
        return {'error': 'Expected key value data not present.'}, 400
    try:
        url = "http://" + host + "/stop?portname=" + port
        resp = requests.post(url)
        if resp.status_code == 200:
            return "", resp.status_code
        else:
            return json.dumps(resp.json()), resp.status_code
    except Exception as e:
        logger.exception(e)
        return {'error': str(e)}, 500


@app.route("/start/console/port", methods=["POST"])
def startconsoleport():
    content = request.json
    try:
        hostname = content["hostname"]
        port = content["port"]
    except KeyError as e:
        logger.exception(e)
        return {'error': 'Expected key value data not present.'}, 400
    try:
        url = "http://" + hostname + "/start?portname=" + port
        resp = requests.post(url)
        if resp.status_code == 200:
            return "", resp.status_code
        else:
            return json.dumps(resp.json()), resp.status_code
    except Exception as e:
        logger.exception(e)
        return {'error': str(e)}, 500


@app.route("/get/hosts", methods=["GET"])
def gethosts():
    try:
        r = getdbdata("SELECT * FROM hosts;")
        data = updatehoststatus([dict(row) for row in r])
        return json.dumps(data)
    except Exception as e:
        logger.exception(e)
        return {'error': str(e)}, 500


def getdbdata(query):
    conn = sqlite3.connect(dbFile)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(query)
    data = cur.fetchall()
    cur.close()
    return data


def updatehoststatus(hostlist):
    data = getdbdata("SELECT * from hosts;")
    hosts = [dict(row) for row in data]
    for index in range(len(hosts)):
        url = "http://" + hosts[index]["hostname"] + ":" + hosts[index]["port"]
        try:
            st = requests.get(url, timeout=5)
            if st.status_code == 200:
                hosts[index]["status"] = 1
            else:
                hosts[index]["status"] = 0
        except BaseException:
            hosts[index]["status"] = 0
    return hosts


@app.route("/add/host", methods=["POST"])
def addhost():
    content = request.json
    try:
        hostname = content["hostname"]
        port = content["port"]
        location = content["location"]
    except KeyError as e:
        logger.exception(e)
        return {'error': 'Expected key value data not present.'}, 400
    try:
        url = "http://" + hostname + ":" + port
        st = requests.get(url, timeout=3)
        if st.status_code == 200:
            conn = sqlite3.connect(dbFile)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("""insert into hosts values (?, ?, ?)""",
                        (hostname, port, location))
            conn.commit()
            cur.close()
            return "", 200
        else:
            return "Remote host is not serial console host.", 400
    except sqlite3.IntegrityError as e:
        logger.exception(e)
        return "Host name and port tuple already exist in database.", 400
    except requests.Timeout as e:
        logger.exception(e)
        return "Host not reachable.", 400
    except requests.ConnectionError as e:
        return "Remote host connection refused on port %s." % port, 400
    except Exception as e:
        return {'error': str(e)}, 500


@app.route("/edit/host", methods=["POST"])
def edithost():
    content = request.json
    try:
        existingname = content["existingname"].split(":")[0]
        existingport = content["existingname"].split(":")[1]
        hostname = content["hostname"]
        port = content["port"]
        location = content["location"]
    except KeyError as e:
        logger.exception(e)
        return {'error': 'Expected key value data not present.'}, 400
    try:
        url = "http://" + hostname + ":" + port
        st = requests.get(url, timeout=3)
        if st.status_code == 200:
            conn = sqlite3.connect(dbFile)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                """update hosts set hostname=(?), port=(?), location=(?) where hostname=(?) and port=(?)""",
                (hostname,
                 port,
                 location,
                 existingname,
                 existingport))
            conn.commit()
            cur.close()
            return "", 200
        else:
            return "Remote host is not serial console host.", 400
    except sqlite3.IntegrityError as e:
        logger.exception(e)
        return "Hostname/Port combination name already exist.", 400
    except requests.Timeout as e:
        logger.exception(e)
        return "Host not reachable.", 400
    except requests.ConnectionError as e:
        return "Remote host connection refused on port %s." % port, 400
    except Exception as e:
        logger.exception(e)
        return {'error': 'Error during inserting values into DB.'}, 500


@app.route("/delete/host", methods=["DELETE"])
def deletehost():
    content = request.json
    try:
        hostname = content["hosttuple"].split(":")[0]
        port = content["hosttuple"].split(":")[1]
    except KeyError as e:
        logger.exception(e)
        return {'error': 'Expected key value data not present.'}, 400
    try:
        conn = sqlite3.connect(dbFile)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            """delete from hosts where hostname=? and port=?""", (hostname, port))
        conn.commit()
        cur.close()
        return "", 200
    except Exception as e:
        logger.exception(e)
        return {"error": "Error during deleting values from db."}, 500
