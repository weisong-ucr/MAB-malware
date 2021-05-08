import os
import datetime
import numpy as np
import matplotlib.pyplot as plt
import matplotlib


DATA_PATH = '/home/wei/code/adversarial_binary/data/final_2020/'
list_av = [
            'ember',
            'malconv',
            'clamav',
            'avast',
            'avira',
            'bitdefender',
            #'kaspersky',
            ]
dict_action_list_to_count = {}
dict_action_to_feature = {
        'O1': 'file hash',
        'P1': 'section hash',
        'S1': 'section count',
        'R1': 'section name',
        'C1': 'section hash',
        'OA': 'data dist',
        'SP': 'section padding',
        'SA': 'data dist',
        'SR': 'section name',
        'RC': 'certificate',
        'RD': 'debug',
        'BC': 'checksum',
        'CR': 'code seq' 
        }

def get_display_name(av):
    if 'kaspersky' in av:
        display_name = 'AV4'
    elif 'bitdefender' in av:
        display_name = 'AV3'
    elif 'avast' in av:
        display_name = 'AV1'
    elif 'avira' in av:
        display_name = 'AV2'
    elif 'ember' in av:
        display_name = 'EMBER'
    elif 'malconv' in av:
        display_name = 'MalConv'
    elif 'clamav' in av:
        display_name = 'ClamAV'
    return display_name

def main():
    list_values = []
    for av in list_av:
        dict_feature_to_sha256 = {
                'file hash': set(),
                'section hash': set(),
                'section count': set(),
                'section name': set(),
                'section padding': set(),
                'debug': set(),
                'checksum': set(),
                'certificate': set(),
                'code seq': set(),
                #'section padding': set(),
                'data dist': set(),
        }
        print('='*40)
        print(av)
        av_path = DATA_PATH + av + '/'
        list_action = []
        for data_folder in os.listdir(av_path):
            if '2020' not in data_folder:
                continue
            #print(data_folder)
            feature_folder = [x for x in os.listdir(av_path + data_folder) if x.endswith('func_feature')]
            path = av_path + data_folder + '/' + feature_folder[0] + '/'
            #print(path)
            list_exe = os.listdir(path)
            #print(len(list_exe))

            for exe in list_exe:
                sha256 = exe.split('.')[0]
                #print(sha256)
                list_action = [x.replace('CP', 'C1').replace('RS', 'RC') for x in exe.split('.') if len(x) == 2]
                list_action.sort()
                for action in list_action:
                    dict_feature_to_sha256[dict_action_to_feature[action]].add(sha256)

        dict_larger = {}
        total_amount = 0
        for k in dict_feature_to_sha256.keys():
            total_amount += len(dict_feature_to_sha256[k])
        for k in dict_feature_to_sha256.keys():
            dict_larger[k] = len(dict_feature_to_sha256[k])/total_amount * 100
        listofTuples = dict_larger.items()
        print(dict_larger)
        list_values.append(list(dict_larger.values()))

        #y = []
        #label = []
        #for elem in listofTuples :
        #    print(elem[0], elem[1] )
        #    y.append(elem[1])
        #    label.append(elem[0])
        #x = np.arange(len(y))
        #fig, ax = plt.subplots()
        #plt.ylabel('percentage %', fontsize=14)

        #plt.bar(x, y, color='silver')
        #plt.xticks(x, label, rotation=90, fontsize=14)
        #fig.subplots_adjust(bottom=0.5)
        ##plt.show()
        #plt.savefig('/home/wei/feature_%s.pdf' %get_display_name(av).lower())
    value_array = None
    features = list(dict_larger.keys())
    print(features)
    print(list_values)
    plot_feature(features, list_values)

