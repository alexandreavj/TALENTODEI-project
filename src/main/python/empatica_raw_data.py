import json
import os
import tkinter
import numpy as np
from enum import Enum

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import pandas as pd
from avro.datafile import DataFileReader
from avro.io import DatumReader

from scipy.signal import find_peaks

pd.options.display.float_format = '{:.10f}'.format


class EmpaticaRawData:
    class Variables(Enum):
        """
        Enum class for Empatica raw data variables.
        """
        EDA = 'eda'
        BVP = 'bvp'

    def __init__(self, avro_folder_path, cards_data):
        """
        Constructor for EmpaticaData object.
        :param avro_folder_path: Path to .avro file.
        """
        self.cards_data = cards_data
        self.schema = list()
        self.data = list()
        self.raw_data_one = None
        self.raw_data_two = None
        self.variable = None
        '''
        self.raw_accelerometer = None
        self.raw_steps = None
        self.raw_temperature = None
        self.raw_gyroscope = None
        self.raw_tags = None
        self.raw_systolic_peaks = None
        '''

        for i, avro_file in enumerate(os.listdir(avro_folder_path)):
            if avro_file.endswith('.avro'):
                reader = DataFileReader(open(os.path.join(avro_folder_path, avro_file), 'rb'), DatumReader())

                self.schema.append(json.loads(reader.meta.get('avro.schema').decode('utf-8')))

                for datum in reader:
                    self.data.append(datum)
                reader.close()

    def variable_raw_data(self, variable, phase_one_path, phase_two_path):
        """
        Extracts raw data for a specific variable from the .avro files.
        :param variable: Variable to extract raw data for.
        :param phase_one_path: Path to phase one raw gaze data.
        :param phase_two_path: Path to phase two raw gaze data.
        """
        var = str()
        if variable == EmpaticaRawData.Variables.EDA:
            self.variable = variable
            var = "eda"
        elif variable == EmpaticaRawData.Variables.BVP:
            self.variable = variable
            var = "bvp"
        else:
            assert "Invalid variable name"

        phase_one_gaze = pd.read_excel(phase_one_path, sheet_name="RAW_GAZE")
        start_timestamp_one = phase_one_gaze.iloc[0]['TIMESTAMP']
        end_timestamp_one = phase_one_gaze.iloc[-1]['TIMESTAMP']

        phase_two_gaze = pd.read_excel(phase_two_path, sheet_name="RAW_GAZE")
        start_timestamp_two = phase_two_gaze.iloc[0]['TIMESTAMP']
        end_timestamp_two = phase_two_gaze.iloc[-1]['TIMESTAMP']

        self.raw_data_one = pd.DataFrame(columns=["TIMESTAMP", self.variable.value])
        self.raw_data_two = pd.DataFrame(columns=["TIMESTAMP", self.variable.value])
        for data in self.data:
            period = (1 / data["rawData"][var]["samplingFrequency"]) * 1000
            start = round(data["rawData"][var]["timestampStart"] / 1000)

            temp = pd.DataFrame({self.variable.value: data["rawData"][var]["values"],
                                 'TIMESTAMP': [round(start + (period * i)) for i in
                                               range(len(data["rawData"][var]["values"]))]})
            temp_one = temp[(temp['TIMESTAMP'] >= start_timestamp_one) & (temp['TIMESTAMP'] <= end_timestamp_one)]
            temp_two = temp[(temp['TIMESTAMP'] >= start_timestamp_two) & (temp['TIMESTAMP'] <= end_timestamp_two)]
            self.raw_data_one = pd.concat([self.raw_data_one, temp_one])
            self.raw_data_two = pd.concat([self.raw_data_two, temp_two])

    def export_data(self, variable, phase_one_path, phase_two_path):
        """
        Exports raw data for a specific variable.
        Maps EDA/BVP raw data to each card region.
        Plots the data and sinalizes local/global peaks.
        :param variable: Variable to export raw data for.
        :param phase_one_path: Path to phase one raw gaze data.
        :param phase_two_path: Path to phase two raw gaze data.
        """
        var = str()
        if variable == EmpaticaRawData.Variables.EDA:
            self.variable = variable
            var = "eda"
        elif variable == EmpaticaRawData.Variables.BVP:
            self.variable = variable
            var = "bvp"
        else:
            assert "Invalid variable name"

        # PHASE ONE
        final_p1 = pd.merge(pd.read_excel(phase_one_path, sheet_name="RAW_GAZE"), self.raw_data_one, on="TIMESTAMP", how='outer')
        final_p1.sort_values(by="TIMESTAMP", inplace=True)
        final_p1.reset_index(inplace=True, drop=True)
        final_p1["X_AXIS"] = final_p1["X_AXIS"].interpolate(method='linear', limit_direction='both')
        final_p1["Y_AXIS"] = final_p1["Y_AXIS"].interpolate(method='linear', limit_direction='both')
        final_p1 = final_p1[final_p1[var].notna()].reset_index(drop=True)

        def get_card_phase1(point):
            for i, card_top_left in enumerate(self.cards_data[0]):
                if card_top_left[0] < point[0] < card_top_left[0] + self.cards_data[1] and card_top_left[1] < point[1] < card_top_left[1] + self.cards_data[2]:
                    return i + 1
            return -1

        final_p1['CARD'] = final_p1.apply(lambda row: get_card_phase1((row['X_AXIS'], row['Y_AXIS'])), axis=1)

        path = phase_one_path.replace(".xlsx", "_") + self.variable.value + '.xlsx'
        final_p1.to_excel(path)

        # PHASE TWO
        phase_two_data = pd.ExcelFile(phase_two_path)
        dfs = {sheet_name: phase_two_data.parse(sheet_name) for sheet_name in phase_two_data.sheet_names}
        final_p2 = pd.merge(pd.read_excel(phase_two_path, sheet_name="RAW_GAZE"), self.raw_data_two, on="TIMESTAMP", how='outer')
        final_p2.sort_values(by="TIMESTAMP", inplace=True)
        final_p2.reset_index(inplace=True, drop=True)
        final_p2["X_AXIS"] = final_p2["X_AXIS"].interpolate(method='linear', limit_direction='both')
        final_p2["Y_AXIS"] = final_p2["Y_AXIS"].interpolate(method='linear', limit_direction='both')
        final_p2 = final_p2[final_p2[var].notna()].reset_index(drop=True)

        timestamps = []
        for sheet_name, df in dfs.items():
            if sheet_name != "RAW_GAZE":
                timestamps.append(df.iloc[0, 2])

        def get_card_phase2(timestamps, timestamp):
            for i, window_start in enumerate(timestamps):
                if timestamp < window_start:
                    return i
            return len(timestamps)

        final_p2['CARD'] = final_p2.apply(lambda row: get_card_phase2(timestamps, row["TIMESTAMP"]), axis=1)

        path = phase_two_path.replace(".xlsx", "_") + self.variable.value + '.xlsx'
        final_p2.to_excel(path)

        '''
        PLOT PHASE 1 & 2
        '''
        for i, data in enumerate(((final_p1['TIMESTAMP'], final_p1[var], final_p1['CARD']),
                                (final_p2['TIMESTAMP'], final_p2[var], final_p2['CARD']))):
            plt.figure(figsize=(25, 10))
            cards_regions = data[2].unique()
            colors = [(1, 0.4, 0.4, 1), (1, 0.698, 0.4, 1), (1, 1, 0.6, 1), (0.4, 1, 0.4, 1), (0.4, 0.6, 1, 1), (0.616, 0.506, 0.729, 1), (0.867, 0.627, 0.867, 1),
                      (1, 0, 0, 1), (1, 0.498, 0, 1), (1, 1, 0, 1), (0, 1, 0, 1), (0, 0, 1, 1), (0.294, 0, 0.514, 1), (0.545, 0, 1, 1),
                      (0.4, 0, 0, 1), (0.8, 0.2, 0, 1), (0.8, 0.6, 0, 1), (0, 0.3, 0, 1), (0, 0, 0.4, 1), (0.13, 0, 0.24, 1), (0.4, 0, 0.6, 1)]
            legend = [mpatches.Patch(color=color, label=str(i + 1)) for i, color in enumerate(colors)]
            plt.plot(data[0], data[1], marker='', linestyle='-', color='black', linewidth="0.25")

            # local peaks
            peaks, _ = find_peaks(abs(data[1]))
            plt.plot(data[0][peaks], data[1][peaks], 'o', label='Local Peaks', color='GREY')

            max_pos = np.argmax(data[1])
            min_neg = np.argmin(data[1])
            max_abs = np.argmax(abs(data[1]))
            plt.plot(data[0][max_pos], data[1][max_pos], 'o', label='Global maximum', color='RED')
            plt.plot(data[0][min_neg], data[1][min_neg], 'o', label='Global minimum', color='BLUE')
            plt.plot(data[0][max_abs], data[1][max_abs], 'o', label='Global absolute maximum', color='GREEN')
            print("MAX PHASE {} VAR {}: {} -> {}".format(i, self.variable.__str__(), data[0][max_pos], data[1][max_pos]))
            print("MIN PHASE {} VAR {}: {} -> {}".format(i, self.variable.__str__(), data[0][min_neg], data[1][min_neg]))

            if i == 0:
                # input longest fixation boundaries
                start_longest_fixation = int(input("Start Longest Fixation: "))
                end_longest_fixation = int(input("End Longest Fixation: "))

                # input longest visit
                start_longest_visit = int(input("Start Longest Visit: "))
                end_longest_visit = int(input("End Longest Visit: "))

                # plot vertical lines
                plt.plot([start_longest_fixation, start_longest_fixation], [min(data[1]), max(data[1])], linestyle='--', color='black')
                plt.plot([end_longest_fixation, end_longest_fixation], [min(data[1]), max(data[1])], linestyle='--', color='black')
                plt.plot([start_longest_visit, start_longest_visit], [min(data[1]), max(data[1])], linestyle='--', color='grey')
                plt.plot([end_longest_visit, end_longest_visit], [min(data[1]), max(data[1])], linestyle='--', color='grey')


                for region in cards_regions:
                    if region != -1:
                        subset = final_p1[final_p1['CARD'] == region].reset_index()

                        rows_to_add = []
                        for row in range(1, len(subset)):
                            if subset.iloc[row]["index"] - subset.iloc[row - 1]["index"] > 1:
                                time = subset.iloc[row - 1]["TIMESTAMP"]
                                for indexes in range(subset.iloc[row - 1]["index"] + 1, subset.iloc[row]["index"]):
                                    if indexes == subset.iloc[row]["index"] - 1:
                                        time = subset.iloc[row]["TIMESTAMP"]
                                    rows_to_add.append({'index': indexes, 'TIMESTAMP': time, 'X_AXIS': 0, 'Y_AXIS': 0, var: 0, 'CARD': region})

                        to_add = pd.DataFrame(rows_to_add)
                        subset = pd.concat([subset, pd.DataFrame(to_add)]).sort_values(by='index')

                        plt.fill_between(subset["TIMESTAMP"].tolist(), subset[var].tolist(), color=colors[region - 1], alpha=1)
            else:
                for region in cards_regions:
                    subset = final_p2[final_p2['CARD'] == region]
                    plt.fill_between(subset["TIMESTAMP"].tolist(), subset[var].tolist(), color=colors[region - 1], alpha=1)

            plt.legend(handles=legend, loc='upper left', bbox_to_anchor=(0, 1), ncol=7, fontsize='small')

            plt.xlim(min(data[0]), max(data[0]))
            plt.ylim(min(data[1]), max(data[1]))

            if i == 0:
                plt.title("PHASE ONE: " + var.upper())
            else:
                plt.title("PHASE TWO: " + var.upper())
            plt.xlabel("TIMESTAMP")
            plt.ylabel(var.upper())
            plt.grid(True)

            if i == 0:
                path = phase_one_path.replace('.xlsx', '_') + self.variable.value + '.png'
                plt.savefig(path)
            else:
                path = phase_two_path.replace('.xlsx', '_') + self.variable.value + '.png'
                plt.savefig(path)
            plt.show()


