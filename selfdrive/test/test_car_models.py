#!/usr/bin/env python3
import shutil
import time
import os
import sys
import signal
import subprocess
import requests
from cereal import car

import selfdrive.manager as manager
import cereal.messaging as messaging
from common.params import Params
from common.basedir import BASEDIR
from selfdrive.car.fingerprints import all_known_cars
from selfdrive.car.subaru.values import CAR as SUBARU
from selfdrive.car.volkswagen.values import CAR as VOLKSWAGEN


os.environ['NOCRASH'] = '1'


def wait_for_socket(name, timeout=10.0):
  socket = messaging.sub_sock(name)
  cur_time = time.time()

  r = None
  while time.time() - cur_time < timeout:
    print("waiting for %s" % name)
    r = socket.receive(non_blocking=True)
    if r is not None:
      break
    time.sleep(0.5)

  if r is None:
    sys.exit(-1)
  return r

def get_route_logs(route_name):
  for log_f in ["rlog.bz2", "fcamera.hevc"]:
    log_path = os.path.join("/tmp", "%s--0--%s" % (route_name.replace("|", "_"), log_f))

    if not os.path.isfile(log_path):
      log_url = "https://commadataci.blob.core.windows.net/openpilotci/%s/0/%s" % (route_name.replace("|", "/"), log_f)
      r = requests.get(log_url)

      if r.status_code == 200:
        with open(log_path, "wb") as f:
          f.write(r.content)
      else:
        print("failed to download test log %s" % route_name)
        sys.exit(-1)

routes = {
  "791340bc01ed993d|2019-03-10--16-28-08": {
    'carFingerprint': SUBARU.IMPREZA,
    'enableCamera': True,
  },
  "76b83eb0245de90e|2019-10-21--17-40-42": {
    'carFingerprint': VOLKSWAGEN.GENERICMQB,
    'enableCamera': True,
  },
}

passive_routes = [
  "07cb8a788c31f645|2018-06-17--18-50-29",
  #"bfa17080b080f3ec|2018-06-28--23-27-47",
]

# TODO: replace all these with public routes
# TODO: add routes for untested cars: HONDA ACCORD 2018 HYBRID TOURING and CHRYSLER PACIFICA 2018
non_public_routes = [
  "0607d2516fc2148f|2019-02-13--23-03-16", # CHRYSLER PACIFICA HYBRID 2019
  "3e9592a1c78a3d63|2018-02-08--20-28-24", # HONDA PILOT 2017 TOURING
  "aa20e335f61ba898|2019-02-05--16-59-04", # BUICK REGAL ESSENCE 2018
  "1851183c395ef471|2018-05-31--18-07-21", # HONDA CR-V 2017 EX
  "9d5fb4f0baa1b3e1|2019-01-14--17-45-59", # KIA SORENTO GT LINE 2018
  "b4c18bf13d5955da|2018-07-29--13-39-46", # TOYOTA C-HR HYBRID 2018
  "5a2cfe4bb362af9e|2018-02-02--23-41-07", # ACURA RDX 2018 ACURAWATCH PLUS
  "362d23d4d5bea2fa|2018-08-10--13-31-40", # TOYOTA HIGHLANDER HYBRID 2018
  "aa20e335f61ba898|2018-12-17--21-10-37", # BUICK REGAL ESSENCE 2018
  "215cd70e9c349266|2018-11-25--22-22-12", # KIA STINGER GT2 2018
  "192a598e34926b1e|2019-04-04--13-27-39", # JEEP GRAND CHEROKEE 2019
  "34a84d2b765df688|2018-08-28--12-41-00", # HONDA PILOT 2019 ELITE
  "b0c9d2329ad1606b|2019-01-06--10-11-23", # CHRYSLER PACIFICA HYBRID 2017
  "31390e3eb6f7c29a|2019-01-23--08-56-00", # KIA OPTIMA SX 2019
  "fd10b9a107bb2e49|2018-07-24--16-32-42", # TOYOTA C-HR 2018
  "9f7a7e50a51fb9db|2019-01-17--18-34-21", # JEEP GRAND CHEROKEE V6 2018
  "aadda448b49c99ad|2018-10-25--17-16-22", # CHEVROLET MALIBU PREMIER 2017
  "362d23d4d5bea2fa|2018-09-02--17-03-55", # TOYOTA HIGHLANDER HYBRID 2018
  "1582e1dc57175194|2018-08-15--07-46-07", # HONDA ACCORD 2018 LX 1.5T
  "fd10b9a107bb2e49|2018-07-24--20-32-08", # TOYOTA C-HR 2018
  "265007255e794bce|2018-11-24--22-08-31", # CADILLAC ATS Premium Performance 2018
  "53ac3251e03f95d7|2019-01-10--13-43-32", # HYUNDAI ELANTRA LIMITED ULTIMATE 2017
  "21aa231dee2a68bd|2018-01-30--04-54-41", # HONDA ODYSSEY 2018 EX-L
  "900ad17e536c3dc7|2018-04-12--22-02-36", # HONDA RIDGELINE 2017 BLACK EDITION
  "975b26878285314d|2018-12-25--14-42-13", # CHRYSLER PACIFICA HYBRID 2018
  "8ae193ceb56a0efe|2018-06-18--20-07-32", # TOYOTA RAV4 HYBRID 2017
  "a893a80e5c5f72c8|2019-01-14--20-02-59", # HYUNDAI GENESIS 2018
  "49c73650e65ff465|2018-11-19--16-58-04", # HOLDEN ASTRA RS-V BK 2017
  "d2d8152227f7cb82|2018-07-25--13-40-56", # TOYOTA CAMRY 2018
  "07cb8a788c31f645|2018-06-17--18-50-29", # mock
  "c9d60e5e02c04c5c|2018-01-08--16-01-49", # HONDA CR-V 2016 TOURING
  "1632088eda5e6c4d|2018-06-07--08-03-18", # HONDA CIVIC HATCHBACK 2017 SEDAN/COUPE 2019
  "fbd011384db5e669|2018-07-26--20-51-48", # TOYOTA CAMRY HYBRID 2018
]

