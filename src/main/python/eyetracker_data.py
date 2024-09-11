import json
import math
import os
import tkinter
from enum import Enum

import numpy as np
import pandas as pd

pd.options.display.float_format = '{:.10f}'.format


class EyetrackerData:
    class DataType(Enum):
        PHASE_ONE = 1
        PHASE_TWO = 2

    DISTANCE_THRESHOLD = 25
    DURATION_THRESHOLD = 100

    def __init__(self, data_type, filepath, grid_shape, card_dim, window_dim, dist_cards):
        """
        Constructor for EyetrackerData.

        :param EyeTracker.DataType data_type: Game phase from which the data was acquired
        :param str filepath: Filename/Filepath containing the data
        """
        self.data_type = data_type
        self.filepath = filepath
        self.grid_shape = grid_shape
        self.card_dim = card_dim
        self.window_dim = window_dim
        self.dist_cards = dist_cards
        self.raw_gaze = None
        self.cards_boundaries = None
        self.fixations = None
        self.aggregated_gaze = None
        self.visits_cards = None
        self.aggregated_fixations = None

    def get_cards_boundaries(self):
        """
        Returns boundaries of the cards on the GUI.
        """
        root_rect = tkinter.Tk()
        width = root_rect.winfo_screenwidth()
        height = root_rect.winfo_screenheight()
        root_rect.deiconify()

        self.cards_boundaries = []
        for j in range(self.grid_shape[1]):
            for k in range(self.grid_shape[0]):
                x = ((width / 2) - (self.window_dim[0] / 2)) + (
                        ((k + 1) * self.dist_cards) + (k * self.card_dim[0]))
                y = ((height / 2) - (self.window_dim[1] / 2)) + (
                        ((j + 1) * self.dist_cards) + (j * self.card_dim[1]))
                self.cards_boundaries.append((x, y))

    def get_data(self) -> pd.DataFrame:
        """
        Gets raw gaze data from text file.
        :return: Raw gaze data.
        """
        with open(self.filepath, "r") as file:
            raw_data = file.readlines()

        # text file structure:
        # X_AXIS_1
        # Y_AXIS_1
        # TIMESTAMP_1
        # [...]
        self.raw_gaze = pd.DataFrame(
            (np.array([[float(raw_data[i].strip()), float(raw_data[i + 1].strip()), int(raw_data[i + 2].strip())]
                       for i in range(0, len(raw_data), 3)], dtype=np.int64)),
            columns=['X_AXIS', 'Y_AXIS', 'TIMESTAMP'])

        self.get_cards_boundaries()

        return self.raw_gaze

    def get_fixations(self) -> pd.DataFrame:
        """
        Returns fixations from raw gaze data.
        :return: Fixations.
        """
        def max_distance(points):
            """
            Returns the maximum distance between set of points.
            """
            points = np.array(points)
            x = points[:, 0]
            y = points[:, 1]
            dist_matrix = np.sqrt((x[:, np.newaxis] - x) ** 2 + (y[:, np.newaxis] - y) ** 2)
            max_dist = np.max(dist_matrix)

            return max_dist

        fixations = []
        current_fixation = []

        print(self.raw_gaze.shape)
        for index, gaze in self.raw_gaze.iterrows():
            if not current_fixation:
                current_fixation.append(gaze)
            else:
                current_fixation.append(gaze)
                print(index)
                if max_distance(current_fixation) <= self.DISTANCE_THRESHOLD:
                    current_fixation.append(gaze)
                else:
                    current_fixation = current_fixation[:-1]
                    if len(current_fixation) >= 2:
                        fixations.append(current_fixation)
                    current_fixation = [gaze]

        if (current_fixation[-1]["TIMESTAMP"] - current_fixation[0]["TIMESTAMP"]) >= self.DURATION_THRESHOLD:
            fixations.append(current_fixation)

        fixations_final = list()
        for i in range(len(fixations)):
            sum_x = 0
            sum_y = 0
            for j in range(len(fixations[i])):
                sum_x = sum_x + fixations[i][j]["X_AXIS"]
                sum_y = sum_y + fixations[i][j]["Y_AXIS"]
            time = fixations[i][-1]["TIMESTAMP"] - fixations[i][0]["TIMESTAMP"]
            fixations_final.append(
                [sum_x / len(fixations[i]), sum_y / len(fixations[i]), time, fixations[i][0]["TIMESTAMP"],
                 fixations[i][-1]["TIMESTAMP"]])

        self.fixations = pd.DataFrame(fixations_final,
                                      columns=['X_AXIS', 'Y_AXIS', 'DURATION', 'START_TIMESTAMP', 'END_TIMESTAMP'])

        return self.fixations

    def aggregated_gaze_fixations(self, timestamps):
        """
        Aggregates gaze and fixations data by card.
        :param list timestamps: List of timestamps of each card first appearance.
        """
        if self.data_type == EyetrackerData.DataType.PHASE_ONE:
            aggregated_gaze = []
            visits_cards = []
            for i in range(len(self.cards_boundaries)):
                aggregated_gaze.append(list())
                visits_cards.append(list())
            prev_rect = None
            for index, gaze in self.raw_gaze.iterrows():
                i = 0
                belongs = False
                for j in range(len(self.cards_boundaries)):
                    if ((self.cards_boundaries[j][0] <= gaze["X_AXIS"] <= self.cards_boundaries[j][0] + self.card_dim[
                        0]) and
                            (self.cards_boundaries[j][1] <= gaze["Y_AXIS"] <= self.cards_boundaries[j][1] +
                             self.card_dim[
                                 1])):
                        belongs = True
                        aggregated_gaze[i].append(gaze)
                        if prev_rect != self.cards_boundaries[j]:
                            visits_cards[i].append([gaze["TIMESTAMP"], gaze["TIMESTAMP"], 0])
                        else:
                            visits_cards[i][-1][1] = gaze["TIMESTAMP"]
                            visits_cards[i][-1][2] = visits_cards[i][-1][1] - visits_cards[i][-1][0]
                        prev_rect = self.cards_boundaries[j]
                        break
                    i = i + 1
                if not belongs:
                    prev_rect = None

            self.aggregated_gaze = list()
            self.visits_cards = list()
            for i in range(len(self.cards_boundaries)):
                self.aggregated_gaze.append(pd.DataFrame(aggregated_gaze[i], columns=["X_AXIS", "Y_AXIS", "TIMESTAMP"]))
                self.visits_cards.append(
                    pd.DataFrame(visits_cards[i], columns=["START_TIMESTAMP", "END_TIMESTAMP", "DURATION"]))

            aggregated_fixations = []
            for i in range(len(self.cards_boundaries)):
                aggregated_fixations.append(list())
            for index, fixation in self.fixations.iterrows():
                i = 0
                for coords in self.cards_boundaries:
                    if (coords[0] <= fixation["X_AXIS"] <= coords[0] + self.card_dim[0]) and (
                            coords[1] <= fixation["Y_AXIS"] <= coords[1] + self.card_dim[1]):
                        aggregated_fixations[i].append(fixation)
                        break
                    i = i + 1

            self.aggregated_fixations = list()
            for i in range(len(self.cards_boundaries)):
                self.aggregated_fixations.append(pd.DataFrame(aggregated_fixations[i],
                                                              columns=['X_AXIS', 'Y_AXIS', 'DURATION',
                                                                       'START_TIMESTAMP',
                                                                       'END_TIMESTAMP']))

        elif self.data_type == EyetrackerData.DataType.PHASE_TWO:
            self.visits_cards = None

            i = 0
            aggregated_gaze = []
            for _ in range(self.grid_shape[0] * self.grid_shape[1]):
                aggregated_gaze.append(list())
            for index, gaze in self.raw_gaze.iterrows():
                if i == len(timestamps) - 1:
                    break
                if timestamps[i] <= gaze["TIMESTAMP"] < timestamps[i + 1]:
                    aggregated_gaze[i].append(gaze)
                else:
                    i += 1
                    if i == len(timestamps) - 1:
                        break
                    aggregated_gaze[i].append(gaze)

            self.aggregated_gaze = list()
            for i in range(len(self.cards_boundaries)):
                self.aggregated_gaze.append(pd.DataFrame(aggregated_gaze[i], columns=["X_AXIS", "Y_AXIS", "TIMESTAMP"]))

            i = 0
            aggregated_fixations = []
            for _ in range(self.grid_shape[0] * self.grid_shape[1]):
                aggregated_fixations.append(list())
            for index, fixation in self.fixations.iterrows():
                if i == len(timestamps) - 1:
                    break
                if timestamps[i] <= fixation["START_TIMESTAMP"] < timestamps[i + 1] and timestamps[i] <= fixation[
                    "END_TIMESTAMP"] < timestamps[i + 1]:
                    aggregated_fixations[i].append(fixation)
                elif timestamps[i + 2] > fixation["START_TIMESTAMP"] >= timestamps[i + 1] and timestamps[i + 2] > \
                        fixation["END_TIMESTAMP"] >= timestamps[i + 1]:
                    i += 1
                    aggregated_fixations[i].append(fixation)
                else:
                    i += 1

            self.aggregated_fixations = list()
            for i in range(len(self.cards_boundaries)):
                self.aggregated_fixations.append(pd.DataFrame(aggregated_fixations[i],
                                                              columns=['X_AXIS', 'Y_AXIS', 'DURATION',
                                                                       'START_TIMESTAMP',
                                                                       'END_TIMESTAMP']))

    def process_data(self, timestamps_phase_two=None):
        """
        Process raw data to get fixations and aggregate data.
        """
        # ADD CARD NUMBER TO DATA
        def get_card_number(data):
            if self.data_type == EyetrackerData.DataType.PHASE_ONE:
                # PHASE ONE
                for i, top_left in enumerate(self.cards_boundaries):
                    if top_left[0] <= data[0] <= top_left[0] + self.card_dim[0] and top_left[1] <= data[1] <= top_left[1] + self.card_dim[1]:
                        return i + 1

                return -1
            else:
                # PHASE TWO
                for i, window_start in enumerate(timestamps_phase_two):
                    if i != 0:
                        if data <= window_start:
                            return i
                return self.grid_shape[0] * self.grid_shape[1]

        self.get_data()
        self.get_fixations()
        self.aggregated_gaze_fixations(timestamps_phase_two)

        if self.data_type == EyetrackerData.DataType.PHASE_ONE:
            self.raw_gaze['CARD'] = self.raw_gaze.apply(lambda row: get_card_number((row['X_AXIS'], row['Y_AXIS'])), axis=1)
            self.fixations['CARD'] = self.fixations.apply(lambda row: get_card_number((row['X_AXIS'], row['Y_AXIS'])), axis=1)
        else:
            self.raw_gaze['CARD'] = self.raw_gaze.apply(lambda row: get_card_number(row['TIMESTAMP']), axis=1)
            self.fixations['CARD'] = self.fixations.apply(lambda row: get_card_number(row['START_TIMESTAMP']), axis=1)

    def export_data(self, output_folder):
        """
        Export data to Excel files and relevant data to JSON file.
        FEATURES:
            - LONGEST VISIT
            - LONGEST FIXATION
            - CARD WITH MORE VISITS
            - CARD WITH LONGEST VISIT
            - CARD WITH LONGEST FIXATION
        """
        number_of_visits = list()
        longest_visit = list()
        longest_fixation = list()

        with pd.ExcelWriter(os.path.join(output_folder, "raw_gaze.xlsx")) as writer:
            self.raw_gaze.to_excel(writer, sheet_name="RAW_GAZE", index=False)
            for i, sheet in enumerate(self.aggregated_gaze):
                sheet.to_excel(writer, sheet_name="CARD_" + str(i + 1) + "_GAZE", index=False)
            if self.visits_cards is not None:
                for i, sheet in enumerate(self.visits_cards):
                    sheet.to_excel(writer, sheet_name="CARD_" + str(i + 1) + "_VISITS", index=False)
                    number_of_visits.append(self.visits_cards[i].shape[0])
                    longest_visit.append(self.visits_cards[i]['DURATION'].max())

        with pd.ExcelWriter(os.path.join(output_folder, "fixations.xlsx")) as writer:
            self.fixations.to_excel(writer, sheet_name="FIXATIONS", index=False)
            for i, sheet in enumerate(self.aggregated_fixations):
                sheet.to_excel(writer, sheet_name="CARD_" + str(i + 1) + "_FIXATIONS", index=False)
                longest_fixation.append(self.aggregated_fixations[i]['DURATION'].max())

        if self.data_type == EyetrackerData.DataType.PHASE_ONE:
            relevant_data = {"COORDS": dict(), "NUMBER_VISITS": dict(), "LONGEST_VISITS": dict(), "LONGEST_FIXATIONS": dict(), "CARD_WITH_MORE_VISITS": 0, "CARD_WITH_LONGEST_VISIT": 0, "CARD_WITH_LONGEST_FIXATION": 0}
            for i in range(self.grid_shape[0] * self.grid_shape[1]):
                card = "CARD_" + str(i + 1)
                relevant_data["COORDS"][card] = {"X": self.cards_boundaries[i][0], "Y": self.cards_boundaries[i][1]}
                if number_of_visits[i] is None or pd.isna(number_of_visits[i]):
                    relevant_data["NUMBER_VISITS"][card] = 0
                else:
                    relevant_data["NUMBER_VISITS"][card] = float(number_of_visits[i])

                if longest_visit[i] is None or pd.isna(longest_visit[i]):
                    relevant_data["LONGEST_VISITS"][card] = 0
                else:
                    relevant_data["LONGEST_VISITS"][card] = float(longest_visit[i])

                if longest_fixation[i] is None or pd.isna(longest_fixation[i]):
                    relevant_data["LONGEST_FIXATIONS"][card] = 0
                else:
                    relevant_data["LONGEST_FIXATIONS"][card] = float(longest_fixation[i])

            longest_visit = [0 if math.isnan(x) else x for x in longest_visit]
            longest_fixation = [0 if math.isnan(x) else x for x in longest_fixation]

            relevant_data["CARD_WITH_MORE_VISITS"] = "CARD_" + str(number_of_visits.index(max(number_of_visits)) + 1)
            relevant_data["CARD_WITH_LONGEST_VISIT"] = "CARD_" + str(longest_visit.index(max(longest_visit)) + 1)
            relevant_data["CARD_WITH_LONGEST_FIXATION"] = "CARD_" + str(longest_fixation.index(max(longest_fixation)) + 1)

            with open(os.path.join(output_folder, "relevant_data.json"), "w") as outfile:
                json.dump(relevant_data, outfile)