def main():
    """
    Main function for using EmpaticaRawData class.
    """

    '''
    Get UI specifications.
    '''
    dist_cards = 10
    card_dim = (200, 300)
    window_dim = (7 * (card_dim[0] + dist_cards) + dist_cards, 3 * (card_dim[1] + dist_cards) + (75 + 2 * dist_cards))

    root_rect = tkinter.Tk()
    width = root_rect.winfo_screenwidth()
    height = root_rect.winfo_screenheight()
    root_rect.deiconify()

    cards_boundaries = []
    for j in range(3):
        for k in range(7):
            x = ((width / 2) - (window_dim[0] / 2)) + (((k + 1) * dist_cards) + (k * card_dim[0]))
            y = ((height / 2) - (window_dim[1] / 2)) + (((j + 1) * dist_cards) + (j * card_dim[1]))
            cards_boundaries.append((x, y))

    '''
    Run data processing.
    '''
    empatica_testing = EmpaticaRawData(r"path/to/directory/with/avro/files", (cards_boundaries, 200, 300))
    path1 = r"path/to/phase/one/raw_gaze.xlsx"
    path2 = r"path/to/phase/two/raw_gaze.xlsx"
    empatica_testing.variable_raw_data(EmpaticaRawData.Variables.EDA, path1, path2)
    empatica_testing.export_data(EmpaticaRawData.Variables.EDA, path1, path2)
    empatica_testing.variable_raw_data(EmpaticaRawData.Variables.BVP, path1, path2)
    empatica_testing.export_data(EmpaticaRawData.Variables.BVP, path1, path2)


if __name__ == '__main__':
    main()
