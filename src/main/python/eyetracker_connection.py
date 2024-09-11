import os
import pickle
import time
import tkinter
from datetime import datetime

import tobii_research as tobii

# duration of data collection
TIME = 60

LICENSE_PATH = r"path/to/license"

FOLDER_PATH = r"path/to/output/folder"

DATA = list()


def create_filename():
    # if the folder data does not exist, create it
    if not os.path.exists(FOLDER_PATH):
        os.makedirs(FOLDER_PATH)
    # create file name with timestamp (just until milliseconds - that's why it's user '[-3]')
    filename = FOLDER_PATH + r"\GAZE-DATA-" + datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")[:-3] + ".bin"

    return filename


def apply_license(eyetracker):
    """
    APPLY LICENSE TO AN EYE-TRACKER
    """
    print("Applying license from {0}.".format(LICENSE_PATH))
    with open(LICENSE_PATH, "rb") as f:
        license = f.read()
    failed_licenses_applied_as_list_of_keys = eyetracker.apply_licenses([tobii.LicenseKey(license)])
    failed_licenses_applied_as_list_of_bytes = eyetracker.apply_licenses([license])
    failed_licenses_applied_as_key = eyetracker.apply_licenses(tobii.LicenseKey(license))
    failed_licenses_applied_as_bytes = eyetracker.apply_licenses(license)
    if len(failed_licenses_applied_as_list_of_keys) == 0:
        print("Successfully applied license from list of keys.")
    else:
        print("Failed to apply license from list of keys. Validation result: {0}.".format(failed_licenses_applied_as_list_of_keys[0].validation_result))
        exit(2)
    if len(failed_licenses_applied_as_list_of_bytes) == 0:
        print("Successfully applied license from list of bytes.")
    else:
        print("Failed to apply license from list of bytes. Validation result: {0}.".format(failed_licenses_applied_as_list_of_bytes[0].validation_result))
        exit(2)
    if len(failed_licenses_applied_as_key) == 0:
        print("Successfully applied license from single key.")
    else:
        print("Failed to apply license from single key. Validation result: {0}.".format(failed_licenses_applied_as_key[0].validation_result))
        exit(2)
    if len(failed_licenses_applied_as_bytes) == 0:
        print("Successfully applied license from bytes object.")
    else:
        print("Failed to apply license from bytes object. Validation result: {0}.". format(failed_licenses_applied_as_bytes[0].validation_result))
        exit(2)


def gaze_data_callback(gaze_data):
    """
    THIS FUNCTION DETERMINES WHAT IS DONE WITH THE DATA COLLECTED.
    THIS IS THE STRUCTURE OF THE DATA COLLECTED:
        self.__left = EyeData(
                data["left_gaze_point_on_display_area"],
                data["left_gaze_point_in_user_coordinate_system"],
                data["left_gaze_point_validity"],
                data["left_pupil_diameter"],
                data["left_pupil_validity"],
                data["left_gaze_origin_in_user_coordinate_system"],
                data["left_gaze_origin_in_trackbox_coordinate_system"],
                data["left_gaze_origin_validity"])

        self.__right = EyeData(
                data["right_gaze_point_on_display_area"],
                data["right_gaze_point_in_user_coordinate_system"],
                data["right_gaze_point_validity"],
                data["right_pupil_diameter"],
                data["right_pupil_validity"],
                data["right_gaze_origin_in_user_coordinate_system"],
                data["right_gaze_origin_in_trackbox_coordinate_system"],
                data["right_gaze_origin_validity"])

        self.__device_time_stamp = data["device_time_stamp"]

        self.__system_time_stamp = data["system_time_stamp"]
    """
    # just store the data with time correction (writing to file is too slow, it would compromise the frequency of the eye-tracker)
    DATA.append(gaze_data)


def get_data_with_pupil():
    """
    GET DATA FROM EYE-TRACKER AND STORE IT IN A FILE (WITH PUPIL DIAMETER)
    """
    # look for connected eye-trackers
    found_eyetrackers = tobii.find_all_eyetrackers()

    # if there are eye-trackers
    if found_eyetrackers:
        # create filename
        filename = create_filename()

        # get screen size
        root_visualize = tkinter.Tk()
        width = root_visualize.winfo_screenwidth()
        height = root_visualize.winfo_screenheight()
        root_visualize.deiconify()

        # print eye-tracker data
        eyetracker = found_eyetrackers[0]
        print("Address: {}; Model: {}; Name: {}; SN: {}.".format(eyetracker.address, eyetracker.model, eyetracker.device_name, eyetracker.serial_number))

        # apply licence
        apply_license(eyetracker)

        # timestamp correction
        now_ns = time.time_ns()  # Time in nanoseconds
        now_ms = int(now_ns / 1000000)
        timestamp_correction = now_ms - int(tobii.get_system_time_stamp() / 1000)
        DATA.append(timestamp_correction)

        # get data
        eyetracker.subscribe_to(tobii.EYETRACKER_GAZE_DATA, gaze_data_callback, as_dictionary=True)

        # data collection duration
        time.sleep(TIME)
        eyetracker.unsubscribe_from(tobii.EYETRACKER_GAZE_DATA, gaze_data_callback)

        # write data to file
        with open(filename, "wb") as file:
            pickle.dump(DATA, file)

        return timestamp_correction

    # if there are no eye-trackers
    else:
        print("No eye-trackers found!")
        exit(1)
