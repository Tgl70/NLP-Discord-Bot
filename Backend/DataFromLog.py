from datetime import datetime
from config import TIME_FORMAT


def data_from_log(path):
    with open(str(path), "r") as f:
        f.readline()
        data = f.read()
    data = [a for a in data.split("\n") if a]
    sliced_data = []
    for i in range(0, len(data)):
        sliced_data.append(data[i].split("\t"))

    time = datetime.strptime(sliced_data[-1][0], TIME_FORMAT) - datetime.strptime(sliced_data[0][0], TIME_FORMAT)
    return {"total_time": str(time), "nb_turn": len(sliced_data)}
