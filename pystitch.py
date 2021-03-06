from PIL import Image, ImageDraw
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.patches as mpatches
import PySimpleGUI as sg
import os.path
import io

def convert_img(pallette, filename):
    with Image.open(filename) as im:
        newarr = np.zeros((im.width,im.height,3))
        cols = im.getcolors(im.size[0]*im.size[1])
        cols = [c[1] for c in cols]
        cols = [c[:3] for c in cols]
        for x in range(im.width):
            for y in range(im.height):
                pixel = im.getpixel((x,y))
                if len(pixel) < 4:
                    pixel = (pixel[0],pixel[1],pixel[2],255)
                if pixel[3] == 0:
                    pixel = (255,255,255,255)
                changed = closest(pallette,pixel[0:3])
                newarr[x][y] = changed[0]
                changed = (changed[0][0],changed[0][1],changed[0][2],255)
                im.putpixel((x,y),changed)
        return im

def closest(pallette, inp):
    colors = np.array(pallette)
    inp = np.array(inp)
    distances = np.sqrt(np.sum((colors-inp)**2, axis=1))
    sind = np.where(distances==np.amin(distances))
    sdist = colors[sind]
    return sdist

def get_chart():
    with open("convert.txt", 'r') as f:
        dmc,names,rgb,hex = [],[],[],[]
        for l in f:
            temp = str.split(l,'\t')
            dmc.append(temp[1])
            names.append(temp[2])
            rgb.append((int(temp[3]),int(temp[4]),int(temp[5])))
            hex.append(str.rsplit(temp[6])[0])
        rgb = np.array(rgb)
    return dmc,names,rgb,hex

def main():
    file_list_column = [
        [
            sg.Text("Image Folder"),
            sg.In(size=(25,1), enable_events=True, key="-FOLDER-"),
            sg.FolderBrowse(),
        ],
        [
            sg.Listbox(
                values=[], enable_events=True, size=(40,20), key="-FILE LIST-"
            )
        ],
    ]

    image_viewer_column = [
        [sg.Text(size=(40,1), key="-TOUT-")],
        [sg.Image(key="-IMAGE-")],
        [sg.Text("Save Name")],
        [sg.Input('', enable_events=True, key='-SINPUT-')],
        [sg.Text("Grid Size")],
        [sg.Slider(orientation ='horizontal', key='-GSLIDER-', range=(1,100),enable_events=True,default_value=20)],
        [sg.Button('Preview', key='-PREVIEW-'), sg.Button('Save', key='-SAVE-'),sg.Button('Exit')]
    ]

    layout = [
        [
            sg.Column(file_list_column),
            sg.VSeperator(),
            sg.Column(image_viewer_column),
        ]
    ]

    window = sg.Window("PyStitch - CrossStitch Pattern Generator", layout)
    dmc,names,rgb,hex = get_chart()
    prevname = ''
    previewing = False
    while True:
        event, values = window.read()
        if event == "Exit" or event == sg.WIN_CLOSED:
            break
        if event == "-FOLDER-":
            folder = values["-FOLDER-"]
            try:
                file_list = os.listdir(folder)
            except:
                file_list = []

            fnames = [
                f
                for f in file_list
                if os.path.isfile(os.path.join(folder, f))
                and f.lower().endswith((".png", ".gif"))
            ]
            window["-FILE LIST-"].update(fnames)
        elif event == "-FILE LIST-":
            try:
                filename = os.path.join(
                    values["-FOLDER-"], values["-FILE LIST-"][0]
                )
                previewing = False
                image = Image.open(filename)
                image.thumbnail((400,400))
                buffer = io.BytesIO()
                image.save(buffer, format='PNG')
                data = buffer.getvalue()
                window["-IMAGE-"].update(data=data)
            except:
                pass
        elif event == "-PREVIEW-":
            try:
                previewing = True
                grid_size = int(values['-GSLIDER-'])
                filename = os.path.join(
                    values["-FOLDER-"], values["-FILE LIST-"][0]
                )
                if filename != prevname:
                    im = convert_img(rgb,filename)
                    rimg = im.resize((im.width*2,im.height*2),resample=0)
                    imgprev = grid_image(rimg, values["-FOLDER-"], grid_size, 'temp.png', True)
                else:
                    imgprev = grid_image(rimg, values["-FOLDER-"], grid_size, 'temp.png', True)
                prevname = filename
                data = imgprev.getvalue()
                window["-IMAGE-"].update(data=data)
            except:
                pass
        elif event == '-SAVE-':
            try:
                grid_size = int(values['-GSLIDER-'])
                save_name = values["-SINPUT-"]
                filename = os.path.join(
                    values["-FOLDER-"], values["-FILE LIST-"][0]
                )
                imgprev = grid_image(rimg, values["-FOLDER-"], grid_size, save_name, False)
                break
            except:
                pass
        elif event == '-GSLIDER-':
            try:
                if previewing:
                    grid_size = int(values['-GSLIDER-'])
                    imgprev = grid_image(rimg, values["-FOLDER-"], grid_size, 'temp.png', True)
                    data = imgprev.getvalue()
                    window["-IMAGE-"].update(data=data)
            except:
                pass

    window.close()


def grid_image(imgdata, savedir, grid_size, save_name, preview):
    dmc,names,rgb,hex = get_chart()
    rimg = imgdata.copy()
    # Draw some lines
    draw = ImageDraw.Draw(rimg)
    y_start = 0
    y_end = rimg.height
    step_size = int(grid_size)

    for x in range(0, rimg.width, step_size):
        line = ((x, y_start), (x, y_end))
        draw.line(line, fill=(220,220,220))

    x_start = 0
    x_end = rimg.width

    for y in range(0, rimg.height, step_size):
        line = ((x_start, y), (x_end, y))
        draw.line(line, fill=(220,220,220))

    cols = rimg.getcolors()
    legenditems = []
    for c in cols:
        search = [c[1][0],c[1][1],c[1][2]]
        if search == [220,220,220] or search == [255,255,255]:
            continue
        loc = rgb.tolist().index(search)
        legenditems.append((hex[loc],dmc[loc],names[loc]))
    img = rimg
    fig = plt.figure()
    imgplot = plt.imshow(img)
    ax = plt.gca()
    ax.axes.xaxis.set_visible(False)
    ax.axes.yaxis.set_visible(False)
    patches = [ mpatches.Patch(color=legenditems[i][0], label="{d} {t}".format(d=legenditems[i][1],t=legenditems[i][2])) for i in range(len(legenditems)) ]
    plt.legend(handles=patches, bbox_to_anchor=(1.05,1), loc=2, borderaxespad=0. )
    img_buf = io.BytesIO()
    if preview:
        plt.savefig(img_buf, bbox_inches='tight',format='png')
        plt.close()
        return img_buf
    else:
        plt.savefig(savedir + '/' + save_name, bbox_inches='tight')
        plt.close()


if __name__ == '__main__':
    main()
