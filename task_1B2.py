import os
import pandas as pd

# If I could assume, that the CSV would fit in the momory, I would do it differently, say with pandas
# depending on use case of course


def sum_small_csv_files(
    dir, col_to_sum, col_to_filter, condition_string, sep=",", header=None
):
    file_dict = {}
    for file_name in [
        f for f in os.listdir(dir) if os.path.isfile(os.path.join(dir, f))
    ]:
        df = pd.read_csv(os.path.join(dir, file_name), sep=sep, header=header)
        # TODO: hanle nans and datatype missmatch
        f_df = df[df.iloc[:, col_to_filter] == condition_string]
        file_sum = f_df.iloc[:, col_to_sum].sum()
        file_dict[file_name] = file_sum

    return file_dict


def sum_csv_files(
    dir, col_to_sum, col_to_filter, condition_string, sep=",", header=False
):
    file_dict = {}
    for file_name in [
        f for f in os.listdir(dir) if os.path.isfile(os.path.join(dir, f))
    ]:
        with open(os.path.join(dir, file_name), "r") as f:
            if header:
                f.readline()  # skip header

            file_sum = 0

            for line in f.readlines():
                line_list = line.split(sep)
                if line_list[col_to_filter] == condition_string:
                    # TODO: parse int validation
                    file_sum += int(line_list[col_to_sum])

            file_dict[file_name] = file_sum
    return file_dict


if __name__ == "__main__":
    file_dict = sum_csv_files("../csv_dir", 4, 1, "SACRAMENTO", sep=",")
    print(file_dict)
    small_file_dict = sum_small_csv_files("../csv_dir", 4, 1, "SACRAMENTO", sep=",")
    print(small_file_dict)
