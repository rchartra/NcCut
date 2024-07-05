def project_file_printer(data, tab):
    """
    Recursively prints the contents of an output data file from CutView in a readable fashion.

    data (dict): Dictionary output from CutView
    tab (int): Always use 0, used in the recursive process for indentation
    """
    for key in list(data.keys()):
        print(" " * tab, end="")
        if isinstance(data[key], list):
            print(key + ": [" + str(data[key][0]) + ", " + str(data[key][1]) + ", ..." + "]")
        else:
            print(key + ":")
            project_file_printer(data[key], tab + 4)