if __name__ == "__main__":

  # TODO: add routes for untested cars and fail test if we have an untested car
  tested_cars = [keys["carFingerprint"] for route, keys in routes.items()]
  for car_model in all_known_cars():
    if car_model not in tested_cars:
      print("***** WARNING: %s not tested *****" % car_model)

  results = {}
  for route, checks in routes.items():
    if route not in non_public_routes:
      get_route_logs(route)
    elif "UNLOGGER_PATH" not in os.environ:
      continue

    for _ in range(3):
      shutil.rmtree('/data/params')
      manager.gctx = {}
      params = Params()
      params.manager_start()
      if route in passive_routes:
        params.put("Passive", "1")
      else:
        params.put("Passive", "0")

      print("testing ", route, " ", checks['carFingerprint'])
      print("Preparing processes")
      manager.prepare_managed_process("radard")
      manager.prepare_managed_process("controlsd")
      manager.prepare_managed_process("plannerd")
      print("Starting processes")
      manager.start_managed_process("radard")
      manager.start_managed_process("controlsd")
      manager.start_managed_process("plannerd")
      time.sleep(2)

      # Start unlogger
      print("Start unlogger")
      if route in non_public_routes:
        unlogger_cmd = [os.path.join(BASEDIR, os.environ['UNLOGGER_PATH']), '%s' % route, '--disable', 'frame,plan,pathPlan,liveLongitudinalMpc,radarState,controlsState,liveTracks,liveMpc,sendcan,carState,carControl,carEvents,carParams', '--no-interactive']
      else:
        unlogger_cmd = [os.path.join(BASEDIR, 'tools/replay/unlogger.py'), '%s' % route, '/tmp', '--disable', 'frame,plan,pathPlan,liveLongitudinalMpc,radarState,controlsState,liveTracks,liveMpc,sendcan,carState,carControl,carEvents,carParams', '--no-interactive']
      unlogger = subprocess.Popen(unlogger_cmd, preexec_fn=os.setsid)

      print("Check sockets")
      controls_state_result = wait_for_socket('controlsState', timeout=30)
      radarstate_result = wait_for_socket('radarState', timeout=30)
      plan_result = wait_for_socket('plan', timeout=30)

      if route not in passive_routes:  # TODO The passive routes have very flaky models
        path_plan_result = wait_for_socket('pathPlan', timeout=30)
      else:
        path_plan_result = True

      carstate_result = wait_for_socket('carState', timeout=30)

      print("Check if everything is running")
      running = manager.get_running()
      controlsd_running = running['controlsd'].is_alive()
      radard_running = running['radard'].is_alive()
      plannerd_running = running['plannerd'].is_alive()

      manager.kill_managed_process("controlsd")
      manager.kill_managed_process("radard")
      manager.kill_managed_process("plannerd")
      os.killpg(os.getpgid(unlogger.pid), signal.SIGTERM)

      sockets_ok = all([
        controls_state_result, radarstate_result, plan_result, path_plan_result, carstate_result,
        controlsd_running, radard_running, plannerd_running
      ])
      params_ok = True
      failures = []

      if not controlsd_running:
        failures.append('controlsd')
      if not radard_running:
        failures.append('radard')
      if not radarstate_result:
        failures.append('radarState')
      if not controls_state_result:
        failures.append('controlsState')
      if not plan_result:
        failures.append('plan')
      if not path_plan_result:
        failures.append('pathPlan')

      try:
        car_params = car.CarParams.from_bytes(params.get("CarParams"))
        for k, v in checks.items():
          if not v == getattr(car_params, k):
            params_ok = False
            failures.append(k)
      except:
        params_ok = False

      if sockets_ok and params_ok:
        print("Success")
        results[route] = True, failures
        break
      else:
        print("Failure")
        results[route] = False, failures

      time.sleep(2)

  for route in results:
    print(results[route])
  Params().put("Passive", "0")   # put back not passive to not leave the params in an unintended state
  if not all(passed for passed, _ in results.values()):
    print("TEST FAILED")
    sys.exit(1)
  else:
    print("TEST SUCCESSFUL")
