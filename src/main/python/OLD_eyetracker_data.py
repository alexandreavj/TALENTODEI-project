import glob
import io
import os
import pickle
import tkinter
import turtle

import numpy as np
from PIL import Image


def get_file_last_alphabetical_order(path_to_folder, extension):
    """
    :param path_to_folder: path to the folder containing the files
    :param extension: file extension
    :return: path to last file (alphabetical order) or None
    """
    files = glob.glob(path_to_folder + "\\*" + extension)
    sorted_files = sorted(files)

    return sorted_files[-1]


def read_file_gaze(filepath):
    with open(filepath, "r") as file:
        lines = file.readlines()

    data = np.array([[float(lines[i].strip()), float(lines[i + 1].strip()), int(lines[i + 2].strip())]
                     for i in range(0, len(lines), 3)],
                    dtype=np.uint64)

    return data


def read_file_gaze_pupil(filepath):
    with open(filepath, "rb") as file:
        data = pickle.load(file)

    return data[0], data[1:]


def get_rectangles_cards_interface_P1(grid_rect, rectangle_size, resolution_window, distance_between_cards):
    root_rect = tkinter.Tk()
    width = root_rect.winfo_screenwidth()
    height = root_rect.winfo_screenheight()
    root_rect.deiconify()

    list_rectangles_coords_on_screen = []
    for j in range(grid_rect[1]):
        for k in range(grid_rect[0]):
            x = ((width / 2) - (resolution_window[0] / 2)) + (((k + 1) * distance_between_cards) + (k * rectangle_size[0]))
            y = ((height / 2) - (resolution_window[1] / 2)) + (((j + 1) * distance_between_cards) + (j * rectangle_size[1]))
            list_rectangles_coords_on_screen.append((x, y))

    return list_rectangles_coords_on_screen


def get_fixations(data, distance_threshold = 25, duration_threshold_ms = 100):
    def max_distance(points):
        points = np.array(points)
        x = points[:, 0]
        y = points[:, 1]
        dist_matrix = np.sqrt((x[:, np.newaxis] - x) ** 2 + (y[:, np.newaxis] - y) ** 2)
        max_dist = np.max(dist_matrix)
        return max_dist

    fixations = []
    current_fixation = []

    for point in data:
        if not current_fixation:
            current_fixation.append(point)
        else:
            current_fixation.append(point)

            if max_distance(current_fixation) <= distance_threshold:
                current_fixation.append(point)
            else:
                current_fixation = current_fixation[:-1]
                if len(current_fixation) >= 2:
                    fixations.append(current_fixation)
                current_fixation = [point]

    if (current_fixation[-1][2] - current_fixation[0][2]) >= duration_threshold_ms:
        fixations.append(current_fixation)

    fixations_final = list()
    for i in range(len(fixations)):
        sum_x = 0
        sum_y = 0
        for j in range(len(fixations[i])):
            sum_x = sum_x + fixations[i][j][0]
            sum_y = sum_y + fixations[i][j][1]
        time = fixations[i][-1][2] - fixations[i][0][2]
        fixations_final.append([sum_x / len(fixations[i]), sum_y / len(fixations[i]), time, fixations[i][0][2], fixations[i][-1][2]])

    return fixations_final


def aggregate_gaze_and_visits_by_card_gaze(data, rectangle_size, list_rectangles_coords_on_screen):
    aggregated_gaze = []
    visits_rectangle = []
    for i in range(len(list_rectangles_coords_on_screen)):
        aggregated_gaze.append(list())
        visits_rectangle.append(list())
    prev_rect = None
    for gaze in data:
        i = 0
        belongs = False
        for coords in list_rectangles_coords_on_screen:
            if (coords[0] <= gaze[0] <= coords[0] + rectangle_size[0]) and (coords[1] <= gaze[1] <= coords[1] + rectangle_size[1]):
                belongs = True
                aggregated_gaze[i].append(gaze)
                if prev_rect != coords:
                    visits_rectangle[i].append([gaze[2], gaze[2], 0])
                else:
                    visits_rectangle[i][-1][1] = gaze[2]
                    visits_rectangle[i][-1][2] = visits_rectangle[i][-1][1] - visits_rectangle[i][-1][0]
                prev_rect = coords
                break
            i = i + 1
        if not belongs:
            prev_rect = None

    return aggregated_gaze, visits_rectangle