def heatmap(data, row_labels, col_labels, ax=None,
            cbar_kw={}, cbarlabel="", **kwargs):
    """
    Create a heatmap from a numpy array and two lists of labels.

    Parameters
    ----------
    data
        A 2D numpy array of shape (N, M).
    row_labels
        A list or array of length N with the labels for the rows.
    col_labels
        A list or array of length M with the labels for the columns.
    ax
        A `matplotlib.axes.Axes` instance to which the heatmap is plotted.  If
        not provided, use current axes or create a new one.  Optional.
    cbar_kw
        A dictionary with arguments to `matplotlib.Figure.colorbar`.  Optional.
    cbarlabel
        The label for the colorbar.  Optional.
    **kwargs
        All other arguments are forwarded to `imshow`.
    """

    if not ax:
        ax = plt.gca()

    # Plot the heatmap
    im = ax.imshow(data, **kwargs)

    # Create colorbar
    cbar = ax.figure.colorbar(im, ax=ax, **cbar_kw)
    cbar.ax.set_ylabel(cbarlabel, rotation=-90, va="bottom")

    # We want to show all ticks...
    ax.set_xticks(np.arange(data.shape[1]))
    ax.set_yticks(np.arange(data.shape[0]))
    # ... and label them with the respective list entries.
    ax.set_xticklabels(col_labels)
    ax.set_yticklabels(row_labels)

    # Let the horizontal axes labeling appear on top.
    ax.tick_params(top=True, bottom=False,
                   labeltop=True, labelbottom=False)

    # Rotate the tick labels and set their alignment.
    plt.setp(ax.get_xticklabels(), rotation=-30, ha="right",
             rotation_mode="anchor")

    # Turn spines off and create white grid.
    for edge, spine in ax.spines.items():
        spine.set_visible(False)

    ax.set_xticks(np.arange(data.shape[1]+1)-.5, minor=True)
    ax.set_yticks(np.arange(data.shape[0]+1)-.5, minor=True)
    ax.grid(which="minor", color="w", linestyle='-', linewidth=0)
    ax.tick_params(which="minor", bottom=False, left=False)

    return im

def annotate_heatmap(im, data=None, valfmt="{x:.2f}",
                     textcolors=["black", "white"],
                     threshold=None, **textkw):
    """
    A function to annotate a heatmap.

    Parameters
    ----------
    im
        The AxesImage to be labeled.
    data
        Data used to annotate.  If None, the image's data is used.  Optional.
    valfmt
        The format of the annotations inside the heatmap.  This should either
        use the string format method, e.g. "$ {x:.2f}", or be a
        `matplotlib.ticker.Formatter`.  Optional.
    textcolors
        A list or array of two color specifications.  The first is used for
        values below a threshold, the second for those above.  Optional.
    threshold
        Value in data units according to which the colors from textcolors are
        applied.  If None (the default) uses the middle of the colormap as
        separation.  Optional.
    **kwargs
        All other arguments are forwarded to each call to `text` used to create
        the text labels.
    """

    if not isinstance(data, (list, np.ndarray)):
        data = im.get_array()

    # Normalize the threshold to the images color range.
    if threshold is not None:
        threshold = im.norm(threshold)
    else:
        threshold = im.norm(data.max())/2.

    # Set default alignment to center, but allow it to be
    # overwritten by textkw.
    kw = dict(horizontalalignment="center",
              verticalalignment="center")
    kw.update(textkw)

    # Get the formatter in case a string is supplied
    if isinstance(valfmt, str):
        valfmt = matplotlib.ticker.StrMethodFormatter(valfmt)

    # Loop over the data and create a `Text` for each "pixel".
    # Change the text's color depending on the data.
    texts = []
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            #if i != j:
            kw.update(color=textcolors[int(im.norm(data[i, j]) > threshold)])
            text = im.axes.text(j, i, valfmt(data[i, j], None), **kw)
            texts.append(text)
            #else:
            #    kw.update(color=textcolors[int(im.norm(data[i, j]) > threshold)])
            #    text = im.axes.text(j, i, "-", **kw)
            #    texts.append(text)

    return texts

def plot_feature(features, list_values):
    #features = ["file hash","section hash", "section count", "section name", "section padding", "debug", "checksum", "certificate", "code seq", "data dist"]
    avs = ["EMBER","ClamAV", "AV1", "AV2", "AV3", "AV4"]
    
    value_array = np.array(list_values)#[[0, 1.93, 1.28, 2.78, 10.49, 9.42, 1],
                        #[0, 0, 3.7, 5.93, 5.93, 9.63,1],
                        #[0.36, 9.49, 0, 11.31, 4.74, 8.76,1],
                        #[1.45, 5.22, 4.35, 0, 10.72, 14.49,1],
                        #[4.08, 7.43, 16.55, 11.51, 0, 13.19,1],
                        #[0, 4.85, 1.32, 7.05, 8.81, 0,1]])
    
    print(features)
    print(value_array)
    fig, ax = plt.subplots()
    
    im = heatmap(value_array, avs, features, ax=ax,
                       cmap="YlOrBr")
    texts = annotate_heatmap(im, valfmt="{x:.2f} %")
    
    fig.tight_layout()
    fig.set_size_inches(10, 5.5)
    fig.subplots_adjust(top=0.85)
    plt.show()

if __name__ == '__main__':
    main()
