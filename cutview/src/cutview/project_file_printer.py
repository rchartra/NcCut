import json

f = open("../../support/example.json")
data = json.load(f)


def project_file_printer(data, tab):
    for key in list(data.keys()):
        print(" " * tab, end="")
        if isinstance(data[key], list):
            print(key + ": [" + str(data[key][0]) + ", " + str(data[key][1]) + ", ..." + "]")
        else:
            print(key + ":")
            project_file_printer(data[key], tab + 4)


project_file_printer(data, 0)
