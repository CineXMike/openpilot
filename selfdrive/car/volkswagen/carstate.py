import numpy as np
from common.kalman.simple_kalman import KF1D
from selfdrive.config import Conversions as CV
from opendbc.can.parser import CANParser
from opendbc.can.can_define import CANDefine
from selfdrive.car.volkswagen.values import DBC, GEAR, TRANS, BUTTON_STATES, NETWORK_MODEL
from selfdrive.car.volkswagen.carcontroller import CarControllerParams

def get_gateway_can_parser(CP, canbus, networkModel):

  if networkModel == NETWORK_MODEL.MQB:
    signals = [
      # sig_name, sig_address, default
      ("LWI_Lenkradwinkel", "LWI_01", 0),               # Absolute steering angle
      ("LWI_VZ_Lenkradwinkel", "LWI_01", 0),            # Steering angle sign
      ("LWI_Lenkradw_Geschw", "LWI_01", 0),             # Absolute steering rate
      ("LWI_VZ_Lenkradw_Geschw", "LWI_01", 0),          # Steering rate sign
      ("ESP_VL_Radgeschw_02", "ESP_19", 0),             # ABS wheel speed, front left
      ("ESP_VR_Radgeschw_02", "ESP_19", 0),             # ABS wheel speed, front right
      ("ESP_HL_Radgeschw_02", "ESP_19", 0),             # ABS wheel speed, rear left
      ("ESP_HR_Radgeschw_02", "ESP_19", 0),             # ABS wheel speed, rear right
      ("ESP_Gierrate", "ESP_02", 0),                    # Absolute yaw rate
      ("ESP_VZ_Gierrate", "ESP_02", 0),                 # Yaw rate sign
      ("ZV_FT_offen", "Gateway_72", 0),                 # Door open, driver
      ("ZV_BT_offen", "Gateway_72", 0),                 # Door open, passenger
      ("ZV_HFS_offen", "Gateway_72", 0),                # Door open, rear left
      ("ZV_HBFS_offen", "Gateway_72", 0),               # Door open, rear right
      ("ZV_HD_offen", "Gateway_72", 0),                 # Trunk or hatch open
      ("BH_Blinker_li", "Gateway_72", 0),               # Left turn signal on
      ("BH_Blinker_re", "Gateway_72", 0),               # Right turn signal on
      ("BCM1_Rueckfahrlicht_Schalter", "Gateway_72", 0),# Reverse light switch
      ("GE_Fahrstufe", "Getriebe_11", 0),               # Auto trans gear selector position
      ("GearPosition","EV_Gearshift", 0),               # EV gear selector position
      ("AB_Gurtschloss_FA", "Airbag_02", 0),            # Seatbelt status, driver
      ("AB_Gurtschloss_BF", "Airbag_02", 0),            # Seatbelt status, passenger
      ("ESP_Fahrer_bremst", "ESP_05", 0),               # Brake pedal pressed
      ("ESP_Status_Bremsdruck", "ESP_05", 0),           # Brakes applied
      ("ESP_Bremsdruck", "ESP_05", 0),                  # Brake pressure applied
      ("MO_Fahrpedalrohwert_01", "Motor_20", 0),        # Accelerator pedal value
      ("MO_Kuppl_schalter", "Motor_14", 0),             # Clutch switch
      ("Driver_Strain", "EPS_01", 0),                   # Absolute driver torque input
      ("Driver_Strain_VZ", "EPS_01", 0),                # Driver torque input sign
      ("HCA_Ready", "EPS_01", 0),                       # Steering rack HCA support configured
      ("ESP_Tastung_passiv", "ESP_21", 0),              # Stability control disabled
      ("KBI_MFA_v_Einheit_02", "Einheiten_01", 0),      # MPH vs KMH speed display
      ("KBI_Handbremse", "Kombi_01", 0),                # Manual handbrake applied
      ("TSK_Fahrzeugmasse_02", "Motor_16", 0),          # Estimated vehicle mass from drivetrain coordinator
      ("GRA_Hauptschalter", "GRA_ACC_01", 0),           # ACC button, on/off
      ("GRA_Abbrechen", "GRA_ACC_01", 0),               # ACC button, cancel
      ("GRA_Tip_Setzen", "GRA_ACC_01", 0),              # ACC button, set
      ("GRA_Tip_Hoch", "GRA_ACC_01", 0),                # ACC button, increase or accel
      ("GRA_Tip_Runter", "GRA_ACC_01", 0),              # ACC button, decrease or decel
      ("GRA_Tip_Wiederaufnahme", "GRA_ACC_01", 0),      # ACC button, resume
      ("GRA_Verstellung_Zeitluecke", "GRA_ACC_01", 0),  # ACC button, time gap adj
      ("GRA_Typ_Hauptschalter", "GRA_ACC_01", 0),       # ACC main button type
      ("GRA_Tip_Stufe_2", "GRA_ACC_01", 0),             # unknown related to stalk type
      ("GRA_ButtonTypeInfo", "GRA_ACC_01", 0),          # unknown related to stalk type
      ("COUNTER", "GRA_ACC_01", 0),                     # GRA_ACC_01 CAN message counter
    ]

    checks = [
      # sig_address, frequency
      ("LWI_01", 100),          # From J500 Steering Assist with integrated sensors
      ("EPS_01", 100),          # From J500 Steering Assist with integrated sensors
      ("ESP_19", 100),          # From J104 ABS/ESP controller
      ("ESP_05", 50),           # From J104 ABS/ESP controller
      ("ESP_21", 50),           # From J104 ABS/ESP controller
      ("Motor_20", 50),         # From J623 Engine control module
      ("GRA_ACC_01", 33),       # From J??? steering wheel control buttons
      ("Getriebe_11", 20),      # From J743 Auto transmission control module
      ("Gateway_72", 10),       # From J533 CAN gateway (aggregated data)
      ("Motor_14", 10),         # From J623 Engine control module
      ("Airbag_02", 5),         # From J234 Airbag control module
      ("Kombi_01", 2),          # From J285 Instrument cluster
      ("Motor_16", 2),          # From J623 Engine control module
      ("Einheiten_01", 1),      # From J??? not known if gateway, cluster, or BCM
    ]

  elif networkModel == NETWORK_MODEL.PQ:
    # this function generates lists for signal, messages and initial values
    signals = [
      # sig_name, sig_address, default
      ("Steering_Angle", "EPS_1", 0),             # Absolute steering angle
      ("Steering_Angle_Sign", "EPS_1", 0),        # Steering angle sign
      ("Lenkradwinkel_Geschwindigkeit", "Lenkwinkel_1", 0), # Absolute steering rate
      ("Lenkradwinkel_Geschwindigkeit_S", "Lenkwinkel_1", 0), # Steering rate sign
      ("Radgeschw__VL_4_1", "Bremse_3", 0),             # ABS wheel speed, front left
      ("Radgeschw__VR_4_1", "Bremse_3", 0),             # ABS wheel speed, front right
      ("Radgeschw__HL_4_1", "Bremse_3", 0),             # ABS wheel speed, rear left
      ("Radgeschw__HR_4_1", "Bremse_3", 0),             # ABS wheel speed, rear right
      ("Giergeschwindigkeit", "Bremse_5", 0),           # Absolute yaw rate
      ("Vorzeichen_der_Giergeschwindigk", "Bremse_5", 0), # Yaw rate sign
      ("Fahrertuerkontakt", "Gateway_Komfort_1", 0),    # Door open, driver
      # Passenger and rear door states don't seem to be available on extended can
      ("Blinker_links_4_1", "Kombi_1", 0),              # Left turn signal on
      ("Blinker_rechts_4_1", "Kombi_1", 0),             # Right turn signal on
      ("Waehlhebelposition__Getriebe_1_", "Getriebe_1", 0), # Transmission gear selector position
      ("Gurtschalter_Fahrer", "Airbag_1", 0),           # Seatbelt status, driver
      ("Gurtschalter_Beifahrer", "Airbag_1", 0),        # Seatbelt status, passenger
      ("Bremstestschalter", "Motor_2", 0),              # Brake pedal pressed (brake light test switch)
      ("Bremslichtschalter", "Motor_2", 0),             # Brakes applied (brake light switch)
      ("Bremsdruck", "Bremse_5", 0),                    # Brake pressure applied
      ("Vorzeichen_Bremsdruck", "Bremse_5", 0),         # Brake pressure applied sign (???)
      ("Fahrpedalwert_oder_Drosselklapp", "Motor_1", 0), # Accelerator pedal value
      ("Driver_Torque", "EPS_1", 0),                    # Absolute driver torque input
      ("Driver_Torque_Sign", "EPS_1", 0),               # Driver torque input sign
      # ("HCA_Ready", "EPS_01", 0),                     # Steering rack HCA support configured
      ("ESP_Passiv_getastet", "Bremse_1", 0),           # Stability control disabled
      ("MFA_v_Einheit_02", "Einheiten_1", 0),           # MPH vs KMH speed display
      ("Bremsinfo", "Kombi_1", 0),                      # Manual handbrake applied
      # ("TSK_Fahrzeugmasse_02", "Motor_16", 0),        # Estimated vehicle mass from drivetrain coordinator
      ("GRA_Status", "Motor_2", 0),                     # ACC engagement status
      ("Hauptschalter", "GRA_neu", 0),                  # ACC button, on/off
      ("Abbrechen", "GRA_neu", 0),                      # ACC button, cancel
      ("Setzen", "GRA_neu", 0),                         # ACC button, set
      ("Lang_Tip_up", "GRA_neu", 0),                    # ACC button, increase or accel, long press
      ("Lang_Tip_down", "GRA_neu", 0),                  # ACC button, decrease or decel, long press
      ("Kurz_Tip_up", "GRA_neu", 0),                    # ACC button, increase or accel, short press
      ("Kurz_Tip_down", "GRA_neu", 0),                  # ACC button, decrease or decel, short press
      ("Wiederaufnahme", "GRA_neu", 0),                 # ACC button, resume
      ("Zeitlueckenverstellung", "GRA_neu", 0),         # ACC button, time gap adj
      ("Rechtslenker", "Systeminfo_1", 0),              # RHD vs LHD vehicle construction
      ("Frei_Gateway_Komfort_1_4", "Gateway_Komfort_1", 16), # Blinker Signals
    ]

    checks = [
      # sig_address, frequency
      ("Bremse_3", 100),        # From J104 ABS/ESP controller
      ("Bremse_5", 50),         # From J104 ABS/ESP controller
      ("EPS_1", 100),           # From J500 Steering Assist with integrated sensors
      ("Getriebe_1", 100),      # From J743 Auto transmission control module
      ("Lenkwinkel_1", 100),    # From J500 Steering Assist with integrated sensors
      ("Airbag_1", 50),         # From J234 Airbag control module
      ("GRA_neu", 50),          # From J??? steering wheel control buttons
      ("Kombi_1", 50),          # From J285 Instrument cluster
      ("Motor_2", 50),          # From J623 Engine control module
      ("Systeminfo_1", 10),     # From J??? not known if gateway, cluster, or BCM
      ("Einheiten_1", 1),       # From ???
      ("Gateway_Komfort_1", 1), # From ???
    ]

  else:
    signals = []
    checks = []

  return CANParser(DBC[CP.carFingerprint]['pt'], signals, checks, canbus.gateway)

