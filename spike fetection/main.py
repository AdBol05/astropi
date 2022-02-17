# spike detection test program

vals = [14.594403267, 14.563790321, 14.263509750, 14.475710869, 14.445699692, 14.077428818, 13.790111542, 13.897954941, 13.79822349]  # test values
absolute = []

for i in range(len(vals)):
    if i != 0:
        absolute.append(abs(vals[i] - vals [i - 1]))


average = sum(absolute) / len(absolute)
absmax = max(absolute) - average

for i in range(len(vals)):
    if i != 0:
        if abs(vals[i] - vals[i - 1]) > average:
            print("Minor spike detected between " + str(vals[i]) + " and " + str(vals[i - 1]))

        if abs(vals[i] - vals[i - 1]) > absmax:
            print("Major spike detected between " + str(vals[i]) + " and " + str(vals[i - 1]))