def aggregate_fixations_by_card_gaze(fixations, rectangle_size, list_rectangles_coords_on_screen):
    aggregated_fixations = []
    for i in range(len(list_rectangles_coords_on_screen)):
        aggregated_fixations.append(list())
    for fixation in fixations:
        i = 0
        for coords in list_rectangles_coords_on_screen:
            if (coords[0] <= fixation[0] <= coords[0] + rectangle_size[0]) and (coords[1] <= fixation[1] <= coords[1] + rectangle_size[1]):
                aggregated_fixations[i].append(fixation)
                break
            i = i + 1

    return aggregated_fixations


def get_relevant_data_gaze(visits_rectangle, aggregated_fixations):
    max_temp_visit = 0
    longest_visits = []
    for i in range(len(visits_rectangle)):
        for j in range(len(visits_rectangle[i])):
            if visits_rectangle[i][j][2] > max_temp_visit:
                max_temp_visit = visits_rectangle[i][j][2]
                longest_visits = [[visits_rectangle[i][j], i + 1]]
            elif visits_rectangle[i][j][2] == max_temp_visit:
                longest_visits.append([visits_rectangle[i][j], i + 1])

    max_temp_fixation = 0
    longest_fixations = []
    for i in range(len(aggregated_fixations)):
        for j in range(len(aggregated_fixations[i])):
            if aggregated_fixations[i][j][2] > max_temp_fixation:
                max_temp_fixation = aggregated_fixations[i][j][2]
                longest_fixations = [[aggregated_fixations[i][j], i + 1]]
            elif aggregated_fixations[i][j][2] == max_temp_fixation:
                longest_fixations.append([aggregated_fixations[i][j], i + 1])

    last_temp_fixation = 0
    last_fixation = []
    for i in range(len(aggregated_fixations)):
        if len(aggregated_fixations[i]) > 0:
            if aggregated_fixations[i][-1][-1] > last_temp_fixation:
                last_temp_fixation = aggregated_fixations[i][-1][-1]
                last_fixation = [[aggregated_fixations[i][-1], i + 1]]

    visits = 0
    max_visits = []
    for i in range(len(visits_rectangle)):
        if len(visits_rectangle[i]) > visits:
            visits = len(visits_rectangle[i])
            max_visits = [[visits, i + 1]]
        elif len(visits_rectangle[i]) == visits:
            max_visits.append([visits, i + 1])

    relevant_data = {"LONGEST VISIT(S)": longest_visits, "LONGEST FIXATION(S)": longest_fixations, "LAST FIXATION": last_fixation, "CARDS WITH MORE VISITS": max_visits}

    return relevant_data


def write_data_to_files_gaze(path, fixations, aggregated_gaze, visits_rectangles, aggregated_fixations, relevant_data):
    folder_path = path.replace(".txt", "")
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    fixations_file_path = folder_path + "\\fixations.txt"
    if not os.path.isfile(fixations_file_path):
        with open(fixations_file_path, "a") as fixations_file:
            for fix in fixations:
                fix_str = [str(elem) for elem in fix]
                fixations_file.write(", ".join(fix_str) + "\n")

    aggregated_gaze_file_path = folder_path + "\\aggregated_gaze.txt"
    if not os.path.isfile(aggregated_gaze_file_path):
        with open(aggregated_gaze_file_path, "a") as aggregated_gaze_file:
            for i in range(len(aggregated_gaze)):
                aggregated_gaze_file.write("--------------------\nCARD {}\n\n".format(i + 1))
                for aggregated_gaze_data in aggregated_gaze[i]:
                    aggregated_gaze_data_str = [str(elem) for elem in aggregated_gaze_data]
                    aggregated_gaze_file.write(", ".join(aggregated_gaze_data_str) + "\n")

    visits_rectangles_file_path = folder_path + "\\visits_rectangles.txt"
    if not os.path.isfile(visits_rectangles_file_path):
        with open(visits_rectangles_file_path, "a") as visits_rectangles_file:
            for i in range(len(visits_rectangles)):
                visits_rectangles_file.write("--------------------\nCARD {}\n\n".format(i + 1))
                for visits_data in visits_rectangles[i]:
                    visits_data_str = [str(elem) for elem in visits_data]
                    visits_rectangles_file.write(", ".join(visits_data_str) + "\n")

    aggregated_fixations_file_path = folder_path + "\\aggregated_fixations.txt"
    if not os.path.isfile(aggregated_fixations_file_path):
        with open(aggregated_fixations_file_path, "a") as aggregated_fixations_file:
            for i in range(len(aggregated_fixations)):
                aggregated_fixations_file.write("--------------------\nCARD {}\n\n".format(i + 1))
                for aggregated_fixations_data in aggregated_fixations[i]:
                    aggregated_fixations_data_str = [str(elem) for elem in aggregated_fixations_data]
                    aggregated_fixations_file.write(", ".join(aggregated_fixations_data_str) + "\n")

    relevant_data_file_path = folder_path + "\\relevant_data.txt"
    if not os.path.isfile(relevant_data_file_path):
        with open(relevant_data_file_path, "a") as relevant_data_file:
            for key in relevant_data.keys():
                relevant_data_file.write(key + "\n")
                for i in relevant_data[key]:
                    relevant_data_file.write("[CARD {}]: ".format(i[1]) + str(i[0]) + "\n")
                relevant_data_file.write("\n")