def get_extended_can_parser(CP, canbus, networkModel):

  if networkModel == NETWORK_MODEL.MQB:
    signals = [
      # sig_name, sig_address, default
      ("ACC_Status_ACC", "ACC_06", 0),                          # ACC engagement status
      ("ACC_Typ", "ACC_06", 0),                                 # ACC type (follow to stop, stop&go)
      ("SetSpeed", "ACC_02", 0),                                # ACC set speed
    ]

    checks = [
      # sig_address, frequency
      ("ACC_06", 50),                                           # From J428 ACC radar control module
      ("ACC_02", 17),                                           # From J428 ACC radar control module
    ]

  elif networkModel == NETWORK_MODEL.PQ:
    signals = [
      ("GRA_Set_Speed", "ACC_XX02", 0),                 # ACC cruise set point from J428 ACC radar
    ]

    checks = [
      ("ACC_XX02", 50),         # From J428 ACC radar control module
    ]

  else:
    signals = []
    checks = []

  return CANParser(DBC[CP.carFingerprint]['pt'], signals, checks, canbus.extended)

def get_mqb_cam_can_parser(CP, canbus):

  signals = [
    # sig_name, sig_address, default
    ("Kombi_Lamp_Green", "LDW_02", 0),            # Lane Assist status LED
  ]

  checks = [
    # sig_address, frequency
    ("LDW_02", 10)        # From R242 Driver assistance camera
  ]

  return CANParser(DBC[CP.carFingerprint]['pt'], signals, checks, canbus.cam)

def parse_gear_shifter(gear, vals):
  # Return mapping of gearshift position to selected gear.

  val_to_capnp = {'P': GEAR.park, 'R': GEAR.reverse, 'N': GEAR.neutral,
                  'D': GEAR.drive, 'E': GEAR.eco, 'S': GEAR.sport, 'T': GEAR.manumatic}
  try:
    return val_to_capnp[vals[gear]]
  except KeyError:
    return "unknown"

class CarState():
  def __init__(self, CP, canbus, networkModel):
    # initialize can parser
    self.CP = CP
    self.car_fingerprint = CP.carFingerprint
    self.can_define = CANDefine(DBC[CP.carFingerprint]['pt'])

    if networkModel == NETWORK_MODEL.MQB:
      self.shifter_values = self.can_define.dv["Getriebe_11"]['GE_Fahrstufe']
      self.update = self.update_mqb
    elif networkModel == NETWORK_MODEL.PQ:
      self.shifter_values = self.can_define.dv["Getriebe_1"]['Waehlhebelposition__Getriebe_1_']
      self.update = self.update_pq

    self.buttonStates = BUTTON_STATES.copy()

    # vEgo Kalman filter
    dt = 0.01
    self.v_ego_kf = KF1D(x0=[[0.], [0.]],
                         A=[[1., dt], [0., 1.]],
                         C=[1., 0.],
                         K=[[0.12287673], [0.29666309]])

  def update_mqb(self, gw_cp, ex_cp, transType):
    # Update vehicle speed and acceleration from ABS wheel speeds.
    self.wheelSpeedFL = gw_cp.vl["ESP_19"]['ESP_VL_Radgeschw_02'] * CV.KPH_TO_MS
    self.wheelSpeedFR = gw_cp.vl["ESP_19"]['ESP_VR_Radgeschw_02'] * CV.KPH_TO_MS
    self.wheelSpeedRL = gw_cp.vl["ESP_19"]['ESP_HL_Radgeschw_02'] * CV.KPH_TO_MS
    self.wheelSpeedRR = gw_cp.vl["ESP_19"]['ESP_HR_Radgeschw_02'] * CV.KPH_TO_MS

    self.vEgoRaw = float(np.mean([self.wheelSpeedFL, self.wheelSpeedFR, self.wheelSpeedRL, self.wheelSpeedRR]))
    v_ego_x = self.v_ego_kf.update(self.vEgoRaw)
    self.vEgo = float(v_ego_x[0])
    self.aEgo = float(v_ego_x[1])
    self.standstill = self.vEgoRaw < 0.1

    # Update steering angle, rate, yaw rate, and driver input torque. VW send
    # the sign/direction in a separate signal so they must be recombined.
    self.steeringAngle = gw_cp.vl["LWI_01"]['LWI_Lenkradwinkel'] * (1,-1)[int(gw_cp.vl["LWI_01"]['LWI_VZ_Lenkradwinkel'])]
    self.steeringRate = gw_cp.vl["LWI_01"]['LWI_Lenkradw_Geschw'] * (1,-1)[int(gw_cp.vl["LWI_01"]['LWI_VZ_Lenkradwinkel'])]
    self.steeringTorque = gw_cp.vl["EPS_01"]['Driver_Strain'] * (1,-1)[int(gw_cp.vl["EPS_01"]['Driver_Strain_VZ'])]
    self.steeringPressed = abs(self.steeringTorque) > CarControllerParams.STEER_DRIVER_ALLOWANCE
    self.yawRate = gw_cp.vl["ESP_02"]['ESP_Gierrate'] * (1,-1)[int(gw_cp.vl["ESP_02"]['ESP_VZ_Gierrate'])] * CV.DEG_TO_RAD

    # Update gas, brakes, and gearshift.
    self.gas = gw_cp.vl["Motor_20"]['MO_Fahrpedalrohwert_01'] / 100.0
    self.gasPressed = self.gas > 0
    self.brake = gw_cp.vl["ESP_05"]['ESP_Bremsdruck'] / 250.0 # FIXME: this is pressure in Bar, not sure what OP expects
    self.brakePressed = bool(gw_cp.vl["ESP_05"]['ESP_Fahrer_bremst'])
    self.brakeLights = bool(gw_cp.vl["ESP_05"]['ESP_Status_Bremsdruck'])

    # Update gear and/or clutch position data based on transmission type.
    if transType == TRANS.automatic:
      self.clutchPressed = False
      detectedGear = gw_cp.vl["Getriebe_11"]['GE_Fahrstufe']
    elif transType == TRANS.unknown: # FIXME: abusing trans type unknown for EV because it's the only way to get info from get_params w/o refactoring
      self.clutchPressed = False
      detectedGear = gw_cp.vl["EV_Gearshift"]['GearPosition']
    elif transType == TRANS.manual:
      self.clutchPressed = not gw_cp.vl["Motor_14"]['MO_Kuppl_schalter']
      self.reverseLight = gw_cp.vl["Gateway_72"]['BCM1_Rueckfahrlicht_Schalter']
      self.handBrakeSet = gw_cp.vl["Kombi_01"]['KBI_Handbremse'] # FIXME: do an EPB check here too
      if self.reverseLight:
        detectedGear = "R"
      elif self.standstill and self.handBrakeSet:
        detectedGear = "P"
      elif self.clutchPressed:
        detectedGear = "N"
      else:
        detectedGear = "D"
    else:
      detectedGear = None
    self.gearShifter = parse_gear_shifter(detectedGear, self.shifter_values)

    # Update door and trunk/hatch lid open status.
    self.doorOpen = any([gw_cp.vl["Gateway_72"]['ZV_FT_offen'],
                         gw_cp.vl["Gateway_72"]['ZV_BT_offen'],
                         gw_cp.vl["Gateway_72"]['ZV_HFS_offen'],
                         gw_cp.vl["Gateway_72"]['ZV_HBFS_offen'],
                         gw_cp.vl["Gateway_72"]['ZV_HD_offen']])

    # Update seatbelt fastened status.
    self.seatbeltUnlatched = False if gw_cp.vl["Airbag_02"]["AB_Gurtschloss_FA"] == 3 else True

    # Update driver preference for metric. VW stores many different unit
    # preferences, including separate units for for distance vs. speed.
    # We use the speed preference for OP.
    self.displayMetricUnits = not gw_cp.vl["Einheiten_01"]["KBI_MFA_v_Einheit_02"]

    # Update ACC radar status.
    accStatus = ex_cp.vl["ACC_06"]['ACC_Status_ACC']
    if accStatus == 1:
      # ACC okay but disabled
      self.accFault = False
      self.accAvailable = False
      self.accEnabled = False
    elif accStatus == 2:
      # ACC okay and enabled, but not currently engaged
      self.accFault = False
      self.accAvailable = True
      self.accEnabled = False
    elif accStatus in [3, 4, 5]:
      # ACC okay and enabled, currently engaged and regulating speed (3) or engaged with driver accelerating (4) or overrun (5)
      self.accFault = False
      self.accAvailable = True
      self.accEnabled = True
    else:
      # ACC fault of some sort. Seen statuses 6 or 7 for CAN comms disruptions, visibility issues, etc.
      self.accFault = True
      self.accAvailable = False
      self.accEnabled = False

    # Update ACC setpoint. When the setpoint is zero or there's an error, the
    # radar sends a set-speed of ~90.69 m/s / 203mph.
    self.accSetSpeed = ex_cp.vl["ACC_02"]['SetSpeed']
    if self.accSetSpeed > 90: self.accSetSpeed = 0

    # Update control button states for turn signals and ACC controls.
    self.buttonStates["leftBlinker"] = bool(gw_cp.vl["Gateway_72"]['BH_Blinker_li'])
    self.buttonStates["leftBlinker"] = bool(gw_cp.vl["Gateway_72"]['BH_Blinker_re'])
    self.buttonStates["accelCruise"] = bool(gw_cp.vl["GRA_ACC_01"]['GRA_Tip_Hoch'])
    self.buttonStates["decelCruise"] = bool(gw_cp.vl["GRA_ACC_01"]['GRA_Tip_Runter'])
    self.buttonStates["cancel"] = bool(gw_cp.vl["GRA_ACC_01"]['GRA_Abbrechen'])
    self.buttonStates["setCruise"] = bool(gw_cp.vl["GRA_ACC_01"]['GRA_Tip_Setzen'])
    self.buttonStates["resumeCruise"] = bool(gw_cp.vl["GRA_ACC_01"]['GRA_Tip_Wiederaufnahme'])
    self.buttonStates["gapAdjustCruise"] = bool(gw_cp.vl["GRA_ACC_01"]['GRA_Verstellung_Zeitluecke'])

    # Read ACC hardware button type configuration info that has to pass thru
    # to the radar. Ends up being different for steering wheel buttons vs
    # third stalk type controls.
    self.graHauptschalter = gw_cp.vl["GRA_ACC_01"]['GRA_Hauptschalter']
    self.graTypHauptschalter = gw_cp.vl["GRA_ACC_01"]['GRA_Typ_Hauptschalter']
    self.graButtonTypeInfo = gw_cp.vl["GRA_ACC_01"]['GRA_ButtonTypeInfo']
    self.graTipStufe2 = gw_cp.vl["GRA_ACC_01"]['GRA_Tip_Stufe_2']
    # Pick up the GRA_ACC_01 CAN message counter so we can sync to it for
    # later cruise-control button spamming.
    self.graMsgBusCounter = gw_cp.vl["GRA_ACC_01"]['COUNTER']

    # Check to make sure the electric power steering rack is configured to
    # accept and respond to HCA_01 messages and has not encountered a fault.
    self.steeringFault = not gw_cp.vl["EPS_01"]["HCA_Ready"]

    # Additional safety checks performed in CarInterface.
    self.parkingBrakeSet = bool(gw_cp.vl["Kombi_01"]['KBI_Handbremse']) # FIXME: need to include an EPB check as well
    self.stabilityControlDisabled = gw_cp.vl["ESP_21"]['ESP_Tastung_passiv']

  def update_pq(self, gw_cp, ex_cp, transType):
    # Update vehicle speed and acceleration from ABS wheel speeds.
    self.wheelSpeedFL = gw_cp.vl["Bremse_3"]['Radgeschw__VL_4_1'] * CV.KPH_TO_MS
    self.wheelSpeedFR = gw_cp.vl["Bremse_3"]['Radgeschw__VR_4_1'] * CV.KPH_TO_MS
    self.wheelSpeedRL = gw_cp.vl["Bremse_3"]['Radgeschw__HL_4_1'] * CV.KPH_TO_MS
    self.wheelSpeedRR = gw_cp.vl["Bremse_3"]['Radgeschw__HR_4_1'] * CV.KPH_TO_MS

    self.vEgoRaw = float(np.mean([self.wheelSpeedFL, self.wheelSpeedFR, self.wheelSpeedRL, self.wheelSpeedRR]))
    v_ego_x = self.v_ego_kf.update(self.vEgoRaw)
    self.vEgo = float(v_ego_x[0])
    self.aEgo = float(v_ego_x[1])
    self.standstill = self.vEgoRaw < 0.1

    # Update steering angle, rate, yaw rate, and driver input torque. VW send
    # the sign/direction in a separate signal so they must be recombined.
    self.steeringAngle = gw_cp.vl["EPS_1"]['Steering_Angle'] * (1,-1)[int(gw_cp.vl["EPS_1"]['Steering_Angle_Sign'])]
    self.steeringRate = gw_cp.vl["Lenkwinkel_1"]['Lenkradwinkel_Geschwindigkeit'] * (1,-1)[int(gw_cp.vl["Lenkwinkel_1"]['Lenkradwinkel_Geschwindigkeit_S'])]
    self.steeringTorque = gw_cp.vl["EPS_1"]['Driver_Torque'] * (1,-1)[int(gw_cp.vl["EPS_1"]['Driver_Torque_Sign'])]
    self.steeringPressed = abs(self.steeringTorque) > CarControllerParams.STEER_DRIVER_ALLOWANCE
    self.yawRate = gw_cp.vl["Bremse_5"]['Giergeschwindigkeit'] * (1,-1)[int(gw_cp.vl["Bremse_5"]['Vorzeichen_der_Giergeschwindigk'])] * CV.DEG_TO_RAD

    # Update gas, brakes, and gearshift.
    self.gas = gw_cp.vl["Motor_1"]['Fahrpedalwert_oder_Drosselklapp'] / 100.0
    self.gasPressed = self.gas > 0
    self.brake = gw_cp.vl["Bremse_5"]['Bremsdruck'] / 250.0 # FIXME: this is pressure in Bar, not sure what OP expects
    self.brakePressed = bool(gw_cp.vl["Motor_2"]['Bremstestschalter'])
    self.brakeLights = bool(gw_cp.vl["Motor_2"]['Bremslichtschalter'])

    # Update gear and/or clutch position data based on transmission type.
    if transType == TRANS.automatic:
      self.clutchPressed = False
      detectedGear = gw_cp.vl["Getriebe_1"]['Waehlhebelposition__Getriebe_1_']
    # FIXME: Need to find some more signals to do manual trans on PQ
    else:
      detectedGear = None
    self.gearShifter = parse_gear_shifter(detectedGear, self.shifter_values)

    # Update door and trunk/hatch lid open status.
    self.doorOpen = bool(gw_cp.vl["Gateway_Komfort_1"]['Fahrertuerkontakt'])

    # Update seatbelt fastened status.
    self.seatbeltUnlatched = not bool(gw_cp.vl["Airbag_1"]["Gurtschalter_Fahrer"])

    # Update driver preference for metric. VW stores many different unit
    # preferences, including separate units for for distance vs. speed.
    # We use the speed preference for OP.
    self.displayMetricUnits = not gw_cp.vl["Einheiten_1"]["MFA_v_Einheit_02"]

    # Update ACC radar status.
    # FIXME: This is unfinished and not fully correct, need to improve further
    self.accFault = False  # need a detection mechanism for radar obstructed or otherwise faulted out
    self.accAvailable = bool(gw_cp.vl["GRA_neu"]['Hauptschalter'])
    if gw_cp.vl["Motor_2"]['GRA_Status'] in [1, 2]:
      self.accEnabled = True
    else:
      self.accEnabled = False

    # Update ACC setpoint. When the setpoint reads as 255, the driver has not
    # yet established an ACC setpoint, so treat it as zero.
    self.accSetSpeed = ex_cp.vl["ACC_XX02"]['GRA_Set_Speed']
    if self.accSetSpeed == 255:
      self.accSetSpeed = 0

    # Update control button states for turn signals and ACC controls.
    newBlinkerState = gw_cp.vl["Gateway_Komfort_1"]['Frei_Gateway_Komfort_1_4']

    self.buttonStates["leftBlinker"] = True if newBlinkerState == 17 else False
    self.buttonStates["rightBlinker"] = True if newBlinkerState == 18 else False
    self.buttonStates["accelCruise"] = bool(gw_cp.vl["GRA_neu"]['Kurz_Tip_up']) or bool(gw_cp.vl["GRA_neu"]['Lang_Tip_up'])
    self.buttonStates["decelCruise"] = bool(gw_cp.vl["GRA_neu"]['Kurz_Tip_down']) or bool(gw_cp.vl["GRA_neu"]['Lang_Tip_down'])
    self.buttonStates["cancel"] = bool(gw_cp.vl["GRA_neu"]['Abbrechen'])
    self.buttonStates["setCruise"] = bool(gw_cp.vl["GRA_neu"]['Setzen'])
    self.buttonStates["resumeCruise"] = bool(gw_cp.vl["GRA_neu"]['Wiederaufnahme'])
    self.buttonStates["gapAdjustCruise"] = bool(gw_cp.vl["GRA_neu"]['Zeitlueckenverstellung'])

    # Read ACC hardware button type configuration info that has to pass thru
    # to the radar. Ends up being different for steering wheel buttons vs
    # third stalk type controls.
    # TODO: Check to see what info we need to passthru and spoof on PQ
    self.graHauptschalter = gw_cp.vl["GRA_neu"]['Hauptschalter']
    self.graTypHauptschalter = False
    self.graButtonTypeInfo = False
    self.graTipStufe2 = False
    # Pick up the GRA_ACC_01 CAN message counter so we can sync to it for
    # later cruise-control button spamming.
    # FIXME: will need msg counter and checksum algo to spoof GRA_neu
    self.graMsgBusCounter = 0

    # Check to make sure the electric power steering rack is configured to
    # accept and respond to HCA_01 messages and has not encountered a fault.
    # FIXME: Need to check for EPS coding validity and errors
    self.steeringFault = False

    # Additional safety checks performed in CarInterface.
    self.parkingBrakeSet = bool(gw_cp.vl["Kombi_1"]['Bremsinfo']) # FIXME: need to include an EPB check as well
    self.stabilityControlDisabled = gw_cp.vl["Bremse_1"]['ESP_Passiv_getastet']