def visualize_data_gaze(path, gaze, fixations, relevant_data, grid_rect, rectangle_size, resolution_window, distance_between_cards):
    def turtle_rectangle(top_left_corner, dimensions, color="black", pensize=1):
        turtle.up()
        turtle.goto(top_left_corner)
        turtle.color(color)
        turtle.pensize(pensize)
        turtle.down()
        for i in range(4):
            turtle.fd(dimensions[i % 2])
            turtle.right(90)
        turtle.up()
        turtle.ht()

    root_visualize = tkinter.Tk()
    width = root_visualize.winfo_screenwidth()
    height = root_visualize.winfo_screenheight()
    root_visualize.deiconify()
    turtle.Screen().setup(width = 1.0, height = 1.0, startx = width, starty = height)
    turtle.tracer(0)

    turtle_rectangle((-(width / 2), height / 2), (width, height))
    rects = get_rectangles_cards_interface_P1(grid_rect, rectangle_size, resolution_window, distance_between_cards)
    turtle_rectangle((-(resolution_window[0] / 2), resolution_window[1] / 2), resolution_window)
    for rect in rects:
        turtle_rectangle((- (width / 2) + rect[0], (height / 2) - rect[1]), rectangle_size)
    turtle.up()
    turtle.goto(- (width / 2) + gaze[0][0], (height / 2) - gaze[0][1])
    turtle.down()
    for data in gaze:
        turtle.goto(- (width / 2) + data[0], (height / 2) - data[1])
    turtle.up()
    for fixs in fixations:
        turtle.goto(- (width / 2) + fixs[0], (height / 2) - fixs[1])
        turtle.dot(10, "blue")
    for i in relevant_data["LONGEST FIXATION(S)"]:
        turtle.goto(- (width / 2) + i[0][0], (height / 2) - i[0][1])
        turtle.dot(10, "red")
    turtle.goto(- (width / 2) + relevant_data["LAST FIXATION"][0][0][0], (height / 2) - relevant_data["LAST FIXATION"][0][0][1])
    turtle.dot(10, "orange")
    for i in relevant_data["LONGEST VISIT(S)"]:
        turtle_rectangle((- (width / 2) + rects[i[1] - 1][0], (height / 2) - rects[i[1] - 1][1]), rectangle_size, "red", 5)
    for i in relevant_data["CARDS WITH MORE VISITS"]:
        turtle_rectangle((- (width / 2) + rects[i[1] - 1][0], (height / 2) - rects[i[1] - 1][1]), rectangle_size, "blue", 3)

    turtle.update()

    folder_path = path.replace(".txt", "")
    png_filepath = folder_path + "\\visualization.png"
    if not os.path.isfile(png_filepath):
        turtle_canvas = turtle.getcanvas().postscript(colormode='color')
        img = Image.open(io.BytesIO(turtle_canvas.encode('utf-8')))
        img.save(png_filepath, "png")


def data_by_card_period_gaze_pupil(data, time_correction, timestamps):
    aggregated_data = []
    for i in range(len(timestamps) - 1):    # last timestamp is just the end
        aggregated_data.append(list())
    i = 0
    for gaze in data:
        gaze["system_time_stamp"] = int(gaze["system_time_stamp"] / 1000) + time_correction
        if i + 1 < len(timestamps) - 1:
            if gaze["system_time_stamp"] >= timestamps[i + 1]:
                i = i + 1
        if gaze["system_time_stamp"] >= timestamps[-1]:
            break
        aggregated_data[i].append(gaze)

    return aggregated_data


def write_to_file_gaze_pupil(raw_data, aggregated_data, path):
    path = path.replace(".bin", "")
    if not os.path.exists(path):
        os.makedirs(path)

    with open(path + "\\raw_data_P2.txt", "w") as file:
        for i in raw_data:
            file.write(str(i))

    with open(path + "\\aggregated_data_P2.txt", "w") as file:
        for i in range(len(aggregated_data)):
            file.write("--------------------\nCARD {}\n".format(i + 1) + str(aggregated_data[i]))
